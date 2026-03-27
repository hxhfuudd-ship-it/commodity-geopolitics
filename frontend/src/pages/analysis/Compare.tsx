import { useEffect, useState, useRef, useMemo } from 'react'
import { marketApi } from '../../lib/api'
import { COMMODITIES } from '../../lib/constants'
import echarts from '../../lib/echarts'
import type { EChartsOption } from 'echarts'

const COLORS = ['#3b82f6', '#ef4444', '#22c55e', '#f59e0b', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316']

export default function Compare() {
  const [selected, setSelected] = useState<string[]>(['AU', 'CU', 'SC'])
  const [data, setData] = useState<Record<string, { dates: string[]; prices: number[] }> | null>(null)
  const [firstLoad, setFirstLoad] = useState(true)
  const [normalize, setNormalize] = useState(true)
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<echarts.ECharts | null>(null)

  useEffect(() => {
    if (selected.length < 2) return
    if (chartRef.current) chartRef.current.showLoading({ text: '加载中...', maskColor: 'rgba(255,255,255,0.7)' })
    marketApi.getCompare(selected, normalize)
      .then(setData)
      .catch(console.error)
      .finally(() => {
        setFirstLoad(false)
        if (chartRef.current) chartRef.current.hideLoading()
      })
  }, [selected, normalize])

  const toggle = (symbol: string) => {
    setSelected(prev =>
      prev.includes(symbol)
        ? prev.filter(s => s !== symbol)
        : prev.length < 8 ? [...prev, symbol] : prev
    )
  }

  const option = useMemo<EChartsOption | null>(() => {
    if (!data) return null
    const allDates = new Set<string>()
    for (const v of Object.values(data)) v.dates.forEach(d => allDates.add(d))
    const dates = Array.from(allDates).sort()

    const series = Object.entries(data).map(([symbol, v], idx) => {
      const priceMap = new Map(v.dates.map((d, i) => [d, v.prices[i]]))
      const name = COMMODITIES.find(c => c.symbol === symbol)?.name || symbol
      return {
        name,
        type: 'line' as const,
        data: dates.map(d => priceMap.get(d) ?? null),
        smooth: true,
        symbol: 'none' as const,
        sampling: 'lttb' as const,
        lineStyle: { width: 2, color: COLORS[idx % COLORS.length] },
        itemStyle: { color: COLORS[idx % COLORS.length] },
        connectNulls: true,
      }
    })

    return {
      tooltip: { trigger: 'axis' },
      legend: {
        top: 0,
        data: series.map(s => s.name),
        icon: 'roundRect',
        itemWidth: 18,
        itemHeight: 3,
      },
      grid: { left: '6%', right: '4%', top: '12%', bottom: '15%' },
      xAxis: { type: 'category', data: dates },
      yAxis: { type: 'value', scale: true, name: normalize ? '归一化 (%)' : '价格' },
      dataZoom: [{ type: 'inside', start: 50, end: 100 }, { type: 'slider', start: 50, end: 100 }],
      series,
    }
  }, [data, normalize])

  // Direct chart management to avoid flicker
  useEffect(() => {
    if (!chartContainerRef.current) return
    if (!chartRef.current) {
      chartRef.current = echarts.init(chartContainerRef.current)
    }
    if (option) {
      chartRef.current.setOption(option, true)
    }
    const handleResize = () => chartRef.current?.resize()
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [option])

  useEffect(() => {
    return () => { chartRef.current?.dispose(); chartRef.current = null }
  }, [])

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h2 className="text-lg font-semibold">品种对比</h2>
        <button
          onClick={() => setNormalize(!normalize)}
          className={`px-3 py-1.5 text-sm rounded-md ${normalize ? 'bg-primary-600 text-white' : 'bg-white dark:bg-gray-800 border dark:border-gray-700 text-gray-600 dark:text-gray-300'}`}
        >
          {normalize ? '归一化' : '原始价格'}
        </button>
      </div>

      <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-4">
        <div className="text-xs text-gray-500 mb-2">选择品种（2~8个）</div>
        <div className="flex flex-wrap gap-2">
          {COMMODITIES.map(c => (
            <button
              key={c.symbol}
              onClick={() => toggle(c.symbol)}
              className={`px-2.5 py-1 text-xs rounded-full transition-colors ${
                selected.includes(c.symbol)
                  ? 'text-white'
                  : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
              }`}
              style={selected.includes(c.symbol) ? { backgroundColor: COLORS[selected.indexOf(c.symbol) % COLORS.length] } : undefined}
            >
              {c.name}
            </button>
          ))}
        </div>
      </div>

      {selected.length < 2 ? (
        <div className="text-center py-12 text-gray-400">请至少选择 2 个品种</div>
      ) : firstLoad ? (
        <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" /></div>
      ) : (
        <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-4">
          <div ref={chartContainerRef} style={{ width: '100%', height: 500 }} />
        </div>
      )}
    </div>
  )
}
