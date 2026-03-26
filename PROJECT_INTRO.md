# 大宗商品地缘政治数据平台（GeoInsight）

## 一、项目概述

本项目是一个聚焦**大宗商品与地缘政治事件关联分析**的全栈数据平台，通过 OpenClaw 智能体在本地构建开发，部署于云服务器运行。平台自动采集期货行情、全球新闻和宏观经济指标，借助 AI 进行新闻情感分析和品种关联，为用户提供行情总览、多维分析、事件回测、AI 对话等一站式分析能力。

**在线地址**：`http://43.160.241.35:9180`

---

## 二、OpenClaw 与 Skills 体系

### OpenClaw 简介

OpenClaw 是本项目的核心构建工具——一个基于 gateway 架构的 AI Agent，在本地通过 TUI 终端界面交互，支持接入飞书机器人。通过安装 Skills 扩展其专业能力，覆盖从地缘分析到容器部署的完整开发链路。

**配置概览**：
- 模型：Claude Opus 4.6
- 工作区：`~/clawd`
- Gateway 端口：18789
- 飞书机器人：龙虾王

### OpenClaw 内置 Skills

以下是 OpenClaw 环境自带的能力模块，执行任务时会优先调用：

| Skill | 作用 |
|-------|------|
| **feishu-doc** | 飞书文档读写，可将项目计划、日报、需求说明、测试报告整理进飞书 |
| **feishu-drive** | 飞书云盘文件管理，适合整理项目资料、上传交付物 |
| **feishu-perm** | 飞书权限管理，项目文档分享协作时使用 |
| **feishu-wiki** | 飞书知识库导航，可直接查阅和整理 wiki 中的项目资料 |
| **coding-agent** | 处理较大的编码/重构任务，适合搭建功能、重构模块、批量修改代码 |
| **gh-issues** | GitHub issue / PR 工作流，按 issue 推进开发 |
| **github** | GitHub 日常操作，查看 PR、CI、issue、提交记录 |
| **healthcheck** | 环境/安全检查，部署后检查服务状态、机器风险、暴露面 |
| **node-connect** | OpenClaw 节点连接诊断 |
| **skill-creator** | 创建/整理/审查 skill，可为项目定制专属 skill |
| **tmux** | 控制 tmux 会话，同时运行前端、后端、数据库日志、worker 时使用 |
| **weather** | 天气查询 |

### 项目级 Skills

以下 Skills 安装在项目目录 `commodity-geopolitics/.claude/skills`，直接服务于本项目的开发和运行：

| Skill | 作用 |
|-------|------|
| **commodities-quote** | 贴近大宗商品业务，在黄金、原油、铜等品种分析时提供行情展示和品种上下文支持 |
| **docker-compose-orchestration** | 用于前后端 + PostgreSQL + Redis 的本地/部署编排，便于启动、停止、排查容器问题 |
| **e2e-testing-patterns** | 为关键流程补充 E2E 测试（行情页、新闻筛选、AI 对话、回测流程），提升系统稳定性 |
| **echarts** | 项目高度依赖图表，K 线、热力图、时间轴、地图等均直接受益，辅助图表配置和性能优化 |
| **fastapi-python** | 后端基于 FastAPI，编写 API、schema、service、异步接口更高效，对 SSE、任务调度、数据接口直接有帮助 |
| **geopolitical-driver** | 贴合"地缘政治事件影响商品"的项目主线，在事件分类、冲突区域、事件影响分析方面更有针对性 |
| **news-aggregator** | 项目包含 RSS / 新闻抓取 / 摘要模块，有助于设计新闻采集、去重、聚合流程 |
| **political-scientist-analyst** | 增强对国际政治、冲突背景、事件逻辑的理解，适合做解释层、分析文本、事件标签 |
| **react** | 前端基于 React，在组件拆分、状态管理、性能优化、页面结构方面提供支持 |
| **redis-store** | 项目 Redis 用于缓存、锁、session、任务控制，辅助设计 key 规范、TTL 策略、分布式锁 |
| **sql-toolkit** | 数据库为 PostgreSQL，在表设计、索引、查询、迁移、SQL 分析方面直接受益 |
| **tailwind-css** | 加速前端 UI 开发，做仪表盘、卡片、响应式布局、筛选栏更高效 |

### 核心 Skills 与业务 Skills

对本项目帮助最大的 7 个核心 Skills：

**fastapi-python** / **react** / **sql-toolkit** / **redis-store** / **echarts** / **news-aggregator** / **docker-compose-orchestration**

覆盖了后端开发、前端开发、数据库、缓存/锁、图表可视化、新闻采集、运行和部署。

更贴业务特色的 3 个 Skills：

**commodities-quote** / **geopolitical-driver** / **political-scientist-analyst**

