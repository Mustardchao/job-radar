#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
JobRadar - 招聘岗位监控爬虫
自动抓取招聘网站岗位信息，智能筛选后推送到飞书
"""

import os
import re
import json
import yaml
import time
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup

# ============== 配置加载 ==============

def load_config() -> dict:
    """加载配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

# ============== Cookie 配置 ==============

def get_liepin_cookie() -> Optional[str]:
    """获取猎聘网 Cookie"""
    # 优先从环境变量获取（GitHub Secrets）
    cookie = os.environ.get('LIEPIN_COOKIE', '')
    if cookie:
        return cookie
    
    # 其次从配置文件获取（本地测试用）
    try:
        config = load_config()
        cookie = config.get('liepin_cookie', '')
        if cookie:
            return cookie
    except:
        pass
    
    return None

def get_headers(site: str = 'liepin') -> dict:
    """获取请求头"""
    base_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    # 添加 Cookie
    if site == 'liepin':
        cookie = get_liepin_cookie()
        if cookie:
            base_headers['Cookie'] = cookie
            base_headers['Referer'] = 'https://www.liepin.com/'
    
    return base_headers

# ============== 数据去重 ==============

class Deduplication:
    """岗位去重管理器"""
    
    def __init__(self, cache_file: str = 'job_cache.json', ttl_hours: int = 24):
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

# ============== 爬虫模块 ==============

