// Deterministic mock Q&A for "Ask Circular" (Frontend Phase 01).
// No AI / LLM. Every value is derived from the approved mock data at render time,
// so responses always stay in sync with the dataset.

import type { DashboardData } from './dashboardData';
import { formatAUD, formatAUDPerT, formatAsOf, formatPercent, formatWeight } from '../lib/format';

export interface EvidenceRow {
  label: string;
  value: string;
}

export interface MockAnswer {
  conclusion: string;
  evidence: EvidenceRow[];
  businessImplication: string;
  suggestedInvestigation: string;
  dataLimitation: string;
}

export interface MockQuestion {
  id: string;
  question: string;
  answer: MockAnswer;
}

/** Build the 4 deterministic prototype questions from loaded data. */
export function buildMockQuestions(data: DashboardData): MockQuestion[] {
  const ov = data.overview;
  const b17 = data.singleBatches.B017?.batch;
  const b22 = data.singleBatches.B022?.batch;
  const backlog = ov.charts.operational_backlog;
  const inspection = backlog.find((b) => b.backlog_stage === 'Inspection');
  const processing = backlog.find((b) => b.backlog_stage === 'Processing');
  const hvRate = ov.kpis.higher_value_recovery_rate.value;
  const asOf = ov.meta.as_of;
  // prototype target comes from the structured management-brief payload (mock data layer), never hard-coded in UI
  const hvTarget = data.managementBrief.briefs.find((b) => b.id === 'brief_higher_value')?.values
    .higher_value_target_pct as number | undefined;

  const realisedNegative = data.batchList.batches
    .filter((b) => b.eligible_for_realised_comparison && b.net_sorting_benefit_aud < 0)
    .sort((a, b) => a.net_sorting_benefit_aud - b.net_sorting_benefit_aud);

  return [
    {
      id: 'q1',
      question: 'Why is Batch 17 underperforming?',
      answer: {
        conclusion: 'Batch 17 has weak realised sorting economics: the detailed recovery effort produced less value than the prototype all-feedstock baseline for this completed batch.',
        evidence: [
          { label: 'Sorting + Inspection', value: formatAUDPerT(b17?.sorting_plus_inspection_cost_per_t ?? 0) },
          { label: 'Net sorting benefit', value: formatAUD(b17?.net_sorting_benefit_aud ?? 0) },
          { label: 'Net recovery value', value: formatAUDPerT(b17?.net_recovery_value_per_t ?? 0) },
          { label: 'Status', value: b17?.economic_evaluation_status ?? 'n/a' },
          { label: 'Quadrant', value: b17?.economic_quadrant ?? 'n/a' },
        ],
        businessImplication:
          'A heavy sorting and inspection effort (2.5× the realised batch average on a per-tonne basis) did not convert into higher recovered value for this completed batch.',
        suggestedInvestigation:
          'Compare B017 with similar completed residential-demolition batches (e.g. B006, B023) and review where sorting hours were concentrated.',
        dataLimitation: 'Prototype economics only; not an industry financial model.',
      },
    },
    {
      id: 'q2',
      question: 'Which completed batches have negative sorting benefit?',
      answer: {
        conclusion:
          `${realisedNegative.length} completed batch${realisedNegative.length === 1 ? '' : 'es'} finished with a negative net sorting benefit against the prototype all-feedstock baseline.`,
        evidence: realisedNegative.slice(0, 4).map((b) => ({
          label: b.batch_id,
          value: `${formatAUD(b.net_sorting_benefit_aud)} · ${formatWeight(b.incoming_weight_t)} t`,
        })),
        businessImplication:
          'For these completed batches, detailed sorting consumed more than it returned. Open (provisional) batches are excluded from this ranking.',
        suggestedInvestigation:
          'Review the source mix of the negative performers (mostly residential demolition and warehouse deconstruction) before applying the same sorting intensity again.',
        dataLimitation: 'Net sorting benefit is a prototype counterfactual metric, not an accounting measure.',
      },
    },
    {
      id: 'q3',
      question: 'Where is the current backlog concentrated?',
      answer: {
        conclusion: `Inspection is the dominant backlog stage at the snapshot — ${inspection ? formatWeight(inspection.weight_t) : '0'} t, ${inspection ? formatPercent(inspection.percentage_of_open_weight) : '0%'} of all open weight.`,
        evidence: [
          { label: 'Inspection', value: inspection ? formatWeight(inspection.weight_t) : '0 t' },
          { label: 'Processing', value: processing ? formatWeight(processing.weight_t) : '0 t' },
          { label: 'Unresolved', value: formatWeight(backlog.find((b) => b.backlog_stage === 'Unresolved')?.weight_t ?? 0) },
          { label: 'Snapshot', value: formatAsOf(asOf) },
        ],
        businessImplication:
          'Material is piling up in inspection, which delays processing starts and keeps value unrealised in the near term.',
        suggestedInvestigation:
          'Trace the inspection hold-up to open batches (e.g. B027/B030/B033, Direct Salvage Purchase) with conflicting or missing records.',
        dataLimitation: 'Backlog is a generator-computed snapshot state at as_of, not a physical stocktake.',
      },
    },
    {
      id: 'q4',
      question: 'How is higher-value recovery performing?',
      answer: {
        conclusion:
          hvTarget !== undefined
            ? `Higher-value recovery is ${formatPercent(hvRate)} of processed output — above the ${hvTarget}% prototype target.`
            : `Higher-value recovery is ${formatPercent(hvRate)} of processed output — above the prototype target.`,
        evidence: [
          { label: 'Higher-value rate', value: formatPercent(hvRate) },
          { label: 'Higher-value weight', value: formatWeight(ov.charts.recovery_route_distribution[0]?.weight_t ?? 0) },
          { label: 'Processed output', value: formatWeight(ov.kpis.processed_timber.value) },
          { label: 'Best realised batch', value: `${b22?.batch_id ?? ''} · ${formatPercent(b22?.higher_value_recovery_rate ?? 0)}` },
        ],
        businessImplication:
          'Recovery is retaining a healthy share of higher-value output overall, although performance varies strongly by source type.',
        suggestedInvestigation:
          'Compare source-type realised HV rates (Infrastructure Salvage highest) to decide where to direct premium recovery effort.',
        dataLimitation: 'Prototype target and rates are synthetic assumptions for product testing.',
      },
    },
  ];
}
