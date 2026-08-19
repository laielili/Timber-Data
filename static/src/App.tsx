// Executive Overview — Frontend Phase 01 (01.1 cleanup).
// Composes the five layers: navigation, AI brief, North Star, six KPIs, six charts,
// plus the Ask Circular mock drawer. All data flows through the typed data layer;
// React components perform presentation/formatting only — no business calculations.

import { useState } from 'react';
import { useDashboardData } from './data/dashboardData';
import { buildMockQuestions } from './data/mockAnswers';
import { describeError } from './data/apiClient';
import { postAnalystQuery } from './data/analystClient';
import type { AnalystContext, AnalystQueryRequest } from './types/analyst';
import { formatAsOf } from './lib/format';
import { SideNavigation } from './components/SideNavigation';
import { OverviewHeader } from './components/OverviewHeader';
import { AIManagementBrief } from './components/AIManagementBrief';
import { NorthStarCard } from './components/NorthStarCard';
import { KPIGrid } from './components/KPIGrid';
import { ChartCard } from './components/ChartCard';
import { RecoveryRouteChart } from './components/RecoveryRouteChart';
import { IncomingProcessedChart } from './components/IncomingProcessedChart';
import { OperationalBacklogChart } from './components/OperationalBacklogChart';
import { SortingBenefitChart } from './components/SortingBenefitChart';
import { CostValueChart } from './components/CostValueChart';
import { BatchEconomicsChart } from './components/BatchEconomicsChart';
import { AskCircularDrawer } from './components/AskCircularDrawer';
import { ErrorScreen, LoadingScreen } from './components/PageStates';

export default function App() {
  const { data, loading, error } = useDashboardData();
  const [drawerOpen, setDrawerOpen] = useState(false);

  if (loading) return <LoadingScreen />;
  if (error || !data) {
    return <ErrorScreen message={describeError(error)} onRetry={() => window.location.reload()} />;
  }

  const { overview } = data;
  const meta = overview.meta;
  const period = `Jan–Dec ${meta.period_start.slice(0, 4)}`;
  const snapshotLabel = `Snapshot · ${formatAsOf(meta.as_of)}`;
  const questions = buildMockQuestions(data);

  // AI Analyst configuration (Phase 02). Mode + base URL come from env; never the key.
  const env = import.meta.env as Record<string, string | undefined>;
  const analystMode: 'real' | 'mock' = env.VITE_ANALYST_MODE === 'real' ? 'real' : 'mock';
  const apiBase = env.VITE_API_BASE_URL ?? 'http://localhost:8000';
  const analystContext: AnalystContext = {
    period_start: meta.period_start,
    period_end: meta.period_end,
    as_of: meta.as_of,
    current_page: 'overview',
    selected_batch_id: null,
  };
  const handleAnalystQuery = (req: AnalystQueryRequest) => postAnalystQuery(req, apiBase);

  // AI Management Brief items are served by the mock data layer (management_brief.json).
  // React only renders them; all numbers originate from the approved synthetic dataset.
  const briefItems = data.managementBrief.briefs;

  const openAsk = (_questionId: string | null = null) => {
    setDrawerOpen(true);
  };

  return (
    <div className="app">
      <SideNavigation />
      <main className="content">
        <OverviewHeader meta={meta} />

        <section className="top-band" aria-label="Management summary">
          <AIManagementBrief items={briefItems} onAsk={openAsk} />
          <NorthStarCard
            value={overview.north_star.value}
            unit={overview.north_star.unit}
            label={overview.north_star.label}
            description={overview.north_star.description}
            meta={meta}
            closedBatchValue={overview.north_star.closed_batch_net_recovery_value_per_t}
            processedWeight={overview.kpis.processed_timber.value}
          />
        </section>

        <KPIGrid kpis={overview.kpis} meta={meta} />

        <section className="charts-grid" aria-label="Analytical charts">
          <ChartCard
            title="Cost vs Recovered Value"
            question="Do months with higher recovery cost deliver higher value?"
            basis={period}
            tier="wide"
            span={8}
            empty={overview.charts.cost_vs_recovered_value.length === 0}
          >
            <CostValueChart rows={overview.charts.cost_vs_recovered_value} />
          </ChartCard>

          <ChartCard
            title="Recovery Route Distribution"
            question="Where did recovered timber go?"
            basis={period}
            span={4}
            empty={overview.charts.recovery_route_distribution.length === 0}
          >
            <RecoveryRouteChart rows={overview.charts.recovery_route_distribution} />
          </ChartCard>

          <ChartCard
            title="Batch Economics"
            question="Which completed batches are expensive to recover relative to the value they generate?"
            basis="Selected period · realised benchmark"
            tier="primary"
            span={7}
            empty={overview.charts.batch_economics.length === 0}
          >
            <BatchEconomicsChart rows={overview.charts.batch_economics} />
          </ChartCard>

          <ChartCard
            title="Net Sorting Benefit by Batch"
            question="Which completed batches benefited from detailed sorting?"
            basis="Selected period · realised batches"
            tier="primary"
            span={5}
            empty={overview.charts.net_sorting_benefit.length === 0}
          >
            <SortingBenefitChart rows={overview.charts.net_sorting_benefit} />
          </ChartCard>

          <ChartCard
            title="Incoming vs Processed Timber"
            question="Is processing keeping up with incoming material?"
            basis={period}
            span={6}
            empty={overview.charts.incoming_vs_processed.length === 0}
          >
            <IncomingProcessedChart rows={overview.charts.incoming_vs_processed} />
          </ChartCard>

          <ChartCard
            title="Operational Backlog"
            question="Where is open material currently stuck?"
            basis={snapshotLabel}
            span={6}
            empty={overview.charts.operational_backlog.length === 0}
          >
            <OperationalBacklogChart rows={overview.charts.operational_backlog} />
          </ChartCard>
        </section>

        <footer className="page-foot">
          Circular Timber Intelligence · synthetic prototype dataset (seed {meta.seed ?? 20260818}) · values are
          prototype assumptions, not an industry financial model.
        </footer>
      </main>

      <AskCircularDrawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        mode={analystMode}
        questions={questions}
        onAnalystQuery={analystMode === 'real' ? handleAnalystQuery : undefined}
        context={analystContext}
      />
    </div>
  );
}