它们的价值在于更懂大宗商品、更懂地缘事件、更懂政治分析背景，在处理"中东局势影响原油、避险情绪推升黄金"这类分析逻辑时发挥作用。

**一句话总结**：这些 Skills 让 OpenClaw 既熟悉项目的技术栈，也深入理解业务主题，因此在搭建 FastAPI 接口、编写 React 页面、设计数据库、管理 Redis 缓存、制作 ECharts 图表、采集新闻、分析地缘事件、部署 Docker 容器等环节中均能高效工作。

---

## 三、部署方案

### 服务器环境

- **云服务器**：腾讯云（IP: 43.160.241.35）
- **操作系统**：Linux
- **容器引擎**：Docker Compose
- **对外端口**：9180（Nginx → 前端 + API 反向代理）

### 容器编排

```yaml
services:
  postgres:     # PostgreSQL 15, 数据持久化到 pgdata 卷
  redis:        # Redis 7 Alpine, AOF 持久化, 256MB 内存限制, LRU 淘汰
  backend:      # FastAPI 应用, 依赖 postgres + redis 健康检查通过后启动
  frontend:     # Nginx 托管 Vite 构建产物, 依赖 backend 健康检查
```

### 兼容性处理

- 集成 `@vitejs/plugin-legacy` 插件，生成 ES5 降级包，兼容微信内置浏览器（Chrome 64+/Safari 12+）

---

## 四、系统架构

### 技术栈

| 层级 | 技术选型 | 说明 |
|------|---------|------|
| 前端 | React 18 + TypeScript + Vite | SPA 单页应用，Tailwind CSS 样式 |
| 可视化 | Apache ECharts | K 线图、相关性热力图、散点图等 |
| 后端 | FastAPI (Python) + async/await | 全异步 API 服务，支持 SSE 流式推送 |
| 数据库 | PostgreSQL 15 | 持久化存储行情、新闻、地缘事件、宏观数据 |
| 缓存 | Redis 7 | 实时行情缓存 + 任务分布式锁 + AI 会话存储 |
| AI 引擎 | DeepSeek (兼容 OpenAI 协议) | 新闻情感分析、市场日报生成、AI 对话 |
| 容器化 | Docker Compose | 四容器编排：postgres / redis / backend / frontend |
| 智能体 | OpenClaw | 项目构建与迭代的核心 AI Agent |

### 服务架构图

```
用户浏览器
    │
    ▼
┌─────────────────────┐
│  Nginx (frontend)   │ ← 静态资源 + API 反向代理
│  :9180 → :80        │
└────────┬────────────┘
         │ /api/v1/*
         ▼
┌─────────────────────┐     ┌──────────┐
│  FastAPI (backend)   │────▶│  Redis 7 │  实时缓存 / 分布式锁 / 会话
│  :8000              │     └──────────┘
│                     │     ┌──────────────┐
│  ┌─ APScheduler ──┐ │────▶│ PostgreSQL 15│  行情 / 新闻 / 事件
│  │  定时任务引擎   │ │     └──────────────┘
│  └────────────────┘ │
│  ┌─ AsyncTask ────┐ │     ┌──────────────┐
│  │  实时行情循环   │ │────▶│ akshare API  │  期货数据源
│  └────────────────┘ │     │ yfinance     │
│                     │     │ RSS feeds    │  新闻数据源
│  ┌─ DeepSeek LLM ─┐│     │ DeepSeek API │  AI 引擎
│  │  AI 分析引擎    ││     └──────────────┘
│  └────────────────┘ │
└─────────────────────┘
```

### 目录结构

```
commodity-geopolitics/
├── frontend/                   # React 前端
│   ├── src/
│   │   ├── pages/             # 页面组件（Dashboard, Market, News, Analysis...）
│   │   ├── lib/               # API 客户端 / 常量定义 / ECharts 配置
│   │   ├── hooks/             # 自定义 Hooks（useECharts 等）
│   │   └── layouts/           # 布局组件
│   ├── vite.config.ts         # Vite 构建配置（含 legacy 插件）
│   └── Dockerfile             # 多阶段构建 → Nginx
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── api/v1/            # API 路由（market / news / analysis / ai / backtest）
│   │   ├── services/          # 业务逻辑层
│   │   ├── models/            # SQLAlchemy ORM 模型
│   │   ├── schemas/           # Pydantic 数据校验
│   │   ├── tasks/             # 定时任务 + 实时行情循环
│   │   ├── data_sources/      # 外部数据源客户端（akshare / RSS）
│   │   └── core/              # 基础设施（缓存 / LLM / 异常处理 / 分布式锁）
│   ├── requirements.txt
│   └── Dockerfile
├── skills/                     # OpenClaw Skills（11 个）
├── .claude/skills/             # Claude Code Skills（12 个）
├── docker-compose.yml          # 开发环境编排
└── .gitignore
```

