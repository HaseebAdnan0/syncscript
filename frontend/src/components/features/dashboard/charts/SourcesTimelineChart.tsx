'use client';

import { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { ChartWrapper, chartColors, tooltipStyles } from './ChartWrapper';
import { FileText } from 'lucide-react';

interface TimelineData {
  date: string;
  count: number;
}

export default function SourcesTimelineChart() {
  const [data, setData] = useState<TimelineData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const token = localStorage.getItem('access_token');
        if (!token) {
          throw new Error('No authentication token found');
        }

        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/dashboard/analytics/sources-timeline/`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        if (!response.ok) {
          throw new Error('Failed to fetch timeline data');
        }

        const result = await response.json();
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <ChartWrapper title="Sources Added Over Time">
        <div className="flex items-center justify-center h-64 animate-pulse">
          <div className="text-muted">Loading chart...</div>
        </div>
      </ChartWrapper>
    );
  }

  if (error) {
    return (
      <ChartWrapper title="Sources Added Over Time">
        <div className="flex items-center justify-center h-64 text-red-400">
          Error: {error}
        </div>
      </ChartWrapper>
    );
  }

  // Empty state: no sources yet
  if (data.length === 0) {
    return (
      <ChartWrapper title="Sources Added Over Time">
        <div className="flex flex-col items-center justify-center h-64 text-center">
          <div className="w-16 h-16 rounded-full bg-gradient-to-r from-[#F7931A] to-[#FFD600] flex items-center justify-center mb-4">
            <FileText className="w-8 h-8 text-black" />
          </div>
          <p className="text-lg font-medium text-white mb-2">No sources yet</p>
          <p className="text-muted">
            Add your first source to see analytics and track your research productivity
          </p>
        </div>
      </ChartWrapper>
    );
  }

  // Format date for display (MM/DD)
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return `${date.getMonth() + 1}/${date.getDate()}`;
  };

  return (
    <ChartWrapper title="Sources Added Over Time">
      <ResponsiveContainer width="100%" height={300}>
        <LineChart
          data={data}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="rgba(255, 255, 255, 0.1)"
          />
          <XAxis
            dataKey="date"
            tickFormatter={formatDate}
            stroke="rgba(255, 255, 255, 0.5)"
            tick={{ fill: 'rgba(255, 255, 255, 0.5)' }}
          />
          <YAxis
            stroke="rgba(255, 255, 255, 0.5)"
            tick={{ fill: 'rgba(255, 255, 255, 0.5)' }}
            allowDecimals={false}
          />
          <Tooltip
            contentStyle={tooltipStyles}
            labelFormatter={(value) => formatDate(value as string)}
            formatter={(value: number) => [value, 'Sources']}
          />
          <Line
            type="monotone"
            dataKey="count"
            stroke={chartColors.primary}
            strokeWidth={3}
            dot={{
              fill: chartColors.primary,
              strokeWidth: 2,
              r: 4,
            }}
            activeDot={{
              r: 6,
              fill: chartColors.primary,
              stroke: chartColors.accent,
              strokeWidth: 2,
            }}
          />
        </LineChart>
      </ResponsiveContainer>
    </ChartWrapper>
  );
}
