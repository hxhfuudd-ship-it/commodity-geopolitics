import { useEffect, useState, useMemo, useRef } from 'react'
import { newsApi, type SentimentTrendItem } from '../../lib/api'
import { COMMODITIES } from '../../lib/constants'
import { BULLISH_COLOR, BEARISH_COLOR, NEUTRAL_COLOR } from '../../lib/colors'
import echarts from '../../lib/echarts'
import type { EChartsOption } from 'echarts'

export default function Sentiment() {
  const [data, setData] = useState<SentimentTrendItem[]>([])
  const [commodity, setCommodity] = useState('')
  const [days, setDays] = useState(30)
  const [loading, setLoading] = useState(true)

  const barRef = useRef<HTMLDivElement>(null)
  const scoreRef = useRef<HTMLDivElement>(null)
  const barChart = useRef<echarts.ECharts | null>(null)
  const scoreChart = useRef<echarts.ECharts | null>(null)

  useEffect(() => {
    setLoading(true)
    newsApi.getSentimentTrend(commodity || undefined, days)
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [commodity, days])

  const barOption = useMemo<EChartsOption | null>(() => {
    if (!data.length) return null
    const dates = data.map(d => d.date)
    return {
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      legend: { data: ['利多', '利空', '中性'], top: 0 },
      grid: { left: '6%', right: '4%', top: '12%', bottom: '15%' },
      xAxis: { type: 'category', data: dates },
      yAxis: { type: 'value', name: '新闻数量' },
      dataZoom: [{ type: 'inside' }, { type: 'slider', showDataShadow: false }],
      series: [
        { name: '利多', type: 'bar', stack: 'total', data: data.map(d => d.bullish_count), itemStyle: { color: BULLISH_COLOR } },
        { name: '利空', type: 'bar', stack: 'total', data: data.map(d => d.bearish_count), itemStyle: { color: BEARISH_COLOR } },
        { name: '中性', type: 'bar', stack: 'total', data: data.map(d => d.neutral_count), itemStyle: { color: NEUTRAL_COLOR } },
      ],
    }
  }, [data])

  const scoreOption = useMemo<EChartsOption | null>(() => {
    if (!data.length) return null
    const dates = data.map(d => d.date)
    const scores = data.map(d => d.avg_score)
    return {
      tooltip: { trigger: 'axis', formatter: (p: any) => `${p[0].axisValue}<br/>平均情绪: ${p[0].value != null ? p[0].value.toFixed(3) : 'N/A'}` },
      grid: { left: '6%', right: '4%', top: '8%', bottom: '15%' },
      xAxis: { type: 'category', data: dates },
      yAxis: { type: 'value', scale: true, name: '情绪分数', min: 0, max: 1 },
      dataZoom: [{ type: 'inside' }, { type: 'slider', showDataShadow: false }],
      visualMap: {
        show: false, dimension: 1, pieces: [
          { lt: 0.4, color: BEARISH_COLOR },
          { gte: 0.4, lte: 0.6, color: NEUTRAL_COLOR },
          { gt: 0.6, color: BULLISH_COLOR },
        ],
      },
      series: [{
        type: 'line', data: scores, smooth: 0.15, symbol: 'circle', symbolSize: 6,
        lineStyle: { width: 2 },
        markLine: {
          symbol: 'none', silent: true,
          data: [{ yAxis: 0.5, label: { formatter: '中性线', position: 'insideEndTop' }, lineStyle: { color: '#d1d5db', type: 'dashed' } }],
        },
      }],
    }
  }, [data])

  // Render charts
  useEffect(() => {
    if (loading) return
    if (barRef.current) {
      if (!barChart.current) barChart.current = echarts.init(barRef.current)
      if (barOption) barChart.current.setOption(barOption, true)
      else barChart.current.clear()
    }
    if (scoreRef.current) {
      if (!scoreChart.current) scoreChart.current = echarts.init(scoreRef.current)
      if (scoreOption) scoreChart.current.setOption(scoreOption, true)
      else scoreChart.current.clear()
    }
    const h = () => { barChart.current?.resize(); scoreChart.current?.resize() }
    window.addEventListener('resize', h)
    return () => window.removeEventListener('resize', h)
  }, [barOption, scoreOption, loading])

  useEffect(() => {
    return () => {
      barChart.current?.dispose(); barChart.current = null
      scoreChart.current?.dispose(); scoreChart.current = null
    }
  }, [])

  const totalBullish = data.reduce((s, d) => s + d.bullish_count, 0)
  const totalBearish = data.reduce((s, d) => s + d.bearish_count, 0)
  const withScore = data.filter(d => d.avg_score != null)
  const avgScore = withScore.length ? withScore.reduce((s, d) => s + (d.avg_score || 0), 0) / withScore.length : 0

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h2 className="text-lg font-semibold">情绪趋势</h2>
        <div className="flex gap-2 flex-wrap">
          <select value={commodity} onChange={e => setCommodity(e.target.value)}
            className="px-3 py-1.5 text-sm border rounded-md bg-white dark:bg-gray-800 dark:border-gray-700 dark:text-gray-200">
            <option value="">全部品种</option>
            {COMMODITIES.map(c => <option key={c.symbol} value={c.symbol}>{c.name}</option>)}
          </select>
          {[7, 14, 30].map(d => (
            <button key={d} onClick={() => setDays(d)}
              className={`px-3 py-1.5 text-sm rounded-md ${days === d ? 'bg-primary-600 text-white' : 'bg-white dark:bg-gray-800 border dark:border-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-50'}`}>
              {d}天
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" /></div>
      ) : !data.length ? (
        <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-8 text-center text-gray-400">
          该品种暂无情绪数据
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-3">
              <div className="text-xs text-gray-500">利多新闻</div>
              <div className="text-lg font-semibold mt-1" style={{ color: BULLISH_COLOR }}>{totalBullish}</div>
            </div>
            <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-3">
              <div className="text-xs text-gray-500">利空新闻</div>
              <div className="text-lg font-semibold mt-1" style={{ color: BEARISH_COLOR }}>{totalBearish}</div>
            </div>
            <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-3">
              <div className="text-xs text-gray-500">多空比</div>
              <div className="text-lg font-semibold mt-1">{totalBearish > 0 ? (totalBullish / totalBearish).toFixed(2) : '-'}</div>
            </div>
            <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-3">
              <div className="text-xs text-gray-500">平均情绪分</div>
              <div className="text-lg font-semibold mt-1" style={{ color: avgScore > 0.6 ? BULLISH_COLOR : avgScore < 0.4 ? BEARISH_COLOR : NEUTRAL_COLOR }}>
                {avgScore ? avgScore.toFixed(3) : '-'}
              </div>
            </div>
          </div>
        </>
      )}

      <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-4">
        <h3 className="text-sm font-medium mb-2">每日情绪分布</h3>
        <div ref={barRef} style={{ width: '100%', height: 350 }} />
      </div>
      <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-4">
        <h3 className="text-sm font-medium mb-2">情绪分数走势</h3>
        <div ref={scoreRef} style={{ width: '100%', height: 350 }} />
      </div>
    </div>
  )
}
