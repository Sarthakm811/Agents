import { Area, AreaChart, CartesianGrid, XAxis, YAxis } from 'recharts';
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from '@/components/ui/chart';

const chartData = [
  { month: 'Jan', originality: 86, novelty: 82, ethics: 95 },
  { month: 'Feb', originality: 88, novelty: 85, ethics: 96 },
  { month: 'Mar', originality: 91, novelty: 88, ethics: 94 },
  { month: 'Apr', originality: 89, novelty: 86, ethics: 97 },
  { month: 'May', originality: 93, novelty: 90, ethics: 96 },
  { month: 'Jun', originality: 94, novelty: 92, ethics: 98 },
];

const chartConfig = {
  originality: {
    label: 'Originality Score',
    color: 'hsl(var(--chart-1))',
  },
  novelty: {
    label: 'Novelty Score',
    color: 'hsl(var(--chart-2))',
  },
  ethics: {
    label: 'Ethics Score',
    color: 'hsl(var(--chart-3))',
  },
};

export function MetricsChart() {
  return (
    <ChartContainer config={chartConfig} className="h-[300px] w-full">
      <AreaChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
        <XAxis
          dataKey="month"
          tickLine={false}
          axisLine={false}
          tickMargin={8}
          className="text-xs"
        />
        <YAxis
          tickLine={false}
          axisLine={false}
          tickMargin={8}
          className="text-xs"
        />
        <ChartTooltip content={<ChartTooltipContent />} />
        <Area
          type="monotone"
          dataKey="originality"
          stroke="var(--color-chart-1)"
          fill="var(--color-chart-1)"
          fillOpacity={0.2}
          strokeWidth={2}
        />
        <Area
          type="monotone"
          dataKey="novelty"
          stroke="var(--color-chart-2)"
          fill="var(--color-chart-2)"
          fillOpacity={0.2}
          strokeWidth={2}
        />
        <Area
          type="monotone"
          dataKey="ethics"
          stroke="var(--color-chart-3)"
          fill="var(--color-chart-3)"
          fillOpacity={0.2}
          strokeWidth={2}
        />
      </AreaChart>
    </ChartContainer>
  );
}