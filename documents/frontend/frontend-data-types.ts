// frontend-data-types.ts — Circular Timber Intelligence
// Contract types ONLY. No React components, no logic, no styling.
// Mirrors FRONTEND_DATA_SCHEMA.json (synthetic prototype data).

export type TimeBasis = "selected_period" | "snapshot" | "comparison_period";
export type KpiStatus = "positive" | "negative" | "neutral";
export type EconomicEvaluationStatus = "Realised" | "Provisional";
export type EconomicQuadrant = "Efficient" | "High-value / High-cost" | "Commodity" | "Review Required";
export type RecoveryRoute = "Higher-value Recovery" | "Board Feedstock" | "Special Handling" | "Residual / Disposal";
export type BacklogStage = "Sorting" | "Inspection" | "Processing" | "Unresolved";

export interface Meta {
  dataset_type: "synthetic_prototype";
  currency: "AUD";
  weight_unit: "t";
  period_start: string; // ISO date
  period_end: string;   // ISO date
  as_of: string;        // ISO datetime
  seed?: number;
  prototype: true;
}

export interface Kpi {
  id: string;
  label: string;
  value: number;
  unit: string;
  basis: TimeBasis;
  status: KpiStatus;
  description: string;
  prototype: true;
  comparison_value?: number | null;
  change_absolute?: number | null;
  change_percent?: number | null;
  trend?: string | null;
}

export interface RecoveryRouteRow { recovery_route: RecoveryRoute; weight_t: number; percentage: number; }
export interface IncomingVsProcessedRow { month: string; incoming_timber_t: number; processed_timber_t: number; }
export interface OperationalBacklogRow {
  backlog_stage: BacklogStage;
  weight_t: number;
  percentage_of_open_weight: number;
  as_of_date: string;
}
export interface NetSortingBenefitRow {
  batch_id: string; source_type: string; incoming_weight_t: number;
  net_sorting_benefit_aud: number; net_sorting_benefit_per_t: number;
  economic_evaluation_status: EconomicEvaluationStatus;
  eligible_for_realised_comparison: boolean;
}
export interface CostVsRecoveredValueRow {
  month: string; total_recovery_cost_aud: number;
  gross_recovered_value_aud: number; net_recovery_value_aud: number;
}
export interface BatchEconomicsRow {
  batch_id: string; source_type: string; scenario: string;
  sorting_plus_inspection_cost_per_t: number; recovered_value_per_t: number;
  incoming_weight_t: number; economic_quadrant: EconomicQuadrant | null;
  economic_evaluation_status: EconomicEvaluationStatus;
  eligible_for_realised_comparison: boolean;
}

export interface OverviewCharts {
  recovery_route_distribution: RecoveryRouteRow[];
  incoming_vs_processed: IncomingVsProcessedRow[];
  operational_backlog: OperationalBacklogRow[];
  net_sorting_benefit: NetSortingBenefitRow[];
  cost_vs_recovered_value: CostVsRecoveredValueRow[];
  batch_economics: BatchEconomicsRow[];
}

export interface OverviewKpis {
  incoming_timber: Kpi;
  processed_timber: Kpi;
  higher_value_recovery_rate: Kpi;
  processing_cost_per_processed_t: Kpi;
  recovered_value_per_t: Kpi;
  unresolved_inspection_rate: Kpi;
}

export interface OverviewResponse {
  meta: Meta;
  north_star: Kpi;
  kpis: OverviewKpis;
  charts: OverviewCharts;
}

export interface BatchSummary {
  batch_id: string;
  source_id: string;
  source_type: string;
  arrival_date: string;
  status: string;
  incoming_weight_t: number;
  processed_weight_t: number;
  higher_value_weight_t: number;
  board_feedstock_weight_t: number;
  special_handling_weight_t: number;
  residual_weight_t: number;
  unresolved_weight_t: number;
  higher_value_recovery_rate: number;
  sorting_cost_aud: number;
  inspection_cost_aud: number;
  processing_cost_aud: number;
  total_recovery_cost_aud: number;
  gross_recovered_value_aud: number;
  net_recovery_value_aud: number;
  net_recovery_value_per_t: number;
  sorting_plus_inspection_cost_per_t: number;
  net_sorting_benefit_aud: number;
  inspection_exposure_rate: number; // share of incoming material with inspection activity in the batch lifecycle; NOT "currently under inspection"
  unresolved_rate: number;
  downgrade_rate: number;
  economic_evaluation_status: EconomicEvaluationStatus;
  eligible_for_realised_comparison: boolean;
  economic_quadrant: EconomicQuadrant | null;
  scenario?: string; // prototype demonstration only
  notes?: string;    // prototype demonstration only
}

export interface BatchList { meta: Meta; batches: BatchSummary[]; }
export interface SingleBatch { meta: Meta; batch: BatchSummary; }

export interface RealisedSourcePerformance {
  source_type: string;
  completed_batch_count: number;
  completed_incoming_weight_t: number;
  realised_higher_value_recovery_rate: number;
  realised_processing_cost_per_processed_t: number;
  realised_total_recovery_cost_per_incoming_t: number;
  realised_recovered_value_per_t: number;
  realised_net_recovery_value_per_t: number;
  realised_net_sorting_benefit_aud: number;
}
export interface OpenSourceExposure {
  source_type: string;
  open_batch_count: number;
  open_incoming_weight_t: number;
  open_processed_weight_t: number;
  open_unresolved_weight_t: number;
  open_inspection_weight_t: number;
  cost_incurred_to_date_aud: number;
  value_realised_to_date_aud: number;
}
export interface SourcePerformanceList {
  meta: Meta;
  realised_source_performance: RealisedSourcePerformance[];
  current_operational_exposure: OpenSourceExposure[];
}

export interface MonthlyRow {
  month: string;
  incoming_timber_t: number;
  processed_timber_t: number;
  higher_value_recovery_rate: number;
  processing_cost_aud: number;
  total_recovery_cost_aud: number;
  gross_recovered_value_aud: number;
  net_recovery_value_aud: number;
  processing_cost_per_processed_t: number;
  recovered_value_per_t: number;
  net_recovery_value_per_t: number;
  sorting_backlog_t: number;
  inspection_backlog_t: number;
  processing_backlog_t: number;
  unresolved_backlog_t: number;
}
export interface MonthlyPerformance { meta: Meta; months: MonthlyRow[]; }

export interface ManagementReportData {
  meta: Meta;
  sections: {
    executive_metrics: Record<string, number>;
    recovery_performance: Record<string, unknown>;
    sorting_economics: Record<string, unknown>;
    operations: Record<string, unknown>;
    risk_uncertainty: Record<string, number>;
    source_performance: {
      realised_source_performance: RealisedSourcePerformance[];
      current_operational_exposure: OpenSourceExposure[];
    };
    outlier_batches: Record<string, unknown>;
    data_limitations: string[];
  };
}
