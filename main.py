#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JobRadar - 招聘岗位监控主程序
抓取智联招聘、前程无忧、猎聘网的 AI 相关岗位
"""

import requests
from bs4 import BeautifulSoup
import json
import yaml
import re
from datetime import datetime
from typing import List, Dict
import hashlib


class JobRadar:
    def __init__(self, config_path: str = "config.yaml"):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        
        self.jobs_cache = self.load_cache()
    
    def load_cache(self) -> set:
        """加载去重缓存"""
        try:
            with open('jobs_cache.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                return set(data.get('job_ids', []))
        except:
            return set()
    
    def save_cache(self):
        """保存去重缓存"""
        with open('jobs_cache.json', 'w', encoding='utf-8') as f:
            json.dump({
                'updated_at': datetime.now().isoformat(),
                'job_ids': list(self.jobs_cache)
            }, f, ensure_ascii=False, indent=2)
    
    def generate_job_id(self, job: Dict) -> str:
        """生成岗位唯一 ID"""
        key = f"{job['title']}_{job['company']}_{job['salary']}"
        return hashlib.md5(key.encode('utf-8')).hexdigest()
    
    def is_duplicate(self, job: Dict) -> bool:
        """检查是否重复"""
        job_id = self.generate_job_id(job)
        return job_id in self.jobs_cache
    
    def add_to_cache(self, job: Dict):
        """添加到缓存"""
        job_id = self.generate_job_id(job)
        self.jobs_cache.add(job_id)
    
    def filter_by_salary(self, salary_str: str) -> bool:
        """筛选薪资范围"""
        min_salary = self.config['salary']['min']
        max_salary = self.config['salary']['max']
        
        # 提取薪资数字 (处理 15k-40k, 15-40k, 15k-40 等格式)
        match = re.search(r'(\d+)k?[-~至](\d+)k?', salary_str)
        if match:
            low = int(match.group(1))
            high = int(match.group(2))
            # 岗位薪资范围与目标范围有交集即可
            return low <= max_salary and high >= min_salary
        
        # 处理面议等情况
        if '面议' in salary_str:
            return True
        
        return False
    
    def filter_by_city(self, location: str) -> bool:
        """筛选城市"""
        cities = self.config['cities']
        return any(city in location for city in cities)
    
    def filter_by_keywords(self, title: str, requirements: str) -> bool:
        """筛选关键词"""
        keywords = self.config['keywords']
        text = f"{title} {requirements}".lower()
        return any(kw.lower() in text for kw in keywords)
    
    def crawl_zhipin(self) -> List[Dict]:
        """抓取智联招聘"""
        jobs = []
        print("📌 抓取智联招聘...")
        
        # 智联招聘搜索 URL (需要根据实际调整)
        base_url = "https://sou.zhaopin.com/"
        
        for keyword in self.config['keywords'][:3]:  # 限制关键词数量避免被封
            try:
                params = {
                    'jl': '530,653,763,538,622',  # 北京上海深圳广州杭州
                    'kw': keyword,
                    'sl': f"{self.config['salary']['min']},{self.config['salary']['max']}",
                }
                
                response = requests.get(base_url, params=params, headers=self.headers, timeout=10)
                response.encoding = 'utf-8'
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 解析岗位列表 (需要根据实际 HTML 结构调整)
                    job_cards = soup.select('.joblist-box__item')
                    
                    for card in job_cards[:10]:  # 每个关键词最多 10 个
                        try:
                            title_elem = card.select_one('.position-head__position-name a')
                            company_elem = card.select_one('.company-name__company-name a')
                            salary_elem = card.select_one('.position-detail__position-income')
                            location_elem = card.select_one('.position-detail__position-address')
                            
                            if title_elem and company_elem:
                                job = {
                                    'title': title_elem.get_text(strip=True),
                                    'company': company_elem.get_text(strip=True),
                                    'salary': salary_elem.get_text(strip=True) if salary_elem else '面议',
                                    'location': location_elem.get_text(strip=True) if location_elem else '',
                                    'requirements': '',
                                    'url': title_elem.get('href', ''),
                                    'source': '智联招聘',
                                    'publish_time': datetime.now().strftime('%Y-%m-%d')
                                }
                                
                                # 筛选
                                if self.filter_by_city(job['location']) and \
                                   self.filter_by_salary(job['salary']) and \
                                   not self.is_duplicate(job):
                                    jobs.append(job)
                                    self.add_to_cache(job)
                                    
                        except Exception as e:
                            print(f"  解析岗位失败：{e}")
                
            except Exception as e:
                print(f"  抓取失败：{e}")
            
            import time
            time.sleep(2)  # 延迟避免被封
        
        return jobs
    
    def crawl_51job(self) -> List[Dict]:
        """抓取前程无忧"""
        jobs = []
        print("📌 抓取前程无忧...")
        
        # 前程无忧搜索 URL
        base_url = "https://search.51job.com/"
        
        for keyword in self.config['keywords'][:3]:
            try:
                params = {
                    'keyword': keyword,
                    'searchType': '2',
                    'area': '010200,020200,030200,040200,060200',  # 城市代码
                    'salary': f"{self.config['salary']['min']},{self.config['salary']['max']}",
                }
                
                response = requests.get(base_url, params=params, headers=self.headers, timeout=10)
                response.encoding = 'utf-8'
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 解析岗位列表
                    job_cards = soup.select('.job-item')
                    
                    for card in job_cards[:10]:
                        try:
                            title_elem = card.select_one('.j-name a')
                            company_elem = card.select_one('.company-name a')
                            salary_elem = card.select_one('.salary')
                            location_elem = card.select_one('.location')
                            
                            if title_elem:
                                job = {
                                    'title': title_elem.get_text(strip=True),
                                    'company': company_elem.get_text(strip=True) if company_elem else '',
                                    'salary': salary_elem.get_text(strip=True) if salary_elem else '面议',
                                    'location': location_elem.get_text(strip=True) if location_elem else '',
                                    'requirements': '',
                                    'url': title_elem.get('href', ''),
                                    'source': '前程无忧',
                                    'publish_time': datetime.now().strftime('%Y-%m-%d')
                                }
                                
                                if self.filter_by_city(job['location']) and \
                                   self.filter_by_salary(job['salary']) and \
                                   not self.is_duplicate(job):
                                    jobs.append(job)
                                    self.add_to_cache(job)
                                    
                        except Exception as e:
                            print(f"  解析岗位失败：{e}")
                
            except Exception as e:
                print(f"  抓取失败：{e}")
            
            import time
            time.sleep(2)
        
        return jobs
    
    def crawl_liepin(self) -> List[Dict]:
        """抓取猎聘网"""
        jobs = []
        print("📌 抓取猎聘网...")
        
        # 猎聘网搜索 URL
        base_url = "https://www.liepin.com/zhaopin/"
        
        for keyword in self.config['keywords'][:3]:
            try:
                params = {
                    'key': keyword,
                    'city': '010,020,030,040,060',  # 城市
                    'salary': f"{self.config['salary']['min']}-{self.config['salary']['max']}",
                }
                
                response = requests.get(base_url, params=params, headers=self.headers, timeout=10)
                response.encoding = 'utf-8'
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 解析岗位列表
                    job_cards = soup.select('.job-card')
                    
                    for card in job_cards[:10]:
                        try:
                            title_elem = card.select_one('.job-title a')
                            company_elem = card.select_one('.company-name')
                            salary_elem = card.select_one('.salary')
                            location_elem = card.select_one('.location')
                            
                            if title_elem:
                                job = {
                                    'title': title_elem.get_text(strip=True),
                                    'company': company_elem.get_text(strip=True) if company_elem else '',
                                    'salary': salary_elem.get_text(strip=True) if salary_elem else '面议',
                                    'location': location_elem.get_text(strip=True) if location_elem else '',
                                    'requirements': '',
                                    'url': title_elem.get('href', ''),
                                    'source': '猎聘网',
                                    'publish_time': datetime.now().strftime('%Y-%m-%d')
                                }
                                
                                if self.filter_by_city(job['location']) and \
                                   self.filter_by_salary(job['salary']) and \
                                   not self.is_duplicate(job):
                                    jobs.append(job)
                                    self.add_to_cache(job)
                                    
                        except Exception as e:
                            print(f"  解析岗位失败：{e}")
                
            except Exception as e:
                print(f"  抓取失败：{e}")
            
            import time
            time.sleep(2)
        
        return jobs
    
    def crawl_all(self) -> List[Dict]:
        """抓取所有网站"""
        all_jobs = []
        
        all_jobs.extend(self.crawl_zhipin())
        all_jobs.extend(self.crawl_51job())
        all_jobs.extend(self.crawl_liepin())
        
        # 保存缓存
        self.save_cache()
        
        print(f"\n✅ 共抓取 {len(all_jobs)} 个新岗位")
        return all_jobs
    
    def format_message(self, jobs: List[Dict]) -> str:
        """格式化飞书消息"""
        if not jobs:
            return "😴 今天没有新的匹配岗位哦~"
        
        # 按城市分组
        by_city = {}
        for job in jobs:
            city = job['location'].split()[0] if job['location'] else '其他'
            if city not in by_city:
                by_city[city] = []
            by_city[city].append(job)
        
        # 构建消息
        lines = [f"🔍 **JobRadar 岗位监控** - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"]
        lines.append(f"今日新增 **{len(jobs)}** 个匹配岗位\n")
        lines.append("---\n")
        
        for city, city_jobs in sorted(by_city.items()):
            lines.append(f"📍 **{city}** ({len(city_jobs)}个)\n")
            
            for i, job in enumerate(city_jobs[:5], 1):  # 每个城市最多 5 个
                lines.append(f"{i}. **{job['title']}**")
                lines.append(f"   💰 {job['salary']} | 🏢 {job['company']}")
                lines.append(f"   🔗 {job['url']}\n")
            
            if len(city_jobs) > 5:
                lines.append(f"   ... 还有 {len(city_jobs) - 5} 个岗位\n")
            
            lines.append("\n")
        
        lines.append("---\n")
        lines.append(f"数据来源：智联招聘 | 前程无忧 | 猎聘网")
        
        return "\n".join(lines)


def main():
    radar = JobRadar()
    jobs = radar.crawl_all()
    
    if jobs:
        # 发送飞书消息
        from send_feishu import send_to_feishu
        message = radar.format_message(jobs)
        send_to_feishu(message)
        print("📤 消息已发送")
    else:
        print("😴 没有新岗位")


if __name__ == "__main__":
    main()
