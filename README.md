# JobRadar 🎯 - 招聘岗位监控 Agent

> 自动抓取智联招聘、前程无忧、猎聘网的 AI 相关岗位，每天 9:00 飞书推送

---

## 🚀 快速开始

### 1. 启用 GitHub Actions

> 💡 **Webhook 已内置**，无需配置 Secret，直接使用即可！
> 如需自定义，可在 GitHub Secrets 中添加 `FEISHU_WEBHOOK_URL` 覆盖默认值。

- 点击 **Actions** 标签页
- 点击 **"I understand my workflows, go ahead and enable them"**
- 手动触发测试：**Run workflow** → **Run workflow**

### 2. 等待推送

- 点击 **Actions** 标签页
- 点击 **"I understand my workflows, go ahead and enable them"**
- 手动触发测试：**Run workflow** → **Run workflow**

### 3. 等待推送

每天 **9:00 (北京时间)** 自动运行，飞书接收岗位消息

---

## 📋 功能特性

✅ **3 大招聘网站**: 智联招聘、前程无忧、猎聘网  
✅ **智能筛选**: 城市 + 薪资 + 关键词自动过滤  
✅ **自动去重**: 24 小时内不重复推送  
✅ **飞书推送**: 卡片格式，按城市分组展示  
✅ **定时运行**: GitHub Actions 每天自动执行  

---

## ⚙️ 配置说明

### 目标网站
- 智联招聘 (zhaopin.com)
- 前程无忧 (51job.com)
- 猎聘网 (liepin.com)

### 筛选条件

| 类型 | 配置值 |
|------|--------|
| **关键词** | AI Agent, Python, 大模型，AI, 人工智能，LLM, Agent, 自动化，爬虫 |
| **城市** | 北京，上海，深圳，广州，杭州 |
| **薪资** | 15k-40k |

### 抓取字段
- 岗位名称
- 薪资范围
- 公司名称
- 工作地点
- 发布时间
- 岗位链接
- 数据来源

### 推送设置
- **频率**: 每天 9:00 (北京时间)
- **渠道**: 飞书群机器人
- **格式**: 交互式卡片（按城市分组）

---

## 📊 消息示例

```
🔍 JobRadar 岗位监控 - 2026-03-17 09:00

今日新增 8 个匹配岗位

📍 北京 (3 个)
1. AI Agent 开发工程师
   💰 25-40k | 🏢 某科技公司
   🔗 https://...

2. Python 开发工程师
   💰 20-35k | 🏢 某互联网公司
   🔗 https://...

📍 上海 (2 个)
1. 大模型算法工程师
   💰 30-50k | 🏢 某 AI 公司
   🔗 https://...

---
数据来源：智联招聘 | 前程无忧 | 猎聘网
```

---

## 🛠️ 项目结构

```
job-radar/
├── main.py                     # 主程序 (爬虫 + 筛选 + 格式化)
├── config.yaml                 # 配置文件 (关键词/城市/薪资)
├── send_feishu.py              # 飞书推送模块
├── requirements.txt            # Python 依赖
├── README.md                   # 使用说明
├── DEPLOY.md                   # 部署指南
└── .github/workflows/
    └── job_crawler.yml         # GitHub Actions 工作流
```

---

## 🔧 本地测试

```bash
# 克隆项目
git clone https://github.com/Mustardchao/job-radar.git
cd job-radar

# 安装依赖
pip install -r requirements.txt

# 设置环境变量
export FEISHU_WEBHOOK_URL="你的飞书 webhook"

# 运行爬虫
python main.py
```

---

## 📝 自定义配置

编辑 `config.yaml` 修改筛选条件：

```yaml
# 搜索关键词
keywords:
  - AI Agent
  - Python
  - 大模型
  - AI
  - 人工智能
  - LLM
  - Agent

# 目标城市
cities:
  - 北京
  - 上海
  - 深圳
  - 广州
  - 杭州
  - 成都  # 添加新城市

# 薪资范围 (单位：k)
salary:
  min: 15
  max: 40
```

### 修改推送时间

编辑 `.github/workflows/job_crawler.yml`：

```yaml
schedule:
  - cron: "0 1 * * *"  # UTC 1:00 = 北京 9:00
```

常用时间：
- `0 1 * * *` → 每天 9:00
- `0 5 * * *` → 每天 13:00
- `0 9 * * *` → 每天 17:00
- `0 */4 * * *` → 每 4 小时

---

## ⚠️ 注意事项

1. **反爬策略**: 招聘网站有反爬机制，已添加请求延迟，但仍可能被封 IP
2. **HTML 结构**: 网站改版后需要更新 BeautifulSoup 选择器
3. **去重逻辑**: 基于岗位标题 + 公司 + 薪资，24 小时内不重复推送
4. **推送频率**: 建议每天 1 次，避免消息骚扰

---

## 🐛 常见问题

**Q: 抓取不到数据？**  
A: 检查网站 HTML 结构是否变化，更新 main.py 中的选择器

**Q: 飞书消息发送失败？**  
A: 检查 FEISHU_WEBHOOK_URL 是否正确配置到 GitHub Secrets

**Q: 重复推送？**  
A: 检查 jobs_cache.json 是否正常保存，或手动删除缓存文件

**Q: 如何添加更多城市？**  
A: 编辑 config.yaml 的 cities 列表，添加城市名称即可

---

## 📈 后续优化

- [ ] 添加岗位要求详情抓取
- [ ] 支持 BOSS 直聘、拉勾网
- [ ] 岗位趋势分析图表
- [ ] 支持微信/邮件推送
- [ ] 简历匹配度评分
- [ ] 一键投递功能

---

## 📄 License

MIT License

---

## 👤 Author

**mustarddd**  
GitHub: [@Mustardchao](https://github.com/Mustardchao)

---

*有问题欢迎提 Issue 或 Discussion!* 🐈
