import { Link } from 'react-router-dom'
import { BarChart3, GitBranch, Activity } from 'lucide-react'

const ANALYSIS_MODULES = [
  {
    title: '相关性矩阵',
    desc: '分析不同大宗商品之间的价格相关性',
    icon: BarChart3,
    path: '/analysis/correlation',
    color: 'bg-blue-50 text-blue-600',
  },
  {
    title: '事件时间轴',
    desc: '地缘政治事件与商品价格的时间对照',
    icon: GitBranch,
    path: '/analysis/timeline',
    color: 'bg-amber-50 text-amber-600',
  },
  {
    title: '宏观对比',
    desc: '宏观经济指标与商品价格走势对比',
    icon: Activity,
    path: '/analysis/macro',
    color: 'bg-green-50 text-green-600',
  },
]

export default function AnalysisHome() {
  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">数据分析</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {ANALYSIS_MODULES.map(m => (
          <Link
            key={m.path}
            to={m.path}
            className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-5 hover:shadow-md transition-shadow group"
          >
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${m.color} mb-3`}>
              <m.icon className="w-5 h-5" />
            </div>
            <h3 className="font-medium text-gray-900 group-hover:text-primary-600 transition-colors">
              {m.title}
            </h3>
            <p className="text-sm text-gray-500 mt-1">{m.desc}</p>
          </Link>
        ))}
      </div>
    </div>
  )
}
