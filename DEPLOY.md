# JobRadar 部署指南

## 📦 项目结构

```
job-radar/
├── main.py              # 主程序
├── config.yaml          # 配置文件
├── send_feishu.py       # 飞书推送
├── requirements.txt     # 依赖
└── .github/workflows/
    └── job_crawler.yml  # GitHub Actions
```

---

## 🚀 部署步骤

### 1. Fork 项目

```bash
# 将项目 fork 到你的 GitHub 账号
github.com/Mustardchao/job-radar
```

### 2. 配置 GitHub Secrets

进入你的 fork 仓库 → Settings → Secrets and variables → Actions

添加以下 Secret:
- **FEISHU_WEBHOOK_URL**: 飞书机器人 Webhook URL

### 3. 修改配置 (可选)

编辑 `config.yaml`:
- 修改关键词
- 修改城市
- 修改薪资范围
- 修改推送时间 (cron 表达式)

### 4. 启用 GitHub Actions

- 进入 Actions 标签页
- 点击 "I understand my workflows, go ahead and enable them"
- 手动触发一次测试运行

### 5. 验证推送

- 检查飞书是否收到消息
- 查看 Actions 运行日志

---

## ⚙️ 配置说明

### 关键词配置

```yaml
keywords:
  - AI Agent
  - Python
  - 大模型
  - AI
  - 人工智能
  - LLM
  - Agent
```

### 城市配置

```yaml
cities:
  - 北京
  - 上海
  - 深圳
  - 广州
  - 杭州
```

### 薪资配置

```yaml
salary:
  min: 15  # 最低 15k
  max: 40  # 最高 40k
```

### 推送时间

```yaml
push:
  schedule: "0 1 * * *"  # UTC 时间 1:00 = 北京时间 9:00
```

---

## 🔧 本地测试

```bash
# 安装依赖
pip install -r requirements.txt

# 设置环境变量
export FEISHU_WEBHOOK_URL="你的飞书 webhook"

# 运行
python main.py
```

---

## ⚠️ 注意事项

1. **反爬策略**: 招聘网站有反爬，已添加延迟，但仍可能被封 IP
2. **HTML 结构变化**: 网站改版后需要更新选择器
3. **去重逻辑**: 基于岗位标题 + 公司 + 薪资，24 小时内不重复
4. **推送频率**: 建议每天 1 次，避免骚扰

---

## 📊 后续优化

- [ ] 添加岗位要求详情抓取
- [ ] 支持更多招聘网站
- [ ] 添加岗位趋势分析
- [ ] 支持微信/邮件推送
- [ ] 添加简历匹配度评分

---

## 🐛 常见问题

**Q: 抓取不到数据？**
A: 检查网站 HTML 结构是否变化，更新 BeautifulSoup 选择器

**Q: 飞书消息发送失败？**
A: 检查 FEISHU_WEBHOOK_URL 是否正确配置

**Q: 重复推送？**
A: 检查 jobs_cache.json 是否正常保存

---

*有问题随时提 Issue!* 🐈
