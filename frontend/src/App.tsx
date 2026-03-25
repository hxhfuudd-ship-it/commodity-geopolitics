import { lazy, Suspense, Component, type ReactNode, type ErrorInfo } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import MainLayout from './layouts/MainLayout'

class ErrorBoundary extends Component<{ children: ReactNode }, { error: Error | null }> {
  state = { error: null as Error | null }
  static getDerivedStateFromError(error: Error) { return { error } }
  componentDidCatch(error: Error, info: ErrorInfo) { console.error('Page error:', error, info) }
  render() {
    if (this.state.error) {
      return (
        <div className="flex flex-col items-center justify-center h-64 gap-4">
          <p className="text-red-500 text-sm">页面加载出错</p>
          <button
            onClick={() => { this.setState({ error: null }); window.location.reload() }}
            className="px-4 py-2 text-sm bg-primary-600 text-white rounded-md"
          >刷新重试</button>
        </div>
      )
    }
    return this.props.children
  }
}

const Dashboard = lazy(() => import('./pages/Dashboard'))
const MarketList = lazy(() => import('./pages/market/MarketList'))
const MarketDetail = lazy(() => import('./pages/market/MarketDetail'))
const NewsList = lazy(() => import('./pages/news/NewsList'))
const Correlation = lazy(() => import('./pages/analysis/Correlation'))
const Timeline = lazy(() => import('./pages/analysis/Timeline'))
const Macro = lazy(() => import('./pages/analysis/Macro'))
const Ratios = lazy(() => import('./pages/analysis/Ratios'))
const Sentiment = lazy(() => import('./pages/analysis/Sentiment'))
const Volatility = lazy(() => import('./pages/analysis/Volatility'))
const Compare = lazy(() => import('./pages/analysis/Compare'))
const AiChat = lazy(() => import('./pages/AiChat'))
const Backtest = lazy(() => import('./pages/Backtest'))

function Loading() {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
    </div>
  )
}

export default function App() {
  return (
    <MainLayout>
      <ErrorBoundary>
        <Suspense fallback={<Loading />}>
          <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/market" element={<MarketList />} />
          <Route path="/market/:symbol" element={<MarketDetail />} />
          <Route path="/news" element={<NewsList />} />
          <Route path="/analysis" element={<Navigate to="/analysis/correlation" replace />} />
          <Route path="/analysis/correlation" element={<Correlation />} />
          <Route path="/analysis/timeline" element={<Timeline />} />
          <Route path="/analysis/macro" element={<Macro />} />
          <Route path="/analysis/ratios" element={<Ratios />} />
          <Route path="/analysis/sentiment" element={<Sentiment />} />
          <Route path="/analysis/volatility" element={<Volatility />} />
          <Route path="/analysis/compare" element={<Compare />} />
          <Route path="/ai" element={<AiChat />} />
          <Route path="/backtest" element={<Backtest />} />
        </Routes>
        </Suspense>
      </ErrorBoundary>
    </MainLayout>
  )
}
