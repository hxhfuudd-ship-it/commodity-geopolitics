#!/usr/bin/env python3
"""
地缘驱动报告格式化工具
用于格式化地缘政治分析报告的标准输出
"""

import json
from datetime import datetime

def format_event_report(
    date: str = None,
    heatmap_summary: str = "",
    hotspots: list = None,
    regions: dict = None,
    commodities: dict = None,
    long_sectors: list = None,
    short_sectors: list = None
) -> str:
    """
    格式化地缘驱动报告
    
    Args:
        date: 报告日期，默认今天
        heatmap_summary: 局势综述
        hotspots: 今日焦点事件列表
        regions: 各区域事件字典
        commodities: 大宗商品分析
        long_sectors: 做多板块列表
        short_sectors: 做空/规避板块列表
    """
    
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    if hotspots is None:
        hotspots = []
    if regions is None:
        regions = {}
    if long_sectors is None:
        long_sectors = []
    if short_sectors is None:
        short_sectors = []
    
    report_lines = [
        f"# 全球地缘局势推演与A股事件驱动报告",
        "",
        f"**报告日期**：{date}",
        f"**生成时间**：{datetime.now().strftime('%H:%M:%S')}",
        "",
        "---",
        "",
        "## 🌍 全球地缘风暴眼 (Heatmap)",
        "",
        f"**局势综述**：{heatmap_summary}",
        "",
        "### 今日焦点",
        "",
    ]
    
    # 热点事件表格
    report_lines.append("| 排名 | 事件 | 紧急度 | 影响板块 |")
    report_lines.append("|:---:|------|:---:|:--------:|")
    for i, hotspot in enumerate(hotspots[:5], 1):
        urgency = "🔴" * hotspot.get("urgency", 1) + "⚪" * (3 - hotspot.get("urgency", 1))
        report_lines.append(f"| {i} | {hotspot.get('title', 'N/A')} | {urgency} | {hotspot.get('sector', 'N/A')} |")
    
    report_lines.extend(["", "---", ""])
    
    # 各区域详情
    report_lines.append("## 🗺️ 全球区域深度扫描与局势推演")
    report_lines.append("")
    
    region_emojis = {
        "china": "🇨🇳",
        "americas": "🌎", 
        "europe": "❄️",
        "middle_east": "🛢️"
    }
    
    for region_key, region_data in regions.items():
        emoji = region_emojis.get(region_key, "📍")
        report_lines.append(f"### {emoji} {region_data.get('name', region_key)}")
        report_lines.append("")
        
        for event in region_data.get("events", []):
            report_lines.append(f"#### {event.get('title', '未命名事件')}")
            report_lines.append(f"- **时间**：{event.get('time', 'N/A')}")
            report_lines.append(f"- **地点**：{event.get('location', 'N/A')}")
            report_lines.append(f"- **关键人物**：{event.get('actors', 'N/A')}")
            report_lines.append(f"- **具体内容**：{event.get('content', 'N/A')}")
            report_lines.append(f"- **信息来源**：{event.get('source', 'N/A')}")
            report_lines.append(f"- **费曼解读**：{event.get('simple_explain', 'N/A')}")
            report_lines.append("")
            
            if "forecast" in event:
                report_lines.append("**📊 沙盘推演**")
                for scenario, prob in event["forecast"].items():
                    report_lines.append(f"- {scenario}：{prob}")
                report_lines.append("")
        
        report_lines.append("---")
        report_lines.append("")
    
    # 金融映射
    report_lines.append("## 🔗 传导链条与金融映射")
    report_lines.append("")
    
    # 大宗商品
    if commodities:
        report_lines.append("### 大宗商品")
        report_lines.append("")
        report_lines.append("| 品种 | 驱动因素 | 预判 |")
        report_lines.append("|-----|---------|:----:|")
        for commodity, data in commodities.items():
            direction = "📈" if data.get("direction") == "up" else "📉" if data.get("direction") == "down" else "➡️"
            report_lines.append(f"| {commodity} | {data.get('driver', 'N/A')} | {direction} |")
        report_lines.append("")
    
    # A股策略
    report_lines.append("## 📈 A股事件驱动与多空策略")
    report_lines.append("")
    
    # 做多板块
    if long_sectors:
        report_lines.append("### 🟢 受益板块（做多逻辑）")
        report_lines.append("")
        for sector in long_sectors:
            report_lines.append(f"#### {sector.get('name', '未命名板块')}")
            report_lines.append(f"**核心逻辑**：{sector.get('logic', 'N/A')}")
            report_lines.append("")
            if "stocks" in sector:
                report_lines.append("| 代码 | 名称 | 逻辑 |")
                report_lines.append("|:---:|-----|------|")
                for stock in sector["stocks"]:
                    report_lines.append(f"| {stock.get('code', 'N/A')} | {stock.get('name', 'N/A')} | {stock.get('logic', 'N/A')} |")
                report_lines.append("")
    
    # 规避板块
    if short_sectors:
        report_lines.append("### 🔴 受损板块（规避风险）")
        report_lines.append("")
        for sector in short_sectors:
            report_lines.append(f"#### {sector.get('name', '未命名板块')}")
            report_lines.append(f"**受损逻辑**：{sector.get('logic', 'N/A')}")
            report_lines.append("")
            if "stocks" in sector:
                report_lines.append("| 代码 | 名称 | 风险 |")
                report_lines.append("|:---:|-----|:----:|")
                for stock in sector["stocks"]:
                    risk = "🔴" * stock.get("risk", 1)
                    report_lines.append(f"| {stock.get('code', 'N/A')} | {stock.get('name', 'N/A')} | {risk} |")
                report_lines.append("")
    
    report_lines.extend([
        "---",
        "",
        "**免责声明**：本报告仅供研究参考，不构成投资建议。",
        "",
        "*报告由 地缘驱动策略系统 生成*"
    ])
    
    return "\n".join(report_lines)


if __name__ == "__main__":
    # 示例用法
    sample_report = format_event_report(
        heatmap_summary="高危临界 - 中东局势恶化叠加台海紧张",
        hotspots=[
            {"title": "伊朗核设施遇袭", "urgency": 3, "sector": "石油/黄金"},
            {"title": "台海军事演习", "urgency": 3, "sector": "军工/半导体"}
        ],
        long_sectors=[
            {
                "name": "稀土永磁",
                "logic": "格陵兰稀土出口受限，中国稀土话语权提升",
                "stocks": [
                    {"code": "600111", "name": "北方稀土", "logic": "轻稀土龙头"},
                    {"code": "000831", "name": "中国稀土", "logic": "中重稀土整合平台"}
                ]
            }
        ]
    )
    print(sample_report)
