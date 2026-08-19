"""Typed input/output models for the deterministic analyst tool layer.

Every tool has a typed Pydantic input and output. These models are also the source
for ANALYST_TOOL_SCHEMAS.json (machine-readable, provider-neutral future LLM tool
definitions). No `dict[str, Any]` for core analytical outputs.
"""
from __future__ import annotations

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field

from ..models.api import (
    EconomicEvaluationStatus,
    EconomicQuadrant,
    ManagementReportSections,
    RecoveryRoute,
)

# --------------------------------------------------------------------------- common


class Provenance(BaseModel):
    """Evidence provenance so the future AI never presents synthetic data as real
    commercial operations."""
    dataset_type: Literal["synthetic_prototype"] = "synthetic_prototype"
    period_start: str
    period_end: str
    as_of: str
    currency: Literal["AUD"] = "AUD"
    weight_unit: Literal["t"] = "t"
    prototype: Literal[True] = True


class TimeInput(BaseModel):
    """Optional time window. Defaults reproduce the approved prototype dataset.
    Validation happens in the tool context (InvalidPeriod / UnsupportedPrototypeDateRange)."""
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    as_of: Optional[str] = None


# --------------------------------------------------------------------------- tool 01


class OverviewMetricsInput(TimeInput):
    pass


class NorthStarEvidence(BaseModel):
    value: float
    unit: Literal["AUD/t"] = "AUD/t"
    basis: Literal["selected_period"] = "selected_period"
    closed_batch_net_recovery_value_per_t: float


class OverviewKpis(BaseModel):
    incoming_timber_t: float
    processed_timber_t: float
    higher_value_recovery_rate: float
    processing_cost_per_processed_t: float
    recovered_value_per_t: float
    unresolved_inspection_rate: float


class OverviewTotals(BaseModel):
    total_recovery_cost_aud: float
    gross_recovered_value_aud: float
    net_recovery_value_aud: float


class OverviewMetricsOutput(BaseModel):
    provenance: Provenance
    time_basis: Literal["selected_period"] = "selected_period"
    north_star: NorthStarEvidence
    kpis: OverviewKpis
    totals: OverviewTotals
    prototype_target: dict[str, float | str]


# --------------------------------------------------------------------------- tool 02


class RecoveryPerformanceInput(TimeInput):
    pass


class RecoveryRoutes(BaseModel):
    higher_value_weight_t: float
    board_feedstock_weight_t: float
    special_handling_weight_t: float
    residual_weight_t: float


class RecoveryRates(BaseModel):
    higher_value_recovery_rate: float
    board_feedstock_rate: float
    special_handling_rate: float
    residual_rate: float
    downgrade_rate: float


class MonthlyRecoveryRow(BaseModel):
    month: str
    processed_timber_t: float
    higher_value_recovery_rate: float


class RecoveryPerformanceOutput(BaseModel):
    provenance: Provenance
    processed_weight_t: float
    routes: RecoveryRoutes
    rates: RecoveryRates
    monthly_recovery_performance: list[MonthlyRecoveryRow]


# --------------------------------------------------------------------------- tool 03


class OperationalBacklogInput(TimeInput):
    pass


class BacklogBuckets(BaseModel):
    sorting_backlog_t: float
    inspection_backlog_t: float
    processing_backlog_t: float
    unresolved_backlog_t: float


class BacklogComparison(BaseModel):
    previous_snapshot: BacklogBuckets
    change_absolute: BacklogBuckets
    change_percent: BacklogBuckets


class OperationalBacklogOutput(BaseModel):
    provenance: Provenance
    as_of_date: str
    buckets: BacklogBuckets
    total_open_weight_t: float
    open_batch_count: int
    comparison: Optional[BacklogComparison] = None  # null when no supported previous snapshot


# --------------------------------------------------------------------------- tool 04


class BatchDetailsInput(BaseModel):
    batch_id: str = Field(min_length=1, description="Approved batch id, e.g. B017")


class BatchEvidence(BaseModel):
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
    inspection_exposure_rate: float
    unresolved_rate: float
    downgrade_rate: float
    economic_evaluation_status: EconomicEvaluationStatus
    eligible_for_realised_comparison: bool
    economic_quadrant: Optional[EconomicQuadrant] = None
    scenario: Optional[str] = None
    notes: Optional[str] = None
    evidence_status: Literal["realised", "provisional"]
    economics_note: str


class BatchDetailsOutput(BaseModel):
    provenance: Provenance
    batch: BatchEvidence


# --------------------------------------------------------------------------- tool 05


class CompareBatchesInput(BaseModel):
    batch_ids: list[str] = Field(min_length=2, max_length=10, description="2-10 batch ids")


class BatchComparisonRow(BaseModel):
    batch_id: str
    status: str
    economic_evaluation_status: EconomicEvaluationStatus
    incoming_weight_t: float
    higher_value_recovery_rate: float
    sorting_plus_inspection_cost_per_t: float
    processing_cost_per_processed_t: float
    total_recovery_cost_per_incoming_t: float
    recovered_value_per_t: float
    net_recovery_value_per_t: float
    net_sorting_benefit_aud: float
    unresolved_rate: float
    downgrade_rate: float
    economic_quadrant: Optional[EconomicQuadrant] = None


class BatchRef(BaseModel):
    batch_id: str
    value: float


class ComparisonHelpers(BaseModel):
    scope: Literal["realised"] = "realised"
    highest_recovered_value_per_t: BatchRef
    lowest_recovered_value_per_t: BatchRef
    highest_sorting_inspection_cost_per_t: BatchRef
    lowest_sorting_inspection_cost_per_t: BatchRef
    best_realised_net_sorting_benefit: BatchRef
    worst_realised_net_sorting_benefit: BatchRef


