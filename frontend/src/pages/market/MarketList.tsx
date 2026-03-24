import { useEffect, useState, useRef } from 'react'
import { Link } from 'react-router-dom'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { marketApi, type MarketOverviewItem } from '../../lib/api'
import { clsx } from 'clsx'

const CATEGORY_MAP: Record<string, { label: string; style: string }> = {
  metal: { label: '金属', style: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400' },
  energy: { label: '能源', style: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' },
  agriculture: { label: '农产品', style: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' },
  chemical: { label: '化工', style: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400' },
}

function categoryLabel(cat: string) { return CATEGORY_MAP[cat]?.label ?? cat }
function categoryStyle(cat: string) { return CATEGORY_MAP[cat]?.style ?? 'bg-gray-100 text-gray-700' }

export default function MarketList() {
  const [commodities, setCommodities] = useState<MarketOverviewItem[]>([])
  const [category, setCategory] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const prevPrices = useRef<Record<string, number>>({})
  const [flashing, setFlashing] = useState<Record<string, 'up' | 'down'>>({})

  // Initial load
  useEffect(() => {
    setLoading(true)
    marketApi.getOverview()
      .then(data => {
        data.forEach(d => { if (d.latest_price != null) prevPrices.current[d.symbol] = d.latest_price })
        setCommodities(data)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  // SSE realtime
  useEffect(() => {
    const es = new EventSource('/api/v1/market/overview/stream')
    es.onmessage = (event) => {
      try {
        const data: MarketOverviewItem[] = JSON.parse(event.data)
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
        setCommodities(data)
        if (Object.keys(newFlash).length > 0) {
          setFlashing(newFlash)
          setTimeout(() => setFlashing({}), 600)
        }
      } catch {}
    }
    return () => es.close()
  }, [])

  const filtered = category ? commodities.filter(d => d.category === category) : commodities
  const sorted = [...filtered].sort((a, b) => (b.change_pct ?? -Infinity) - (a.change_pct ?? -Infinity))

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">行情列表</h2>
        <div className="flex gap-2">
          {[{ v: '', l: '全部' }, { v: 'metal', l: '金属' }, { v: 'energy', l: '能源' }, { v: 'agriculture', l: '农产品' }, { v: 'chemical', l: '化工' }].map(opt => (
            <button
              key={opt.v}
              onClick={() => setCategory(opt.v)}
              className={clsx(
                'px-3 py-1.5 text-sm rounded-md',
                category === opt.v ? 'bg-primary-600 text-white' : 'bg-white dark:bg-gray-800 border dark:border-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
              )}
            >
              {opt.l}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" /></div>
      ) : (
        <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 dark:bg-gray-800 text-gray-500 dark:text-gray-400">
              <tr>
                <th className="text-left px-4 py-3">品种</th>
                <th className="text-left px-4 py-3">代码</th>
                <th className="text-right px-4 py-3">最新价</th>
                <th className="text-right px-4 py-3">涨跌幅</th>
                <th className="text-right px-4 py-3">开盘价</th>
                <th className="text-right px-4 py-3">结算价</th>
                <th className="text-right px-4 py-3">成交量</th>
                <th className="text-right px-4 py-3">持仓量</th>
                <th className="text-right px-4 py-3">分类</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
              {sorted.map(c => {
                const flash = flashing[c.symbol]
                return (
                  <tr key={c.symbol} className={clsx(
                    'transition-colors duration-300',
                    flash === 'up' && 'bg-red-50/50 dark:bg-red-900/10',
                    flash === 'down' && 'bg-green-50/50 dark:bg-green-900/10',
                    !flash && 'hover:bg-gray-50 dark:hover:bg-gray-800/50',
                  )}>
                    <td className="px-4 py-3">
                      <Link to={`/market/${c.symbol}`} className="text-primary-600 hover:underline font-medium">
                        {c.name_cn}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-gray-500 dark:text-gray-400">{c.symbol}</td>
                    <td className={clsx('px-4 py-3 text-right font-mono transition-colors duration-300',
                      flash === 'up' && 'text-bullish font-bold',
                      flash === 'down' && 'text-bearish font-bold',
                    )}>
                      {c.latest_price != null ? c.latest_price.toFixed(2) : '--'}
                    </td>
                    <td className={clsx('px-4 py-3 text-right font-mono', c.change_pct != null && c.change_pct > 0 ? 'text-bullish' : c.change_pct != null && c.change_pct < 0 ? 'text-bearish' : 'text-gray-500')}>
                      {c.change_pct != null ? `${c.change_pct > 0 ? '+' : ''}${c.change_pct.toFixed(2)}%` : '--'}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-gray-600 dark:text-gray-300">
                      {c.open != null ? c.open.toFixed(2) : '--'}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-gray-600 dark:text-gray-300">
                      {c.settle != null && c.settle > 0 ? c.settle.toFixed(2) : '--'}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-gray-600 dark:text-gray-300">
                      {c.volume != null ? c.volume.toLocaleString() : '--'}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-gray-600 dark:text-gray-300">
                      {c.open_interest != null && c.open_interest > 0 ? c.open_interest.toLocaleString() : '--'}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <span className={clsx('px-2 py-0.5 rounded text-xs', categoryStyle(c.category))}>
                        {categoryLabel(c.category)}
                      </span>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
