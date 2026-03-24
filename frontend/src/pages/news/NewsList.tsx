import { useEffect, useState } from 'react'
import { newsApi, type NewsArticle, type NewsListResponse } from '../../lib/api'
import { clsx } from 'clsx'
import dayjs from 'dayjs'

const SENTIMENTS = [
  { value: '', label: '全部' },
  { value: 'bullish', label: '利多', color: 'text-red-600' },
  { value: 'bearish', label: '利空', color: 'text-green-600' },
  { value: 'neutral', label: '中性', color: 'text-gray-500' },
]

export default function NewsList() {
  const [articles, setArticles] = useState<NewsArticle[]>([])
  const [total, setTotal] = useState(0)
  const [sentiment, setSentiment] = useState('')
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    newsApi.getArticles({ page, page_size: 20, sentiment: sentiment || undefined })
      .then(res => {
        setArticles(res.items)
        setTotal(res.total)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [page, sentiment])

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">新闻资讯</h2>
        <div className="flex gap-2">
          {SENTIMENTS.map(s => (
            <button
              key={s.value}
              onClick={() => { setSentiment(s.value); setPage(1) }}
              className={clsx(
                'px-3 py-1.5 text-sm rounded-md',
                sentiment === s.value ? 'bg-primary-600 text-white' : 'bg-white border text-gray-600 hover:bg-gray-50'
              )}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" /></div>
      ) : (
        <div className="space-y-3">
          {articles.map(article => (
            <div key={article.id} className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-4 hover:shadow-sm transition-shadow">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <a
                    href={article.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm font-medium text-gray-900 dark:text-gray-100 hover:text-primary-600 line-clamp-2"
                  >
                    {article.title}
                  </a>
                  {article.summary && (
                    <p className="text-xs text-gray-500 mt-1 line-clamp-2">{article.summary}</p>
                  )}
                  <div className="flex items-center gap-3 mt-2 text-xs text-gray-400">
                    <span>{article.source}</span>
                    <span>{dayjs(article.published_at).format('MM-DD HH:mm')}</span>
                    {article.importance && (
                      <span>重要性: {'★'.repeat(article.importance)}{'☆'.repeat(5 - article.importance)}</span>
                    )}
                  </div>
                </div>
                {article.sentiment && (
                  <SentimentBadge sentiment={article.sentiment} score={article.sentiment_score} />
                )}
              </div>
            </div>
          ))}
          {articles.length === 0 && (
            <div className="text-center py-12 text-gray-400">暂无新闻数据</div>
          )}
        </div>
      )}

      <div className="flex justify-center items-center gap-2">
        <button
          onClick={() => setPage(p => Math.max(1, p - 1))}
          disabled={page <= 1}
          className="px-3 py-1.5 text-sm bg-white dark:bg-gray-800 border dark:border-gray-700 rounded-md disabled:opacity-50"
        >
          上一页
        </button>
        <span className="px-3 py-1.5 text-sm text-gray-500">第 {page} / {Math.ceil(total / 20)} 页 (共 {total} 条)</span>
        <button
          onClick={() => setPage(p => p + 1)}
          disabled={articles.length < 20}
          className="px-3 py-1.5 text-sm bg-white dark:bg-gray-800 border dark:border-gray-700 rounded-md disabled:opacity-50"
        >
          下一页
        </button>
      </div>
    </div>
  )
}

function SentimentBadge({ sentiment, score }: { sentiment: string; score: number | null }) {
  const config: Record<string, { label: string; bg: string; text: string }> = {
    bullish: { label: '利多', bg: 'bg-red-100', text: 'text-red-700' },
    bearish: { label: '利空', bg: 'bg-green-100', text: 'text-green-700' },
    neutral: { label: '中性', bg: 'bg-gray-100', text: 'text-gray-600' },
  }
  const c = config[sentiment] || config.neutral
  return (
    <span className={clsx('px-2 py-0.5 rounded text-xs whitespace-nowrap', c.bg, c.text)}>
      {c.label}{score != null ? ` ${score.toFixed(1)}` : ''}
    </span>
  )
}
