'use client';

import SourcesTimelineChart from './charts/SourcesTimelineChart';
import SourceTypesChart from './charts/SourceTypesChart';
import TopCollaborators from './TopCollaborators';

export default function AnalyticsSection() {
  return (
    <section className="space-y-6">
      {/* Section Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold bg-gradient-to-r from-[#F7931A] to-[#FFD600] bg-clip-text text-transparent">
          Analytics
        </h2>
      </div>

      {/* Analytics Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sources Timeline Chart - Full width on mobile, left column on desktop */}
        <div className="lg:col-span-1">
          <SourcesTimelineChart />
        </div>

        {/* Source Types Chart - Full width on mobile, right column on desktop */}
        <div className="lg:col-span-1">
          <SourceTypesChart />
        </div>

        {/* Top Collaborators - Full width on mobile, spans both columns on desktop */}
        <div className="lg:col-span-2">
          <TopCollaborators />
        </div>
      </div>
    </section>
  );
}