---

## 五、数据来源

### 1. 期货行情数据

平台覆盖 **20 个中国期货品种**，分四大板块：

| 板块 | 品种 |
|------|------|
| 金属 | 黄金(AU)、白银(AG)、铜(CU)、铝(AL)、镍(NI)、铁矿石(FE) |
| 能源 | 上海原油(SC)、燃料油(FU)、LPG液化气(PG) |
| 农产品 | 大豆(A)、豆粕(M)、豆油(Y)、棕榈油(P)、玉米(C)、棉花(CF)、白糖(SR)、橡胶(RU) |
| 化工 | PTA(TA)、甲醇(MA)、聚丙烯(PP) |

**数据来源与接口**：

- **新浪期货 `futures_main_sina`**（通过 akshare 调用）：主力合约历史日线数据（OHLCV + 结算价 + 持仓量），提供完整的 K 线回溯
- **东方财富 push2 批量接口**（`push2.eastmoney.com`）：盘中实时行情报价，一次请求批量获取全部 20 个品种，用于交易时段的实时更新
- **Yahoo Finance `yfinance`**：美元指数(DXY)和美联储利率(^IRX)等境外宏观指标

### 2. 新闻数据

通过 **17 个 RSS 订阅源** 全天候抓取全球大宗商品与地缘政治新闻：

- **专业财经媒体**：CNBC Commodities、FT Commodities、Investing.com
- **Google News 聚合**：按品种细分（金属、农产品、原油、黄金）、按主题细分（地缘政治、贸易战、美联储）
- **一线通讯社代理**：通过 Google News 代理聚合 Reuters、Bloomberg、WSJ、MarketWatch 等源

系统内置基于关键词权重的**相关性评分算法**，自动过滤低相关性新闻，优先保留大宗商品、地缘政治、宏观经济相关的高价值资讯。

### 3. 宏观经济指标

| 指标 | 数据源 | 说明 |
|------|--------|------|
| 美元指数 (DXY) | Yahoo Finance (DX-Y.NYB) | ICE 美元指数日线 |
| 人民币汇率 (USDCNY) | 央行中间价 (akshare) | USD/CNY 每日报价 |
| 美国10年期国债 (US10Y) | 中国债券信息网 (akshare) | 美债基准收益率 |
| 中国10年期国债 (CN10Y) | 中国债券信息网 (akshare) | 中债基准收益率 |
| 美联储利率 (FED_RATE) | Yahoo Finance (^IRX) | 13周美债收益率代理 |
| 波罗的海指数 (BDI) | akshare | 干散货运价指数 |

### 4. 地缘政治事件

系统维护地缘政治事件数据库，每个事件包含：标题、描述、事件类型、严重等级（1-5级）、起止日期，用于与价格曲线叠加分析。

---

## 六、功能模块

### 前端页面（共 13 个核心页面）

| 页面 | 路由 | 功能描述 |
|------|------|---------|
| **总览面板** | `/` | 市场行情速览，所有品种实时价格、涨跌幅、成交量一览 |
| **行情列表** | `/market` | 按板块筛选的品种列表，支持排序和详情跳转 |
| **品种详情** | `/market/:symbol` | 单品种 K 线图（OHLCV + 结算价 + 持仓量），支持缩放 |
| **新闻聚合** | `/news` | AI 分析后的新闻流，含情感标签、关联品种、重要度评级 |
| **相关性分析** | `/analysis/correlation` | 多品种价格相关性矩阵热力图 |
| **事件时间轴** | `/analysis/timeline` | 地缘事件标注叠加在价格曲线上，可视化事件与价格的时空关系 |
| **宏观对比** | `/analysis/macro` | 宏观指标与商品价格双轴对比图，支持多指标/多品种/多周期切换 |
| **价格比值** | `/analysis/ratios` | 品种间价格比值走势（如金银比、铜金比等） |
| **情绪分析** | `/analysis/sentiment` | 基于 AI 分析的市场情绪面板 |
| **波动率分析** | `/analysis/volatility` | 价格波动率历史走势 |
| **多品种对比** | `/analysis/compare` | 多品种归一化价格走势对比 |
| **事件回测** | `/backtest` | 选择历史地缘事件，回测其前后 N 天内相关品种的价格表现 |
| **AI 助手** | `/ai` | 基于 DeepSeek 的流式对话 AI，可讨论市场行情与地缘分析 |

### 后端 API（RESTful + SSE）

