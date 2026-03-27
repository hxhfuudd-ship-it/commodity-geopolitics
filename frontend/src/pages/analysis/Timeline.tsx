import { useEffect, useState, useRef, useMemo, useCallback } from 'react'
import { newsApi, marketApi, type GeoEvent, type PriceDaily } from '../../lib/api'
import { COMMODITIES } from '../../lib/constants'
import { clsx } from 'clsx'
import echarts from '../../lib/echarts'
import type { EChartsOption } from 'echarts'

const SEV_COLOR: Record<number, string> = {
  5: '#b83250', 4: '#b87830', 3: '#a89838', 2: '#388c78', 1: '#64748b',
}
const SEV_TAG: Record<number, string> = {
  5: 'bg-rose-50 text-rose-700 dark:bg-rose-900/20 dark:text-rose-400',
  4: 'bg-amber-50 text-amber-700 dark:bg-amber-900/20 dark:text-amber-400',
  3: 'bg-yellow-50 text-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-400',
  2: 'bg-teal-50 text-teal-700 dark:bg-teal-900/20 dark:text-teal-400',
  1: 'bg-slate-50 text-slate-600 dark:bg-slate-800 dark:text-slate-400',
}

interface Laid {
  dateIdx: number; date: string; price: number; event: GeoEvent
  labelPos: 'top' | 'bottom'; labelOff: [number, number]
}

function layoutEvents(
  pts: { dateIdx: number; date: string; price: number; event: GeoEvent }[],
  total: number,
): Laid[] {
  if (!pts.length) return []
  const sorted = [...pts].sort((a, b) => a.dateIdx - b.dateIdx)
  const out: Laid[] = []
  const threshold = Math.max(total * 0.025, 30)

  const groups: typeof sorted[] = []
  let cur = [sorted[0]]
  for (let i = 1; i < sorted.length; i++) {
    if (sorted[i].dateIdx - sorted[i - 1].dateIdx > threshold) {
      groups.push(cur); cur = [sorted[i]]
    } else { cur.push(sorted[i]) }
  }
  groups.push(cur)

  for (const group of groups) {
    const n = group.length
    group.forEach((pt, gi) => {
      const isUp = gi % 2 === 0
      const tier = Math.floor(gi / 2)
      const baseY = 38 + tier * 34
      const yLabel = isUp ? -baseY : baseY
      const xSpread = n > 2 ? (gi - (n - 1) / 2) * 14 : 0
      out.push({
        ...pt,
        labelPos: isUp ? 'top' as const : 'bottom' as const,
        labelOff: [xSpread, yLabel] as [number, number],
      })
    })
  }
  return out
}

