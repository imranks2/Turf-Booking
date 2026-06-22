import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { Card } from '@/components/ui/Card';

export interface RevenueChartProps {
  title: string;
  data: Array<Record<string, number | string>>;
  xKey: string;
  series: Array<{ key: string; color: string; label: string }>;
}

export function RevenueChart({ title, data, xKey, series }: RevenueChartProps): JSX.Element {
  return (
    <Card>
      <h3 className="mb-4 font-semibold text-gray-900">{title}</h3>
      {data.length === 0 ? (
        <p className="py-10 text-center text-sm text-gray-400">No data for this period.</p>
      ) : (
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey={xKey} tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              {series.map((s) => (
                <Line key={s.key} type="monotone" dataKey={s.key} name={s.label} stroke={s.color} strokeWidth={2} dot={false} />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </Card>
  );
}