| 模块 | 端点 | 功能 |
|------|------|------|
| 行情 | `GET /api/v1/market/overview` | 所有品种实时行情总览 |
| | `GET /api/v1/market/kline/{symbol}` | 品种历史 K 线数据 |
| | `GET /api/v1/market/compare` | 多品种价格对比 |
| | `GET /api/v1/market/overview/stream` | SSE 实时行情推送流 |
| 新闻 | `GET /api/v1/news/` | 新闻列表（支持筛选/搜索） |
| 分析 | `GET /api/v1/analysis/correlation` | 相关性矩阵计算 |
| | `GET /api/v1/analysis/macro/comparison` | 宏观指标 vs 商品价格 |
| | `GET /api/v1/analysis/ratios` | 品种比值分析 |
| | `GET /api/v1/analysis/report/daily` | AI 生成每日市场报告 |
| 回测 | `POST /api/v1/backtest/run` | 运行事件回测 |
| | `GET /api/v1/backtest/compare` | 多事件横向对比 |
| AI | `POST /api/v1/ai/chat` | AI 对话（SSE 流式响应） |

---

## 七、数据更新机制

系统所有数据全自动更新，无需人工干预。行情数据在交易时段以 3 秒为周期通过东方财富 push2 API 批量获取全部品种实时报价，前端通过 SSE 实时推送至浏览器，用户无需刷新即可看到盘中价格变动；新闻每 15 分钟自动抓取并立即由 AI 完成分析；宏观指标每 6 小时同步一次。具体分三层：

### 第一层：实时行情循环（AsyncTask）

- **触发方式**：应用启动后立即运行，常驻后台
- **更新周期**：交易时段 **3 秒/轮**，连续失败时自动退避至 30-60 秒
- **执行逻辑**：
  1. 通过东方财富 push2 批量接口（`push2.eastmoney.com/api/qt/ulist.np/get`）一次 HTTP 请求获取全部 20 个品种的实时行情
  2. push2 失败时回退到逐品种获取（东方财富 → 新浪 → 数据库兜底）
  3. 启动时先从数据库加载历史价格写入缓存，确保 API 立即有数据可用
  4. 更新结果写入 Redis 缓存（TTL=300s），同时将实时价格写入 PostgreSQL 作为当日日线记录（更新 close/high/low 极值）
  5. 结算价通过数据库回退机制补充（push2 不返回结算价，自动查询最近一条有结算价的历史记录）
- **前端推送**：后端通过 SSE（Server-Sent Events）将最新行情实时推送至浏览器，用户无需刷新即可看到盘中价格变动

### 第二层：定时日线任务（APScheduler）

| 任务 | 执行间隔 | 功能 |
|------|---------|------|
| `fetch_market_data` | 5 分钟 | 拉取新浪日线全量数据，补充缺失日期，回填结算价 |
| `fetch_news_data` | 15 分钟 | 抓取 17 个 RSS 源新闻，去重入库 |
| `process_news_ai` | 16 分钟 | 对未分析的新闻调用 DeepSeek 做情感分析和品种关联 |
| `fetch_macro_data` | 6 小时 | 更新宏观经济指标（DXY/汇率/国债利率等） |
| `cleanup_old_news` | 12 小时 | 清理 30 天前的过期新闻及关联数据 |

### 第三层：兜底补充

- 新浪日线数据缺失今日时，自动调用东方财富实时接口补充当日 OHLCV + 结算价
- 所有定时任务通过 Redis 分布式锁防止并发重复执行

---

## 八、AI 能力集成

### 新闻智能分析

每条新闻入库后，系统自动调用 DeepSeek 模型进行：

1. **摘要生成**：100 字以内的中文摘要
2. **情感判断**：bullish（利多）/ bearish（利空）/ neutral（中性）
3. **情感评分**：0.0-1.0 连续评分
4. **品种关联**：自动识别新闻关联的商品品种代码（支持多品种）
5. **重要度评级**：1-5 级重要性打分

### AI 对话助手

基于 DeepSeek 的流式对话接口，支持：
- 市场行情问答
- 地缘政治分析讨论
- 品种走势解读
- 会话历史管理（Redis 存储）

### 每日市场报告

自动整合当日行情数据和重点新闻，AI 生成包含市场概况、重点品种分析、地缘政治影响、后市展望的结构化日报。

---

## 九、项目源码

**GitHub 仓库**：[https://github.com/hxhfuudd-ship-it/commodity-geopolitics](https://github.com/hxhfuudd-ship-it/commodity-geopolitics)

---

## 十、总结

本项目通过 OpenClaw 智能体驱动开发迭代，构建了一个从数据采集到智能分析的完整闭环系统。核心价值在于将分散的期货行情、全球新闻、宏观指标、地缘事件**四维数据**聚合到统一平台，借助 AI 能力实现自动化分析，帮助用户从**地缘政治视角**理解大宗商品价格变动的深层逻辑。
