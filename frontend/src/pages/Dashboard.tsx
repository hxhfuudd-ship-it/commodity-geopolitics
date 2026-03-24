import { useEffect, useState, useRef } from 'react'
import { Link } from 'react-router-dom'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { marketApi, type MarketOverviewItem } from '../lib/api'
import { clsx } from 'clsx'

export default function Dashboard() {
  const [overview, setOverview] = useState<MarketOverviewItem[]>([])
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState<string>('')
  const prevPrices = useRef<Record<string, number>>({})
  const [flashing, setFlashing] = useState<Record<string, 'up' | 'down'>>({})

  // Initial load
  useEffect(() => {
    marketApi.getOverview()
      .then(data => {
        setOverview(data)
        setLastUpdate(new Date().toLocaleTimeString('zh-CN'))
        data.forEach(d => { if (d.latest_price != null) prevPrices.current[d.symbol] = d.latest_price })
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  // SSE realtime stream
  useEffect(() => {
    const es = new EventSource('/api/v1/market/overview/stream')
    es.onmessage = (event) => {
      try {
        const data: MarketOverviewItem[] = JSON.parse(event.data)
        // Detect price changes for flash effect
        const newFlash: Record<string, 'up' | 'down'> = {}
        data.forEach(d => {
          if (d.latest_price != null) {
            const prev = prevPrices.current[d.symbol]
            if (prev != null && d.latest_price !== prev) {
              newFlash[d.symbol] = d.latest_price > prev ? 'up' : 'down'
            }
            prevPrices.current[d.symbol] = d.latest_price
          }
        })
        setOverview(data)
        setLastUpdate(new Date().toLocaleTimeString('zh-CN'))
        if (Object.keys(newFlash).length > 0) {
          setFlashing(newFlash)
          setTimeout(() => setFlashing({}), 600)
        }
      } catch {}
    }
    es.onerror = () => {
      // Reconnect handled automatically by EventSource
    }
    return () => es.close()
  }, [])

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" /></div>
  }

  const metals = overview.filter(i => i.category === 'metal')
  const energy = overview.filter(i => i.category === 'energy')
  const agriculture = overview.filter(i => i.category === 'agriculture')
  const chemical = overview.filter(i => i.category === 'chemical')

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">市场概览</h2>
        <div className="flex items-center gap-3 text-xs text-gray-400">
          <span className="inline-block w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
          <span>实时 · {lastUpdate}</span>
        </div>
      </div>

      <Section title="金属" items={metals} flashing={flashing} />
      <Section title="能源" items={energy} flashing={flashing} />
      <Section title="农产品" items={agriculture} flashing={flashing} />
      <Section title="化工" items={chemical} flashing={flashing} />
    </div>
  )
}

function Section({ title, items, flashing }: { title: string; items: MarketOverviewItem[]; flashing: Record<string, 'up' | 'down'> }) {
  return (
    <div>
      <h3 className="text-sm font-medium text-gray-500 mb-3">{title}</h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
        {items.map(item => {
          const flash = flashing[item.symbol]
          return (
            <Link
              key={item.symbol}
              to={`/market/${item.symbol}`}
              className={clsx(
                'bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-4 hover:shadow-md transition-all duration-300',
                flash === 'up' && 'ring-1 ring-red-400/50 bg-red-50/30 dark:bg-red-900/10',
                flash === 'down' && 'ring-1 ring-green-400/50 bg-green-50/30 dark:bg-green-900/10',
              )}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-900 dark:text-gray-100">{item.name_cn}</span>
                <span className="text-xs text-gray-400">{item.symbol}</span>
              </div>
              <div className={clsx(
                'text-xl font-bold mb-1 font-mono transition-colors duration-300',
                flash === 'up' && 'text-bullish',
                flash === 'down' && 'text-bearish',
              )}>
                {item.latest_price != null ? item.latest_price.toFixed(2) : '--'}
              </div>
              <div className={clsx('flex items-center gap-1 text-sm', getPctColor(item.change_pct))}>
                {getPctIcon(item.change_pct)}
                <span>{item.change_pct != null ? `${item.change_pct > 0 ? '+' : ''}${item.change_pct.toFixed(2)}%` : '--'}</span>
              </div>
            </Link>
          )
        })}
      </div>
    </div>
  )
}

function getPctColor(pct: number | null) {
  if (pct == null) return 'text-gray-400'
  if (pct > 0) return 'text-bullish'
  if (pct < 0) return 'text-bearish'
  return 'text-gray-500'
}

function getPctIcon(pct: number | null) {
  if (pct == null) return <Minus className="w-4 h-4" />
  if (pct > 0) return <TrendingUp className="w-4 h-4" />
  if (pct < 0) return <TrendingDown className="w-4 h-4" />
  return <Minus className="w-4 h-4" />
}
