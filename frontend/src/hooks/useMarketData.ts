import useSWR from 'swr'
import { marketApi, type MarketOverviewItem, type PriceDaily, type CftcData, type Commodity } from '../lib/api'

export function useOverview() {
  return useSWR<MarketOverviewItem[]>('market:overview', () => marketApi.getOverview(), {
    refreshInterval: 300000,
  })
}

export function useCommodities(category?: string) {
  return useSWR<Commodity[]>(`market:commodities:${category || 'all'}`, () => marketApi.getCommodities(category))
}

export function useKline(symbol: string, period = 'day', startDate?: string, endDate?: string) {
  return useSWR<PriceDaily[]>(
    symbol ? `market:kline:${symbol}:${period}:${startDate}:${endDate}` : null,
    () => marketApi.getKline(symbol, period, startDate, endDate),
  )
}

export function useCftc(symbol: string) {
  return useSWR<CftcData[]>(
    symbol ? `market:cftc:${symbol}` : null,
    () => marketApi.getCftc(symbol),
  )
}
