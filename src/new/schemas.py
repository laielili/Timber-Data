"""Workbench API schemas (Pydantic)."""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


# --------------------------------------------------------------------------- upload
class UploadResult(BaseModel):
    upload_id: str
    table_name: str
    filename: str
    mode: str
    row_count: int
    status: str  # ok | partial | failed
    message: str
    errors: list[str] = Field(default_factory=list)


class DatasetSummary(BaseModel):
    tables: dict[str, int]
    total_rows: int
    last_upload: Optional[dict[str, Any]] = None


class TableColumn(BaseModel):
    name: str
    type: str
    nullable: bool
    required: bool


class TableSchema(BaseModel):
    table_name: str
    primary_key: str
    columns: list[TableColumn]
    example_row: dict[str, Any] = Field(default_factory=dict)


# --------------------------------------------------------------------------- dashboard
class FilterParams(BaseModel):
    """Dimension filters applied to the dashboard. All optional."""

    period_start: Optional[str] = None  # YYYY-MM-DD
    period_end: Optional[str] = None    # YYYY-MM-DD
    source_type: Optional[str] = None
    region: Optional[str] = None
    species: Optional[str] = None
    material_form: Optional[str] = None
    recovery_route: Optional[str] = None
    batch_status: Optional[str] = None
    current_stage: Optional[str] = None


class DimensionValues(BaseModel):
    """Available values per filter dimension (for the filter rail)."""

    period_start: Optional[str] = None
    period_end: Optional[str] = None
    source_types: list[str] = Field(default_factory=list)
    regions: list[str] = Field(default_factory=list)
    species: list[str] = Field(default_factory=list)
    material_forms: list[str] = Field(default_factory=list)
    recovery_routes: list[str] = Field(default_factory=list)
    batch_statuses: list[str] = Field(default_factory=list)
    current_stages: list[str] = Field(default_factory=list)


class Kpi(BaseModel):
    id: str
    label: str
    value: float
    unit: str
    basis: str
    description: str


class Chart(BaseModel):
    id: str
    title: str
    type: str  # bar | line | pie | scatter
    rows: list[dict[str, Any]] = Field(default_factory=list)


class DashboardResponse(BaseModel):
    meta: dict[str, Any]
    filters: FilterParams
    dimensions: DimensionValues
    kpis: list[Kpi]
    charts: list[Chart]


# --------------------------------------------------------------------------- AI
class ChatMessage(BaseModel):
    role: str  # user | assistant
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(default_factory=list)
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    conversation_id: str
    tools_used: list[str] = Field(default_factory=list)
    model: Optional[str] = None
    provider: Optional[str] = None


class AISettingsUpdate(BaseModel):
    enabled: bool = False
    base_url: str
    model: str
    api_key: Optional[str] = None  # None/empty keeps the previously stored key


class AISettingsResponse(BaseModel):
    enabled: bool
    base_url: str
    model: str
    api_key_configured: bool
    source: str


class AIConnectionTestRequest(BaseModel):
    base_url: Optional[str] = None
    model: Optional[str] = None
    api_key: Optional[str] = None


class AIConnectionTestResult(BaseModel):
    success: bool
    message: str
    code: Optional[str] = None


class AIModelsRequest(BaseModel):
    base_url: Optional[str] = None
    model: Optional[str] = None
    api_key: Optional[str] = None


class AIModelsResponse(BaseModel):
    models: list[str] = Field(default_factory=list)
    supported: bool = True
    message: str = ""