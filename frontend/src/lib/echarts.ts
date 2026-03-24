import * as echarts from 'echarts/core'
import { BarChart, CandlestickChart, HeatmapChart, LineChart, ScatterChart, EffectScatterChart } from 'echarts/charts'
import {
  TitleComponent, TooltipComponent, LegendComponent, GridComponent,
  DataZoomComponent, MarkLineComponent, MarkPointComponent,
  VisualMapComponent, GeoComponent, ToolboxComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([
  BarChart, CandlestickChart, HeatmapChart, LineChart, ScatterChart, EffectScatterChart,
  TitleComponent, TooltipComponent, LegendComponent, GridComponent,
  DataZoomComponent, MarkLineComponent, MarkPointComponent,
  VisualMapComponent, GeoComponent, ToolboxComponent,
  CanvasRenderer,
])

export default echarts
