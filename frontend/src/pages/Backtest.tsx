import { useEffect, useState, useRef, useMemo } from 'react'
import { backtestApi, type BacktestEvent, type BacktestResult, type BacktestCompare } from '../lib/api'
import { COMMODITIES } from '../lib/constants'
import { clsx } from 'clsx'
import echarts from '../lib/echarts'
import type { EChartsOption } from 'echarts'

const COLORS = ['#3b82f6', '#ef4444', '#22c55e', '#f59e0b', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316']

export default function Backtest() {
  const [events, setEvents] = useState<BacktestEvent[]>([])
  const [selectedEvent, setSelectedEvent] = useState<number | null>(null)
  const [selectedCommodities, setSelectedCommodities] = useState<string[]>(['AU', 'SC'])
  const [beforeDays, setBeforeDays] = useState(30)
  const [afterDays, setAfterDays] = useState(60)
  const [result, setResult] = useState<BacktestResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [eventsLoading, setEventsLoading] = useState(true)

  // Compare mode
  const [compareMode, setCompareMode] = useState(false)
  const [compareEventIds, setCompareEventIds] = useState<number[]>([])
  const [compareCommodity, setCompareCommodity] = useState('AU')
  const [compareResult, setCompareResult] = useState<BacktestCompare | null>(null)
  const [compareLoading, setCompareLoading] = useState(false)

  const singleChartRef = useRef<HTMLDivElement>(null)
  const singleInstance = useRef<echarts.ECharts | null>(null)
  const compareChartRef = useRef<HTMLDivElement>(null)
  const compareInstance = useRef<echarts.ECharts | null>(null)

  useEffect(() => {
    backtestApi.getEvents()
      .then(data => {
        setEvents(data)
        if (data.length > 0) setSelectedEvent(data[0].id)
      })
      .catch(console.error)
      .finally(() => setEventsLoading(false))
  }, [])

  const runBacktest = () => {
    if (!selectedEvent || selectedCommodities.length === 0) return
    setLoading(true)
    backtestApi.run(selectedEvent, selectedCommodities, beforeDays, afterDays)
      .then(setResult)
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  const runCompare = () => {
    if (compareEventIds.length < 2) return
    setCompareLoading(true)
    backtestApi.compare(compareEventIds, compareCommodity)
      .then(setCompareResult)
      .catch(console.error)
      .finally(() => setCompareLoading(false))
  }

  const toggleCommodity = (symbol: string) => {
    setSelectedCommodities(prev =>
      prev.includes(symbol) ? prev.filter(s => s !== symbol) : [...prev, symbol]
    )
  }

  const toggleCompareEvent = (id: number) => {
    setCompareEventIds(prev =>
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    )
  }

  // Single backtest chart
  const option = useMemo<EChartsOption | null>(() => {
    if (!result?.data) return null
    const entries = Object.entries(result.data)
    if (entries.length === 0) return null

    const firstDates = entries[0][1].dates
    // Find event date index for markLine
    const eventDate = result.event.start_date
    const eventIdx = firstDates.findIndex(d => d >= eventDate)
    const eventDateOnChart = eventIdx >= 0 ? firstDates[eventIdx] : eventDate

    const series = entries.map(([symbol, d], idx) => ({
      name: COMMODITIES.find(c => c.symbol === symbol)?.name || symbol,
      type: 'line' as const,
      data: d.prices,
      smooth: false,
      color: COLORS[idx % COLORS.length],
      lineStyle: { width: 2 },
      itemStyle: { color: COLORS[idx % COLORS.length] },
      symbol: 'none' as const,
    }))

    return {
      tooltip: { trigger: 'axis' },
      legend: { data: series.map(s => s.name), top: 0, icon: 'roundRect', itemWidth: 14, itemHeight: 3 },
      grid: { left: '8%', right: '4%', top: '12%', bottom: '15%' },
      xAxis: { type: 'category', data: firstDates },
      yAxis: { type: 'value', scale: true, name: '归一化 (事件日=100)' },
      dataZoom: [{ type: 'inside', start: 0, end: 100 }, { type: 'slider', start: 0, end: 100, showDataShadow: false }],
      series: [{
        ...series[0],
        markLine: {
          symbol: 'none', silent: true,
          data: [{
            xAxis: eventDateOnChart,
            label: {
              formatter: `事件日\n${eventDate}`,
              fontSize: 11,
              color: '#fff',
              backgroundColor: '#ef4444',
              borderRadius: 4,
              padding: [4, 8],
            },
            lineStyle: { color: '#ef4444', type: 'dashed', width: 2 },
          }],
        },
        markPoint: eventIdx >= 0 ? {
          data: [{
            coord: [eventDateOnChart, entries[0][1].prices[eventIdx]],
            symbol: 'circle',
            symbolSize: 10,
            itemStyle: { color: '#ef4444', borderColor: '#fff', borderWidth: 2 },
            label: { show: false },
          }],
        } : undefined,
      } as any, ...series.slice(1)],
    }
  }, [result])

  // Compare chart
  const compareOption = useMemo<EChartsOption | null>(() => {
    if (!compareResult?.events?.length) return null
    const series = compareResult.events.map((ev, idx) => {
      // Re-index dates relative to event day (day 0)
      const eventDate = ev.event.start_date
      const eventIdx = ev.dates.findIndex(d => d >= eventDate)
      const relativeDays = ev.dates.map((_, i) => i - (eventIdx >= 0 ? eventIdx : 0))
      return {
        name: `${ev.event.title} (${ev.event.start_date})`,
        type: 'line' as const,
        data: ev.prices,
        smooth: false,
        lineStyle: { width: 2, color: COLORS[idx % COLORS.length] },
        itemStyle: { color: COLORS[idx % COLORS.length] },
        symbol: 'none' as const,
        _relativeDays: relativeDays,
      }
    })

    // Use the longest relative day range as x-axis
    const allDays = new Set<number>()
    series.forEach(s => s._relativeDays.forEach(d => allDays.add(d)))
    const xDays = Array.from(allDays).sort((a, b) => a - b)

    const alignedSeries = series.map(s => {
      const dayMap = new Map(s._relativeDays.map((d, i) => [d, s.data[i]]))
      return {
        name: s.name,
        type: s.type,
        data: xDays.map(d => dayMap.get(d) ?? null),
        smooth: s.smooth,
        lineStyle: s.lineStyle,
        itemStyle: s.itemStyle,
        symbol: s.symbol,
        connectNulls: true,
      }
    })

    return {
      tooltip: { trigger: 'axis' },
      legend: { top: 0, type: 'scroll', icon: 'roundRect', itemWidth: 14, itemHeight: 3 },
      grid: { left: '8%', right: '4%', top: '14%', bottom: '15%' },
      xAxis: { type: 'category', data: xDays.map(d => `T${d >= 0 ? '+' : ''}${d}`) },
      yAxis: { type: 'value', scale: true, name: '归一化 (事件日=100)' },
      dataZoom: [{ type: 'inside', start: 0, end: 100 }, { type: 'slider', start: 0, end: 100, showDataShadow: false }],
      series: [{
        ...alignedSeries[0],
        markLine: {
          symbol: 'none', silent: true,
          data: [{
            xAxis: `T+0`,
            label: { formatter: '事件日', color: '#ef4444' },
            lineStyle: { color: '#ef4444', type: 'dashed', width: 2 },
          }],
        },
      }, ...alignedSeries.slice(1)],
    }
  }, [compareResult])

  // Single backtest chart
  useEffect(() => {
    if (!singleChartRef.current) return
    if (singleInstance.current) {
      if (singleInstance.current.getDom() !== singleChartRef.current) {
        singleInstance.current.dispose()
        singleInstance.current = null
      }
    }
    if (!singleInstance.current) singleInstance.current = echarts.init(singleChartRef.current)
    if (option) singleInstance.current.setOption(option, true)
    else singleInstance.current.clear()
    setTimeout(() => singleInstance.current?.resize(), 0)
    const h = () => singleInstance.current?.resize()
    window.addEventListener('resize', h)
    return () => window.removeEventListener('resize', h)
  }, [option])

  // Compare chart
  useEffect(() => {
    if (!compareChartRef.current) return
    if (compareInstance.current) {
      if (compareInstance.current.getDom() !== compareChartRef.current) {
        compareInstance.current.dispose()
        compareInstance.current = null
      }
    }
    if (!compareInstance.current) compareInstance.current = echarts.init(compareChartRef.current)
    if (compareOption) compareInstance.current.setOption(compareOption, true)
    else compareInstance.current.clear()
    setTimeout(() => compareInstance.current?.resize(), 0)
    const h = () => compareInstance.current?.resize()
    window.addEventListener('resize', h)
    return () => window.removeEventListener('resize', h)
  }, [compareOption])

  useEffect(() => {
    return () => {
      singleInstance.current?.dispose(); singleInstance.current = null
      compareInstance.current?.dispose(); compareInstance.current = null
    }
  }, [])

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">事件回测</h2>
        <div className="flex gap-2">
          <button onClick={() => setCompareMode(false)}
            className={clsx('px-3 py-1.5 text-sm rounded-md', !compareMode ? 'bg-primary-600 text-white' : 'bg-white dark:bg-gray-800 border dark:border-gray-700 text-gray-600 dark:text-gray-300')}>
            单事件回测
          </button>
          <button onClick={() => setCompareMode(true)}
            className={clsx('px-3 py-1.5 text-sm rounded-md', compareMode ? 'bg-primary-600 text-white' : 'bg-white dark:bg-gray-800 border dark:border-gray-700 text-gray-600 dark:text-gray-300')}>
            多事件对比
          </button>
        </div>
      </div>

      {eventsLoading ? (
        <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" /></div>
      ) : !compareMode ? (
        /* Single backtest mode */
        <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-4 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">选择事件</label>
            <select value={selectedEvent ?? ''} onChange={e => setSelectedEvent(Number(e.target.value))}
              className="w-full px-3 py-2 text-sm border rounded-md bg-white dark:bg-gray-800 dark:border-gray-700 dark:text-gray-200">
              {events.map(ev => (
                <option key={ev.id} value={ev.id}>
                  [{ev.start_date}] {ev.title} (严重度: {ev.severity})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">选择商品</label>
            <div className="flex flex-wrap gap-2">
              {COMMODITIES.map(c => (
                <button key={c.symbol} onClick={() => toggleCommodity(c.symbol)}
                  className={clsx('px-2.5 py-1 text-xs rounded-full',
                    selectedCommodities.includes(c.symbol) ? 'bg-primary-600 text-white' : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400')}>
                  {c.name}
                </button>
              ))}
            </div>
          </div>

          <div className="flex gap-4">
            <div>
              <label className="block text-xs text-gray-500 mb-1">事件前 (天)</label>
              <input type="number" value={beforeDays} onChange={e => setBeforeDays(+e.target.value)} min={1} max={365}
                className="w-20 px-2 py-1.5 text-sm border rounded-md bg-white dark:bg-gray-800 dark:border-gray-700 dark:text-gray-200" />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">事件后 (天)</label>
              <input type="number" value={afterDays} onChange={e => setAfterDays(+e.target.value)} min={1} max={365}
                className="w-20 px-2 py-1.5 text-sm border rounded-md bg-white dark:bg-gray-800 dark:border-gray-700 dark:text-gray-200" />
            </div>
          </div>

          <button onClick={runBacktest}
            disabled={!selectedEvent || selectedCommodities.length === 0 || loading}
            className="px-4 py-2 text-sm bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50">
            {loading ? '回测中...' : '运行回测'}
          </button>
        </div>
      ) : (
        /* Compare mode */
        <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-4 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">选择事件（至少2个）</label>
            <div className="space-y-1.5">
              {events.map(ev => (
                <label key={ev.id} className="flex items-center gap-2 text-sm cursor-pointer">
                  <input type="checkbox" checked={compareEventIds.includes(ev.id)}
                    onChange={() => toggleCompareEvent(ev.id)}
                    className="rounded border-gray-300" />
                  <span className="text-gray-400 text-xs">{ev.start_date}</span>
                  <span className={clsx('px-1.5 py-0.5 rounded text-xs',
                    ev.severity >= 4 ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' : 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400')}>
                    {ev.event_type}
                  </span>
                  <span className="dark:text-gray-300">{ev.title}</span>
                </label>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">对比品种</label>
            <select value={compareCommodity} onChange={e => setCompareCommodity(e.target.value)}
              className="px-3 py-2 text-sm border rounded-md bg-white dark:bg-gray-800 dark:border-gray-700 dark:text-gray-200">
              {COMMODITIES.map(c => <option key={c.symbol} value={c.symbol}>{c.name}</option>)}
            </select>
          </div>

          <button onClick={runCompare}
            disabled={compareEventIds.length < 2 || compareLoading}
            className="px-4 py-2 text-sm bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50">
            {compareLoading ? '对比中...' : '运行对比'}
          </button>
        </div>
      )}

      {/* Single backtest chart */}
      <div style={{ display: !compareMode && result ? undefined : 'none' }}>
        <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-4">
          <h3 className="text-sm font-medium mb-2">
            {result?.event.title}  ·  事件日: {result?.event.start_date}
          </h3>
          <div ref={singleChartRef} style={{ width: '100%', height: 450 }} />
        </div>
      </div>

      {/* Compare chart */}
      <div style={{ display: compareMode && compareResult ? undefined : 'none' }}>
        <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-4">
          <h3 className="text-sm font-medium mb-2">
            事件对比: {COMMODITIES.find(c => c.symbol === compareCommodity)?.name || compareCommodity}
          </h3>
          <div ref={compareChartRef} style={{ width: '100%', height: 450 }} />
        </div>
      </div>

      {/* Impact summary for single backtest */}
      {!compareMode && result?.data && (
        <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-4">
          <h3 className="text-sm font-medium mb-1">影响统计</h3>
          <p className="text-xs text-gray-400 mb-3">
            事件: {result.event.title} · 发生日期: <span className="text-red-500 font-medium">{result.event.start_date}</span>
          </p>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500 border-b dark:border-gray-700">
                  <th className="pb-2 pr-4">品种</th>
                  <th className="pb-2 pr-4">事件日价格</th>
                  <th className="pb-2 pr-4">事件后最高</th>
                  <th className="pb-2 pr-4">事件后最低</th>
                  <th className="pb-2 pr-4">最大涨幅</th>
                  <th className="pb-2">最大跌幅</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(result.data).map(([symbol, d]) => {
                  const raw = (d as any).raw_prices as (number | null)[]
                  const basePrice = (d as any).base_price as number | null
                  const eventIdx = d.dates.findIndex(dt => dt >= result.event.start_date)
                  const afterRaw = (raw || d.prices).slice(eventIdx >= 0 ? eventIdx : 0).filter((p): p is number => p != null)
                  const maxP = afterRaw.length ? Math.max(...afterRaw) : 0
                  const minP = afterRaw.length ? Math.min(...afterRaw) : 0
                  const base = basePrice || (afterRaw.length ? afterRaw[0] : 0)
                  const maxChg = base > 0 ? ((maxP - base) / base * 100) : 0
                  const minChg = base > 0 ? ((minP - base) / base * 100) : 0
                  return (
                    <tr key={symbol} className="border-b dark:border-gray-800">
                      <td className="py-2 pr-4 font-medium">{COMMODITIES.find(c => c.symbol === symbol)?.name || symbol}</td>
                      <td className="py-2 pr-4">{base ? base.toFixed(2) : '-'}</td>
                      <td className="py-2 pr-4">{maxP ? maxP.toFixed(2) : '-'}</td>
                      <td className="py-2 pr-4">{minP ? minP.toFixed(2) : '-'}</td>
                      <td className={clsx('py-2 pr-4', maxChg >= 0 ? 'text-red-500' : 'text-green-500')}>{maxChg >= 0 ? '+' : ''}{maxChg.toFixed(2)}%</td>
                      <td className={clsx('py-2', minChg >= 0 ? 'text-red-500' : 'text-green-500')}>{minChg >= 0 ? '+' : ''}{minChg.toFixed(2)}%</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
