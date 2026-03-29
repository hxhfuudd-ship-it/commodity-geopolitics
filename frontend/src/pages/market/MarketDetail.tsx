import { useEffect, useState, useMemo, useRef, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, TrendingUp, TrendingDown, BarChart3, Activity } from 'lucide-react'
import { marketApi, type PriceDaily, type MarketOverviewItem } from '../../lib/api'
import echarts from '../../lib/echarts'
import { BULLISH_COLOR, BEARISH_COLOR } from '../../lib/colors'
import { clsx } from 'clsx'
import type { EChartsOption } from 'echarts'

export default function MarketDetail() {
  const { symbol } = useParams<{ symbol: string }>()
  const [kline, setKline] = useState<PriceDaily[]>([])
  const [loading, setLoading] = useState(true)
  const [visibleRange, setVisibleRange] = useState<[number, number]>([0, 100])
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInstance = useRef<echarts.ECharts | null>(null)
  const [realtime, setRealtime] = useState<MarketOverviewItem | null>(null)

  useEffect(() => {
    if (!symbol) return
    setKline([])
    setLoading(true)
    marketApi.getKline(symbol)
      .then(data => {
        setKline(data)
        setVisibleRange([70, 100])
      })
      .catch(console.error)
      .finally(() => setLoading(false))
    // Initial realtime price
    marketApi.getOverview().then(data => {
      const item = data.find(d => d.symbol === symbol)
      if (item) setRealtime(item)
    }).catch(console.error)
  }, [symbol])

  // SSE for live price updates
  useEffect(() => {
    if (!symbol) return
    const es = new EventSource('/api/v1/market/overview/stream')
    es.onmessage = (event) => {
      try {
        const data: MarketOverviewItem[] = JSON.parse(event.data)
        const item = data.find(d => d.symbol === symbol)
        if (item) setRealtime(item)
      } catch {}
    }
    return () => es.close()
  }, [symbol])

  // 当前可见区间的数据
  const visibleData = useMemo(() => {
    if (!kline.length) return []
    const start = Math.floor(kline.length * visibleRange[0] / 100)
    const end = Math.ceil(kline.length * visibleRange[1] / 100)
    return kline.slice(start, end)
  }, [kline, visibleRange])

  // 最新一条数据作为价格信息
  const priceInfo = useMemo(() => {
    if (!kline.length) return null
    const latest = kline[kline.length - 1]
    const prev = kline.length > 1 ? kline[kline.length - 2] : null
    const changePct = prev && prev.close ? ((latest.close - prev.close) / prev.close * 100) : (latest.change_pct ?? null)
    return {
      close: latest.close,
      open: latest.open,
      high: latest.high,
      low: latest.low,
      volume: latest.volume,
      change_pct: changePct,
      trade_date: latest.trade_date,
    }
  }, [kline])

  // 可见区间的统计
  const stats = useMemo(() => {
    if (!visibleData.length) return null
    const closes = visibleData.map(k => k.close).filter(Boolean)
    const highs = visibleData.map(k => k.high).filter(Boolean)
    const lows = visibleData.map(k => k.low).filter(Boolean)
    const volumes = visibleData.map(k => k.volume).filter(Boolean)
    const high = Math.max(...highs)
    const low = Math.min(...lows)
    const avg = closes.reduce((a, b) => a + b, 0) / closes.length
    const avgVol = volumes.length ? Math.round(volumes.reduce((a, b) => a + b, 0) / volumes.length) : 0
    const latest = closes[closes.length - 1]
    const first = closes[0]
    const periodReturn = first ? ((latest - first) / first * 100) : 0
    const startDate = visibleData[0].trade_date
    const endDate = visibleData[visibleData.length - 1].trade_date
    return { high, low, avg, avgVol, periodReturn, dataPoints: visibleData.length, startDate, endDate }
  }, [visibleData])

  const handleDataZoom = useCallback((params: any) => {
    let start: number, end: number
    if (params.batch) {
      start = params.batch[0].start
      end = params.batch[0].end
    } else {
      start = params.start
      end = params.end
    }
    setVisibleRange([start, end])
  }, [])

  // ECharts 初始化和更新
  useEffect(() => {
    const container = chartRef.current
    if (!container) return

    // 每次 symbol 变化时重建实例，避免残留状态
    if (chartInstance.current) {
      chartInstance.current.dispose()
      chartInstance.current = null
    }

    const inst = echarts.init(container)
    chartInstance.current = inst
    inst.on('datazoom', handleDataZoom)

    if (!kline.length) {
      inst.showLoading({ text: '加载中...', maskColor: 'rgba(255,255,255,0.7)' })
    } else {
      inst.hideLoading()

      const dates = kline.map(k => k.trade_date)
      const ohlc = kline.map(k => [k.open, k.close, k.low, k.high])
      const volumes = kline.map(k => k.volume)
      const ma5 = calcMA(kline.map(k => k.close), 5)
      const ma20 = calcMA(kline.map(k => k.close), 20)
      const ma60 = calcMA(kline.map(k => k.close), 60)

      const option: EChartsOption = {
        animation: false,
        tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
        legend: {
          data: [
            { name: 'MA5', icon: 'roundRect', itemStyle: { color: '#f59e0b' } },
            { name: 'MA20', icon: 'roundRect', itemStyle: { color: '#3b82f6' } },
            { name: 'MA60', icon: 'roundRect', itemStyle: { color: '#8b5cf6' } },
          ],
          top: 0,
          itemWidth: 18,
          itemHeight: 3,
          textStyle: { fontSize: 11 },
        },
        grid: [
          { left: '8%', right: '4%', top: '10%', height: '55%' },
          { left: '8%', right: '4%', top: '70%', height: '18%' },
        ],
        xAxis: [
          { type: 'category', data: dates, gridIndex: 0, axisLabel: { show: false }, boundaryGap: true },
          { type: 'category', data: dates, gridIndex: 1, axisLabel: { fontSize: 10 } },
        ],
        yAxis: [
          { type: 'value', gridIndex: 0, scale: true, splitArea: { show: true, areaStyle: { color: ['rgba(250,250,250,0.1)', 'rgba(200,200,200,0.05)'] } } },
          { type: 'value', gridIndex: 1, splitNumber: 2, axisLabel: { fontSize: 10 } },
        ],
        dataZoom: [
          { type: 'inside', xAxisIndex: [0, 1], start: 70, end: 100 },
          { type: 'slider', xAxisIndex: [0, 1], start: 70, end: 100, top: '93%', height: 20 },
        ],
        series: [
          {
            name: 'K线', type: 'candlestick', data: ohlc, xAxisIndex: 0, yAxisIndex: 0,
            itemStyle: { color: BULLISH_COLOR, color0: BEARISH_COLOR, borderColor: BULLISH_COLOR, borderColor0: BEARISH_COLOR },
          },
          { name: 'MA5', type: 'line', data: ma5, smooth: true, lineStyle: { width: 1, color: '#f59e0b' }, symbol: 'none', xAxisIndex: 0, yAxisIndex: 0 },
          { name: 'MA20', type: 'line', data: ma20, smooth: true, lineStyle: { width: 1, color: '#3b82f6' }, symbol: 'none', xAxisIndex: 0, yAxisIndex: 0 },
          { name: 'MA60', type: 'line', data: ma60, smooth: true, lineStyle: { width: 1, color: '#8b5cf6' }, symbol: 'none', xAxisIndex: 0, yAxisIndex: 0 },
          {
            name: '成交量', type: 'bar', data: volumes, xAxisIndex: 1, yAxisIndex: 1,
            itemStyle: { color: (params: any) => {
              const idx = params.dataIndex
              return ohlc[idx][1] >= ohlc[idx][0] ? BULLISH_COLOR : BEARISH_COLOR
            }},
          },
        ],
      }

      inst.setOption(option, true)
      setTimeout(() => inst.resize(), 0)
    }

    const handleResize = () => chartInstance.current?.resize()
    window.addEventListener('resize', handleResize)
    return () => {
      window.removeEventListener('resize', handleResize)
    }
  }, [kline, handleDataZoom])

  useEffect(() => {
    return () => {
      chartInstance.current?.dispose()
      chartInstance.current = null
    }
  }, [])

  const pct = realtime?.change_pct ?? priceInfo?.change_pct ?? null
  const isUp = pct != null && pct > 0
  const isDown = pct != null && pct < 0
  const displayPrice = realtime?.latest_price ?? priceInfo?.close
  const isRealtime = realtime?.latest_price != null

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <Link to="/market" className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"><ArrowLeft className="w-5 h-5" /></Link>
        <h2 className="text-lg font-semibold">{symbol}</h2>
        {isRealtime && <span className="text-xs text-green-500 bg-green-50 dark:bg-green-900/20 px-1.5 py-0.5 rounded">实时</span>}
      </div>

      {/* 价格卡片 */}
      {(priceInfo || realtime) && (
        <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-5">
          <div className="flex items-baseline gap-4 mb-4">
            <span className={clsx('text-3xl font-bold', isUp ? 'text-bullish' : isDown ? 'text-bearish' : '')}>
              {displayPrice?.toFixed(2) ?? '--'}
            </span>
            <span className={clsx('text-lg font-medium', isUp ? 'text-bullish' : isDown ? 'text-bearish' : 'text-gray-500')}>
              {pct != null ? `${isUp ? '+' : ''}${pct.toFixed(2)}%` : '--'}
              {isUp && <TrendingUp className="inline w-4 h-4 ml-1" />}
              {isDown && <TrendingDown className="inline w-4 h-4 ml-1" />}
            </span>
            <span className="text-sm text-gray-400 ml-auto">{priceInfo?.trade_date}</span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
            <InfoItem label="开盘" value={priceInfo?.open?.toFixed(2)} />
            <InfoItem label="最高" value={priceInfo?.high?.toFixed(2)} />
            <InfoItem label="最低" value={priceInfo?.low?.toFixed(2)} />
            <InfoItem label="成交量" value={priceInfo?.volume?.toLocaleString()} />
          </div>
        </div>
      )}

      {/* 统计指标 - 跟随可见区间 */}
      {stats && (
        <div>
          <div className="text-xs text-gray-400 dark:text-gray-500 mb-2">
            可见区间: {stats.startDate} ~ {stats.endDate} ({stats.dataPoints} 个交易日)
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            <StatCard icon={<TrendingUp className="w-4 h-4" />} label="区间最高" value={stats.high.toFixed(2)} />
            <StatCard icon={<TrendingDown className="w-4 h-4" />} label="区间最低" value={stats.low.toFixed(2)} />
            <StatCard icon={<BarChart3 className="w-4 h-4" />} label="区间均价" value={stats.avg.toFixed(2)} />
            <StatCard icon={<Activity className="w-4 h-4" />} label="日均成交量" value={stats.avgVol.toLocaleString()} />
            <StatCard
              icon={<TrendingUp className="w-4 h-4" />}
              label="区间涨跌"
              value={`${stats.periodReturn > 0 ? '+' : ''}${stats.periodReturn.toFixed(2)}%`}
              valueClass={stats.periodReturn > 0 ? 'text-bullish' : stats.periodReturn < 0 ? 'text-bearish' : ''}
            />
          </div>
        </div>
      )}

      {/* K线图 */}
      <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-4">
        <div ref={chartRef} style={{ width: '100%', height: 500 }} />
      </div>
    </div>
  )
}

function InfoItem({ label, value }: { label: string; value?: string | null }) {
  return (
    <div>
      <div className="text-gray-400 dark:text-gray-500 text-xs mb-0.5">{label}</div>
      <div className="font-mono text-sm">{value ?? '--'}</div>
    </div>
  )
}

function StatCard({ icon, label, value, valueClass }: { icon: React.ReactNode; label: string; value: string; valueClass?: string }) {
  return (
    <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-3">
      <div className="flex items-center gap-1.5 text-gray-400 dark:text-gray-500 text-xs mb-1">
        {icon}
        {label}
      </div>
      <div className={clsx('font-mono text-sm font-medium', valueClass)}>{value}</div>
    </div>
  )
}

function calcMA(data: number[], period: number): (number | null)[] {
  return data.map((_, i) => {
    if (i < period - 1) return null
    const slice = data.slice(i - period + 1, i + 1)
    return +(slice.reduce((a, b) => a + b, 0) / period).toFixed(2)
  })
}
