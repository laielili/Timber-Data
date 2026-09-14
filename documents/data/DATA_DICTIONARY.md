# DATA DICTIONARY — Circular Timber Intelligence (synthetic prototype)

Source values: `Synthetic prototype` | `Derived metric` | `Prototype assumption`
No field claims structural safety, chemical safety or certification.

## SourceProjects
| Table | Field | Data Type | Unit | Nullable | Description | Example | Source |
|---|---|---|---|---|---|---|---|
| SourceProjects | source_id | TEXT | - | No | Primary key. | S01 | Synthetic prototype |
| SourceProjects | source_type | TEXT | - | No | Synthetic source category. | Infrastructure Salvage | Synthetic prototype |
| SourceProjects | region | TEXT | - | No | Synthetic region label (Australia). | Victoria | Synthetic prototype |
| SourceProjects | former_use_category | TEXT | - | No | Former use category of the source. | Bridge decking / handrail renewal | Synthetic prototype |
| SourceProjects | submission_date | DATE | - | No | Date source was submitted to the operation. | 2024-11-20 | Synthetic prototype |
| SourceProjects | estimated_material_quality | TEXT | - | No | High / Medium / Low / Unknown assessment. | High | Synthetic prototype |
| SourceProjects | expected_complexity | TEXT | - | No | Low / Medium / High expected sorting complexity. | Medium | Synthetic prototype |
| SourceProjects | notes | TEXT | - | Yes | Free-text context note. | Bridge renewal hardwood; premium potential. | Synthetic prototype |

## Batches
| Table | Field | Data Type | Unit | Nullable | Description | Example | Source |
|---|---|---|---|---|---|---|---|
| Batches | batch_id | TEXT | - | No | Primary key; B001-B036. | B017 | Synthetic prototype |
| Batches | source_id | TEXT | - | No | FK to SourceProjects. | S10 | Synthetic prototype |
| Batches | arrival_date | DATETIME | - | No | Arrival timestamp (2025-01-01 to 2025-12-31). | 2025-06-15 08:20 | Synthetic prototype |
| Batches | incoming_weight_t | REAL | t | No | Batch incoming weight; year total ~1,240 t. | 42.0 | Synthetic prototype |
| Batches | planned_sorting_intensity | TEXT | - | No | Low / Medium / High. | High | Synthetic prototype |
| Batches | current_stage | TEXT | - | No | Snapshot stage: Received/Sorting/Inspection/Processing/Completed. | Processing | Synthetic prototype |
| Batches | batch_status | TEXT | - | No | Received/Sorting/Inspection/Processing/Completed/Partially Completed. | Partially Completed | Synthetic prototype |
| Batches | priority | TEXT | - | No | High / Medium / Low. | Medium | Synthetic prototype |
| Batches | notes | TEXT | - | Yes | Scenario-driven context note. | Renovation strip-out; unusually heavy sorting effort. | Synthetic prototype |

## Materials
| Table | Field | Data Type | Unit | Nullable | Description | Example | Source |
|---|---|---|---|---|---|---|---|
| Materials | material_id | TEXT | - | No | Primary key; M00001... | M04321 | Synthetic prototype |
| Materials | batch_id | TEXT | - | No | FK to Batches. | B017 | Synthetic prototype |
| Materials | estimated_weight_kg | REAL | kg | No | Estimated material weight; batch sum ~ incoming x 1000 (+/-0.1%). | 412.5 | Synthetic prototype |
| Materials | species | TEXT | - | No | Species label; species-value links are synthetic modelling only. | Radiata Pine | Synthetic prototype |
| Materials | material_form | TEXT | - | No | Beam/Post/Board/Flooring/Cladding/Structural Member/Mixed Salvage/Other. | Beam | Synthetic prototype |
| Materials | former_use | TEXT | - | No | Former use description. | Roof beam | Synthetic prototype |
| Materials | known_treatment_status | TEXT | - | No | Management-level category; never a safety/certification claim. | Unknown | Synthetic prototype |
| Materials | surface_condition | TEXT | - | No | Operational assessment, not structural certification. | Poor | Synthetic prototype |
| Materials | record_completeness | TEXT | - | No | Complete / Partial / Critical Information Missing. | Partial | Synthetic prototype |
| Materials | requires_inspection | TEXT | - | No | Yes/No - drives inspection workload. | Yes | Synthetic prototype |
| Materials | special_handling_flag | TEXT | - | No | Yes/No - special handling routing; not a hazardous-chemical claim. | No | Synthetic prototype |
| Materials | initial_recovery_grade | TEXT | - | No | Initially assessed grade before downgrade. | Character | Synthetic prototype |
| Materials | recovery_grade | TEXT | - | No | Final prototype grade (Premium/Character/Rustic/Feedstock/Unresolved). | Rustic | Synthetic prototype |
| Materials | current_route | TEXT | - | No | Fixed route taxonomy (5 values). | Board Feedstock | Synthetic prototype |
| Materials | resolution_status | TEXT | - | No | Output/Unresolved/Pending Processing/In Progress. | Output | Synthetic prototype |
| Materials | output_date | DATE | - | Yes | Date material was recovered (null if not yet output). | 2025-07-02 | Synthetic prototype |

