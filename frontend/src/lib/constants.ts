export const COMMODITY_CATEGORIES = [
  { value: 'metal', label: '金属' },
  { value: 'energy', label: '能源' },
  { value: 'agriculture', label: '农产品' },
  { value: 'chemical', label: '化工' },
] as const

export const COMMODITIES = [
  { symbol: 'AU', name: '黄金', category: 'metal' },
  { symbol: 'AG', name: '白银', category: 'metal' },
  { symbol: 'CU', name: '铜', category: 'metal' },
  { symbol: 'AL', name: '铝', category: 'metal' },
  { symbol: 'NI', name: '镍', category: 'metal' },
  { symbol: 'FE', name: '铁矿石', category: 'metal' },
  { symbol: 'SC', name: '上海原油', category: 'energy' },
  { symbol: 'FU', name: '燃料油', category: 'energy' },
  { symbol: 'PG', name: 'LPG液化气', category: 'energy' },
  { symbol: 'A', name: '大豆', category: 'agriculture' },
  { symbol: 'M', name: '豆粕', category: 'agriculture' },
  { symbol: 'Y', name: '豆油', category: 'agriculture' },
  { symbol: 'P', name: '棕榈油', category: 'agriculture' },
  { symbol: 'C', name: '玉米', category: 'agriculture' },
  { symbol: 'CF', name: '棉花', category: 'agriculture' },
  { symbol: 'SR', name: '白糖', category: 'agriculture' },
  { symbol: 'RU', name: '橡胶', category: 'agriculture' },
  { symbol: 'TA', name: 'PTA', category: 'chemical' },
  { symbol: 'MA', name: '甲醇', category: 'chemical' },
  { symbol: 'PP', name: '聚丙烯', category: 'chemical' },
] as const

export const SENTIMENTS = [
  { value: 'bullish', label: '利多', color: '#ef4444' },
  { value: 'bearish', label: '利空', color: '#22c55e' },
  { value: 'neutral', label: '中性', color: '#6b7280' },
] as const

export const MACRO_INDICATORS = [
  { code: 'DXY', name: '美元指数' },
  { code: 'USDCNY', name: '人民币汇率' },
  { code: 'US10Y', name: '美国10年期国债收益率' },
  { code: 'CN10Y', name: '中国10年期国债收益率' },
  { code: 'BDI', name: '波罗的海干散货指数' },
] as const

export const PERIODS = [
  { value: '30d', label: '30天' },
  { value: '90d', label: '90天' },
  { value: '180d', label: '半年' },
  { value: '1y', label: '一年' },
  { value: '3y', label: '三年' },
  { value: '5y', label: '五年' },
] as const
