# JobRadar - 招聘岗位监控

## 配置

### 目标网站
- 智联招聘 (zhipin.com)
- 前程无忧 (51job.com)
- 猎聘网 (liepin.com)

### 筛选条件
**关键词**: AI Agent, Python, 大模型，AI, 人工智能，LLM, Agent
**城市**: 北京，上海，深圳，广州，杭州
**薪资**: 15k-40k

### 抓取字段
- 岗位名称
- 薪资范围
- 公司名称
- 岗位要求
- 工作地点
- 发布时间
- 岗位链接

### 推送设置
- **频率**: 每天 9:00
- **渠道**: 飞书
- **格式**: 卡片消息（按城市分组）

---

## 项目结构

```
job-radar/
├── main.py              # 主程序
├── config.yaml          # 配置文件
├── spiders/
│   ├── zhipin.py        # 智联招聘
│   ├── 51job.py         # 前程无忧
│   └── liepin.py        # 猎聘网
├── send_feishu.py       # 飞书推送
├── requirements.txt     # 依赖
└── .github/workflows/
    └── job_crawler.yml  # GitHub Actions
```

---

## 待办事项

- [ ] 创建配置文件 config.yaml
- [ ] 写智联招聘爬虫
- [ ] 写前程无忧爬虫
- [ ] 写猎聘网爬虫
- [ ] 飞书推送模块（复用 TrendRadar）
- [ ] GitHub Actions 工作流
- [ ] 测试运行
- [ ] 部署上线
