'use client';

import { useEffect, useState } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { FileText } from 'lucide-react';
import ChartWrapper, { chartGradient, tooltipStyles } from './ChartWrapper';
import { api } from '@/lib/api';

interface SourceTypeData {
  type: string;
  count: number;
  percentage: number;
}

/**
 * SourceTypesChart - Donut chart showing distribution of source types
 * Fetches from /api/v1/dashboard/analytics/source-types/
 * Shows percentage labels and custom tooltip with count + percentage
 */
export default function SourceTypesChart() {
  const [data, setData] = useState<SourceTypeData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchSourceTypes() {
      try {
        const response = await api.get('/dashboard/analytics/source-types/');
        setData(response.data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load source types');
      } finally {
        setLoading(false);
      }
    }

    fetchSourceTypes();
  }, []);

  if (loading) {
    return (
      <ChartWrapper title="Source Types">
        <div className="h-80 flex items-center justify-center">
          <div className="animate-pulse text-white/60">Loading chart...</div>
        </div>
      </ChartWrapper>
    );
  }

  if (error) {
    return (
      <ChartWrapper title="Source Types">
        <div className="h-80 flex items-center justify-center">
          <p className="text-red-400">{error}</p>
        </div>
      </ChartWrapper>
    );
  }

  if (data.length === 0) {
    return (
      <ChartWrapper title="Source Types">
        <div className="h-80 flex flex-col items-center justify-center">
          <div className="w-20 h-20 rounded-full bg-gradient-to-br from-[#F7931A]/20 to-[#FFD600]/20 flex items-center justify-center mb-4">
            <FileText className="w-10 h-10 text-[#F7931A]" />
          </div>
          <p className="text-white/60 text-center">
            Add your first source to see analytics
          </p>
        </div>
      </ChartWrapper>
    );
  }

  // Custom label to show percentage on each segment
  const renderLabel = (entry: any) => {
    return `${entry.percentage}%`;
  };

  // Custom tooltip content
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div style={tooltipStyles.contentStyle}>
          <p style={tooltipStyles.labelStyle}>{data.type}</p>
          <p style={tooltipStyles.itemStyle}>
            Count: {data.count} ({data.percentage}%)
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <ChartWrapper title="Source Types">
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={renderLabel}
              outerRadius={100}
              innerRadius={60}
              fill="#8884d8"
              dataKey="count"
              paddingAngle={2}
            >
              {data.map((_entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={chartGradient[index % chartGradient.length]}
                  stroke="rgba(255, 255, 255, 0.1)"
                  strokeWidth={1}
                />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
            <Legend
              verticalAlign="bottom"
              height={36}
              iconType="circle"
              wrapperStyle={{
                paddingTop: '20px',
              }}
              formatter={(value: string) => (
                <span style={{ color: '#FFFFFF', fontSize: '14px' }}>{value}</span>
              )}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </ChartWrapper>
  );
}