export default function Timeline() {
  const [events, setEvents] = useState<GeoEvent[]>([])
  const [kline, setKline] = useState<PriceDaily[]>([])
  const [symbol, setSymbol] = useState('AU')
  const [initialLoading, setInitialLoading] = useState(true)
  const [selectedEvent, setSelectedEvent] = useState<GeoEvent | null>(null)
  const chartRef = useRef<HTMLDivElement>(null)
  const chart = useRef<echarts.ECharts | null>(null)

  useEffect(() => {
    newsApi.getEventsTimeline().then(setEvents).catch(console.error)
  }, [])

  useEffect(() => {
    const first = kline.length === 0
    if (first) setInitialLoading(true)
    setSelectedEvent(null)
    if (chart.current) chart.current.showLoading({ text: '加载中...', maskColor: 'rgba(255,255,255,0.7)' })
    marketApi.getKline(symbol)
      .then(data => {
        setKline(data)
      })
      .catch(console.error)
      .finally(() => {
        if (first) setInitialLoading(false)
        if (chart.current) chart.current.hideLoading()
      })
  }, [symbol])

  const option = useMemo<EChartsOption | null>(() => {
    if (!kline.length) return null
    const dates = kline.map(k => k.trade_date)
    const prices = kline.map(k => k.close)
    const name = COMMODITIES.find(c => c.symbol === symbol)?.name || symbol

    const raw = events.map(e => {
      if (e.start_date < dates[0] || e.start_date > dates[dates.length - 1]) return null
      const idx = dates.findIndex(d => d >= e.start_date)
      if (idx < 0) return null
      return { dateIdx: idx, date: dates[idx], price: prices[idx], event: e }
    }).filter(Boolean) as { dateIdx: number; date: string; price: number; event: GeoEvent }[]

    const laid = layoutEvents(raw, dates.length)

    const idxs = laid.map(p => p.dateIdx)
    let zStart = 0
    if (idxs.length) {
      zStart = Math.max(0, ((Math.min(...idxs) - 60) / dates.length) * 100)
    }

    // Small dots on curve + label cards with dashed leader lines
    const dotData = laid.map(pt => {
      const col = SEV_COLOR[pt.event.severity] || '#64748b'
      return {
        value: [pt.date, pt.price],
        symbolSize: 8,
        itemStyle: { color: '#fff', borderColor: col, borderWidth: 2, shadowBlur: 4, shadowColor: 'rgba(0,0,0,0.1)' },
        label: {
          show: true,
          formatter: pt.event.title,
          position: pt.labelPos,
          offset: pt.labelOff,
          fontSize: 11,
          fontFamily: '-apple-system, "PingFang SC", "Noto Sans SC", sans-serif',
          color: col,
          backgroundColor: 'rgba(255,255,255,0.95)',
          borderColor: 'rgba(0,0,0,0.06)',
          borderWidth: 1,
          borderRadius: 6,
          padding: [4, 9] as [number, number],
          shadowBlur: 6,
          shadowOffsetY: 2,
          shadowColor: 'rgba(0,0,0,0.05)',
          lineHeight: 14,
        },
        labelLine: {
          show: true,
          lineStyle: { color: 'rgba(148,163,184,0.5)', width: 1, type: 'dashed' as const },
          length2: Math.abs(pt.labelOff[1]) * 0.55,
        },
        _event: pt.event,
      }
    })

    return {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'line', lineStyle: { color: 'rgba(148,163,184,0.25)', type: 'dashed' } },
        backgroundColor: 'rgba(255,255,255,0.97)',
        borderColor: 'rgba(0,0,0,0.05)',
        borderWidth: 1,
        padding: [10, 14],
        textStyle: { fontSize: 12, color: '#374151' },
        extraCssText: 'border-radius:8px;box-shadow:0 4px 16px rgba(0,0,0,0.06);',
        formatter: (params: any) => {
          const arr = Array.isArray(params) ? params : [params]
          const lp = arr.find((p: any) => p.seriesIndex === 0)
          if (!lp) return ''
          const d = lp.axisValue
          let tip = `<div style="font-family:-apple-system,'PingFang SC',sans-serif"><span style="color:#94a3b8;font-size:11px">${d}</span><br/><b style="font-size:13px">${name}: ${lp.value}</b></div>`
          const matched = events.filter(e => {
            const ei = dates.findIndex(dd => dd >= e.start_date)
            return ei >= 0 && dates[ei] === d
          })
          for (const e of matched) {
            const col = SEV_COLOR[e.severity] || '#64748b'
            tip += `<div style="margin-top:5px;padding:3px 7px;border-left:3px solid ${col};background:rgba(248,250,252,0.9);border-radius:0 4px 4px 0;font-size:11px"><b>${e.title}</b><br/><span style="color:#94a3b8">${e.event_type} · ${'★'.repeat(e.severity)}</span></div>`
          }
          return tip
        },
      },
      grid: { left: '6%', right: '5%', top: '6%', bottom: '14%', containLabel: true },
      xAxis: {
        type: 'category', data: dates, boundaryGap: true,
        axisLine: { lineStyle: { color: '#e2e8f0' } },
        axisTick: { show: false },
        axisLabel: { fontSize: 10, color: '#94a3b8', margin: 12 },
      },
      yAxis: {
        type: 'value', scale: true, name,
        nameTextStyle: { fontSize: 11, color: '#64748b', padding: [0, 0, 8, 0] },
        axisLine: { show: false }, axisTick: { show: false },
        splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } },
        axisLabel: { fontSize: 10, color: '#94a3b8' },
      },
      dataZoom: [
        { type: 'inside', start: zStart, end: 100 },
        {
          type: 'slider', start: zStart, end: 100, height: 22, bottom: 6,
          borderColor: 'transparent', backgroundColor: 'rgba(241,245,249,0.6)',
          fillerColor: 'rgba(139,92,246,0.08)',
          handleStyle: { color: '#94a3b8', borderColor: '#94a3b8' },
          handleSize: '60%',
          textStyle: { fontSize: 10, color: '#94a3b8' },
        },
      ],
      series: [
        {
          name, type: 'line', data: prices,
          smooth: 0.15, symbol: 'none', z: 1,
          sampling: 'lttb',
          lineStyle: {
            width: 1.8,
            color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
              { offset: 0, color: '#3b82f6' },
              { offset: 0.5, color: '#8b5cf6' },
              { offset: 1, color: '#ef4444' },
            ]),
          },
          itemStyle: { color: '#ef4444' },
        },
        {
          name: '事件', type: 'scatter',
          data: dotData, z: 10,
        },
      ],
    }
  }, [kline, events, symbol])

  useEffect(() => {
    if (!chartRef.current) return
    if (!chart.current) {
      chart.current = echarts.init(chartRef.current)
      chart.current.on('click', (params: any) => {
        if (params.seriesIndex === 1 && params.data?._event) setSelectedEvent(params.data._event)
      })
    }
    if (option) chart.current.setOption(option, true)
    const h = () => chart.current?.resize()
    window.addEventListener('resize', h)
    return () => window.removeEventListener('resize', h)
  }, [option])

  useEffect(() => { return () => { chart.current?.dispose(); chart.current = null } }, [])

  const filteredEvents = useMemo(() => {
    if (!kline.length) return events
    const first = kline[0].trade_date
    const last = kline[kline.length - 1].trade_date
    return events.filter(e => e.start_date >= first && e.start_date <= last)
  }, [events, kline])

  const focusEvent = useCallback((e: GeoEvent) => {
    if (!chart.current || !kline.length) return
    setSelectedEvent(e)
    const dates = kline.map(k => k.trade_date)
    const idx = dates.findIndex(d => d >= e.start_date)
    if (idx < 0) return
    const pct = (idx / dates.length) * 100
    chart.current.dispatchAction({ type: 'dataZoom', start: Math.max(0, pct - 10), end: Math.min(100, pct + 10) })
  }, [kline])

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">事件 vs 价格时间轴</h2>
        <div className="flex items-center gap-4">
          <div className="hidden sm:flex items-center gap-3 text-[11px] text-gray-400">
            {[5, 4, 3, 2, 1].map(s => (
              <span key={s} className="flex items-center gap-1">
                <span className="inline-block w-2 h-2 rounded-full border" style={{ backgroundColor: SEV_COLOR[s], borderColor: SEV_COLOR[s] }} />
                {s}级
              </span>
            ))}
          </div>
          <select value={symbol} onChange={e => setSymbol(e.target.value)}
            className="px-3 py-1.5 text-sm border rounded-lg bg-white dark:bg-gray-800 dark:border-gray-700 dark:text-gray-200 shadow-sm">
            {COMMODITIES.map(c => <option key={c.symbol} value={c.symbol}>{c.name}</option>)}
          </select>
        </div>
      </div>

      {initialLoading ? (
        <div className="flex justify-center py-16"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" /></div>
      ) : (
        <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-100 dark:border-gray-800 p-5 shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
          <div ref={chartRef} style={{ width: '100%', height: 560 }} />
        </div>
      )}

      {/* Selected event detail */}
      {selectedEvent && (
        <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-100 dark:border-gray-800 p-4 shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className="px-2.5 py-0.5 rounded-md text-xs font-medium text-white"
                  style={{ backgroundColor: SEV_COLOR[selectedEvent.severity] || '#64748b' }}>
                  {selectedEvent.event_type} · {'★'.repeat(selectedEvent.severity)}
                </span>
                <span className="text-xs text-gray-400">{selectedEvent.start_date}</span>
              </div>
              <h3 className="font-medium">{selectedEvent.title}</h3>
              {selectedEvent.description && (
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1 leading-relaxed">{selectedEvent.description}</p>
              )}
            </div>
            <button onClick={() => setSelectedEvent(null)}
              className="flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 text-sm">×</button>
          </div>
        </div>
      )}

      {/* Event list */}
      {filteredEvents.length > 0 && (
        <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-100 dark:border-gray-800 p-4 shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
          <h3 className="text-sm font-medium mb-3">事件列表 ({filteredEvents.length}) <span className="text-gray-400 font-normal text-xs">点击定位图表</span></h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-1.5">
            {filteredEvents.map(e => (
              <div key={e.id} onClick={() => focusEvent(e)}
                className={clsx(
                  'flex items-center gap-2.5 text-sm px-3 py-2.5 rounded-lg cursor-pointer transition-all',
                  selectedEvent?.id === e.id
                    ? 'bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 shadow-sm'
                    : 'hover:bg-gray-50 dark:hover:bg-gray-800/40 border border-transparent'
                )}>
                <span className="flex-shrink-0 w-2.5 h-2.5 rounded-full"
                  style={{ backgroundColor: SEV_COLOR[e.severity] || '#64748b' }} />
                <span className="text-gray-400 whitespace-nowrap text-xs tabular-nums">{e.start_date}</span>
                <span className={clsx('px-1.5 py-0.5 rounded text-[10px] whitespace-nowrap', SEV_TAG[e.severity] || SEV_TAG[1])}>
                  {e.event_type}
                </span>
                <span className="text-gray-700 dark:text-gray-300 truncate">{e.title}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
