import { ReactNode, useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  BarChart3, Newspaper, TrendingUp, Bot, History, Globe,
  Menu, X, ChevronDown, Moon, Sun
} from 'lucide-react'
import { clsx } from 'clsx'
import Logo from '../components/Logo'

const navItems = [
  { path: '/', label: '概览', icon: Globe },
  { path: '/market', label: '行情', icon: TrendingUp },
  { path: '/news', label: '新闻', icon: Newspaper },
  {
    label: '分析', icon: BarChart3, children: [
      { path: '/analysis/correlation', label: '相关性矩阵' },
      { path: '/analysis/timeline', label: '事件时间轴' },
      { path: '/analysis/macro', label: '宏观对照' },
      { path: '/analysis/ratios', label: '比价分析' },
      { path: '/analysis/sentiment', label: '情绪趋势' },
      { path: '/analysis/volatility', label: '波动率分析' },
      { path: '/analysis/compare', label: '品种对比' },
    ]
  },
  { path: '/ai', label: 'AI 助手', icon: Bot },
  { path: '/backtest', label: '事件回测', icon: History },
]

function useDarkMode() {
  const [dark, setDark] = useState(() => {
    if (typeof window === 'undefined') return false
    return localStorage.getItem('theme') === 'dark'
  })

  useEffect(() => {
    const root = document.documentElement
    if (dark) {
      root.classList.add('dark')
      localStorage.setItem('theme', 'dark')
    } else {
      root.classList.remove('dark')
      localStorage.setItem('theme', 'light')
    }
  }, [dark])

  return [dark, setDark] as const
}

export default function MainLayout({ children }: { children: ReactNode }) {
  const location = useLocation()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [analysisOpen, setAnalysisOpen] = useState(
    location.pathname.startsWith('/analysis')
  )
  const [dark, setDark] = useDarkMode()

  return (
    <div className="min-h-screen flex bg-gray-50 dark:bg-gray-950">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 bg-black/40 z-30 lg:hidden" onClick={() => setSidebarOpen(false)} />
      )}

      {/* Sidebar */}
      <aside className={clsx(
        'fixed lg:static inset-y-0 left-0 z-40 w-60 bg-gray-900 dark:bg-gray-900 text-white flex flex-col transition-transform lg:translate-x-0',
        sidebarOpen ? 'translate-x-0' : '-translate-x-full'
      )}>
        <div className="flex items-center gap-2 px-4 h-14 border-b border-gray-800">
          <Logo size={28} />
          <span className="font-bold text-sm">GeoInsight 地缘洞察</span>
        </div>
        <nav className="flex-1 py-4 overflow-y-auto">
          {navItems.map((item) => {
            if ('children' in item && item.children) {
              return (
                <div key={item.label}>
                  <button
                    onClick={() => setAnalysisOpen(!analysisOpen)}
                    className="flex items-center gap-3 w-full px-4 py-2.5 text-sm text-gray-300 hover:bg-gray-800 hover:text-white transition-colors"
                  >
                    <item.icon className="w-4 h-4" />
                    <span className="flex-1 text-left">{item.label}</span>
                    <ChevronDown className={clsx('w-4 h-4 transition-transform', analysisOpen && 'rotate-180')} />
                  </button>
                  {analysisOpen && (
                    <div className="ml-7 animate-fade-in">
                      {item.children.map((child) => (
                        <Link
                          key={child.path}
                          to={child.path}
                          onClick={() => setSidebarOpen(false)}
                          className={clsx(
                            'block px-4 py-2 text-sm rounded-md transition-colors',
                            location.pathname === child.path
                              ? 'text-primary-400 bg-gray-800'
                              : 'text-gray-400 hover:text-white hover:bg-gray-800'
                          )}
                        >
                          {child.label}
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
              )
            }
            return (
              <Link
                key={item.path}
                to={item.path!}
                onClick={() => setSidebarOpen(false)}
                className={clsx(
                  'flex items-center gap-3 px-4 py-2.5 text-sm transition-colors',
                  location.pathname === item.path
                    ? 'text-primary-400 bg-gray-800'
                    : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                )}
              >
                <item.icon className="w-4 h-4" />
                {item.label}
              </Link>
            )
          })}
        </nav>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-14 border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 flex items-center px-4 gap-4 sticky top-0 z-20">
          <button className="lg:hidden" onClick={() => setSidebarOpen(true)}>
            <Menu className="w-5 h-5 text-gray-600 dark:text-gray-300" />
          </button>
          <h1 className="text-sm font-medium text-gray-600 dark:text-gray-300 flex-1">
            GeoInsight 地缘洞察 · 全球资源地缘策略平台
          </h1>
          <button
            onClick={() => setDark(!dark)}
            className="p-2 rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            title={dark ? '切换亮色模式' : '切换暗色模式'}
          >
            {dark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </button>
        </header>
        <main className="flex-1 p-4 lg:p-6 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  )
}
