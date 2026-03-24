import { useEffect, useState, useMemo, useRef } from 'react'
import { analysisApi, type RatioItem } from '../../lib/api'
import { PERIODS } from '../../lib/constants'
import { clsx } from 'clsx'
import echarts from '../../lib/echarts'
import type { EChartsOption } from 'echarts'

const RATIO_META: Record<string, { color: string; desc: string; decimals: number }> = {
  '金油比': { color: '#f59e0b', desc: '黄金/原油 — 避险情绪指标，比值越高市场越恐慌', decimals: 2 },
  '金银比': { color: '#8b5cf6', desc: '黄金/白银 — 贵金属强弱，比值高说明避险偏好强', decimals: 2 },
  '铜金比': { color: '#b45309', desc: '铜/黄金 — 经济预期指标，比值越高经济越乐观', decimals: 4 },
  '铜油比': { color: '#0891b2', desc: '铜/原油 — 工业需求 vs 能源成本', decimals: 2 },
  '豆粕比': { color: '#16a34a', desc: '大豆/豆粕 — 压榨利润链参考', decimals: 2 },
}

export default function Ratios() {
  const [data, setData] = useState<RatioItem[]>([])
  const [loading, setLoading] = useState(true)
  const [period, setPeriod] = useState('1y')

  useEffect(() => {
    setLoading(true)
    analysisApi.getRatios(period).then(setData).catch(console.error).finally(() => setLoading(false))
  }, [period])

  const ratioNames = useMemo(() => {
    const names: string[] = []
    for (const d of data) {
      if (!names.includes(d.ratio_name)) names.push(d.ratio_name)
    }
    return names
  }, [data])

  const grouped = useMemo(() => {
    const map: Record<string, RatioItem[]> = {}
    for (const d of data) {
      if (!map[d.ratio_name]) map[d.ratio_name] = []
      map[d.ratio_name].push(d)
    }
    return map
  }, [data])

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h2 className="text-lg font-semibold">比价分析</h2>
        <div className="flex gap-1">
          {PERIODS.map(p => (
            <button
              key={p.value}
              onClick={() => setPeriod(p.value)}
              className={clsx(
                'px-3 py-1.5 text-sm rounded-md',
                period === p.value ? 'bg-primary-600 text-white' : 'bg-white border text-gray-600 hover:bg-gray-50'
              )}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>
      <p className="text-sm text-gray-500 dark:text-gray-400">
        比价反映品种间相对强弱，偏离均值越远回归动力越强。
      </p>

      {loading ? (
        <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" /></div>
      ) : (
        <>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            {ratioNames.map(name => {
              const items = grouped[name] || []
              if (!items.length) return null
              const meta = RATIO_META[name] || { color: '#6b7280', desc: '', decimals: 2 }
              const latest = items[items.length - 1].value
              const avg = items.reduce((a, b) => a + b.value, 0) / items.length
              const latestDate = items[items.length - 1].date
              return (
                <div key={name} className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-3">
                  <div className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full" style={{ backgroundColor: meta.color }} />
                    {name}
                  </div>
                  <div className="text-lg font-semibold mt-1">{latest.toFixed(meta.decimals)}</div>
                  <div className="text-xs text-gray-400">{latestDate} · 均值 {avg.toFixed(meta.decimals)}</div>
                </div>
              )
            })}
          </div>

          {ratioNames.map(name => (
            <RatioChart key={`${name}-${period}`} name={name} items={grouped[name] || []} />
          ))}
        </>
      )}
    </div>
  )
}

function RatioChart({ name, items }: { name: string; items: RatioItem[] }) {
  const ref = useRef<HTMLDivElement>(null)
  const chartInstance = useRef<echarts.ECharts | null>(null)

  const meta = RATIO_META[name] || { color: '#6b7280', desc: '', decimals: 2 }

  useEffect(() => {
    if (!ref.current || !items.length) return
    if (!chartInstance.current) {
      chartInstance.current = echarts.init(ref.current)
    }
    const dates = items.map(d => d.date)
    const values = items.map(d => d.value)
    const avg = values.reduce((a, b) => a + b, 0) / values.length

    const option: EChartsOption = {
      title: { text: name, subtext: meta.desc, left: 'center', textStyle: { fontSize: 14 }, subtextStyle: { fontSize: 11 } },
      tooltip: {
        trigger: 'axis',
        formatter: (p: any) => {
          const v = p[0]
          return `${v.axisValue}<br/>${name}: ${Number(v.value).toFixed(meta.decimals)}`
        },
      },
      grid: { left: '8%', right: '10%', top: '16%', bottom: '18%' },
      xAxis: { type: 'category', data: dates },
      yAxis: { type: 'value', scale: true },
      dataZoom: [
        { type: 'inside' },
        { type: 'slider', showDataShadow: false },
      ],
      series: [{
        type: 'line', data: values, smooth: 0.15, symbol: 'none', sampling: 'lttb',
        lineStyle: { width: 1.8, color: meta.color },
        itemStyle: { color: meta.color },
        areaStyle: { color: `${meta.color}12` },
        markLine: {
          symbol: 'none', silent: true,
          label: { position: 'insideEndTop', fontSize: 11 },
          data: [{ yAxis: avg, label: { formatter: `均值 ${avg.toFixed(meta.decimals)}` }, lineStyle: { color: '#9ca3af', type: 'dashed' } }],
        },
      }],
    }
    chartInstance.current.setOption(option, true)

    const h = () => chartInstance.current?.resize()
    window.addEventListener('resize', h)
    return () => window.removeEventListener('resize', h)
  }, [items, name, meta])

  useEffect(() => {
    return () => { chartInstance.current?.dispose(); chartInstance.current = null }
  }, [])

  if (!items.length) return null

  return (
    <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-4">
      <div ref={ref} style={{ width: '100%', height: 360 }} />
    </div>
  )
}
