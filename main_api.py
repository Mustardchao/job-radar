#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
JobRadar - 招聘岗位监控爬虫 (第三方 API 版)
使用 APISpace 招聘 API 获取岗位信息，推送到飞书
"""

import os
import json
import yaml
import time
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import requests

# ============== 配置加载 ==============

def load_config() -> dict:
    """加载配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

# ============== 第三方 API 配置 ==============

class APISpaceClient:
    """APISpace 招聘 API 客户端"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = 'https://apispace.com'
        self.session = requests.Session()
        self.session.headers.update({
            'X-APISpace-Token': api_key,
            'Content-Type': 'application/json'
        })
    
    def search_jobs(self, keyword: str, city: str, salary_min: int = 15, salary_max: int = 40, page: int = 1, page_size: int = 20) -> List[dict]:
        """
        搜索招聘岗位
        
        Args:
            keyword: 搜索关键词
            city: 城市
            salary_min: 最低薪资 (k)
            salary_max: 最高薪资 (k)
            page: 页码
            page_size: 每页数量
        
        Returns:
            岗位列表
        """
        # APISpace 招聘 API 端点（示例，实际需替换为真实 API）
        url = f'{self.base_url}/api/recruitment/jobs/search'
        
        params = {
            'keyword': keyword,
            'city': city,
            'salary_min': salary_min,
            'salary_max': salary_max,
            'page': page,
            'page_size': page_size
        }
        
        try:
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('code') == 0 or data.get('success'):
                jobs = data.get('data', {}).get('list', [])
                print(f'✅ APISpace: {keyword} @ {city} → {len(jobs)} 个岗位')
                return jobs
            else:
                print(f'❌ APISpace API 错误：{data.get("msg", "Unknown error")}')
                return []
                
        except requests.exceptions.RequestException as e:
            print(f'❌ APISpace 请求失败：{keyword} @ {city} - {str(e)}')
            return []


class JuheDataClient:
    """聚合数据招聘 API 客户端"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = 'http://v.juhe.cn'
        self.session = requests.Session()
    
    def search_jobs(self, keyword: str, city: str, page: int = 1, page_size: int = 20) -> List[dict]:
        """
        搜索招聘岗位（聚合数据）
        
        API 文档：http://v.juhe.cn/touTiao/index
        实际需替换为招聘 API
        """
        url = f'{self.base_url}/job/search'
        
        params = {
            'key': self.api_key,
            'keyword': keyword,
            'city': city,
            'page': page,
            'pagesize': page_size
        }
        
        try:
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('error_code') == 0:
                jobs = data.get('result', {}).get('data', [])
                print(f'✅ 聚合数据：{keyword} @ {city} → {len(jobs)} 个岗位')
                return jobs
            else:
                print(f'❌ 聚合数据 API 错误：{data.get("reason", "Unknown error")}')
                return []
                
        except requests.exceptions.RequestException as e:
            print(f'❌ 聚合数据请求失败：{keyword} @ {city} - {str(e)}')
            return []


# ============== 数据去重 ==============

