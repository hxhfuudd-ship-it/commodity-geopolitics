<div align="center">

# GeoInsight

**大宗商品地缘政治分析平台**

**Commodity Geopolitics Analysis Platform**

[![React](https://img.shields.io/badge/React-18-61dafb?logo=react&logoColor=white)](https://react.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-Python-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169e1?logo=postgresql&logoColor=white)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ed?logo=docker&logoColor=white)](https://docker.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)

[中文](#功能特性) · [English](#features)

**在线体验 / Live Demo**：`http://43.160.241.35:9180`

</div>

---

## 预览 / Preview

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

---

## Features

| Module | Details |
|--------|---------|
| **Market Dashboard** | 20 commodities real-time prices, K-line charts (OHLCV + MA), 3s SSE push |
| **Multi-dimensional Analysis** | Cross-commodity comparison, correlation matrix, macro overlay, price ratios, volatility, AI sentiment |
| **Event Timeline** | Geopolitical events overlaid on price curves, event backtesting (N-day impact) |
| **News Aggregation** | 18 RSS feeds, AI-powered summary + sentiment + commodity tagging + importance rating |
| **AI Assistant** | DeepSeek-powered streaming chat, market Q&A + geopolitical analysis + daily reports |

---

## 技术栈 / Tech Stack

| 层级 / Layer | 技术 / Technology |
|------|------|
| 前端 / Frontend | React 18 + TypeScript + Vite + Tailwind CSS |
| 可视化 / Charts | Apache ECharts（K 线、热力图、时间轴） |
| 后端 / Backend | FastAPI (Python) + async/await + SSE |
| 数据库 / Database | PostgreSQL 15 |
| 缓存 / Cache | Redis 7（行情缓存 + 分布式锁 + 会话存储） |
| AI | DeepSeek（情感分析 + 市场日报 + 对话助手） |
| 部署 / Deploy | Docker Compose（四容器编排） |

---

## 数据来源 / Data Sources

| 数据 / Data | 来源 / Source |
|------|------|
| 期货日线 / Futures daily | 新浪期货 via akshare |
| 实时行情 / Real-time quotes | 东方财富 push2 批量接口 |
| 宏观指标 / Macro indicators | akshare（DXY / USDCNY / US10Y / CN10Y / BDI） |
| 新闻 / News | 18 个 RSS 订阅源 |
| 地缘事件 / Geopolitical events | 人工维护事件数据库 |

---

## 数据更新 / Update Schedule

| 任务 / Task | 周期 / Interval | 说明 / Description |
|------|------|------|
| 实时行情 | 3 秒 | 交易时段 SSE 推送 |
| 日线补全 | 5 分钟 | 全量日线数据拉取 |
| 新闻抓取 | 15 分钟 | 18 路 RSS + 去重 |
| AI 分析 | 16 分钟 | 未分析新闻自动调用 DeepSeek |
| 宏观指标 | 6 小时 | DXY / 汇率 / 国债利率 |

---

## 品种覆盖 / Commodities

| 板块 / Sector | 品种 / Commodities |
|------|------|
| 金属 / Metals | 黄金 / 白银 / 铜 / 铝 / 镍 / 铁矿石 |
| 能源 / Energy | 上海原油 / 燃料油 / LPG |
| 农产品 / Agriculture | 大豆 / 豆粕 / 豆油 / 棕榈油 / 玉米 / 棉花 / 白糖 / 橡胶 |
| 化工 / Chemicals | PTA / 甲醇 / 聚丙烯 |

---

## 快速开始 / Getting Started

### 环境要求 / Prerequisites

- Docker + Docker Compose

### 部署 / Deploy

```bash
git clone https://github.com/hxhfuudd-ship-it/commodity-geopolitics.git
cd commodity-geopolitics
docker compose up -d
```

浏览器打开 / Open http://localhost:9180

---

## 项目结构 / Project Structure

```
commodity-geopolitics/
├── frontend/                # React 前端 / React frontend
│   ├── src/
│   │   ├── pages/          # 页面组件 / Page components
│   │   ├── lib/            # API 客户端 / API client & utils
│   │   └── hooks/          # 自定义 Hooks / Custom hooks
│   └── Dockerfile
├── backend/                 # FastAPI 后端 / FastAPI backend
│   ├── app/
│   │   ├── api/v1/         # API 路由 / API routes
│   │   ├── services/       # 业务逻辑 / Business logic
│   │   ├── models/         # ORM 模型 / ORM models
│   │   ├── tasks/          # 定时任务 / Scheduled tasks
│   │   ├── data_sources/   # 外部数据源 / External data sources
│   │   └── core/           # 缓存 / LLM / 锁 / Core utilities
│   └── Dockerfile
├── docker-compose.yml
└── .gitignore
```

---

## 规划中 / Roadmap

- [ ] 更多品种覆盖（外盘期货）
- [ ] 用户自定义看板
- [ ] 事件影响量化模型
- [ ] 移动端适配

---

## 参与贡献 / Contributing

欢迎贡献！请先开 Issue 讨论。

Contributions are welcome! Please open an issue first.

1. Fork 本仓库 / Fork the repo
2. 创建分支 / Create your branch (`git checkout -b feat/amazing-feature`)
3. 提交改动 / Commit your changes
4. 推送分支 / Push to the branch
5. 发起 PR / Open a Pull Request

---

## 许可证 / License

[MIT](./LICENSE)

---

<div align="center">
<sub>实时追踪 20 种大宗商品，结合地缘政治事件与宏观数据分析价格驱动因素。</sub>
<br>
<sub>Track 20 commodities in real-time, combining geopolitical events and macro data to analyze price drivers.</sub>
</div>
