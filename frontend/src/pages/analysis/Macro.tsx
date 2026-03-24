import { useEffect, useState, useMemo } from 'react'
import { analysisApi, type MacroComparison } from '../../lib/api'
import { useECharts } from '../../hooks/useECharts'
import { COMMODITIES, MACRO_INDICATORS, PERIODS } from '../../lib/constants'
import { clsx } from 'clsx'
import type { EChartsOption } from 'echarts'

export default function Macro() {
  const [data, setData] = useState<MacroComparison | null>(null)
  const [indicator, setIndicator] = useState<string>(MACRO_INDICATORS[0].code)
  const [commodity, setCommodity] = useState('AU')
  const [period, setPeriod] = useState('180d')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    analysisApi.getMacroComparison(indicator, commodity, period)
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [indicator, commodity, period])

  const option = useMemo<EChartsOption | null>(() => {
    if (!data || !data.dates.length) return null
    const indicatorName = MACRO_INDICATORS.find(i => i.code === indicator)?.name || indicator
    const commodityName = COMMODITIES.find(c => c.symbol === commodity)?.name || commodity

    return {
      tooltip: { trigger: 'axis' },
      legend: {
        data: [indicatorName, commodityName],
        top: 0,
        icon: 'roundRect',
        itemWidth: 18,
        itemHeight: 3,
      },
      grid: { left: '8%', right: '8%', top: '12%', bottom: '18%' },
      xAxis: { type: 'category', data: data.dates },
      yAxis: [
        { type: 'value', name: indicatorName, scale: true },
        { type: 'value', name: commodityName, scale: true },
      ],
      dataZoom: [
        { type: 'inside', start: 0, end: 100 },
        { type: 'slider', start: 0, end: 100, showDataShadow: false },
      ],
      series: [
        {
          name: indicatorName, type: 'line', data: data.indicator_values,
          smooth: 0.15, symbol: 'none', yAxisIndex: 0, sampling: 'lttb',
          lineStyle: { width: 1.8, color: '#3b82f6' },
          itemStyle: { color: '#3b82f6' },
        },
        {
          name: commodityName, type: 'line', data: data.commodity_prices,
          smooth: 0.15, symbol: 'none', yAxisIndex: 1, sampling: 'lttb',
          lineStyle: { width: 1.8, color: '#ef4444' },
          itemStyle: { color: '#ef4444' },
        },
      ],
    }
  }, [data, indicator, commodity])

  const chartRef = useECharts(option, [data])

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h2 className="text-lg font-semibold">宏观指标对比</h2>
        <div className="flex gap-2 flex-wrap">
          <select
            value={indicator}
            onChange={e => setIndicator(e.target.value)}
            className="px-3 py-1.5 text-sm border rounded-md bg-white"
          >
            {MACRO_INDICATORS.map(i => (
              <option key={i.code} value={i.code}>{i.name}</option>
            ))}
          </select>
          <select
            value={commodity}
            onChange={e => setCommodity(e.target.value)}
            className="px-3 py-1.5 text-sm border rounded-md bg-white"
          >
            {COMMODITIES.map(c => (
              <option key={c.symbol} value={c.symbol}>{c.name}</option>
            ))}
          </select>
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
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" /></div>
      ) : (
        <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-4">
          <div ref={chartRef} style={{ width: '100%', height: 500 }} />
        </div>
      )}
    </div>
  )
}
