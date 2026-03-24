import { useEffect, useState, useRef, useMemo } from 'react'
import { marketApi, type PriceDaily } from '../../lib/api'
import { COMMODITIES } from '../../lib/constants'
import { clsx } from 'clsx'
import echarts from '../../lib/echarts'
import type { EChartsOption } from 'echarts'

function calcVolatility(prices: number[], winSize: number): number[] {
  const result: number[] = []
  for (let i = 0; i < prices.length; i++) {
    if (i < winSize) { result.push(NaN); continue }
    const slice = prices.slice(i - winSize, i)
    const returns: number[] = []
    for (let j = 1; j < slice.length; j++) {
      if (slice[j - 1] > 0) returns.push(Math.log(slice[j] / slice[j - 1]))
    }
    if (returns.length < 2) { result.push(NaN); continue }
    const mean = returns.reduce((a, b) => a + b, 0) / returns.length
    const variance = returns.reduce((a, b) => a + (b - mean) ** 2, 0) / (returns.length - 1)
    result.push(Math.sqrt(variance) * Math.sqrt(252) * 100)
  }
  return result
}

export default function Volatility() {
  const [symbol, setSymbol] = useState('AU')
  const [kline, setKline] = useState<PriceDaily[]>([])
  const [loading, setLoading] = useState(true)
  const [winSize, setWinSize] = useState(20)
  const volChartRef = useRef<HTMLDivElement>(null)
  const volInstanceRef = useRef<echarts.ECharts | null>(null)
  const distChartRef = useRef<HTMLDivElement>(null)
  const distInstanceRef = useRef<echarts.ECharts | null>(null)

  useEffect(() => {
    setLoading(true)
    marketApi.getKline(symbol)
      .then(setKline)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [symbol])

  const { volOption, distOption, stats } = useMemo(() => {
    if (!kline.length) return { volOption: null, distOption: null, stats: null }
    const dates = kline.map(k => k.trade_date)
    const closes = kline.map(k => k.close)
    const vol = calcVolatility(closes, winSize)
    const commodityName = COMMODITIES.find(c => c.symbol === symbol)?.name || symbol

    // Daily returns for distribution — use recent 1 year
    const recentN = Math.min(252, closes.length - 1)
    const recentCloses = closes.slice(-recentN - 1)
    const dailyReturns: number[] = []
    for (let i = 1; i < recentCloses.length; i++) {
      if (recentCloses[i - 1] > 0) dailyReturns.push(((recentCloses[i] - recentCloses[i - 1]) / recentCloses[i - 1]) * 100)
    }

    // Stats — percentile against recent 1 year of vol data only
    const validVol = vol.filter(v => !isNaN(v))
    const recentVolCount = Math.min(252, validVol.length)
    const recentVol = validVol.slice(-recentVolCount)
    const currentVol = validVol[validVol.length - 1]
    const avgVol = recentVol.reduce((a, b) => a + b, 0) / recentVol.length
    const maxVol = Math.max(...recentVol)
    const minVol = Math.min(...recentVol)
    // Percentile: what % of recent 1y vol values are <= current
    const percentile = recentVol.filter(v => v <= currentVol).length / recentVol.length * 100

    // Return distribution stats
    const retMean = dailyReturns.reduce((a, b) => a + b, 0) / dailyReturns.length
    const retStd = Math.sqrt(dailyReturns.reduce((a, b) => a + (b - retMean) ** 2, 0) / (dailyReturns.length - 1))
    const skewness = dailyReturns.reduce((a, b) => a + ((b - retMean) / retStd) ** 3, 0) / dailyReturns.length
    const kurtosis = dailyReturns.reduce((a, b) => a + ((b - retMean) / retStd) ** 4, 0) / dailyReturns.length - 3
    // VaR 5%
    const sortedReturns = [...dailyReturns].sort((a, b) => a - b)
    const var5 = sortedReturns[Math.floor(sortedReturns.length * 0.05)]
    const var95 = sortedReturns[Math.floor(sortedReturns.length * 0.95)]

    // Histogram bins
    const binCount = 30
    const rMin = Math.min(...dailyReturns)
    const rMax = Math.max(...dailyReturns)
    const binWidth = (rMax - rMin) / binCount
    const bins: number[] = new Array(binCount).fill(0)
    const binCenters: number[] = []
    const binLabels: string[] = []
    for (let i = 0; i < binCount; i++) {
      const center = rMin + binWidth * (i + 0.5)
      binCenters.push(center)
      binLabels.push(center.toFixed(2) + '%')
    }
    for (const r of dailyReturns) {
      const idx = Math.min(Math.floor((r - rMin) / binWidth), binCount - 1)
      bins[idx]++
    }

    // Normal distribution curve overlay
    const normalCurve = binCenters.map(x => {
      const z = (x - retMean) / retStd
      const pdf = Math.exp(-0.5 * z * z) / (retStd * Math.sqrt(2 * Math.PI))
      return +(pdf * dailyReturns.length * binWidth).toFixed(2)
    })

    const volOpt: EChartsOption = {
      tooltip: { trigger: 'axis', formatter: (p: any) => `${p[0].axisValue}<br/>${winSize}日波动率: ${p[0].value != null && !isNaN(p[0].value) ? p[0].value.toFixed(2) + '%' : 'N/A'}` },
      grid: { left: '8%', right: '4%', top: '8%', bottom: '15%' },
      xAxis: { type: 'category', data: dates },
      yAxis: { type: 'value', scale: true, name: `${winSize}日年化波动率 (%)` },
      dataZoom: [{ type: 'inside', start: 50, end: 100 }, { type: 'slider', start: 50, end: 100 }],
      series: [{
        type: 'line', data: vol.map(v => isNaN(v) ? null : +v.toFixed(2)), smooth: true, symbol: 'none',
        lineStyle: { width: 2, color: '#8b5cf6' },
        areaStyle: { color: 'rgba(139,92,246,0.1)' },
        markLine: {
          symbol: 'none', silent: true,
          data: [{ yAxis: avgVol, label: { formatter: `均值 ${avgVol.toFixed(1)}%`, position: 'insideEndTop', fontSize: 11 }, lineStyle: { color: '#9ca3af', type: 'dashed' } }],
        },
      }],
    }

    const distOpt: EChartsOption = {
      tooltip: {
        trigger: 'axis',
        formatter: (p: any) => {
          const items = p.map((s: any) => `${s.marker}${s.seriesName}: ${s.value}`).join('<br/>')
          return `${p[0].axisValue}<br/>${items}`
        },
      },
      legend: {
        data: [
          { name: '跌 (实际)', icon: 'roundRect', itemStyle: { color: '#22c55e' } },
          { name: '涨 (实际)', icon: 'roundRect', itemStyle: { color: '#ef4444' } },
          { name: '正态分布', icon: 'roundRect', itemStyle: { color: '#f59e0b' } },
        ],
        top: 0, itemWidth: 14, itemHeight: 10,
      },
      grid: { left: '8%', right: '4%', top: '12%', bottom: '10%' },
      xAxis: {
        type: 'category', data: binLabels, name: '日收益率 (近1年)',
        axisLabel: { interval: Math.floor(binCount / 8) },
      },
      yAxis: { type: 'value', name: '频次' },
      series: [
        {
          name: '跌 (实际)', type: 'bar', stack: 'dist',
          data: bins.map((v, i) => parseFloat(binLabels[i]) <= 0 ? v : null),
          itemStyle: { color: '#22c55e' },
        },
        {
          name: '涨 (实际)', type: 'bar', stack: 'dist',
          data: bins.map((v, i) => parseFloat(binLabels[i]) > 0 ? v : null),
          itemStyle: { color: '#ef4444' },
        },
        {
          name: '正态分布', type: 'line', data: normalCurve, smooth: true, symbol: 'none',
          lineStyle: { width: 2, color: '#f59e0b', type: 'dashed' },
          itemStyle: { color: '#f59e0b' },
        },
      ],
    }

    return {
      volOption: volOpt,
      distOption: distOpt,
      stats: { currentVol, avgVol, maxVol, minVol, percentile, skewness, kurtosis, var5 },
    }
  }, [kline, symbol, winSize])

  // Manage vol chart — recreate instance if DOM element changed
  useEffect(() => {
    if (!volChartRef.current || loading) return
    if (volInstanceRef.current) {
      const dom = volInstanceRef.current.getDom()
      if (dom !== volChartRef.current) {
        volInstanceRef.current.dispose()
        volInstanceRef.current = null
      }
    }
    if (!volInstanceRef.current) volInstanceRef.current = echarts.init(volChartRef.current)
    if (volOption) volInstanceRef.current.setOption(volOption, true)
    // Ensure correct size after display:none -> visible
    setTimeout(() => volInstanceRef.current?.resize(), 0)
    const h = () => volInstanceRef.current?.resize()
    window.addEventListener('resize', h)
    return () => window.removeEventListener('resize', h)
  }, [volOption, loading])

  useEffect(() => {
    if (!distChartRef.current || loading) return
    if (distInstanceRef.current) {
      const dom = distInstanceRef.current.getDom()
      if (dom !== distChartRef.current) {
        distInstanceRef.current.dispose()
        distInstanceRef.current = null
      }
    }
    if (!distInstanceRef.current) distInstanceRef.current = echarts.init(distChartRef.current)
    if (distOption) distInstanceRef.current.setOption(distOption, true)
    setTimeout(() => distInstanceRef.current?.resize(), 0)
    const h = () => distInstanceRef.current?.resize()
    window.addEventListener('resize', h)
    return () => window.removeEventListener('resize', h)
  }, [distOption, loading])

  useEffect(() => {
    return () => {
      volInstanceRef.current?.dispose(); volInstanceRef.current = null
      distInstanceRef.current?.dispose(); distInstanceRef.current = null
    }
  }, [])

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h2 className="text-lg font-semibold">波动率分析</h2>
        <div className="flex gap-2 flex-wrap">
          <select value={symbol} onChange={e => setSymbol(e.target.value)}
            className="px-3 py-1.5 text-sm border rounded-md bg-white dark:bg-gray-800 dark:border-gray-700 dark:text-gray-200">
            {COMMODITIES.map(c => <option key={c.symbol} value={c.symbol}>{c.name}</option>)}
          </select>
          {[10, 20, 60].map(w => (
            <button key={w} onClick={() => setWinSize(w)}
              className={clsx('px-3 py-1.5 text-sm rounded-md',
                winSize === w ? 'bg-primary-600 text-white' : 'bg-white dark:bg-gray-800 border dark:border-gray-700 text-gray-600 dark:text-gray-300')}>
              {w}日窗口
            </button>
          ))}
        </div>
      </div>

      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <StatCard label={`当前${winSize}日波动率`} value={`${stats.currentVol.toFixed(2)}%`} />
          <StatCard label="近1年均值" value={`${stats.avgVol.toFixed(2)}%`} />
          <StatCard label="近1年最高" value={`${stats.maxVol.toFixed(2)}%`} />
          <StatCard label="近1年分位"
            value={`${stats.percentile.toFixed(0)}%`}
            sub={stats.percentile > 80 ? '偏高' : stats.percentile < 20 ? '偏低' : '正常'}
            subColor={stats.percentile > 80 ? '#ef4444' : stats.percentile < 20 ? '#22c55e' : '#6b7280'} />
          <StatCard label="偏度 (Skewness)" value={stats.skewness.toFixed(3)}
            sub={stats.skewness < -0.5 ? '左偏·下行风险大' : stats.skewness > 0.5 ? '右偏·上行弹性大' : '近似对称'}
            subColor={stats.skewness < -0.5 ? '#ef4444' : stats.skewness > 0.5 ? '#22c55e' : '#6b7280'} />
          <StatCard label="峰度 (Kurtosis)" value={stats.kurtosis.toFixed(3)}
            sub={stats.kurtosis > 1 ? '厚尾·极端波动多' : stats.kurtosis < -0.5 ? '薄尾' : '近似正态'}
            subColor={stats.kurtosis > 1 ? '#ef4444' : '#6b7280'} />
          <StatCard label="VaR 5% (日)" value={`${stats.var5.toFixed(2)}%`}
            sub="95%置信最大日亏损" subColor="#ef4444" />
        </div>
      )}

      {loading && (
        <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" /></div>
      )}
      <div style={{ display: loading ? 'none' : undefined }}>
        <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-4">
          <h3 className="text-sm font-medium mb-2">{winSize}日历史波动率</h3>
          <div ref={volChartRef} style={{ width: '100%', height: 400 }} />
        </div>
        <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-4 mt-4">
          <h3 className="text-sm font-medium mb-2">日收益率分布 (近1年)</h3>
          <div ref={distChartRef} style={{ width: '100%', height: 350 }} />
        </div>
      </div>
    </div>
  )
}

function StatCard({ label, value, sub, subColor }: { label: string; value: string; sub?: string; subColor?: string }) {
  return (
    <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-3">
      <div className="text-xs text-gray-500 dark:text-gray-400">{label}</div>
      <div className="text-lg font-semibold mt-1">{value}</div>
      {sub && <div className="text-xs mt-0.5" style={{ color: subColor || '#9ca3af' }}>{sub}</div>}
    </div>
  )
}
