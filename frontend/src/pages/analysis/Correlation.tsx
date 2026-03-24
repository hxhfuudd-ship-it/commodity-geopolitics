import { useEffect, useState, useMemo } from 'react'
import { analysisApi, type CorrelationMatrix } from '../../lib/api'
import { useECharts } from '../../hooks/useECharts'
import { COMMODITIES, PERIODS } from '../../lib/constants'
import { clsx } from 'clsx'
import type { EChartsOption } from 'echarts'

export default function Correlation() {
  const [matrix, setMatrix] = useState<CorrelationMatrix | null>(null)
  const [period, setPeriod] = useState('90d')
  const [loading, setLoading] = useState(true)

  const symbols = COMMODITIES.map(c => c.symbol)

  useEffect(() => {
    setLoading(true)
    analysisApi.getCorrelation(symbols, period)
      .then(setMatrix)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [period])

  const option = useMemo<EChartsOption | null>(() => {
    if (!matrix) return null
    const names = matrix.symbols
    const data: [number, number, number][] = []
    for (let i = 0; i < names.length; i++) {
      for (let j = 0; j < names.length; j++) {
        data.push([j, i, matrix.matrix[i][j]])
      }
    }
    return {
      tooltip: {
        formatter: (params: any) => {
          const d = params.data
          return `${names[d[1]]} vs ${names[d[0]]}: ${d[2].toFixed(3)}`
        },
      },
      grid: { left: '12%', right: '12%', top: '8%', bottom: '12%' },
      xAxis: { type: 'category', data: names, splitArea: { show: true } },
      yAxis: { type: 'category', data: names, splitArea: { show: true } },
      visualMap: {
        min: -1, max: 1, calculable: true, orient: 'horizontal',
        left: 'center', bottom: 0,
        inRange: { color: ['#3b82f6', '#ffffff', '#ef4444'] },
      },
      series: [{
        type: 'heatmap', data, label: { show: true, formatter: (p: any) => p.data[2].toFixed(2), fontSize: 10 },
        emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.3)' } },
      }],
    }
  }, [matrix])

  const chartRef = useECharts(option, [matrix])

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">相关性矩阵</h2>
        <div className="flex gap-2">
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
