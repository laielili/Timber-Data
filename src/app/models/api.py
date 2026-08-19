"""Pydantic response models — aligned with FRONTEND_DATA_SCHEMA.json / frontend-data-types.ts.

Numbers are raw numeric values with explicit units; formatting is a frontend responsibility.
`management_brief.detail` is the single documented exception (deterministic display copy),
and every brief also carries structured numeric `values`.
"""
from __future__ import annotations

from typing import Literal, Optional, Union

from pydantic import BaseModel, Field

# --------------------------------------------------------------------------- meta / KPI


class Meta(BaseModel):
    dataset_type: Literal["synthetic_prototype"] = "synthetic_prototype"
    currency: Literal["AUD"] = "AUD"
    weight_unit: Literal["t"] = "t"
    period_start: str
    period_end: str
    as_of: str
    seed: int = 20260818
    prototype: Literal[True] = True


TimeBasis = Literal["selected_period", "snapshot", "comparison_period"]
KpiStatus = Literal["positive", "negative", "neutral"]


class KPI(BaseModel):
    id: str
    label: str
    value: float
    unit: str
    basis: TimeBasis
    status: KpiStatus
    description: str
    prototype: Literal[True] = True
    comparison_value: Optional[float] = None
    change_absolute: Optional[float] = None
    change_percent: Optional[float] = None
    trend: Optional[str] = None


class NorthStar(KPI):
    closed_batch_net_recovery_value_per_t: Optional[float] = None
    closed_batch_basis: Optional[str] = None


# --------------------------------------------------------------------------- charts


RecoveryRoute = Literal[
    "Higher-value Recovery", "Board Feedstock", "Special Handling", "Residual / Disposal"
]
BacklogStage = Literal["Sorting", "Inspection", "Processing", "Unresolved"]
EconomicQuadrant = Literal["Efficient", "High-value / High-cost", "Commodity", "Review Required"]
EconomicEvaluationStatus = Literal["Realised", "Provisional"]


class RecoveryRouteRow(BaseModel):
    recovery_route: RecoveryRoute
    weight_t: float
    percentage: float


class IncomingVsProcessedRow(BaseModel):
    month: str
    incoming_timber_t: float
    processed_timber_t: float


class OperationalBacklogRow(BaseModel):
    backlog_stage: BacklogStage
    weight_t: float
    percentage_of_open_weight: float
    as_of_date: str


class NetSortingBenefitRow(BaseModel):
    batch_id: str
    source_type: str
    incoming_weight_t: float
    net_sorting_benefit_aud: float
    net_sorting_benefit_per_t: float
    economic_evaluation_status: EconomicEvaluationStatus
    eligible_for_realised_comparison: bool


class CostVsRecoveredValueRow(BaseModel):
    month: str
    total_recovery_cost_aud: float
    gross_recovered_value_aud: float
    net_recovery_value_aud: float


class BatchEconomicsRow(BaseModel):
    batch_id: str
    source_type: str
    scenario: Optional[str] = None
    sorting_plus_inspection_cost_per_t: float
    recovered_value_per_t: float
    incoming_weight_t: float
    economic_quadrant: Optional[EconomicQuadrant] = None
    economic_evaluation_status: EconomicEvaluationStatus
    eligible_for_realised_comparison: bool


class OverviewCharts(BaseModel):
    recovery_route_distribution: list[RecoveryRouteRow]
    incoming_vs_processed: list[IncomingVsProcessedRow]
    operational_backlog: list[OperationalBacklogRow]
    net_sorting_benefit: list[NetSortingBenefitRow]
    cost_vs_recovered_value: list[CostVsRecoveredValueRow]
    batch_economics: list[BatchEconomicsRow]


class OverviewKpis(BaseModel):
    incoming_timber: KPI
    processed_timber: KPI
    higher_value_recovery_rate: KPI
    processing_cost_per_processed_t: KPI
    recovered_value_per_t: KPI
    unresolved_inspection_rate: KPI


class OverviewResponse(BaseModel):
    meta: Meta
    north_star: NorthStar
    kpis: OverviewKpis
    charts: OverviewCharts


# --------------------------------------------------------------------------- batches


class BatchSummary(BaseModel):
    batch_id: str
    source_id: str
    source_type: str
    arrival_date: str
    status: str
    incoming_weight_t: float
    processed_weight_t: float
    higher_value_weight_t: float
    board_feedstock_weight_t: float
    special_handling_weight_t: float
    residual_weight_t: float
    unresolved_weight_t: float
    higher_value_recovery_rate: float
    sorting_cost_aud: float
    inspection_cost_aud: float
    processing_cost_aud: float
    total_recovery_cost_aud: float
    gross_recovered_value_aud: float
    net_recovery_value_aud: float
    net_recovery_value_per_t: float
    sorting_plus_inspection_cost_per_t: float
    net_sorting_benefit_aud: float
    inspection_exposure_rate: float  # lifecycle share; NOT "currently under inspection"
    unresolved_rate: float
    downgrade_rate: float
    economic_evaluation_status: EconomicEvaluationStatus
    eligible_for_realised_comparison: bool
    economic_quadrant: Optional[EconomicQuadrant] = None
    scenario: Optional[str] = None  # demo-only; not persisted in DB (see README)
    notes: Optional[str] = None