class Deduplication:
    """岗位去重管理器"""
    
    def __init__(self, cache_file: str = 'jobs_cache.json', ttl_hours: int = 24):
        self.cache_file = cache_file
        self.ttl_seconds = ttl_hours * 3600
        self.cache = self._load_cache()
    
    def _load_cache(self) -> dict:
        """加载缓存"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_cache(self):
        """保存缓存"""
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)
    
    def _clean_expired(self):
        """清理过期数据"""
        now = time.time()
        expired_keys = [k for k, v in self.cache.items() if now - v['timestamp'] > self.ttl_seconds]
        for key in expired_keys:
            del self.cache[key]
        if expired_keys:
            self._save_cache()
    
    def is_duplicate(self, job_id: str) -> bool:
        """检查是否重复"""
        self._clean_expired()
        return job_id in self.cache
    
    def add(self, job_id: str, job_data: dict):
        """添加新岗位"""
        self.cache[job_id] = {
            'timestamp': time.time(),
            'data': job_data
        }
        self._save_cache()
    
    def get_new_jobs(self, jobs: List[dict]) -> List[dict]:
        """过滤出新岗位"""
        self._clean_expired()
        new_jobs = []
        for job in jobs:
            job_id = job.get('id', hashlib.md5(job.get('title', '').encode()).hexdigest())
            if not self.is_duplicate(job_id):
                self.add(job_id, job)
                new_jobs.append(job)
        return new_jobs


# ============== API 爬虫 ==============

class APIJobCrawler:
    """第三方 API 招聘爬虫"""
    
    def __init__(self, config: dict):
        self.config = config
        self.dedup = Deduplication()
        
        # 初始化 API 客户端
        self.apispace_key = os.environ.get('APISPACE_KEY', config.get('apispace_key', ''))
        self.juhe_key = os.environ.get('JUHE_KEY', config.get('juhe_key', ''))
        
        self.apispace_client = APISpaceClient(self.apispace_key) if self.apispace_key else None
        self.juhe_client = JuheDataClient(self.juhe_key) if self.juhe_key else None
    
    def crawl_all(self) -> Dict[str, List[dict]]:
        """爬取所有关键词和城市"""
        all_jobs = {}
        
        for keyword in self.config['keywords']:
            for city in self.config['cities']:
                jobs = []
                key = f'{city}_{keyword}'
                
                # 使用 APISpace
                if self.apispace_client:
                    apispace_jobs = self.apispace_client.search_jobs(
                        keyword=keyword,
                        city=city,
                        salary_min=self.config.get('salary_min', 15),
                        salary_max=self.config.get('salary_max', 40)
                    )
                    jobs.extend(apispace_jobs)
                
                # 使用聚合数据（备选）
                if self.juhe_client and len(jobs) == 0:
                    juhe_jobs = self.juhe_client.search_jobs(
                        keyword=keyword,
                        city=city
                    )
                    jobs.extend(juhe_jobs)
                
                # 去重
                jobs = self.dedup.get_new_jobs(jobs)
                all_jobs[key] = jobs
                
                # 避免请求过快
                time.sleep(0.5)
        
        return all_jobs


# ============== 飞书推送 ==============

def send_to_feishu(jobs_by_city: Dict[str, List[dict]], webhook_url: str):
    """发送飞书卡片消息"""
    
    # 按城市分组
    city_jobs = {}
    for key, jobs in jobs_by_city.items():
        city = key.split('_')[0]
        if city not in city_jobs:
            city_jobs[city] = []
        city_jobs[city].extend(jobs)
    
    # 构建卡片内容
    elements = []
    
    for city, jobs in city_jobs.items():
        if not jobs:
            continue
        
        # 城市标题
        elements.append({
            "tag": "div",
            "text": {
                "content": f"**📍 {city}**",
                "tag": "lark_md"
            }
        })
        
        # 岗位列表
        for job in jobs[:5]:  # 每个城市最多 5 个
            elements.append({
                "tag": "div",
                "text": {
                    "content": f"**{job['title']}**\n💰 {job.get('salary', '面议')} | 🏢 {job.get('company', '')}\n📌 {job.get('source', 'API')} | 🔍 {job.get('keyword', '')}",
                    "tag": "lark_md"
                }
            })
        
        elements.append({"tag": "hr"})
    
    if not elements:
        print('⚠️  没有新岗位可推送')
        return
    
    # 飞书卡片
    card = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": f"🔥 新岗位推荐 ({datetime.now().strftime('%m-%d')})"
                },
                "template": "blue"
            },
            "elements": elements
        }
    }
    
    # 发送请求
    headers = {'Content-Type': 'application/json'}
    response = requests.post(webhook_url, json=card, headers=headers, timeout=10)
    
    if response.status_code == 200:
        result = response.json()
        if result.get('StatusCode') == 0 or result.get('code') == 0:
            print(f'✅ 飞书推送成功！共 {sum(len(jobs) for jobs in city_jobs.values())} 个岗位')
        else:
            print(f'❌ 飞书推送失败：{result}')
    else:
        print(f'❌ 飞书请求错误：{response.status_code} - {response.text}')


# ============== 主函数 ==============

def main():
    """主函数"""
    print(f'🚀 JobRadar API 版启动时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    
    # 加载配置
    config = load_config()
    print(f'📋 配置加载完成：{len(config["keywords"])} 个关键词，{len(config["cities"])} 个城市')
    
    # 检查 API Key
    apispace_key = os.environ.get('APISPACE_KEY', config.get('apispace_key', ''))
    juhe_key = os.environ.get('JUHE_KEY', config.get('juhe_key', ''))
    
    if apispace_key:
        print('✅ APISpace API Key 已配置')
    elif juhe_key:
        print('✅ 聚合数据 API Key 已配置')
    else:
        print('⚠️  API Key 未配置，无法获取数据')
        print('请在 GitHub Secrets 中设置：APISPACE_KEY 或 JUHE_KEY')
        return
    
    # 获取飞书 Webhook
    webhook_url = os.environ.get('FEISHU_WEBHOOK_URL', '')
    if not webhook_url:
        webhook_url = 'https://open.feishu.cn/open-apis/bot/v2/hook/c93b8faf-4f7e-4b27-8bfb-4c693febe244'
        print('ℹ️ 使用内置飞书 Webhook')
    
    # 开始爬取
    crawler = APIJobCrawler(config)
    jobs = crawler.crawl_all()
    
    # 推送飞书
    send_to_feishu(jobs, webhook_url)
    
    print(f'🎉 JobRadar 完成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')


if __name__ == '__main__':
    main()