## ProcessingEvents
| Table | Field | Data Type | Unit | Nullable | Description | Example | Source |
|---|---|---|---|---|---|---|---|
| ProcessingEvents | event_id | TEXT | - | No | Primary key; PE00001... | PE00123 | Synthetic prototype |
| ProcessingEvents | batch_id | TEXT | - | No | FK to Batches. | B017 | Synthetic prototype |
| ProcessingEvents | stage | TEXT | - | No | Intake/Sorting/Inspection Hold/Processing/Grading/Output. | Sorting | Synthetic prototype |
| ProcessingEvents | start_datetime | DATETIME | - | No | Event start; >= batch arrival. | 2025-06-16 10:00 | Synthetic prototype |
| ProcessingEvents | end_datetime | DATETIME | - | Yes | Event end; null while open. Never before start. | 2025-06-18 17:00 | Synthetic prototype |
| ProcessingEvents | weight_in_t | REAL | t | No | Weight into the stage. | 42.0 | Synthetic prototype |
| ProcessingEvents | weight_out_t | REAL | t | No | Weight out of the stage. | 42.0 | Synthetic prototype |
| ProcessingEvents | labour_hours | REAL | h | No | Labour hours consumed. | 138.6 | Synthetic prototype |
| ProcessingEvents | machine_hours | REAL | h | No | Machine hours consumed. | 0.0 | Synthetic prototype |
| ProcessingEvents | status | TEXT | - | No | Completed/Open. | Completed | Synthetic prototype |

## InspectionEvents
| Table | Field | Data Type | Unit | Nullable | Description | Example | Source |
|---|---|---|---|---|---|---|---|
| InspectionEvents | inspection_id | TEXT | - | No | Primary key; INSP00001... | INSP00111 | Synthetic prototype |
| InspectionEvents | batch_id | TEXT | - | No | FK to Batches. | B017 | Synthetic prototype |
| InspectionEvents | material_id | TEXT | - | Yes | FK to Materials; null = batch-level review. | M04321 | Synthetic prototype |
| InspectionEvents | inspection_type | TEXT | - | No | Record Review / Quality Verification / Treatment Information Verification / Manual Material Review / Routing Verification. | Treatment Information Verification | Synthetic prototype |
| InspectionEvents | reason | TEXT | - | No | Free-text reason. | Treatment history unknown or conflicting in source records. | Synthetic prototype |
| InspectionEvents | opened_datetime | DATETIME | - | No | Opened timestamp. | 2025-06-17 09:30 | Synthetic prototype |
| InspectionEvents | closed_datetime | DATETIME | - | Yes | Closed timestamp; null while open. | 2025-06-19 11:00 | Synthetic prototype |
| InspectionEvents | status | TEXT | - | No | Open/Completed/Cancelled. | Completed | Synthetic prototype |
| InspectionEvents | labour_hours | REAL | h | No | Inspection labour hours. | 2.5 | Synthetic prototype |
| InspectionEvents | external_cost_aud | REAL | AUD | No | External cost (0 when none). | 450.00 | Synthetic prototype |
| InspectionEvents | outcome | TEXT | - | Yes | Cleared/Route Changed/Special Handling/Still Unresolved/No Change; null while open. | Route Changed | Synthetic prototype |

## RecoveryOutputs
| Table | Field | Data Type | Unit | Nullable | Description | Example | Source |
|---|---|---|---|---|---|---|---|
| RecoveryOutputs | output_id | TEXT | - | No | Primary key; OUT00001... | OUT00134 | Synthetic prototype |
| RecoveryOutputs | batch_id | TEXT | - | No | FK to Batches. | B017 | Synthetic prototype |
| RecoveryOutputs | output_date | DATE | - | No | Date the output was dispatched. | 2025-07-05 | Synthetic prototype |
| RecoveryOutputs | recovery_route | TEXT | - | No | Fixed route taxonomy (Unresolved never output). | Board Feedstock | Synthetic prototype |
| RecoveryOutputs | recovery_grade | TEXT | - | No | Prototype grade of the output. | Rustic | Synthetic prototype |
| RecoveryOutputs | weight_t | REAL | t | No | Output weight. | 11.238 | Synthetic prototype |
| RecoveryOutputs | unit_value_aud_per_t | REAL | AUD/t | No | Assumption base +/- variation (10%). | 252.00 | Prototype assumption |
| RecoveryOutputs | gross_value_aud | REAL | AUD | No | Ledger identity: weight_t × unit_value_aud_per_t. | 2831.98 | Derived metric |

## CostLedger
| Table | Field | Data Type | Unit | Nullable | Description | Example | Source |
|---|---|---|---|---|---|---|---|
| CostLedger | cost_id | TEXT | - | No | Primary key; C00001... | C00157 | Synthetic prototype |
| CostLedger | batch_id | TEXT | - | No | FK to Batches. | B017 | Synthetic prototype |
| CostLedger | cost_date | DATE | - | No | Cost date within batch lifecycle. | 2025-06-27 | Synthetic prototype |
| CostLedger | cost_category | TEXT | - | No | Sorting Labour/Inspection/Processing/Special Handling/Disposal/Transport/Other. | Sorting Labour | Synthetic prototype |
| CostLedger | quantity | REAL | h|t|aud | No | Quantity in the stated unit. | 138.6 | Synthetic prototype |
| CostLedger | unit | TEXT | - | No | h / t / aud. | h | Synthetic prototype |
| CostLedger | unit_cost_aud | REAL | AUD | No | Synthetic unit rate from Assumptions. | 48.00 | Prototype assumption |
| CostLedger | total_cost_aud | REAL | AUD | No | Ledger identity: quantity × unit_cost_aud. | 6652.80 | Derived metric |
| CostLedger | notes | TEXT | - | Yes | Calculation trace note. | Sorting labour hours from ProcessingEvents stage=Sorting x synthetic sorting rate. | Synthetic prototype |