class JobCrawler:
    """招聘网站爬虫"""
    
    def __init__(self, config: dict):
        self.config = config
        self.session = requests.Session()
        self.dedup = Deduplication()
    
    def crawl_liepin(self, keyword: str, city: str) -> List[dict]:
        """爬取猎聘网"""
        jobs = []
        headers = get_headers('liepin')
        
        # 猎聘网搜索 URL
        url = 'https://www.liepin.com/zhaopin/'
        params = {
            'key': keyword,
            'city': self._get_city_code(city),
            'salary': f'{self.config["salary_min"]}-{self.config["salary_max"]}',
        }
        
        try:
            response = self.session.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            
            # 检查是否需要登录
            if '登录' in response.text or 'login' in response.text.lower():
                print(f'⚠️  猎聘网需要登录 (keyword={keyword}, city={city})')
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 解析岗位列表（根据实际 HTML 结构调整）
            job_cards = soup.find_all('div', class_='job-card') or soup.find_all('li', class_='job-item')
            
            for card in job_cards[:20]:  # 每个关键词最多 20 个
                try:
                    job = self._parse_liepin_job(card, keyword, city)
                    if job:
                        jobs.append(job)
                except Exception as e:
                    continue
            
            print(f'✅ 猎聘网：{keyword} @ {city} → {len(jobs)} 个岗位')
            
        except requests.exceptions.RequestException as e:
            print(f'❌ 猎聘网请求失败：{keyword} @ {city} - {str(e)}')
        
        return jobs
    
    def _parse_liepin_job(self, card, keyword: str, city: str) -> Optional[dict]:
        """解析猎聘网岗位卡片"""
        try:
            title_elem = card.find('a', class_='title') or card.find('div', class_='job-title')
            title = title_elem.get_text(strip=True) if title_elem else ''
            
            salary_elem = card.find('span', class_='salary') or card.find('div', class_='job-salary')
            salary = salary_elem.get_text(strip=True) if salary_elem else '面议'
            
            company_elem = card.find('a', class_='company') or card.find('div', class_='company-name')
            company = company_elem.get_text(strip=True) if company_elem else ''
            
            location_elem = card.find('span', class_='location') or card.find('div', class_='job-location')
            location = location_elem.get_text(strip=True) if location_elem else city
            
            # 生成唯一 ID
            job_id = hashlib.md5(f'{title}_{company}_{city}'.encode()).hexdigest()
            
            return {
                'id': job_id,
                'title': title,
                'salary': salary,
                'company': company,
                'location': location,
                'source': '猎聘网',
                'keyword': keyword,
                'publish_time': datetime.now().strftime('%Y-%m-%d'),
                'url': title_elem.get('href', '') if title_elem else ''
            }
        except Exception as e:
            return None
    
    def _get_city_code(self, city: str) -> str:
        """获取城市代码"""
        city_codes = {
            '北京': '010',
            '上海': '020',
            '深圳': '090',
            '广州': '080',
            '杭州': '060'
        }
        return city_codes.get(city, '010')
    
    def crawl_zhaopin(self, keyword: str, city: str) -> List[dict]:
        """爬取智联招聘"""
        jobs = []
        headers = get_headers('zhaopin')
        
        url = 'https://sou.zhaopin.com/'
        params = {
            'jl': self._get_zhaopin_city_code(city),
            'kw': keyword,
            'sl': f'{self.config["salary_min"]*1000},{self.config["salary_max"]*1000}'
        }
        
        try:
            response = self.session.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 解析岗位（根据实际 HTML 结构调整）
            job_cards = soup.find_all('div', class_='joblist-box__item')
            
            for card in job_cards[:20]:
                try:
                    job = self._parse_zhaopin_job(card, keyword, city)
                    if job:
                        jobs.append(job)
                except:
                    continue
            
            print(f'✅ 智联招聘：{keyword} @ {city} → {len(jobs)} 个岗位')
            
        except Exception as e:
            print(f'❌ 智联招聘请求失败：{keyword} @ {city} - {str(e)}')
        
        return jobs
    
    def _parse_zhaopin_job(self, card, keyword: str, city: str) -> Optional[dict]:
        """解析智联招聘岗位"""
        try:
            title = card.find('a', class_='position-head').get_text(strip=True) if card.find('a', class_='position-head') else ''
            salary = card.find('span', class_='position-head__salary').get_text(strip=True) if card.find('span', class_='position-head__salary') else '面议'
            company = card.find('a', class_='company-name').get_text(strip=True) if card.find('a', class_='company-name') else ''
            
            job_id = hashlib.md5(f'{title}_{company}_{city}'.encode()).hexdigest()
            
            return {
                'id': job_id,
                'title': title,
                'salary': salary,
                'company': company,
                'location': city,
                'source': '智联招聘',
                'keyword': keyword,
                'publish_time': datetime.now().strftime('%Y-%m-%d'),
                'url': ''
            }
        except:
            return None
    
    def _get_zhaopin_city_code(self, city: str) -> str:
        """获取智联招聘城市代码"""
        city_codes = {
            '北京': '530',
            '上海': '530',
            '深圳': '760',
            '广州': '760',
            '杭州': '650'
        }
        return city_codes.get(city, '530')
    
    def crawl_51job(self, keyword: str, city: str) -> List[dict]:
        """爬取前程无忧"""
        # 前程无忧反爬较严，暂时返回空
        print(f'⏭️  前程无忧跳过：{keyword} @ {city}')
        return []
    
    def crawl_all(self) -> Dict[str, List[dict]]:
        """爬取所有网站和城市"""
        all_jobs = {}
        
        for keyword in self.config['keywords']:
            for city in self.config['cities']:
                # 猎聘网
                liepin_jobs = self.crawl_liepin(keyword, city)
                key = f'{city}_{keyword}'
                all_jobs[key] = liepin_jobs
                
                # 智联招聘
                zhaopin_jobs = self.crawl_zhaopin(keyword, city)
                all_jobs[key].extend(zhaopin_jobs)
                
                # 前程无忧
                job51_jobs = self.crawl_51job(keyword, city)
                all_jobs[key].extend(job51_jobs)
                
                # 去重
                all_jobs[key] = self.dedup.get_new_jobs(all_jobs[key])
                
                # 避免请求过快
                time.sleep(1)
        
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
                    "content": f"**{job['title']}**\n💰 {job['salary']} | 🏢 {job['company']}\n📌 {job['source']} | 🔍 {job['keyword']}",
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
    print(f'🚀 JobRadar 启动时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    
    # 加载配置
    config = load_config()
    print(f'📋 配置加载完成：{len(config["keywords"])} 个关键词，{len(config["cities"])} 个城市')
    
    # 检查 Cookie
    cookie = get_liepin_cookie()
    if cookie:
        print('✅ 猎聘网 Cookie 已配置')
    else:
        print('⚠️  猎聘网 Cookie 未配置，可能无法获取数据')
    
    # 获取飞书 Webhook
    webhook_url = os.environ.get('FEISHU_WEBHOOK_URL', '')
    if not webhook_url:
        print('❌ 飞书 Webhook 未配置')
        return
    
    # 开始爬取
    crawler = JobCrawler(config)
    jobs = crawler.crawl_all()
    
    # 推送飞书
    send_to_feishu(jobs, webhook_url)
    
    print(f'🎉 JobRadar 完成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

if __name__ == '__main__':
    main()
