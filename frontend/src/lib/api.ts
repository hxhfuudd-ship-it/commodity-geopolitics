const API_BASE = '/api/v1'

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    throw new Error(`API Error: ${res.status} ${res.statusText}`)
  }
  return res.json()
}

// 行情
export const marketApi = {
  getCommodities: (category?: string) =>
    request<Commodity[]>(`/market/commodities${category ? `?category=${category}` : ''}`),
  getPrice: (symbol: string) =>
    request<PriceInfo>(`/market/commodities/${symbol}/price`),
  getKline: (symbol: string, period = 'day', startDate?: string, endDate?: string) => {
    const params = new URLSearchParams({ period })
    if (startDate) params.set('start_date', startDate)
    if (endDate) params.set('end_date', endDate)
    return request<PriceDaily[]>(`/market/commodities/${symbol}/kline?${params}`)
  },
  getCompare: (symbols: string[], normalize = true) =>
    request<Record<string, { dates: string[]; prices: number[] }>>(
      `/market/commodities/compare?symbols=${symbols.join(',')}&normalize=${normalize}`
    ),
  getOverview: () => request<MarketOverviewItem[]>('/market/overview'),
  getCftc: (symbol: string) => request<CftcData[]>(`/market/cftc/${symbol}`),
}

// 新闻
export const newsApi = {
  getArticles: (params?: { page?: number; page_size?: number; commodity?: string; sentiment?: string }) => {
    const sp = new URLSearchParams()
    if (params?.page) sp.set('page', String(params.page))
    if (params?.page_size) sp.set('page_size', String(params.page_size))
    if (params?.commodity) sp.set('commodity', params.commodity)
    if (params?.sentiment) sp.set('sentiment', params.sentiment)
    return request<NewsListResponse>(`/news/articles?${sp}`)
  },
  getArticle: (id: number) => request<NewsArticle>(`/news/articles/${id}`),
  getSentimentTrend: (commodity?: string, days = 30) =>
    request<SentimentTrendItem[]>(`/news/sentiment/trend?days=${days}${commodity ? `&commodity=${commodity}` : ''}`),
  getEvents: () => request<GeoEvent[]>('/news/events'),
  getEventsTimeline: () => request<GeoEvent[]>('/news/events/timeline'),
}

// 分析
export const analysisApi = {
  getCorrelation: (symbols: string[], period = '90d') =>
    request<CorrelationMatrix>(`/analysis/correlation?symbols=${symbols.join(',')}&period=${period}`),
  getEventImpact: (eventId: number) =>
    request<EventImpact[]>(`/analysis/event-impact/${eventId}`),
  getMacroComparison: (indicatorCode: string, commoditySymbol: string, period = '180d') =>
    request<MacroComparison>(`/analysis/macro/comparison?indicator_code=${indicatorCode}&commodity_symbol=${commoditySymbol}&period=${period}`),
  getRatios: (period = '1y') => request<RatioItem[]>(`/analysis/ratios?period=${period}`),
  getDailyReport: () => request<{ report: string }>('/analysis/report/daily'),
}

// AI
export const aiApi = {
  newSession: () => request<{ session_id: string }>('/ai/chat/new', { method: 'POST' }),
  getHistory: (sessionId: string) => request<ChatSession>(`/ai/chat/${sessionId}/history`),
  chat: (sessionId: string, message: string, signal?: AbortSignal) =>
    fetch(`${API_BASE}/ai/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, message }),
      signal,
    }),
}

// 回测
export const backtestApi = {
  getEvents: () => request<BacktestEvent[]>('/backtest/events'),
  run: (eventId: number, commodities: string[], beforeDays = 30, afterDays = 30) =>
    request<BacktestResult>(
      `/backtest/run?event_id=${eventId}&commodities=${commodities.join(',')}&before_days=${beforeDays}&after_days=${afterDays}`,
      { method: 'POST' }
    ),
  compare: (eventIds: number[], commodity: string) =>
    request<BacktestCompare>(`/backtest/compare?event_ids=${eventIds.join(',')}&commodity=${commodity}`),
}

// Types
export interface Commodity {
  id: number; symbol: string; name_cn: string; category: string; exchange: string; unit: string
}
export interface PriceInfo {
  symbol: string; name_cn: string; price: number | null; change_pct: number | null
  trade_date: string; open: number | null; high: number | null; low: number | null; volume: number | null
}
export interface PriceDaily {
  trade_date: string; open: number; high: number; low: number; close: number
  volume: number; open_interest: number | null; change_pct: number | null
}
export interface MarketOverviewItem {
  symbol: string; name_cn: string; category: string
  latest_price: number | null; change_pct: number | null
  open: number | null; settle: number | null; prev_close: number | null
  volume: number | null; open_interest: number | null
  updated_at: string | null
}
export interface CftcData {
  report_date: string; long_positions: number; short_positions: number; net_positions: number
}
export interface NewsListResponse {
  total: number; page: number; page_size: number; items: NewsArticle[]
}
export interface NewsArticle {
  id: number; title: string; summary: string | null; source: string; source_url: string
  published_at: string; sentiment: string | null; sentiment_score: number | null; importance: number | null
}
export interface SentimentTrendItem {
  date: string; bullish_count: number; bearish_count: number; neutral_count: number; avg_score: number
}
export interface GeoEvent {
  id: number; title: string; description: string; event_type: string; region: string
  country_codes: string; start_date: string; end_date: string | null; severity: number
  latitude: number; longitude: number
}
export interface CorrelationMatrix { symbols: string[]; matrix: number[][] }
export interface EventImpact {
  event: GeoEvent; commodity: Commodity
  price_before: number | null; price_after_1d: number | null; price_after_7d: number | null; price_after_30d: number | null
  change_pct_1d: number | null; change_pct_7d: number | null; change_pct_30d: number | null; ai_analysis: string | null
}
export interface MacroComparison {
  indicator_code: string; indicator_name: string; commodity_symbol: string
  dates: string[]; indicator_values: (number | null)[]; commodity_prices: (number | null)[]
}
export interface RatioItem { date: string; ratio_name: string; value: number }
export interface ChatMessage { role: string; content: string; timestamp: string }
export interface ChatSession { session_id: string; messages: ChatMessage[] }
export interface BacktestEvent { id: number; title: string; start_date: string; event_type: string; severity: number }
export interface BacktestResult { event: GeoEvent; data: Record<string, { dates: string[]; prices: number[] }> }
export interface BacktestCompare { commodity: string; events: { event: GeoEvent; dates: string[]; prices: number[] }[] }
