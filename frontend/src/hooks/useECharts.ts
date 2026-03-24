import { useEffect, useRef } from 'react'
import echarts from '../lib/echarts'
import type { EChartsOption } from 'echarts'

export function useECharts(option: EChartsOption | null, deps: any[] = []) {
  const chartRef = useRef<HTMLDivElement>(null)
  const instanceRef = useRef<echarts.ECharts | null>(null)

  useEffect(() => {
    if (!chartRef.current) return

    if (!instanceRef.current) {
      instanceRef.current = echarts.init(chartRef.current)
    }

    if (option) {
      instanceRef.current.setOption(option, true)
    }

    const handleResize = () => instanceRef.current?.resize()
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
    }
  }, [option, ...deps])

  useEffect(() => {
    return () => {
      instanceRef.current?.dispose()
      instanceRef.current = null
    }
  }, [])

  return chartRef
}
