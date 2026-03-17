#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书消息推送模块
复用 TrendRadar 的推送逻辑
"""

import requests
import json
import os


def send_to_feishu(content: str, webhook_url: str = None):
    """发送飞书消息"""
    
    # 从环境变量获取 webhook URL
    if not webhook_url:
        webhook_url = os.environ.get('FEISHU_WEBHOOK_URL', '')
    
    if not webhook_url:
        print("❌ 未配置 FEISHU_WEBHOOK_URL")
        return
    
    # 构建卡片消息
    card_content = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": "🔍 JobRadar 岗位监控"
                },
                "template": "blue"
            },
            "elements": [
                {
                    "tag": "markdown",
                    "content": content
                },
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {
                                "tag": "plain_text",
                                "content": "查看全部岗位"
                            },
                            "url": "https://github.com/Mustardchao/job-radar",
                            "type": "default"
                        }
                    ]
                }
            ]
        }
    }
    
    try:
        response = requests.post(
            webhook_url,
            json=card_content,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('StatusCode') == 0 or result.get('code') == 0:
                print("✅ 飞书消息发送成功")
            else:
                print(f"❌ 飞书消息发送失败：{result}")
        else:
            print(f"❌ HTTP 错误：{response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ 发送异常：{e}")


if __name__ == "__main__":
    # 测试
    test_content = """今日新增 **5** 个匹配岗位

📍 **北京** (3 个)
1. **AI Agent 开发工程师**
   💰 25-40k | 🏢 某科技公司
   🔗 https://example.com/job1

2. **Python 开发工程师**
   💰 20-35k | 🏢 某互联网公司
   🔗 https://example.com/job2

---
数据来源：智联招聘 | 前程无忧 | 猎聘网"""
    
    send_to_feishu(test_content)
