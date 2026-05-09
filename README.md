<div align="center">

# GeoInsight

**大宗商品地缘政治分析平台**

[![React](https://img.shields.io/badge/React-18-61dafb?logo=react&logoColor=white)](https://react.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-Python-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169e1?logo=postgresql&logoColor=white)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ed?logo=docker&logoColor=white)](https://docker.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)

[中文](#功能特性) · [English](#features)

**在线体验**：`http://43.160.241.35:9180`

</div>

---

## 架构

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
│  FastAPI (backend)   │────▶│  Redis 7 │
│  :8000              │     └──────────┘
│                     │     ┌──────────────┐
│  APScheduler 定时任务 │────▶│ PostgreSQL 15│
│  实时行情循环        │     └──────────────┘
│  DeepSeek AI 引擎    │     ┌──────────────┐
│                     │────▶│ akshare / RSS│
└─────────────────────┘     └──────────────┘
```

---

## 功能特性

| 模块 | 说明 |
|------|------|
| **行情看板** | 20 个品种实时价格、涨跌幅、成交量，K 线图（OHLCV + MA），盘中 3 秒级 SSE 推送 |
| **多维分析** | 品种对比、相关性矩阵、宏观对比、价格比值、波动率分析、AI 情绪面板 |
| **事件时间轴** | 地缘政治事件叠加价格曲线，支持事件回测（前后 N 天表现） |
| **新闻聚合** | 18 路 RSS 源全天候抓取，AI 自动摘要 + 情感判断 + 品种关联 + 重要度评级 |
| **AI 助手** | 基于 DeepSeek 的流式对话，行情问答 + 地缘分析 + 每日市场报告 |

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 18 + TypeScript + Vite + Tailwind CSS |
| 可视化 | Apache ECharts（K 线、热力图、时间轴） |
| 后端 | FastAPI (Python) + 异步 + SSE |
| 数据库 | PostgreSQL 15 |
| 缓存 | Redis 7（行情缓存 + 分布式锁 + 会话存储） |
| AI | DeepSeek（情感分析 + 市场日报 + 对话助手） |
| 部署 | Docker Compose（四容器编排） |

## 数据来源

| 数据 | 来源 |
|------|------|
| 期货日线 | 新浪期货 via akshare |
| 实时行情 | 东方财富 push2 批量接口 |
| 宏观指标 | akshare（DXY / USDCNY / US10Y / CN10Y / BDI） |
| 新闻 | 18 个 RSS 订阅源 |
| 地缘事件 | 人工维护事件数据库 |

## 数据更新

| 任务 | 周期 | 说明 |
|------|------|------|
| 实时行情 | 3 秒 | 交易时段 SSE 推送 |
| 日线补全 | 5 分钟 | 全量日线数据拉取 |
| 新闻抓取 | 15 分钟 | 18 路 RSS + 去重 |
| AI 分析 | 16 分钟 | 未分析新闻自动调用 DeepSeek |
| 宏观指标 | 6 小时 | DXY / 汇率 / 国债利率 |

## 品种覆盖

| 板块 | 品种 |
|------|------|
| 金属 | 黄金 / 白银 / 铜 / 铝 / 镍 / 铁矿石 |
| 能源 | 上海原油 / 燃料油 / LPG |
| 农产品 | 大豆 / 豆粕 / 豆油 / 棕榈油 / 玉米 / 棉花 / 白糖 / 橡胶 |
| 化工 | PTA / 甲醇 / 聚丙烯 |

## 快速开始

### 环境要求

- Docker + Docker Compose

### 部署

```bash
git clone https://github.com/hxhfuudd-ship-it/commodity-geopolitics.git
cd commodity-geopolitics
docker compose up -d
```

浏览器打开 http://localhost:9180 即可使用。

## 项目结构

```
commodity-geopolitics/
├── frontend/                # React 前端
│   ├── src/
│   │   ├── pages/          # 页面组件
│   │   ├── lib/            # API 客户端、常量、图表配置
│   │   └── hooks/          # 自定义 Hooks
│   └── Dockerfile
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── api/v1/         # API 路由
│   │   ├── services/       # 业务逻辑
│   │   ├── models/         # ORM 模型
│   │   ├── tasks/          # 定时任务 + 实时行情
│   │   ├── data_sources/   # 外部数据源
│   │   └── core/           # 缓存、大模型、分布式锁
│   └── Dockerfile
├── docker-compose.yml
└── .gitignore
```

## 规划中

- [ ] 更多品种覆盖（外盘期货）
- [ ] 用户自定义看板
- [ ] 事件影响量化模型
- [ ] 移动端适配

## 参与贡献

欢迎贡献！请先开 Issue 讨论你想做的改动。

1. Fork 本仓库
2. 创建分支 (`git checkout -b feat/amazing-feature`)
3. 提交改动
4. 推送分支
5. 发起 Pull Request

---

## Features

| Module | Details |
|--------|---------|
| **Market Dashboard** | 20 commodities with real-time prices, K-line charts (OHLCV + MA), 3-second SSE push |
| **Multi-dimensional Analysis** | Cross-commodity comparison, correlation matrix, macro overlay, price ratios, volatility, AI sentiment |
| **Event Timeline** | Geopolitical events overlaid on price curves, event backtesting (N-day impact) |
| **News Aggregation** | 18 RSS feeds around the clock, AI-powered summary + sentiment + commodity tagging + importance rating |
| **AI Assistant** | DeepSeek-powered streaming chat, market Q&A + geopolitical analysis + daily reports |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS |
| Charts | Apache ECharts (candlestick, heatmap, timeline) |
| Backend | FastAPI (Python) + async/await + SSE |
| Database | PostgreSQL 15 |
| Cache | Redis 7 (quotes cache + distributed lock + session store) |
| AI | DeepSeek (sentiment analysis + daily report + chat assistant) |
| Deploy | Docker Compose (4 containers) |

## Data Sources

| Data | Source |
|------|--------|
| Futures daily | Sina Futures via akshare |
| Real-time quotes | East Money push2 batch API |
| Macro indicators | akshare (DXY / USDCNY / US10Y / CN10Y / BDI) |
| News | 18 RSS feeds |
| Geopolitical events | Manually curated event database |

## Update Schedule

| Task | Interval | Description |
|------|----------|-------------|
| Real-time quotes | 3 seconds | SSE push during trading hours |
| Daily OHLCV | 5 minutes | Full daily data pull |
| News crawl | 15 minutes | 18 RSS feeds + deduplication |
| AI analysis | 16 minutes | Auto-analyze unprocessed news via DeepSeek |
| Macro indicators | 6 hours | DXY / FX rates / bond yields |

## Commodities Covered

| Sector | Commodities |
|--------|-------------|
| Metals | Gold / Silver / Copper / Aluminum / Nickel / Iron Ore |
| Energy | Shanghai Crude / Fuel Oil / LPG |
| Agriculture | Soybean / Soybean Meal / Soybean Oil / Palm Oil / Corn / Cotton / Sugar / Rubber |
| Chemicals | PTA / Methanol / Polypropylene |

## Getting Started

### Prerequisites

- Docker + Docker Compose

### Deploy

```bash
git clone https://github.com/hxhfuudd-ship-it/commodity-geopolitics.git
cd commodity-geopolitics
docker compose up -d
```

Open http://localhost:9180 in your browser.

## Project Structure

```
commodity-geopolitics/
├── frontend/                # React frontend
│   ├── src/
│   │   ├── pages/          # Page components
│   │   ├── lib/            # API client, constants, chart config
│   │   └── hooks/          # Custom hooks
│   └── Dockerfile
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/v1/         # API routes
│   │   ├── services/       # Business logic
│   │   ├── models/         # ORM models
│   │   ├── tasks/          # Scheduled tasks + real-time quotes
│   │   ├── data_sources/   # External data sources
│   │   └── core/           # Cache, LLM, distributed lock
│   └── Dockerfile
├── docker-compose.yml
└── .gitignore
```

## Roadmap

- [ ] More commodities (international futures)
- [ ] Custom user dashboards
- [ ] Event impact quantification model
- [ ] Mobile responsive design

## Contributing

Contributions are welcome! Please open an issue first to discuss what you'd like to change.

1. Fork the repo
2. Create your branch (`git checkout -b feat/amazing-feature`)
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

---

## License

[MIT](./LICENSE)

---

<div align="center">
<sub>实时追踪 20 种大宗商品，结合地缘政治事件与宏观数据分析价格驱动因素。</sub>
<br>
<sub>Track 20 commodities in real-time, combining geopolitical events and macro data to analyze price drivers.</sub>
</div>