class BatchListResponse(BaseModel):
    meta: Meta
    batches: list[BatchSummary]


class SingleBatchResponse(BaseModel):
    meta: Meta
    batch: BatchSummary


# --------------------------------------------------------------------------- sources


class RealisedSourcePerformance(BaseModel):
    source_type: str
    completed_batch_count: int
    completed_incoming_weight_t: float
    realised_higher_value_recovery_rate: float
    realised_processing_cost_per_processed_t: float
    realised_total_recovery_cost_per_incoming_t: float
    realised_recovered_value_per_t: float
    realised_net_recovery_value_per_t: float
    realised_net_sorting_benefit_aud: float


class OpenSourceExposure(BaseModel):
    source_type: str
    open_batch_count: int
    open_incoming_weight_t: float
    open_processed_weight_t: float
    open_unresolved_weight_t: float
    open_inspection_weight_t: float
    cost_incurred_to_date_aud: float
    value_realised_to_date_aud: float


class SourcePerformanceResponse(BaseModel):
    meta: Meta
    realised_source_performance: list[RealisedSourcePerformance]
    current_operational_exposure: list[OpenSourceExposure]


class SourcePerformanceSections(BaseModel):
    """source_performance section inside ManagementReportData (no meta — matches contract)."""
    realised_source_performance: list[RealisedSourcePerformance]
    current_operational_exposure: list[OpenSourceExposure]


# --------------------------------------------------------------------------- monthly


class MonthlyRow(BaseModel):
    month: str
    incoming_timber_t: float
    processed_timber_t: float
    higher_value_recovery_rate: float
    processing_cost_aud: float
    total_recovery_cost_aud: float
    gross_recovered_value_aud: float
    net_recovery_value_aud: float
    processing_cost_per_processed_t: float
    recovered_value_per_t: float
    net_recovery_value_per_t: float
    sorting_backlog_t: float
    inspection_backlog_t: float
    processing_backlog_t: float
    unresolved_backlog_t: float


class MonthlyPerformanceResponse(BaseModel):
    meta: Meta
    months: list[MonthlyRow]


# --------------------------------------------------------------------------- management brief


class ManagementBriefItem(BaseModel):
    id: str
    title: str
    detail: str
    severity: Literal["attention", "positive", "neutral"]
    related_batch_id: Optional[str] = None
    question_id: Optional[str] = None
    basis: TimeBasis
    values: dict[str, Union[float, str, None]]


class ManagementBriefResponse(BaseModel):
    meta: Meta
    briefs: list[ManagementBriefItem]


# --------------------------------------------------------------------------- management report


class ReportBatchRef(BaseModel):
    batch_id: str
    net_recovery_value_per_t: Optional[float] = None
    net_sorting_benefit_aud: Optional[float] = None
    unresolved_weight_t: Optional[float] = None


class BestPerfRef(BaseModel):
    batch_id: str
    net_recovery_value_per_t: float


class WorstNsbRef(BaseModel):
    batch_id: str
    net_sorting_benefit_aud: float


class HighestUnresolvedRef(BaseModel):
    batch_id: str
    unresolved_weight_t: float


class Batch30ProvisionalExposure(BaseModel):
    economic_evaluation_status: Literal["Provisional"]
    cost_incurred_to_date_aud: float
    unresolved_weight_t: float
    note: str


class OutlierBatches(BaseModel):
    best_by_net_recovery_value_per_t_realised: list[BestPerfRef]
    worst_by_net_sorting_benefit_realised: list[WorstNsbRef]
    highest_unresolved_weight_t: list[HighestUnresolvedRef]
    batch_17_sorting_plus_inspection_cost_per_t: float
    batch_30_provisional_exposure: Batch30ProvisionalExposure


class ManagementReportSections(BaseModel):
    executive_metrics: dict[str, float]
    recovery_performance: dict[str, object]
    sorting_economics: dict[str, object]
    operations: dict[str, object]
    risk_uncertainty: dict[str, float]
    source_performance: SourcePerformanceSections
    outlier_batches: OutlierBatches
    data_limitations: list[str]


class ManagementReportData(BaseModel):
    meta: Meta
    sections: ManagementReportSections