class CompareBatchesOutput(BaseModel):
    provenance: Provenance
    scope_note: str
    rows: list[BatchComparisonRow]
    helpers: ComparisonHelpers
    limitation: str


# --------------------------------------------------------------------------- tool 06


class SortingEconomicsInput(TimeInput):
    source_type: Optional[str] = None
    realised_only: bool = True


class SortingEconomicsResults(BaseModel):
    realised_batch_count: int
    positive_sorting_benefit_count: int
    negative_sorting_benefit_count: int
    total_net_sorting_benefit_aud: float
    average_net_sorting_benefit_per_t: float
    sorting_cost_per_t: float
    inspection_cost_per_t: float


class SortingEconomicsOutput(BaseModel):
    provenance: Provenance
    scope: dict[str, object]
    results: SortingEconomicsResults
    top_positive_batches: list[dict]
    top_negative_batches: list[dict]
    baseline_definition: str
    metric_limitation: str


# --------------------------------------------------------------------------- tool 07


class BatchEconomicsInput(TimeInput):
    include_provisional: bool = False


class BatchEconomicsPoint(BaseModel):
    batch_id: str
    source_type: str
    sorting_plus_inspection_cost_per_t: float
    recovered_value_per_t: float
    incoming_weight_t: float
    economic_quadrant: Optional[EconomicQuadrant] = None


class BatchEconomicsBenchmark(BaseModel):
    realised_median_x: float
    realised_median_y: float
    note: str = "Medians computed from realised (completed) batches only."


class BatchEconomicsOutput(BaseModel):
    provenance: Provenance
    benchmark: BatchEconomicsBenchmark
    batches: list[BatchEconomicsPoint]


# --------------------------------------------------------------------------- tool 08


class SourcePerformanceInput(TimeInput):
    pass


class RealisedSourceRow(BaseModel):
    source_type: str
    completed_batch_count: int
    completed_incoming_weight_t: float
    realised_higher_value_recovery_rate: float
    realised_processing_cost_per_processed_t: float
    realised_total_recovery_cost_per_incoming_t: float
    realised_recovered_value_per_t: float
    realised_net_recovery_value_per_t: float
    realised_net_sorting_benefit_aud: float


class OpenExposureRow(BaseModel):
    source_type: str
    open_batch_count: int
    open_incoming_weight_t: float
    open_processed_weight_t: float
    open_unresolved_weight_t: float
    open_inspection_weight_t: float
    cost_incurred_to_date_aud: float
    value_realised_to_date_aud: float


class SourcePerformanceOutput(BaseModel):
    provenance: Provenance
    realised_source_performance: list[RealisedSourceRow]
    current_operational_exposure: list[OpenExposureRow]
    note: str = "Two separate layers — never merged into one profitability conclusion."


# --------------------------------------------------------------------------- tool 09


class UncertaintyInput(TimeInput):
    pass


class RecordQualityRates(BaseModel):
    complete_record_rate: float
    partial_record_rate: float
    critical_missing_rate: float


class TreatmentRates(BaseModel):
    unknown_treatment_rate: float
    conflicting_record_rate: float


class OperationalUncertainty(BaseModel):
    open_inspection_rate: float
    unresolved_rate: float


class UncertaintyBatchRef(BaseModel):
    batch_id: str
    unresolved_rate: float
    inspection_exposure_rate: float
    economic_evaluation_status: EconomicEvaluationStatus


class UncertaintySourceRef(BaseModel):
    source_type: str
    unresolved_rate: float


class UncertaintyOutput(BaseModel):
    provenance: Provenance
    record_quality: RecordQualityRates
    treatment: TreatmentRates
    operational: OperationalUncertainty
    top_uncertainty_batches: list[UncertaintyBatchRef]
    top_uncertainty_sources: list[UncertaintySourceRef]
    limitation: str = "Unknown treatment information does not establish structural or chemical unsafety."


# --------------------------------------------------------------------------- tool 10


class MonthlyPerformanceInput(TimeInput):
    pass


class MonthlyPerformanceToolRow(BaseModel):
    month: str
    incoming_timber_t: float
    processed_timber_t: float
    higher_value_recovery_rate: float
    processing_cost_per_processed_t: float
    total_recovery_cost_per_incoming_t: float
    recovered_value_per_t: float
    net_recovery_value_per_t: float
    sorting_backlog_t: float
    inspection_backlog_t: float
    processing_backlog_t: float
    unresolved_backlog_t: float


class MonthlyPerformanceOutput(BaseModel):
    provenance: Provenance
    months: list[MonthlyPerformanceToolRow]


# --------------------------------------------------------------------------- tool 11


class ManagementReportToolInput(TimeInput):
    pass


class ManagementReportToolOutput(BaseModel):
    provenance: Provenance
    sections: ManagementReportSections


# --------------------------------------------------------------------------- tool 12


class FindBatchesInput(BaseModel):
    status: Optional[str] = None
    source_type: Optional[str] = None
    economic_evaluation_status: Optional[str] = None
    economic_quadrant: Optional[str] = None
    min_net_sorting_benefit: Optional[float] = None
    max_net_sorting_benefit: Optional[float] = None
    min_unresolved_rate: Optional[float] = None


class FindBatchRow(BaseModel):
    batch_id: str
    status: str
    source_type: str
    incoming_weight_t: float
    processed_weight_t: float
    higher_value_recovery_rate: float
    net_sorting_benefit_aud: float
    unresolved_rate: float
    economic_evaluation_status: EconomicEvaluationStatus
    eligible_for_realised_comparison: bool
    economic_quadrant: Optional[EconomicQuadrant] = None


class FindBatchesOutput(BaseModel):
    provenance: Provenance
    count: int
    batches: list[FindBatchRow]
