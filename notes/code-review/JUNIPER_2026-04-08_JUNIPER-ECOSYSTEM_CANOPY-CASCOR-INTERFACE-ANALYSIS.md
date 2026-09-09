# Canopy-Cascor Interface: Comprehensive Code Review and Documentation

**Version**: 1.0.0
**Date**: 2026-04-08
**Author**: Claude Code (Opus 4.6, automated deep review)
**Owner**: Paul Calnon
**Status**: ACTIVE
**Scope**: juniper-canopy, juniper-cascor, juniper-cascor-client (full interface audit)
**Prior Art**: `JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` (P5-RC-01 through P5-RC-18, 2026-03-28, IMPLEMENTED)
**Prior Art**: `JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md` (CR-006 through CR-076, 38 findings)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Interface Architecture Overview](#2-interface-architecture-overview)
3. [REST API Contract](#3-rest-api-contract)
4. [WebSocket Protocol Contract](#4-websocket-protocol-contract)
5. [Data Contract: Field-Level Breakdown](#5-data-contract-field-level-breakdown)
6. [Interface Agreement: Canopy-Side Components](#6-interface-agreement-canopy-side-components)
7. [Interface Agreement: Cascor-Side Components](#7-interface-agreement-cascor-side-components)
8. [Interface Agreement: Cascor-Client Library](#8-interface-agreement-cascor-client-library)
9. [Naming Convention Discrepancies](#9-naming-convention-discrepancies)
10. [Mapping Classes and Translation Functions](#10-mapping-classes-and-translation-functions)
11. [Instantiation and Usage Locations](#11-instantiation-and-usage-locations)
12. [High-Level Code Walkthrough](#12-high-level-code-walkthrough)
13. [Detailed Operational Code Walkthrough](#13-detailed-operational-code-walkthrough)
14. [Cross-Side Requirements Asymmetries](#14-cross-side-requirements-asymmetries)
15. [Current Issue Registry](#15-current-issue-registry)
16. [Remediation Plan](#16-remediation-plan)
17. [Development Roadmap](#17-development-roadmap)
18. [Appendix A: Complete Data Structure Registry](#appendix-a-complete-data-structure-registry)
19. [Appendix B: Constants Reference](#appendix-b-constants-reference)
20. [Appendix C: Explanatory Diagrams](#appendix-c-explanatory-diagrams)

---

## 1. Executive Summary

### 1.1 Purpose

This document provides a definitive, field-level description of the interface between the **juniper-canopy** (monitoring dashboard) and **juniper-cascor** (CasCor neural network backend) applications. It serves as the authoritative reference for:

- Data contracts between the two applications
- API specifications and behavioral expectations
- Naming conventions and translation requirements
- Known discrepancies and their remediation status
- Code locations where interface components are instantiated, assigned, and consumed

### 1.2 Interface Summary

The Canopy-Cascor interface consists of three communication channels:

| Channel                   | Protocol  | Direction       | Primary Purpose                                    |
|---------------------------|-----------|-----------------|----------------------------------------------------|
| REST API                  | HTTP/JSON | Bidirectional   | Training control, state queries, parameter updates |
| WebSocket Training Stream | WS/JSON   | Cascor → Canopy | Real-time metrics broadcast                        |
| WebSocket Control Stream  | WS/JSON   | Canopy → Cascor | Training commands                                  |

These channels are mediated by the **juniper-cascor-client** library, which provides a Python HTTP/WebSocket client that Canopy's `CascorServiceAdapter` wraps.

### 1.3 Interface Health Assessment (2026-04-08)

| Area                         | Status                       | Notes                                                                                                                                |
|------------------------------|------------------------------|--------------------------------------------------------------------------------------------------------------------------------------|
| REST API contract            | **Functional**               | ResponseEnvelope unwrapping, field normalization, topology transformation all implemented                                            |
| WebSocket relay              | **Partial**                  | Relay operational; metrics not normalized (P5-RC-14); dashboard doesn't consume WS data (P5-RC-05)                                   |
| Metrics format               | **Fixed**                    | Flat → nested transformation via `_to_dashboard_metric()` (FIX-A, 2026-03-28)                                                        |
| Topology format              | **Fixed**                    | Weight-oriented → graph-oriented via `_transform_topology()` (FIX-B, 2026-03-28)                                                     |
| Status normalization         | **Fixed**                    | Case-insensitive `_normalize_status()` (FIX-C, 2026-03-28)                                                                           |
| Parameter mapping            | **Functional**               | Comprehensive param map with 13 entries; `max_iterations` mapped end-to-end                                                          |
| Training limits              | **Fixed**                    | `max_iterations` fully implemented: config, API, TrainingState, param map, `fit()` deconflated (CR-006 verified resolved 2026-04-08) |
| State machine recovery       | **Fixed**                    | Auto-reset from FAILED/COMPLETED in `_handle_start()` + duplicate handler removed (CR-007 verified resolved 2026-04-08)              |
| WebSocket `set_params`       | **Fixed**                    | Implemented in control stream with `_VALID_COMMANDS` and handler (CR-008 verified resolved 2026-04-08)                               |
| Metrics emission granularity | **Architectural limitation** | No metrics during candidate training phase (Appendix G analysis)                                                                     |
| Worker security integration  | **Partially integrated**     | Security modules wired via feature flags (PR #111, CR-009)                                                                           |

**Key finding from validation**: The three highest-severity interface issues (CR-006 S1, CR-007 S1, CR-008 S2) have ALL been resolved since the prior analyses (2026-03-28 and 2026-04-04). The interface is in significantly better health than the prior analyses indicated.

### 1.4 Relationship to Prior Analysis Documents

This document **supersedes and consolidates** the following prior analyses:

| Document                                              | Date       | Findings                            | Status                                 |
|-------------------------------------------------------|------------|-------------------------------------|----------------------------------------|
| `JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md`          | 2026-03-28 | P5-RC-01 through P5-RC-18, KL-1     | IMPLEMENTED (FIX-A through FIX-K)      |
| `JUNIPER_2026-04-04_JUNIPER-CASCOR_CODE-REVIEW-FINDINGS.md`           | 2026-04-04 | CR-006 through CR-076 (38 findings) | Partially remediated via PRs #104-#118 |
| `JUNIPER_2026-04-04_JUNIPER-CASCOR_COMPREHENSIVE-CODE-REVIEW-PLAN.md` | 2026-04-04 | Methodology and tooling             | Executed                               |

This document adds:

- **Complete field-level data contract documentation** not previously compiled
- **Updated current-state verification** against HEAD of all three repos (2026-04-08)
- **Integrated issue registry** combining P5-RC and CR findings with current status
- **Comprehensive code location inventory** for all interface components
- **Explanatory diagrams** for data flows, state transitions, and architecture
- **Remediation plan** for remaining and newly identified issues

---

## 2. Interface Architecture Overview

### 2.1 Component Diagram

```bash
┌───────────────────────────────────────────────────┐
│                  juniper-canopy                   │
│                                                   │
│  ┌──────────────┐    ┌──────────────────────────┐ │
│  │   Frontend   │    │        Backend           │ │
│  │ (Dash/Plotly)│◄──►│                          │ │
│  │              │    │  ┌────────────────────┐  │ │
│  │ MetricsPanel │    │  │  BackendProtocol   │  │ │
│  │ NetworkViz   │    │  │   (interface)      │  │ │
│  │ ParamsPanel  │    │  └────────┬───────────┘  │ │
│  │ DatasetPlot  │    │           │              │ │
│  │ StatusBar    │    │  ┌────────┴───────────┐  │ │
│  │ CandidateTab │    │  │  ServiceBackend    │  │ │
│  └──────────────┘    │  │                    │  │ │
│         ▲            │  │  ┌───────────────┐ │  │ │
│         │            │  │  │CascorService  │ │  │ │
│  ┌──────┴──────┐     │  │  │Adapter        │ │  │ │
│  │  main.py    │     │  │  │               │ │  │ │
│  │ (FastAPI+   │     │  │  │ _normalize_   │ │  │ │
│  │  Dash)      │     │  │  │ _transform_   │ │  │ │
│  └─────────────┘     │  │  │ _to_dashboard │ │  │ │
│                      │  │  └───────┬───────┘ │  │ │
│                      │  └──────────┼─────────┘  │ │
│                      └─────────────┼────────────┘ │
└────────────────────────────────────┼──────────────┘
                                     │
                        ┌────────────┴────────────┐
                        │  juniper-cascor-client  │
                        │  JuniperCascorClient    │
                        │  JuniperCascorWSClient  │
                        └────────────┬────────────┘
                                     │
                           HTTP / WebSocket
                                     │
┌────────────────────────────────────┼──────────────────┐
│                                    │                  │
│                 juniper-cascor     │                  │
│                                    │                  │
│  ┌─────────────────────────────────┴───────────────┐  │
│  │              FastAPI Application                │  │
│  │                                                 │  │
│  │  ┌───────────┐  ┌────────────┐  ┌────────────┐  │  │
│  │  │  Routes   │  │ WebSocket  │  │ Middleware │  │  │
│  │  │ /v1/...   │  │ /ws/...    │  │  Auth/     │  │  │
│  │  └────┬──────┘  └─────┬──────┘  │  Rate/CSP│ │  │  │
│  │       │               │         └────────────┘  │  │
│  │  ┌────┴───────────────┴──────┐                  │  │
│  │  │  TrainingLifecycleManager │                  │  │
│  │  │  TrainingStateMachine     │                  │  │
│  │  │  TrainingMonitor          │                  │  │
│  │  └────────────┬──────────────┘                  │  │
│  └───────────────┼─────────────────────────────────┘  │
│                  │                                    │
│  ┌───────────────┴─────────────────────────────┐      │
│  │       CascadeCorrelationNetwork             │      │
│  │       CandidateUnit (multiprocessing)       │      │
│  │       TaskDistributor                       │      │
│  └─────────────────────────────────────────────┘      │
└───────────────────────────────────────────────────────┘
```

### 2.2 Data Flow Overview

```bash
Training Metrics Flow (Cascor → Canopy):

  CascadeCorrelationNetwork.fit()
    → TrainingMonitor.on_epoch_end()
      → TrainingState.update_state()
        → WebSocket broadcast (create_metrics_message)
          → JuniperCascorWSClient receives
            → CascorServiceAdapter._metrics_relay_callback()
              → _normalize_metric() → _to_dashboard_metric()
                → Canopy WebSocket broadcast (to browser)
    AND/OR
      → TrainingMonitor.metrics_buffer[]
        → GET /v1/metrics/history
          → JuniperCascorClient.get_metrics_history()
            → CascorServiceAdapter._normalize_metric() → _to_dashboard_metric()
              → MetricsPanel via dcc.Interval polling

Training Control Flow (Canopy → Cascor):

  Dashboard UI button click
    → main.py /api/training/{command}
      → ServiceBackend.{start|stop|pause|resume|reset}_training()
        → CascorServiceAdapter.{command}()
          → JuniperCascorClient.{command}_training()
            → POST /v1/training/{command}
              → TrainingLifecycleManager.{command}_training()
                → TrainingStateMachine.handle_command()
                → CascadeCorrelationNetwork.fit() / stop / pause / resume

Parameter Update Flow (Canopy → Cascor):

  Dashboard parameter input change
    → main.py /api/params (POST)
      → ServiceBackend.apply_params()
        → CascorServiceAdapter.apply_params()
          → _CANOPY_TO_CASCOR_PARAM_MAP translation
            → JuniperCascorClient.update_params()
              → PATCH /v1/training/params
                → TrainingLifecycleManager.update_params()
```

### 2.3 Service Ports and Endpoints

| Service        | Default Port | Health Endpoint | Auth Required           |
|----------------|--------------|-----------------|-------------------------|
| juniper-cascor | 8200         | `/v1/health`    | No (health); Yes (data) |
| juniper-canopy | 8050         | `/v1/health`    | No (health); Yes (data) |
| juniper-data   | 8100         | `/v1/health`    | No (health); Yes (data) |

---

## 3. REST API Contract

### 3.1 Cascor Server API Endpoints

All endpoints use the `/v1/` prefix. Authenticated endpoints require `X-API-Key` header when `JUNIPER_CASCOR_API_KEYS` is configured.

#### 3.1.1 Health Endpoints (No Auth)

| Method | Path               | Response Model                       | Purpose                          |
|--------|--------------------|--------------------------------------|----------------------------------|
| `GET`  | `/v1/health`       | `{"status": "ok", "version": "..."}` | Simple liveness                  |
| `GET`  | `/v1/health/live`  | `{"status": "alive"}`                | Kubernetes liveness probe        |
| `GET`  | `/v1/health/ready` | `ReadinessResponse`                  | Readiness with dependency checks |

#### 3.1.2 Network Management (Auth Required)

| Method   | Path                   | Request Model          | Response Envelope Data          | Purpose             |
|----------|------------------------|------------------------|---------------------------------|---------------------|
| `POST`   | `/v1/network`          | `NetworkCreateRequest` | Network info dict               | Create network      |
| `GET`    | `/v1/network`          | —                      | Network info dict               | Get current network |
| `DELETE` | `/v1/network`          | —                      | Confirmation                    | Delete network      |
| `GET`    | `/v1/network/topology` | —                      | Topology dict (weight-oriented) | Network topology    |
| `GET`    | `/v1/network/stats`    | —                      | Weight statistics dict          | Weight statistics   |

#### 3.1.3 Training Control (Auth Required)

| Method  | Path                  | Request Model                | Response Envelope Data   | Purpose             |
|---------|-----------------------|------------------------------|--------------------------|---------------------|
| `POST`  | `/v1/training/start`  | `TrainingStartRequest`       | Training status          | Start training      |
| `POST`  | `/v1/training/stop`   | —                            | Status confirmation      | Stop training       |
| `POST`  | `/v1/training/pause`  | —                            | Status confirmation      | Pause training      |
| `POST`  | `/v1/training/resume` | —                            | Status confirmation      | Resume training     |
| `POST`  | `/v1/training/reset`  | —                            | Status confirmation      | Reset training      |
| `GET`   | `/v1/training/status` | —                            | Full training state dict | Get training status |
| `GET`   | `/v1/training/params` | —                            | Training parameters dict | Get parameters      |
| `PATCH` | `/v1/training/params` | `TrainingParamUpdateRequest` | Updated params           | Update parameters   |

#### 3.1.4 Dataset & Visualization (Auth Required)

| Method | Path                    | Request/Query    | Response Data                           | Purpose           |
|--------|-------------------------|------------------|-----------------------------------------|-------------------|
| `GET`  | `/v1/dataset`           | —                | Dataset metadata                        | Dataset info      |
| `GET`  | `/v1/dataset/data`      | —                | Dataset arrays (train_x, train_y)       | Dataset arrays    |
| `GET`  | `/v1/decision-boundary` | `?resolution=50` | Grid data (grid_x, grid_y, predictions) | Decision boundary |

#### 3.1.5 Metrics (Mixed Auth)

| Method | Path                  | Query      | Response Data         | Auth |
|--------|-----------------------|------------|-----------------------|------|
| `GET`  | `/v1/metrics`         | —          | Prometheus metrics    | No   |
| `GET`  | `/v1/metrics/history` | `?count=N` | Metrics history array | Yes  |

#### 3.1.6 Snapshots (Auth Required)

| Method | Path                         | Request                  | Response Data         | Purpose          |
|--------|------------------------------|--------------------------|-----------------------|------------------|
| `GET`  | `/v1/snapshots`              | —                        | Snapshot list         | List snapshots   |
| `POST` | `/v1/snapshots`              | `{"description": "..."}` | Snapshot metadata     | Save snapshot    |
| `GET`  | `/v1/snapshots/{id}`         | —                        | Snapshot metadata     | Get snapshot     |
| `POST` | `/v1/snapshots/{id}/restore` | —                        | Restored network info | Restore snapshot |

#### 3.1.7 Workers (Auth Required)

| Method | Path                | Response Data        | Purpose      |
|--------|---------------------|----------------------|--------------|
| `GET`  | `/v1/workers`       | Worker list          | List workers |
| `GET`  | `/v1/workers/stats` | Aggregate statistics | Worker stats |
| `GET`  | `/v1/workers/{id}`  | Worker details       | Get worker   |

### 3.2 Response Envelope Pattern

All cascor API responses use the `ResponseEnvelope` wrapper:

```python
# Cascor: src/api/models/common.py
class ResponseEnvelope(BaseModel):
    status: str = "success"      # "success" | "error"
    data: Optional[Any] = None   # Payload (present on success)
    error: Optional[ErrorResponse] = None  # Error details (present on error)
    request_id: Optional[str] = None
    timestamp: Optional[str] = None

class ErrorResponse(BaseModel):
    code: str           # Error code (e.g., "TRAINING_NOT_ACTIVE")
    message: str        # Human-readable message
    details: Optional[Dict[str, Any]] = None
```

**Canopy unwrapping**: `CascorServiceAdapter._unwrap_response()` extracts the `data` field from the envelope. All client methods in `JuniperCascorClient` return the raw JSON response (including the envelope); unwrapping happens in the adapter layer.

### 3.3 Canopy Internal API Endpoints

Canopy exposes its own internal API (served by FastAPI) for the Dash dashboard to consume:

| Method            | Path                      | Purpose                  | Data Source                              |
|-------------------|---------------------------|--------------------------|------------------------------------------|
| `GET`             | `/api/status`             | Dashboard status bar     | Fresh REST calls to cascor               |
| `GET`             | `/api/metrics`            | Current metrics snapshot | `ServiceBackend.get_current_metrics()`   |
| `GET`             | `/api/metrics/history`    | Metrics history          | `ServiceBackend.get_metrics_history()`   |
| `GET`             | `/api/network/topology`   | Network graph            | `ServiceBackend.get_network_topology()`  |
| `GET`             | `/api/network/stats`      | Weight statistics        | `ServiceBackend.get_network_stats()`     |
| `GET`             | `/api/state`              | Training state           | `TrainingState` (local cache)            |
| `GET`             | `/api/dataset`            | Dataset info             | `ServiceBackend.get_dataset()`           |
| `GET`             | `/api/decision-boundary`  | Decision boundary        | `ServiceBackend.get_decision_boundary()` |
| `POST`            | `/api/training/{command}` | Training control         | Forward to cascor                        |
| `POST`            | `/api/params`             | Parameter updates        | Forward to cascor                        |
| `GET/POST/DELETE` | `/api/v1/metrics/layouts` | Metrics panel layouts    | Local file I/O                           |

---

## 4. WebSocket Protocol Contract

### 4.1 Cascor WebSocket Endpoints

#### `/ws/training` — Metrics Stream

- **Direction**: Server → Client (broadcast)
- **Auth**: `X-API-Key` header on connection
- **Handler**: `api.websocket.training_stream.training_stream_handler()`
- **Message types**:

| Type     | Payload Schema                                             | Trigger                          |
|----------|------------------------------------------------------------|----------------------------------|
| `metric` | `{"type": "metric", "data": {epoch, loss, accuracy, ...}}` | `TrainingMonitor.on_epoch_end()` |
| `state`  | `{"type": "state", "data": {status, phase}}`               | State transitions                |
| `event`  | `{"type": "event", "data": {event_type, ...}}`             | Training lifecycle events        |

**Message builder**: `api.websocket.messages.py`:

- `create_metrics_message(metrics_dict)` → `{"type": "metric", "data": {...}}`
- `create_state_message(state_dict)` → `{"type": "state", "data": {...}}`
- `create_event_message(event_type, data)` → `{"type": "event", "data": {...}}`

#### `/ws/control` — Command Channel

- **Direction**: Client → Server
- **Auth**: `X-API-Key` header on connection
- **Handler**: `api.websocket.control_stream.control_stream_handler()`
- **Valid commands**: `{"start", "stop", "pause", "resume", "reset", "set_params"}`
- **CR-008 RESOLVED**: `set_params` now implemented (verified 2026-04-08)

#### `/ws/v1/workers` — Remote Worker Protocol

- **Direction**: Bidirectional (machine-to-machine)
- **Auth**: API key; rejects browser Origin headers
- **Format**: JSON envelope + binary numpy frames (up to 100MB)
- **Handler**: `api.websocket.worker_stream.worker_stream_handler()`

### 4.2 Canopy WebSocket Management

Canopy's `WebSocketManager` (`src/communication/websocket_manager.py`):

- Manages browser WebSocket connections
- Thread-safe broadcast via `asyncio.run_coroutine_threadsafe()`
- Heartbeat keepalive
- Re-broadcasts metrics relay from cascor to browser clients

**KNOWN ISSUE (P5-RC-05)**: Dashboard uses `dcc.Interval` polling exclusively; WebSocket data not consumed by Dash callbacks.

**KNOWN ISSUE (P5-RC-14)**: Relay broadcasts raw cascor field names without normalization.

### 4.3 Metrics Relay Pipeline

```bash
Cascor WS /ws/training
  → JuniperCascorWSClient (in juniper-cascor-client)
    → CascorServiceAdapter._metrics_relay_callback()
      ├── msg_type == "metric":
      │     → broadcast raw payload to browser clients  ← P5-RC-14: unnormalized
      ├── msg_type == "state":
      │     → _state_update_callback(status, phase, current_epoch, ...)
      │     → TrainingState.update_state()
      └── msg_type == "event":
            → _event_callback(event_type, data)
```

---

## 5. Data Contract: Field-Level Breakdown

### 5.1 Cascor Pydantic Request Models

#### NetworkCreateRequest

**Location**: `juniper-cascor/src/api/models/network.py`
**Parent**: `pydantic.BaseModel`

| Field                     | Type    | Default     | Description                   | Canopy Equivalent                                                |
|---------------------------|---------|-------------|-------------------------------|------------------------------------------------------------------|
| `input_size`              | `int`   | `2`         | Number of input features      | Settings: `training.input_size`                                  |
| `output_size`             | `int`   | `2`         | Number of outputs             | Settings: `training.output_size`                                 |
| `epochs_max`              | `int`   | `200`       | Max training epochs           | **DISCREPANCY**: Canopy default is 1,000,000                     |
| `candidate_pool_size`     | `int`   | `8`         | Candidates per growth cycle   | Settings: `training.candidate_pool_size`                         |
| `candidate_epochs`        | `int`   | `200`       | Epochs per candidate training | —                                                                |
| `learning_rate`           | `float` | `0.01`      | Output layer learning rate    | `nn_learning_rate`                                               |
| `candidate_learning_rate` | `float` | `0.01`      | Candidate learning rate       | `cn_candidate_learning_rate` (added FIX-H)                       |
| `max_hidden_units`        | `int`   | `100`       | Maximum hidden units allowed  | `nn_max_hidden_units`                                            |
| `patience`                | `int`   | `50`        | Early stopping patience       | `nn_growth_convergence_threshold` (P5-RC-12b: semantic mismatch) |
| `use_quickprop`           | `bool`  | `True`      | Use quickprop optimizer       | —                                                                |
| `activation`              | `str`   | `"sigmoid"` | Activation function           | —                                                                |

#### TrainingStartRequest

**Location**: `juniper-cascor/src/api/models/training.py`
**Parent**: `pydantic.BaseModel`

| Field              | Type                       | Default | Description                                              |
|--------------------|----------------------------|---------|----------------------------------------------------------|
| `data_source`      | `Optional[str]`            | `None`  | Dataset source type                                      |
| `generator`        | `Optional[str]`            | `None`  | Generator name (e.g., "spiral")                          |
| `generator_params` | `Optional[Dict]`           | `None`  | Generator parameters                                     |
| `data`             | `Optional[Dict]`           | `None`  | Inline training data                                     |
| `epochs`           | `Optional[int]`            | `None`  | Training epochs override                                 |
| `params`           | `Optional[Dict[str, Any]]` | `None`  | **ISSUE (CR-023)**: Unvalidated, forwarded as `**kwargs` |

#### TrainingParamUpdateRequest

**Location**: `juniper-cascor/src/api/models/training.py`
**Parent**: `pydantic.BaseModel`

| Field                     | Type              | Default | Description             | Canopy Source                     |
|---------------------------|-------------------|---------|-------------------------|-----------------------------------|
| `learning_rate`           | `Optional[float]` | `None`  | Output learning rate    | `nn_learning_rate`                |
| `candidate_learning_rate` | `Optional[float]` | `None`  | Candidate learning rate | `cn_candidate_learning_rate`      |
| `max_hidden_units`        | `Optional[int]`   | `None`  | Max hidden units        | `nn_max_hidden_units`             |
| `patience`                | `Optional[int]`   | `None`  | Early stopping patience | `nn_growth_convergence_threshold` |
| `epochs_max`              | `Optional[int]`   | `None`  | Max epochs              | `nn_max_total_epochs`             |

**Updatable keys** (enforced in `TrainingLifecycleManager.update_params()`):

```python
updatable_keys = {
    "learning_rate", "candidate_learning_rate", "max_hidden_units",
    "patience", "epochs_max"
}
```

**NOT updatable at runtime**: `candidate_pool_size`, `candidate_epochs`, `activation`, `use_quickprop`, `input_size`, `output_size`

### 5.2 Cascor Response Payload Schemas

#### Training Status Response

Produced by `TrainingLifecycleManager.get_status()` → `TrainingState.get_state()`:

| Field              | Type    | Default     | Description                                               |
|--------------------|---------|-------------|-----------------------------------------------------------|
| `status`           | `str`   | `"Stopped"` | Training status (Stopped/Started/Paused/Completed/Failed) |
| `phase`            | `str`   | `"idle"`    | Training phase (idle/output/candidate/inference)          |
| `current_epoch`    | `int`   | `0`         | Current training epoch                                    |
| `max_epochs`       | `int`   | `200`       | Maximum training epochs                                   |
| `current_step`     | `int`   | `0`         | Current step within epoch                                 |
| `learning_rate`    | `float` | `0.01`      | Current learning rate                                     |
| `max_hidden_units` | `int`   | `100`       | Maximum hidden units                                      |
| `network_name`     | `str`   | `""`        | Network identifier                                        |
| `timestamp`        | `str`   | `""`        | ISO timestamp                                             |

#### Training Metrics Entry

Produced by `TrainingMonitor.on_epoch_end()`:

| Field                 | Type              | Source                                  | Description               |
|-----------------------|-------------------|-----------------------------------------|---------------------------|
| `epoch`               | `int`             | `network.history["train_loss"]` length  | Current epoch number      |
| `loss`                | `float`           | `network.history["train_loss"][-1]`     | Training loss             |
| `accuracy`            | `float`           | `network.history["train_accuracy"][-1]` | Training accuracy         |
| `validation_loss`     | `Optional[float]` | `network.history["value_loss"][-1]`     | Validation loss           |
| `validation_accuracy` | `Optional[float]` | `network.history["value_accuracy"][-1]` | Validation accuracy       |
| `hidden_units`        | `int`             | `len(network.hidden_units)`             | Current hidden unit count |
| `phase`               | `str`             | `monitor.current_phase`                 | Training phase            |
| `timestamp`           | `str`             | `datetime.now().isoformat()`            | ISO timestamp             |

#### Network Topology Response (Weight-Oriented)

Produced by `TrainingLifecycleManager.get_topology()`:

| Field            | Type                | Description                                |
|------------------|---------------------|--------------------------------------------|
| `input_size`     | `int`               | Number of inputs                           |
| `output_size`    | `int`               | Number of outputs                          |
| `hidden_units`   | `List[Dict]`        | Array of `{id, weights, bias, activation}` |
| `output_weights` | `List[List[float]]` | Output layer weight matrix                 |
| `output_bias`    | `List[float]`       | Output layer bias vector                   |

### 5.3 Canopy Dashboard Expected Formats

#### Dashboard Metrics Format (Nested)

Expected by `MetricsPanel` (`metrics_panel.py`):

| Access Pattern                          | Type              | Description         |
|-----------------------------------------|-------------------|---------------------|
| `m["epoch"]`                            | `int`             | Epoch number        |
| `m["metrics"]["loss"]`                  | `float`           | Training loss       |
| `m["metrics"]["accuracy"]`              | `float`           | Training accuracy   |
| `m["metrics"]["val_loss"]`              | `Optional[float]` | Validation loss     |
| `m["metrics"]["val_accuracy"]`          | `Optional[float]` | Validation accuracy |
| `m["network_topology"]["hidden_units"]` | `int`             | Hidden unit count   |
| `m["phase"]`                            | `str`             | Training phase      |
| `m["timestamp"]`                        | `str`             | ISO timestamp       |

**Transformation**: `CascorServiceAdapter._to_dashboard_metric()` converts flat → nested.

#### Dashboard Topology Format (Graph-Oriented)

Expected by `NetworkVisualizer` (`network_visualizer.py`):

| Field          | Type         | Description                                 |
|----------------|--------------|---------------------------------------------|
| `input_units`  | `int`        | Number of input nodes                       |
| `output_units` | `int`        | Number of output nodes                      |
| `hidden_units` | `int`        | Number of hidden nodes (integer, NOT array) |
| `nodes`        | `List[Dict]` | `[{id, type, layer}]`                       |
| `connections`  | `List[Dict]` | `[{from, to, weight}]`                      |

**Transformation**: `CascorServiceAdapter._transform_topology()` converts weight-oriented → graph-oriented.

### 5.4 Canopy TrainingState Fields

**Location**: `juniper-canopy/src/backend/training_monitor.py`
**Class**: `TrainingState`

| Attribute            | Type    | Default     | Updated By                        |
|----------------------|---------|-------------|-----------------------------------|
| `__status`           | `str`   | `"Stopped"` | `update_state(status=)`           |
| `__phase`            | `str`   | `"idle"`    | `update_state(phase=)`            |
| `__current_epoch`    | `int`   | `0`         | `update_state(current_epoch=)`    |
| `__max_epochs`       | `int`   | `200`       | `update_state(max_epochs=)`       |
| `__current_step`     | `int`   | `0`         | `update_state(current_step=)`     |
| `__learning_rate`    | `float` | `0.01`      | `update_state(learning_rate=)`    |
| `__max_hidden_units` | `int`   | `100`       | `update_state(max_hidden_units=)` |
| `__hidden_units`     | `int`   | `0`         | `update_state(hidden_units=)`     |
| `__network_name`     | `str`   | `""`        | `update_state(network_name=)`     |
| `__loss`             | `float` | `0.0`       | `update_state(loss=)`             |
| `__accuracy`         | `float` | `0.0`       | `update_state(accuracy=)`         |
| `__timestamp`        | `str`   | `""`        | `update_state(timestamp=)`        |

### 5.5 Canopy SyncedState Dataclass

**Location**: `juniper-canopy/src/backend/state_sync.py`
**Class**: `SyncedState` (dataclass)

| Field             | Type             | Default     | Purpose                                          |
|-------------------|------------------|-------------|--------------------------------------------------|
| `is_training`     | `bool`           | `False`     | Whether cascor is actively training              |
| `status`          | `str`            | `"Stopped"` | Normalized status string                         |
| `phase`           | `str`            | `"Idle"`    | Current training phase                           |
| `current_epoch`   | `int`            | `0`         | Current epoch from cascor                        |
| `max_epochs`      | `int`            | `0`         | Max epochs from cascor                           |
| `params`          | `Dict[str, Any]` | `{}`        | Training parameters (mapped to Canopy namespace) |
| `topology`        | `Optional[Dict]` | `None`      | Network topology (transformed to graph format)   |
| `metrics_history` | `List[Dict]`     | `[]`        | Metrics history (normalized to dashboard format) |

---

## 6. Interface Agreement: Canopy-Side Components

### 6.1 BackendProtocol

**Location**: `juniper-canopy/src/backend/protocol.py`
**Type**: `typing.Protocol`
**Implementations**: `DemoBackend`, `ServiceBackend`

| Method                       | Return Type                | Purpose                 |
|------------------------------|----------------------------|-------------------------|
| `initialize()`               | `None`                     | Setup and connection    |
| `get_status()`               | `Dict[str, Any]`           | Training status         |
| `get_metrics_history(limit)` | `List[Dict[str, Any]]`     | Metrics history         |
| `get_current_metrics()`      | `Dict[str, Any]`           | Latest metrics snapshot |
| `get_network_topology()`     | `Optional[Dict[str, Any]]` | Network topology        |
| `get_network_stats()`        | `Optional[Dict[str, Any]]` | Weight statistics       |
| `get_dataset()`              | `Optional[Dict[str, Any]]` | Dataset info/data       |
| `get_decision_boundary()`    | `Optional[Dict[str, Any]]` | Decision boundary       |
| `get_training_params()`      | `Dict[str, Any]`           | Training parameters     |
| `start_training(**kwargs)`   | `Dict[str, Any]`           | Start training          |
| `stop_training()`            | `Dict[str, Any]`           | Stop training           |
| `pause_training()`           | `Dict[str, Any]`           | Pause training          |
| `resume_training()`          | `Dict[str, Any]`           | Resume training         |
| `reset_training()`           | `Dict[str, Any]`           | Reset training          |
| `apply_params(params)`       | `Dict[str, Any]`           | Apply parameter updates |

**SYSTEMIC ISSUE (P5-RC-18)**: All methods return `Dict[str, Any]` — no TypedDict or dataclass enforcement. Dead abstractions exist in `data_adapter.py` (`TrainingMetrics`, `NetworkNode`, `NetworkConnection`, `NetworkTopology`) that are never used.

### 6.2 ServiceBackend

**Location**: `juniper-canopy/src/backend/service_backend.py`
**Wraps**: `CascorServiceAdapter`
**State**: Holds `_synced_state: SyncedState` from initial connection

### 6.3 CascorServiceAdapter

**Location**: `juniper-canopy/src/backend/cascor_service_adapter.py`
**Wraps**: `JuniperCascorClient` (from juniper-cascor-client)
**Critical role**: All data transformation between cascor wire format and dashboard format

#### Transformation Functions

| Function                     | Purpose                              | Input Format                             | Output Format                                                        |
|------------------------------|--------------------------------------|------------------------------------------|----------------------------------------------------------------------|
| `_unwrap_response(response)` | Extract `data` from ResponseEnvelope | `{"status": "success", "data": {...}}`   | `{...}`                                                              |
| `_normalize_metric(entry)`   | Normalize cascor field names         | `{loss, accuracy, validation_loss, ...}` | `{train_loss, train_accuracy, val_loss, ...}`                        |
| `_to_dashboard_metric(flat)` | Convert flat → nested for dashboard  | `{train_loss, train_accuracy, ...}`      | `{metrics: {loss, accuracy, ...}, network_topology: {...}}`          |
| `_transform_topology(raw)`   | Convert weight → graph format        | `{input_size, hidden_units: [...], ...}` | `{input_units, hidden_units: int, nodes: [...], connections: [...]}` |
| `_normalize_status(raw)`     | Normalize status strings             | Various cases                            | Title-case canonical                                                 |

#### Parameter Mapping

**`_CANOPY_TO_CASCOR_PARAM_MAP`** (Canopy → Cascor field name translation):

| Canopy Key                          | Cascor Key                        | Functional  | Notes                                                                |
|-------------------------------------|-----------------------------------|-------------|----------------------------------------------------------------------|
| `nn_learning_rate`                  | `learning_rate`                   | Yes         |                                                                      |
| `nn_max_hidden_units`               | `max_hidden_units`                | Yes         |                                                                      |
| `nn_max_total_epochs`               | `epochs_max`                      | Yes         |                                                                      |
| `nn_max_iterations`                 | `max_iterations`                  | **Partial** | Mapped, but cascor `CascadeCorrelationConfig` may lack field         |
| `nn_init_output_weights`            | `init_output_weights`             | Yes         |                                                                      |
| `nn_growth_convergence_threshold`   | `convergence_threshold`           | Yes         |                                                                      |
| `nn_patience`                       | `patience`                        | Yes         |                                                                      |
| `cn_patience`                       | `candidate_patience`              | Yes         |                                                                      |
| `cn_training_convergence_threshold` | `candidate_convergence_threshold` | Yes         |                                                                      |
| `cn_training_iterations`            | `candidate_epochs`                | **Partial** | Mapped, but `candidate_epochs` may not be in cascor `updatable_keys` |
| `cn_pool_size`                      | `candidate_pool_size`             | Yes         | Now in cascor `updatable_keys`                                       |
| `cn_correlation_threshold`          | `correlation_threshold`           | Yes         | Now in cascor `updatable_keys`                                       |
| `cn_candidate_learning_rate`        | `candidate_learning_rate`         | Yes         | Added FIX-H                                                          |

**NOTE**: The param map has been significantly expanded since the prior analysis (2026-03-28). Key additions: `nn_max_iterations` → `max_iterations`, `cn_pool_size` → `candidate_pool_size`, `cn_correlation_threshold` → `correlation_threshold`, and several convergence/patience mappings.

**Cascor `updatable_keys`** (current, verified 2026-04-08):

```python
updatable_keys = {
    "learning_rate", "candidate_learning_rate", "correlation_threshold",
    "candidate_pool_size", "max_hidden_units", "epochs_max",
    "max_iterations", "patience"
}
```

**UPDATE (2026-04-08)**: `max_iterations` IS now in cascor's `updatable_keys` and `_CANOPY_TO_CASCOR_PARAM_MAP`. The CR-006 issue regarding `max_iterations` being a dead-end has been **partially addressed** in the param mapping layer. However, the deeper issue — whether `CascadeCorrelationConfig` has a `max_iterations` field and whether `fit()` properly deconflates epochs vs iterations — requires further verification.

### 6.4 CascorStateSync

**Location**: `juniper-canopy/src/backend/state_sync.py`
**Purpose**: One-time connect-time synchronization

Fetches from cascor via raw client, normalizes, and produces `SyncedState`:

- Status normalized via case-insensitive `_normalize_status()`
- Metrics normalized via `_normalize_metric()` + `_to_dashboard_metric()`
- Params mapped via reverse param map to Canopy namespace
- Topology transformed via `_transform_topology()`

---

## 7. Interface Agreement: Cascor-Side Components

### 7.1 TrainingLifecycleManager

**Location**: `juniper-cascor/src/api/lifecycle/manager.py`
**Role**: Central orchestrator — all route handlers delegate to this class

Key interface-relevant methods:

- `create_network(**kwargs)` → Creates network, updates `TrainingState`
- `start_training(**kwargs)` → Starts training via `CascadeCorrelationNetwork.fit()`
- `stop_training()` / `pause_training()` / `resume_training()` / `reset_training()`
- `update_params(params)` → Validates against `updatable_keys`, applies to network
- `get_status()` → Returns `TrainingState.get_state()`
- `get_topology()` → Returns weight-oriented topology dict
- `get_metrics_history(count)` → Returns `TrainingMonitor.metrics_buffer`

### 7.2 TrainingStateMachine

**Location**: `juniper-cascor/src/api/lifecycle/state_machine.py`

#### TrainingStatus Enum

| Value       | `.name` (uppercase) | Display String                |
|-------------|---------------------|-------------------------------|
| `STOPPED`   | `"STOPPED"`         | Used in `get_state_summary()` |
| `STARTED`   | `"STARTED"`         | Active training               |
| `PAUSED`    | `"PAUSED"`          | Training paused               |
| `COMPLETED` | `"COMPLETED"`       | Training complete             |
| `FAILED`    | `"FAILED"`          | Training failed               |

#### TrainingPhase Enum

| Value       | Meaning                 |
|-------------|-------------------------|
| `IDLE`      | No training active      |
| `OUTPUT`    | Output layer training   |
| `CANDIDATE` | Candidate unit training |
| `INFERENCE` | Post-training inference |

**WebSocket broadcasts use hardcoded title-case** (`"Started"`, `"Output"`) in `manager.py`, NOT enum `.name` values. This is why P5-RC-03 is latent rather than active.

### 7.3 TrainingMonitor

**Location**: `juniper-cascor/src/api/lifecycle/monitor.py`

Key fields:

- `current_phase: str` — Updated during phase transitions (fixed 2026-03-28 and 2026-03-29)
- `metrics_buffer: List[Dict]` — Accumulated metrics entries
- `metrics_queue: Queue` — **DEAD**: Populated but never consumed (Appendix G.4.2)

### 7.4 CascadeCorrelationConfig

**Location**: `juniper-cascor/src/cascade_correlation/cascade_correlation_config/cascade_correlation_config.py`

| Field                     | Type    | Default     | Used For                    |
|---------------------------|---------|-------------|-----------------------------|
| `input_size`              | `int`   | `2`         | Network input dimensions    |
| `output_size`             | `int`   | `2`         | Network output dimensions   |
| `epochs_max`              | `int`   | `10000`     | Max training epochs         |
| `candidate_pool_size`     | `int`   | `8`         | Candidates per growth cycle |
| `candidate_epochs`        | `int`   | `200`       | Epochs per candidate        |
| `learning_rate`           | `float` | `0.01`      | Output layer learning rate  |
| `candidate_learning_rate` | `float` | `0.01`      | Candidate learning rate     |
| `max_hidden_units`        | `int`   | `100`       | Max hidden units            |
| `patience`                | `int`   | `50`        | Early stopping patience     |
| `use_quickprop`           | `bool`  | `True`      | Optimizer selection         |
| `activation`              | `str`   | `"sigmoid"` | Activation function         |

**UPDATE (2026-04-08)**: `max_iterations` NOW EXISTS in the config (line 150, default from `_CASCADE_CORRELATION_NETWORK_MAX_ITERATIONS`). This is a significant remediation of CR-006 since the prior analysis.

---

## 8. Interface Agreement: Cascor-Client Library

### 8.1 JuniperCascorClient

**Location**: `juniper-cascor-client/juniper_cascor_client/client.py`

#### Constructor

```python
JuniperCascorClient(
    base_url: str = "http://localhost:8200",
    api_key: Optional[str] = None,
    timeout: float = 30.0,
    session: Optional[requests.Session] = None
)
```

#### Method-to-Endpoint Mapping

| Client Method                | HTTP   | Cascor Endpoint               | Notes         |
|------------------------------|--------|-------------------------------|---------------|
| `health_check()`             | GET    | `/v1/health`                  |               |
| `is_alive()`                 | GET    | `/v1/health`                  | Returns bool  |
| `is_ready()`                 | GET    | `/v1/health/ready`            | Returns bool  |
| `create_network(**kwargs)`   | POST   | `/v1/network`                 |               |
| `get_network()`              | GET    | `/v1/network`                 |               |
| `delete_network()`           | DELETE | `/v1/network`                 |               |
| `get_topology()`             | GET    | `/v1/network/topology`        |               |
| `get_statistics()`           | GET    | `/v1/network/stats`           |               |
| `start_training(**kwargs)`   | POST   | `/v1/training/start`          |               |
| `stop_training()`            | POST   | `/v1/training/stop`           |               |
| `pause_training()`           | POST   | `/v1/training/pause`          |               |
| `resume_training()`          | POST   | `/v1/training/resume`         |               |
| `reset_training()`           | POST   | `/v1/training/reset`          |               |
| `get_training_status()`      | GET    | `/v1/training/status`         |               |
| `get_training_params()`      | GET    | `/v1/training/params`         |               |
| `update_params(params)`      | PATCH  | `/v1/training/params`         |               |
| `get_metrics()`              | GET    | `/v1/metrics/history?count=1` |               |
| `get_metrics_history(count)` | GET    | `/v1/metrics/history`         |               |
| `get_dataset()`              | GET    | `/v1/dataset`                 | Metadata only |
| `get_dataset_data()`         | GET    | `/v1/dataset/data`            | With arrays   |
| `get_decision_boundary(res)` | GET    | `/v1/decision-boundary`       |               |
| `list_snapshots()`           | GET    | `/v1/snapshots`               |               |
| `save_snapshot(desc)`        | POST   | `/v1/snapshots`               |               |
| `get_snapshot(id)`           | GET    | `/v1/snapshots/{id}`          |               |
| `load_snapshot(id)`          | POST   | `/v1/snapshots/{id}/restore`  |               |
| `list_workers()`             | GET    | `/v1/workers`                 |               |
| `get_worker(id)`             | GET    | `/v1/workers/{id}`            |               |
| `get_worker_stats()`         | GET    | `/v1/workers/stats`           |               |

### 8.2 JuniperCascorWSClient

**Location**: `juniper-cascor-client/juniper_cascor_client/ws_client.py`

WebSocket client for consuming cascor training streams:

- Connects to `ws://{host}:{port}/ws/training`
- Receives JSON messages (`metric`, `state`, `event` types)
- Callback-based API: `on_metric`, `on_state`, `on_event`

### 8.3 FakeCascorClient (Testing)

**Location**: `juniper-cascor-client/juniper_cascor_client/testing/fake_client.py`

Provides a test double for `JuniperCascorClient` with configurable responses.

**KNOWN ISSUE**: Sends uppercase status values (triggering P5-RC-03 in tests). Returns a third topology format (graph-oriented with `input_size`/`output_size` keys — hybrid of CasCor and graph formats).

---

## 9. Naming Convention Discrepancies

### 9.1 Field Name Translation Map

| Concept                 | Cascor Field Name                        | Canopy Field Name                 | Cascor-Client         | Dashboard Access                  |
|-------------------------|------------------------------------------|-----------------------------------|-----------------------|-----------------------------------|
| Training loss           | `loss`                                   | `train_loss`                      | `loss`                | `metrics.loss`                    |
| Training accuracy       | `accuracy`                               | `train_accuracy`                  | `accuracy`            | `metrics.accuracy`                |
| Validation loss         | `validation_loss`                        | `val_loss`                        | `validation_loss`     | `metrics.val_loss`                |
| Validation accuracy     | `validation_accuracy`                    | `val_accuracy`                    | `validation_accuracy` | `metrics.val_accuracy`            |
| Hidden unit count       | `hidden_units` (int in topology context) | `hidden_units`                    | `hidden_units`        | `network_topology.hidden_units`   |
| Input count             | `input_size`                             | `input_units`                     | `input_size`          | `input_units`                     |
| Output count            | `output_size`                            | `output_units`                    | `output_size`         | `output_units`                    |
| Max epochs              | `epochs_max`                             | `nn_max_total_epochs`             | —                     | UI: `nn-max-total-epochs-input`   |
| Learning rate           | `learning_rate`                          | `nn_learning_rate`                | —                     | UI: `nn-learning-rate-input`      |
| Max hidden units        | `max_hidden_units`                       | `nn_max_hidden_units`             | —                     | UI: `nn-max-hidden-units-input`   |
| Patience                | `patience`                               | `nn_growth_convergence_threshold` | —                     | UI: semantic mismatch             |
| Candidate learning rate | `candidate_learning_rate`                | `cn_candidate_learning_rate`      | —                     | —                                 |
| Max iterations          | `max_iterations`                         | `nn_max_iterations`               | —                     | **NOW MAPPED** (CR-006 addressed) |

### 9.2 Status String Conventions

| Context                                     | Format           | Example Values                 |
|---------------------------------------------|------------------|--------------------------------|
| Cascor `TrainingStatus` enum `.name`        | UPPERCASE        | `STARTED`, `STOPPED`, `PAUSED` |
| Cascor WS broadcast (manager.py)            | Title-case       | `Started`, `Output`            |
| Canopy normalized                           | Title-case       | `Started`, `Stopped`, `Paused` |
| Canopy `_normalize_status()` input handling | Case-insensitive | Accepts all cases              |

### 9.3 Phase String Conventions

| Context                     | Format          | Values                                     |
|-----------------------------|-----------------|--------------------------------------------|
| Cascor `TrainingPhase` enum | UPPERCASE       | `IDLE`, `OUTPUT`, `CANDIDATE`, `INFERENCE` |
| Cascor WS broadcast         | Title-case      | `Output`, `Candidate`                      |
| Canopy `TrainingState`      | lowercase/mixed | `idle`, `output`, `candidate`              |
| Canopy dashboard display    | Title-case      | `"Output Training"`, `"Candidate Pool"`    |

### 9.4 Default Value Discrepancies

| Parameter                   | Cascor Constant   | Cascor API Default | Canopy Default | Status                                |
|-----------------------------|-------------------|--------------------|----------------|---------------------------------------|
| `epochs_max` / `max_epochs` | 10,000            | 200                | 1,000,000      | **DISCREPANCY** (CR-006)              |
| `max_iterations`            | Exists (constant) | 1,000              | 1,000          | **NOW CONSISTENT** (CR-006 addressed) |
| `candidate_pool_size`       | 8                 | 8                  | 8              | Consistent                            |
| `learning_rate`             | 0.01              | 0.01               | 0.01           | Consistent                            |
| `max_hidden_units`          | 100               | 100                | 1,000          | **DISCREPANCY**                       |
| `patience`                  | 50                | 50                 | 50             | Consistent                            |

**CRITICAL NOTE (verified 2026-04-08)**: The cascor constants chain defaults (`constants_model.py`) have been updated to extremely large values since the prior analysis:

- `_PROJECT_MODEL_EPOCHS_MAX` = 10^20 (was 10,000)
- `_PROJECT_MODEL_MAX_ITERATIONS` = 10^17
- `_PROJECT_MODEL_OUTPUT_EPOCHS` = 10^20
- `_PROJECT_MODEL_MAX_HIDDEN_UNITS` = 1,000
- `_PROJECT_MODEL_CANDIDATE_POOL_SIZE` = 40

These internal constants are designed for long-running research experiments. The API model defaults (`NetworkCreateRequest`) remain conservative (e.g., `epochs_max=200`, `max_hidden_units=10`) and represent a **separate, intentional** default layer for API consumers. This two-tier default system is architectural, not a bug.

---

## 10. Mapping Classes and Translation Functions

### 10.1 Primary Translation Layer: CascorServiceAdapter

All data translation between cascor wire format and canopy dashboard format is centralized in `CascorServiceAdapter`:

| Function                      | Location                    | Direction              | Purpose                              |
|-------------------------------|-----------------------------|------------------------|--------------------------------------|
| `_normalize_metric()`         | `cascor_service_adapter.py` | Cascor → Canopy (flat) | Normalize field names                |
| `_to_dashboard_metric()`      | `cascor_service_adapter.py` | Flat → Nested          | Match dashboard access patterns      |
| `_transform_topology()`       | `cascor_service_adapter.py` | Weight → Graph         | Match NetworkVisualizer expectations |
| `_normalize_status()`         | `state_sync.py`             | Various → Title-case   | Normalize status strings             |
| `_CANOPY_TO_CASCOR_PARAM_MAP` | `cascor_service_adapter.py` | Canopy → Cascor        | Parameter name translation for PATCH |

### 10.2 Reverse Parameter Mapping

Used during state sync to convert cascor parameter names to canopy namespace:

```python
# Reverse of _CANOPY_TO_CASCOR_PARAM_MAP
_CASCOR_TO_CANOPY_PARAM_MAP = {v: k for k, v in _CANOPY_TO_CASCOR_PARAM_MAP.items()}
```

### 10.3 Decision Boundary Transformation

**Location**: `CascorServiceAdapter.get_decision_boundary()`

Transforms cascor response (`grid_x`, `grid_y`, `predictions`) → dashboard format (`xx`, `yy`, `Z`).

This is the **only transformation that was correctly implemented from the start**, demonstrating that the pattern existed but was not applied to metrics or topology paths.

---

## 11. Instantiation and Usage Locations

### 11.1 Where Interface Data Structures Are Created

#### Cascor Side

| Data Structure               | Created At                | File:Line                      | Method                    |
|------------------------------|---------------------------|--------------------------------|---------------------------|
| `ResponseEnvelope`           | Every route response      | `api/routes/*.py` (all routes) | Route handlers wrap data  |
| `NetworkCreateRequest`       | POST /v1/network          | `api/routes/network.py`        | Pydantic deserialization  |
| `TrainingStartRequest`       | POST /v1/training/start   | `api/routes/training.py`       | Pydantic deserialization  |
| `TrainingParamUpdateRequest` | PATCH /v1/training/params | `api/routes/training.py`       | Pydantic deserialization  |
| Training metrics dict        | `on_epoch_end()`          | `api/lifecycle/monitor.py`     | Metrics extraction        |
| Training state dict          | `get_state()`             | `api/lifecycle/monitor.py`     | State serialization       |
| Topology dict                | `get_topology()`          | `api/lifecycle/manager.py`     | Topology construction     |
| WebSocket messages           | Broadcast                 | `api/websocket/messages.py`    | Message builder functions |

#### Canopy Side

| Data Structure             | Created At           | File:Line                           | Method                   |
|----------------------------|----------------------|-------------------------------------|--------------------------|
| `SyncedState`              | Connection init      | `backend/state_sync.py`             | `CascorStateSync.sync()` |
| `TrainingState`            | App startup          | `backend/training_monitor.py`       | Singleton                |
| Dashboard metrics (nested) | Every metrics fetch  | `backend/cascor_service_adapter.py` | `_to_dashboard_metric()` |
| Dashboard topology (graph) | Every topology fetch | `backend/cascor_service_adapter.py` | `_transform_topology()`  |
| Param update dict          | User action          | `main.py`                           | Parameter panel callback |

### 11.2 Where Interface Data Is Consumed

#### Canopy Dashboard Consumers

| Consumer             | File                                             | Data Consumed     | Access Pattern                                                  |
|----------------------|--------------------------------------------------|-------------------|-----------------------------------------------------------------|
| `MetricsPanel`       | `frontend/components/metrics_panel.py`           | Metrics history   | `m["metrics"]["loss"]`, `m["network_topology"]["hidden_units"]` |
| `NetworkVisualizer`  | `frontend/components/network_visualizer.py`      | Topology          | `t["input_units"]`, `t["connections"]`                          |
| `DatasetPlotter`     | `frontend/components/dataset_plotter.py`         | Dataset           | `d["inputs"]`, `d["targets"]`                                   |
| `ParametersPanel`    | `frontend/components/parameters_panel.py`        | Training params   | `nn_*` / `cn_*` keys                                            |
| `TrainingMetrics`    | `frontend/components/training_metrics.py`        | Metrics           | Nested format                                                   |
| `CandidateMetrics`   | `frontend/components/candidate_metrics_panel.py` | Candidate data    | —                                                               |
| `WorkerPanel`        | `frontend/components/worker_panel.py`            | Worker data       | —                                                               |
| Status bar           | `frontend/dashboard_manager.py`                  | Status            | Flat keys (`is_running`, `phase`, `current_epoch`)              |
| `DecisionBoundary`   | `frontend/components/decision_boundary.py`       | Decision boundary | `xx`, `yy`, `Z`                                                 |
| `HDF5SnapshotsPanel` | `frontend/components/hdf5_snapshots_panel.py`    | Snapshot list     | —                                                               |

---

## 12. High-Level Code Walkthrough

### 12.1 Application Startup Flow

```bash
1. juniper-cascor starts:
   server.py → create_app() → FastAPI lifespan:
     - Initialize TrainingStateMachine
     - Initialize TrainingMonitor
     - Initialize TrainingLifecycleManager
     - Initialize WebSocketManager
     - Register routes and WebSocket handlers
     - Auto-start training if JUNIPER_CASCOR_AUTO_START=true

2. juniper-canopy starts:
   main.py → FastAPI + Dash integration:
     - Create Settings (Pydantic)
     - Create backend (BackendProtocol):
       a. If JUNIPER_CANOPY_DEMO_MODE=true:
          → Create DemoBackend → DemoMode simulation
       b. If demo mode disabled:
          → Try ServiceBackend:
            i. Create JuniperCascorClient
            ii. Create CascorServiceAdapter(client)
            iii. Create ServiceBackend(adapter)
            iv. backend.initialize() → CascorStateSync:
                - Fetch status, params, topology, metrics
                - Normalize all data formats
                - Return SyncedState
            v. Start metrics relay (WebSocket)
          → On failure: Fall back to DemoBackend
     - Initialize DashboardManager with backend
     - Register Dash callbacks
     - Start interval polling (1s fast, 5s slow)
```

### 12.2 Training Session Flow

```bash
1. User clicks "Start Training" in Canopy:
   → main.py callback → POST /api/training/start
   → ServiceBackend.start_training()
   → CascorServiceAdapter.start_training()
   → JuniperCascorClient.start_training()
   → POST /v1/training/start
   → Cascor route handler
   → TrainingLifecycleManager.start_training()
   → TrainingStateMachine: STOPPED → STARTED
   → ThreadPoolExecutor: _run_training()
     → CascadeCorrelationNetwork.fit()

2. During training (cascor side):
   → fit() → train_output_layer()
     → TrainingMonitor.on_epoch_end() [after output training]
       → Append to metrics_buffer
       → WebSocket broadcast: create_metrics_message()
   → fit() → grow_network()
     → train_candidates() [multiprocessing, NO metrics]
     → _add_best_candidate()
     → _retrain_output_layer()
       → TrainingMonitor.on_epoch_end()
     → validate_training()
       → TrainingMonitor.on_epoch_end()

3. Canopy receives metrics:
   a. Via REST polling (dcc.Interval, 1s):
      → GET /api/metrics/history
      → ServiceBackend.get_metrics_history()
      → adapter._normalize_metric() → _to_dashboard_metric()
      → Dashboard stores in metrics-store
      → MetricsPanel renders charts

   b. Via WebSocket relay (currently unused by dashboard):
      → Cascor WS broadcast
      → JuniperCascorWSClient receives
      → relay callback → broadcast to browser (unnormalized)
```

### 12.3 Parameter Update Flow

```bash
1. User changes parameter in Canopy dashboard:
   → Dash callback fires
   → main.py /api/params POST handler
   → Collects nn_*/cn_* parameters from form
   → ServiceBackend.apply_params(params)
   → CascorServiceAdapter.apply_params(params)
     → _CANOPY_TO_CASCOR_PARAM_MAP translation:
       nn_learning_rate → learning_rate
       nn_max_hidden_units → max_hidden_units
       nn_growth_convergence_threshold → patience
       nn_max_total_epochs → epochs_max
       cn_candidate_learning_rate → candidate_learning_rate
     → JuniperCascorClient.update_params(cascor_params)
     → PATCH /v1/training/params
     → TrainingLifecycleManager.update_params()
       → Validate against updatable_keys
       → Apply to network: setattr(network, key, value)
```

---

## 13. Detailed Operational Code Walkthrough

### 13.1 Metrics Normalization Pipeline

**Step 1**: Cascor `TrainingMonitor.on_epoch_end()` produces:

```python
{
    "epoch": 5,
    "loss": 0.45,
    "accuracy": 0.82,
    "validation_loss": 0.60,
    "validation_accuracy": 0.65,
    "hidden_units": 3,
    "phase": "output",
    "timestamp": "2026-04-08T12:00:00"
}
```

**Step 2**: `_normalize_metric()` transforms to flat canonical:

```python
{
    "epoch": 5,
    "train_loss": 0.45,
    "train_accuracy": 0.82,
    "val_loss": 0.60,
    "val_accuracy": 0.65,
    "hidden_units": 3,
    "phase": "output",
    "timestamp": "2026-04-08T12:00:00"
}
```

**Step 3**: `_to_dashboard_metric()` transforms to nested:

```python
{
    "epoch": 5,
    "metrics": {
        "loss": 0.45,
        "accuracy": 0.82,
        "val_loss": 0.60,
        "val_accuracy": 0.65
    },
    "network_topology": {
        "hidden_units": 3
    },
    "phase": "output",
    "timestamp": "2026-04-08T12:00:00"
}
```

### 13.2 Topology Transformation Pipeline

**Step 1**: Cascor `get_topology()` produces (weight-oriented):

```python
{
    "input_size": 2,
    "output_size": 1,
    "hidden_units": [
        {"id": 0, "weights": [0.5, -0.3], "bias": 0.1, "activation": "sigmoid"},
        {"id": 1, "weights": [0.2, 0.8, -0.4], "bias": -0.2, "activation": "sigmoid"}
    ],
    "output_weights": [[0.7, -0.1, 0.5]],
    "output_bias": [0.3]
}
```

**Step 2**: `_transform_topology()` produces (graph-oriented):

```python
{
    "input_units": 2,
    "output_units": 1,
    "hidden_units": 2,  # integer count
    "nodes": [
        {"id": "input_0", "type": "input", "layer": 0},
        {"id": "input_1", "type": "input", "layer": 0},
        {"id": "hidden_0", "type": "hidden", "layer": 1},
        {"id": "hidden_1", "type": "hidden", "layer": 2},
        {"id": "output_0", "type": "output", "layer": 3}
    ],
    "connections": [
        {"from": "input_0", "to": "hidden_0", "weight": 0.5},
        {"from": "input_1", "to": "hidden_0", "weight": -0.3},
        {"from": "input_0", "to": "hidden_1", "weight": 0.2},
        {"from": "input_1", "to": "hidden_1", "weight": 0.8},
        {"from": "hidden_0", "to": "hidden_1", "weight": -0.4},  # cascade connection
        {"from": "input_0", "to": "output_0", "weight": 0.7},
        {"from": "hidden_0", "to": "output_0", "weight": -0.1},
        {"from": "hidden_1", "to": "output_0", "weight": 0.5}
    ]
}
```

### 13.3 State Synchronization Sequence

```bash
ServiceBackend.initialize():
  1. adapter.connect() → health check
  2. adapter.attach_to_existing() → non-destructive probe
  3. CascorStateSync(adapter._client).sync():
     a. Fetch training status → normalize status case
     b. Fetch training params → map to Canopy namespace
     c. Fetch topology → transform to graph format
     d. Fetch metrics history → normalize → to_dashboard format
     e. Return SyncedState
  4. Apply synced state to TrainingState
  5. Start metrics relay (WebSocket)
```

---

## 14. Cross-Side Requirements Asymmetries

### 14.1 Features Present in Canopy but Not in Cascor

| Feature                           | Canopy Side                                           | Cascor Side                                                      | Impact                          |
|-----------------------------------|-------------------------------------------------------|------------------------------------------------------------------|---------------------------------|
| `max_iterations` limit            | UI control exists, settings defined, constant defined | **NOW EXISTS**: config, API model, TrainingState, updatable_keys | **RESOLVED** (CR-006 addressed) |
| `candidate_epochs` runtime update | Mapped via `cn_training_iterations`                   | Now mapped to `candidate_epochs`; verify if in `updatable_keys`  | **Verify**                      |
| WebSocket data consumption        | `websocket-data` div exists in DOM                    | Broadcasts correctly                                             | Dashboard ignores it            |
| Redis caching                     | Client and status endpoint exist                      | N/A                                                              | Soft-fail                       |
| Cassandra storage                 | Client and status endpoint exist                      | N/A                                                              | Soft-fail                       |
| Circuit breaker                   | Implemented in `circuit_breaker.py`                   | N/A                                                              | Canopy-side resilience          |

### 14.2 Features Present in Cascor but Not Consumed by Canopy

| Feature                    | Cascor Side                             | Canopy Side                 | Impact                |
|----------------------------|-----------------------------------------|-----------------------------|-----------------------|
| Snapshot management        | Full CRUD API                           | `HDF5SnapshotsPanel` exists | Partially wired       |
| Worker management          | Full registry + coordinator             | `WorkerPanel` exists        | Partially wired       |
| `set_params` via WebSocket | Documented but not implemented (CR-008) | Not attempted               | Both sides incomplete |
| Prometheus metrics         | Available when enabled                  | Not consumed                | Observability gap     |
| Rate limiting (WS)         | Not implemented per-connection          | N/A                         | Security gap          |
| Binary worker protocol     | Full numpy serialization                | Not applicable              | Worker-only feature   |

### 14.3 Validation and Enforcement Asymmetries

| Check                 | Cascor                                     | Canopy                       | Discrepancy                                    |
|-----------------------|--------------------------------------------|------------------------------|------------------------------------------------|
| Parameter validation  | `updatable_keys` whitelist                 | Maps any `nn_*/cn_*` key     | Canopy may send keys cascor silently drops     |
| Training start params | `Optional[Dict[str, Any]]` (no validation) | —                            | CR-023: kwargs forwarded unvalidated           |
| Status normalization  | Enum-based (strict)                        | Case-insensitive mapping     | Canopy handles more cases than cascor produces |
| Topology format       | Weight-oriented (native)                   | Graph-oriented (transformed) | Transformation in adapter                      |

---

## 15. Current Issue Registry

### 15.1 Open Issues (Not Yet Remediated)

| ID         | Source                   | Severity         | Summary                                                                                | Status                                                                      |
|------------|--------------------------|------------------|----------------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| ~~CR-006~~ | Code Review              | ~~S1~~           | ~~`max_epochs`/`max_iterations` conflation~~                                           | **RESOLVED** (verified 2026-04-08):                                         |
|            |                          |                  |                                                                                        | -- `fit()` deconflated, all fields exist, defaults aligned                  |
| ~~CR-007~~ | Code Review              | ~~S1~~           | ~~State machine terminal states irrecoverable~~                                        | **RESOLVED** (verified 2026-04-08):                                         |
|            |                          |                  |                                                                                        | -- auto-reset in `_handle_start()` line 114 + Option C dupe handler removed |
| ~~CR-008~~ | Code Review              | ~~S2~~           | ~~WebSocket `set_params` not implemented~~                                             | **RESOLVED** (verified 2026-04-08):                                         |
|            |                          |                  |                                                                                        | -- `set_params` in `_VALID_COMMANDS`, hndlr ln 97                           |
| CR-023     | Code Review              | S2               | Unvalidated `params` dict in `TrainingStartRequest`                                    | Open                                                                        |
| CR-024     | Code Review              | S2               | Request body limit bypassed by chunked encoding                                        | Open                                                                        |
| CR-025     | Code Review              | S2               | WebSocket connections set lacks async lock                                             | Open                                                                        |
| CR-026     | Code Review              | S1               | Worker `worker_id` client-supplied without validation                                  | Open                                                                        |
| P5-RC-05   | Connection Analysis      | LOW              | Dashboard ignores WebSocket relay                                                      | Deferred                                                                    |
| P5-RC-14   | Connection Analysis      | LOW              | WebSocket relay broadcasts unnormalized metrics                                        | Deferred (per plan)                                                         |
| P5-RC-18   | Connection Analysis      | SYSTEMIC         | No contract: `BackendProtocol` TypedDicts                                              | **PARTIALLY ADDRESSED**                                                     |
|            |                          |                  | -- (`StatusResult`, `MetricsResult`, `TopologyResult`, `DatasetResult`), returns dicts |                                                                             |
| KL-1       | Connection Analysis      | Known Limitation | Dataset scatter plot empty in service mode                                             | Architectural                                                               |
| Appendix G | Metrics Granularity      | Architectural    | candidate training, no metrics.                                                        | Planned (Options A+C)                                                       |
|            |                          |                  | -- (see `JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_FINAL-CANOPY-CASCOR-CONNECTION-ANALYSIS.md` Appendix G)                       |                                                                             |
| NEW-01     | This review (2026-04-08) | LOW              | `_normalize_metric` returns nested+flat format;                                        | Code quality                                                                |
|            |                          |                  | -- `_to_dashboard_metric` discards nested                                              |                                                                             |
| NEW-02     | This review (2026-04-08) | LOW              | CasCor/Canopy `TrainingState` fields differ:                                           | Maintenance hazard                                                          |
|            |                          |                  | -- (`best_candidate_id` / `top_candidate_id`); relay c/b bridges, undoc map            |                                                                             |
| NEW-03     | This review (2026-04-08) | LOW              | cascor `get_training_params()` doesn't return `candidate_learning_rate`                | Active                                                                      |
|            |                          |                  | -- canopy slider, default not actual value on reconnect                                |                                                                             |
|            |                          |                  | -- canopy slider, default not actual value on reconnect                                |                                                                             |
| NEW-04     | This review (2026-04-08) | MODERATE         | CasCor `get_state_summary()` send UpCs enums.                                          | Latent                                                                      |
|            |                          |                  | -- (`OUTPUT`, `CANDIDATE`). `training_state` sends title-case                          |                                                                             |
|            |                          |                  | -- reading wrong source -> canopy bug                                                  |                                                                             |
| —          | Default discrepancy      | LOW              | `max_hidden_units` cascor constant 1000,                                               | Active                                                                      |
|            |                          |                  | -- cascor API 10, canopy 1000. API inconsistent                                        | Active                                                                      |

### 15.2 Resolved Issues (Verified Implemented)

| ID       | Fix                                               | Date          | Status       |
|----------|---------------------------------------------------|---------------|--------------|
| P5-RC-01 | FIX-A: `_to_dashboard_metric()`                   | 2026-03-28    | **RESOLVED** |
| P5-RC-02 | FIX-B: `_transform_topology()`                    | 2026-03-28    | **RESOLVED** |
| P5-RC-03 | FIX-C: Case-insensitive `_normalize_status()`     | 2026-03-28    | **RESOLVED** |
| P5-RC-04 | FIX-D: Expanded relay callback fields             | 2026-03-28    | **RESOLVED** |
| P5-RC-06 | FIX-G: `monitor.current_phase` + `sm.set_phase()` | 2026-03-28/29 | **RESOLVED** |
| P5-RC-07 | FIX-E: State sync metrics normalization           | 2026-03-28    | **RESOLVED** |
| P5-RC-08 | FIX-E: State sync through adapter helpers         | 2026-03-28    | **RESOLVED** |
| P5-RC-09 | FIX-A: Current metrics snapshot nested            | 2026-03-28    | **RESOLVED** |
| P5-RC-10 | FIX-E: State sync params mapped                   | 2026-03-28    | **RESOLVED** |
| P5-RC-11 | FIX-F: Hardcoded URLs replaced                    | 2026-03-28    | **RESOLVED** |
| P5-RC-12 | FIX-H: Dead mapping removed                       | 2026-03-28    | **RESOLVED** |
| P5-RC-13 | FIX-H: `candidate_learning_rate` mapped           | 2026-03-28    | **RESOLVED** |
| P5-RC-15 | FIX-J: Double initialization guard                | 2026-03-28    | **RESOLVED** |
| P5-RC-16 | FIX-K: Contract tests added                       | 2026-03-28    | **RESOLVED** |

### 15.3 Partially Remediated Issues from Code Review

The cascor code review (CR-006 through CR-076) resulted in extensive PR-based remediation. Key PRs:

| PR        | Scope                                  | Findings Addressed                     |
|-----------|----------------------------------------|----------------------------------------|
| #104      | Lazy logging in candidate training     | CR-062                                 |
| #105      | Thread-safety in audit/worker          | CR-027, CR-028                         |
| #106      | Roll sequence capped-loop fix          | CR-041                                 |
| #107      | SharedTrainingMemory validation        | CR-047, CR-049                         |
| #108      | Performance baseline thresholds        | CR-075                                 |
| #109      | Parallel training path coverage        | CR-072                                 |
| #110      | Test quality improvements              | CR-061, CR-063, CR-073, CR-074, CR-076 |
| #111      | Worker security integration via flags  | CR-009                                 |
| #112      | Hidden outputs extraction optimization | CR-060, CR-050                         |
| #113      | Integration test polling helper        | CR-070                                 |
| #115      | Systemd service unit                   | Infrastructure                         |
| #116-#118 | Test suite stabilization               | Multiple                               |

---

## 16. Remediation Plan

### 16.1 Tier 0: Critical Interface Fixes

| # | Issue      | Fix                                           | Effort | Repo | Priority | Status                             |
|---|------------|-----------------------------------------------|--------|------|----------|------------------------------------|
| 1 | ~~CR-006~~ | ~~Full end-to-end max_iterations~~            | —      | —    | —        | **RESOLVED** (verified 2026-04-08) |
| 2 | ~~CR-007~~ | ~~Auto-reset on start from FAILED/COMPLETED~~ | —      | —    | —        | **RESOLVED** (verified 2026-04-08) |
| 3 | ~~CR-008~~ | ~~Implement `set_params` in control stream~~  | —      | —    | —        | **RESOLVED** (verified 2026-04-08) |

### 16.2 Tier 1: Security and Validation

| # | Issue                            | Fix                                             | Effort | Repo   | Priority    |
|---|----------------------------------|-------------------------------------------------|--------|--------|-------------|
| 4 | CR-023: Unvalidated start params | Whitelist allowed params keys                   | Small  | cascor | P1-HIGH     |
| 5 | CR-026: Worker ID impersonation  | Server-assigned UUIDs                           | Medium | cascor | P1-HIGH     |
| 6 | CR-024: Chunked encoding bypass  | Configure uvicorn limit + incremental body read | Small  | cascor | P2-MODERATE |
| 7 | CR-025: WebSocket async lock     | Add asyncio.Lock to connection management       | Small  | cascor | P2-MODERATE |

### 16.3 Tier 2: Metrics Granularity (Appendix G)

| #  | Item                                    | Scope                                    | Effort            | Repo   |
|----|-----------------------------------------|------------------------------------------|-------------------|--------|
| 8  | Define progress fields in TrainingState | New state fields                         | Small (1hr)       | cascor |
| 9  | Option C: Output training callback      | Per-epoch metrics during output training | Small (1-2hrs)    | cascor |
| 10 | Grow-network state updates              | Iteration progress exposure              | Small (1-2hrs)    | cascor |
| 11 | Canopy progress indicators              | Dashboard progress UI                    | Small-Med (2hrs)  | canopy |
| 12 | Option A: Candidate progress queue      | Worker IPC progress                      | Medium (2-3 days) | cascor |

### 16.4 Tier 3: Architectural Improvements

| #  | Issue                           | Fix                                             | Effort | Repo       |
|----|---------------------------------|-------------------------------------------------|--------|------------|
| 13 | P5-RC-18: No canonical contract | TypedDict/dataclass for BackendProtocol returns | Large  | canopy     |
| 14 | P5-RC-14: Relay unnormalized    | Normalize relay payloads                        | Small  | canopy     |
| 15 | P5-RC-05: Dashboard ignores WS  | Wire WebSocket into Dash                        | Medium | canopy     |
| 16 | KL-1: Dataset scatter empty     | CasCor API extension for data arrays            | Large  | cross-repo |

### 16.5 Remediation Analysis: CR-006 (max_epochs/max_iterations)

This is the highest-impact open issue affecting the interface.

**Option A — Full End-to-End Implementation (Recommended)**:

1. Add `max_iterations` constant to cascor constants chain
2. Add `max_iterations: int` field to `CascadeCorrelationConfig`
3. Add `self.max_iterations` to `CascadeCorrelationNetwork`
4. Deconflate `fit()`: pass `max_epochs` to `train_output_layer()`, `max_iterations` to `grow_network()`
5. Add to `NetworkCreateRequest`, `TrainingParamUpdateRequest`
6. Add to `_STATE_FIELDS` in `TrainingState`
7. Fix lifecycle manager key mapping
8. Add `"nn_max_iterations": "max_iterations"` to canopy param map
9. Align defaults: `max_epochs=1,000,000`, `max_iterations=1,000`

- **Strengths**: Correct semantics; independently controllable limits; aligned defaults
- **Weaknesses**: Touches both repos; coordinated PRs needed; API version bump
- **Risks**: Changing `epochs_max` default from 200 to 1,000,000 changes behavior
- **Guardrails**: Unit tests for full data flow; integration test for canopy round-trip

**Option B — Cascor-Only Fix**:

Fix cascor side only, leave canopy `nn_max_iterations` dead-end.

- **Strengths**: Single-repo change, smaller blast radius
- **Weaknesses**: Canopy users still can't control `max_iterations`

**Recommendation**: Option A. The canopy UI already exists — wiring it is primarily adding a param map entry.

### 16.6 Remediation Analysis: CR-007 (State Machine Recovery)

**Option A — Auto-Reset on Start (Recommended)**:

In `TrainingLifecycleManager.start_training()`, if state is FAILED or COMPLETED, auto-reset before proceeding.

- **Strengths**: Self-healing, backward-compatible
- **Risks**: Implicit reset may surprise callers
- **Guardrails**: Log auto-reset at INFO level; regression test

**Option B — Enforce Explicit Reset**:

Return error requiring caller to call reset first.

- **Strengths**: Explicit control
- **Weaknesses**: Breaking change

**Recommendation**: Option A combined with removing duplicate error handler in `_run_training`.

### 16.7 Remediation Analysis: CR-008 (WebSocket set_params)

Implement `set_params` in the control stream:

1. Add `"set_params"` to `_VALID_COMMANDS`
2. Add handler in `_execute_command()`:

   ```python
   elif command == "set_params":
       params = message.get("params", {})
       result = await lifecycle.update_params(params)
       await websocket.send_json({"type": "params_updated", "data": result})
   ```

- **Strengths**: Fulfills documented contract; enables real-time parameter updates via WebSocket
- **Guardrails**: Validate params against same whitelist as REST endpoint

---

## 17. Development Roadmap

### Phase 1: Critical Interface Fixes (Week 1)

| Task                                              | Issues | Effort   | Dependencies |
|---------------------------------------------------|--------|----------|--------------|
| 1.1 CR-006: Implement `max_iterations` end-to-end | CR-006 | 3-4 days | None         |
| 1.2 CR-007: Auto-reset state machine on start     | CR-007 | 1 day    | None         |
| 1.3 CR-008: Implement WebSocket `set_params`      | CR-008 | 0.5 day  | None         |

### Phase 2: Security Hardening (Week 2)

| Task                                        | Issues | Effort  | Dependencies |
|---------------------------------------------|--------|---------|--------------|
| 2.1 CR-023: Whitelist start training params | CR-023 | 0.5 day | None         |
| 2.2 CR-026: Server-assigned worker IDs      | CR-026 | 1 day   | None         |
| 2.3 CR-024: Body limit for chunked encoding | CR-024 | 0.5 day | None         |
| 2.4 CR-025: WebSocket async lock            | CR-025 | 0.5 day | None         |

### Phase 3: Metrics Granularity (Weeks 3-4)

| Task                                    | Issues     | Effort   | Dependencies |
|-----------------------------------------|------------|----------|--------------|
| 3.1 TrainingState progress fields       | Appendix G | 1 day    | None         |
| 3.2 Output training callback (Option C) | Appendix G | 1-2 days | 3.1          |
| 3.3 Grow-network state updates          | Appendix G | 1-2 days | 3.1          |
| 3.4 Canopy progress indicators          | Appendix G | 2 days   | 3.2, 3.3     |
| 3.5 Candidate progress queue (Option A) | Appendix G | 3-5 days | 3.1          |

### Phase 4: Architectural Improvements (Weeks 5-6)

| Task                                  | Issues   | Effort   | Dependencies            |
|---------------------------------------|----------|----------|-------------------------|
| 4.1 BackendProtocol TypedDict returns | P5-RC-18 | 3-5 days | None                    |
| 4.2 Normalize relay payloads          | P5-RC-14 | 0.5 day  | None                    |
| 4.3 Wire WebSocket into Dash          | P5-RC-05 | 2-3 days | 4.2                     |
| 4.4 CasCor dataset data endpoint      | KL-1     | 3-5 days | Cross-repo coordination |

### Milestone Deliverables

| Milestone                       | After Phase | Outcome                                                              |
|---------------------------------|-------------|----------------------------------------------------------------------|
| **M1: Interface Stability**     | Phase 1     | All critical interface bugs resolved; training limits work correctly |
| **M2: Security Ready**          | Phase 2     | All security findings addressed; ready for external deployment       |
| **M3: Real-Time Monitoring**    | Phase 3     | Live metrics during all training phases; progress indicators         |
| **M4: Production Architecture** | Phase 4     | Typed contracts; WebSocket consumption; full observability           |

---

## Appendix A: Complete Data Structure Registry

### A.1 Cascor Pydantic Models

| Model                        | File                     | Type             | Role                        |
|------------------------------|--------------------------|------------------|-----------------------------|
| `ResponseEnvelope`           | `api/models/common.py`   | Response wrapper | All API responses           |
| `ErrorResponse`              | `api/models/common.py`   | Error detail     | Error responses             |
| `ReadinessResponse`          | `api/models/health.py`   | Health response  | `/v1/health/ready`          |
| `NetworkCreateRequest`       | `api/models/network.py`  | Request          | `POST /v1/network`          |
| `TrainingStartRequest`       | `api/models/training.py` | Request          | `POST /v1/training/start`   |
| `TrainingParamUpdateRequest` | `api/models/training.py` | Request          | `PATCH /v1/training/params` |

### A.2 Cascor Internal Data Structures

| Structure                  | File                             | Type      | Role                   |
|----------------------------|----------------------------------|-----------|------------------------|
| `TrainingStatus`           | `api/lifecycle/state_machine.py` | Enum      | Training status values |
| `TrainingPhase`            | `api/lifecycle/state_machine.py` | Enum      | Training phase values  |
| `CascadeCorrelationConfig` | `cascade_correlation_config.py`  | Dataclass | Network configuration  |
| `_STATE_FIELDS`            | `api/lifecycle/monitor.py`       | Dict      | TrainingState schema   |

### A.3 Canopy Data Structures

| Structure           | File                          | Type      | Role                    |
|---------------------|-------------------------------|-----------|-------------------------|
| `SyncedState`       | `backend/state_sync.py`       | Dataclass | Connect-time sync state |
| `TrainingState`     | `backend/training_monitor.py` | Class     | Runtime training state  |
| `TrainingMetrics`   | `backend/data_adapter.py`     | Dataclass | **DEAD** (P5-RC-18)     |
| `NetworkNode`       | `backend/data_adapter.py`     | Dataclass | **DEAD** (P5-RC-18)     |
| `NetworkConnection` | `backend/data_adapter.py`     | Dataclass | **DEAD** (P5-RC-18)     |
| `NetworkTopology`   | `backend/data_adapter.py`     | Dataclass | **DEAD** (P5-RC-18)     |

### A.4 Cascor-Client Data Structures

| Structure                  | File                     | Type      | Role             |
|----------------------------|--------------------------|-----------|------------------|
| `JuniperCascorClient`      | `client.py`              | Class     | HTTP client      |
| `JuniperCascorWSClient`    | `ws_client.py`           | Class     | WebSocket client |
| `JuniperCascorClientError` | `exceptions.py`          | Exception | Client errors    |
| `FakeCascorClient`         | `testing/fake_client.py` | Class     | Test double      |

---

## Appendix B: Constants Reference

### B.1 Cascor Constants (Interface-Relevant)

**Source**: `juniper-cascor/src/cascor_constants/`

| Constant                                  | Value  | File                      | Used For                 |
|-------------------------------------------|--------|---------------------------|--------------------------|
| `_PROJECT_MODEL_EPOCHS_MAX`               | 10,000 | `constants_model.py`      | Default max epochs       |
| `_CASCADE_CORRELATION_NETWORK_EPOCHS_MAX` | 10,000 | `constants.py` (alias)    | Config default           |
| Candidate pool size                       | 8      | `constants_candidates.py` | Default pool size        |
| Candidate epochs                          | 200    | `constants_candidates.py` | Default candidate epochs |
| Learning rate                             | 0.01   | `constants_model.py`      | Default learning rate    |
| Max hidden units                          | 100    | `constants_model.py`      | Default max hidden       |
| Patience                                  | 50     | `constants_model.py`      | Default patience         |

### B.2 Canopy Constants (Interface-Relevant)

**Source**: `juniper-canopy/src/canopy_constants.py`

| Constant                        | Class                | Value     | Used For                      |
|---------------------------------|----------------------|-----------|-------------------------------|
| `DEFAULT_TRAINING_EPOCHS`       | `TrainingConstants`  | 1,000,000 | Default `nn_max_total_epochs` |
| `DEFAULT_MAX_GROWTH_ITERATIONS` | `TrainingConstants`  | 1,000     | Default `nn_max_iterations`   |
| `DEFAULT_LEARNING_RATE`         | `TrainingConstants`  | 0.01      | Default `nn_learning_rate`    |
| `DEFAULT_MAX_HIDDEN_UNITS`      | `TrainingConstants`  | 1,000     | Default `nn_max_hidden_units` |
| `FAST_UPDATE_INTERVAL_MS`       | `DashboardConstants` | 1,000     | Metrics polling interval      |
| `SLOW_UPDATE_INTERVAL_MS`       | `DashboardConstants` | 5,000     | Status polling interval       |
| `DEFAULT_CASCOR_PORT`           | `ServerConstants`    | 8200      | Cascor service port           |
| `DEFAULT_CANOPY_PORT`           | `ServerConstants`    | 8050      | Canopy service port           |

---

## Appendix C: Explanatory Diagrams

### C.1 Data Format Transformation Pipeline

```bash
                   CASCOR SERVER                    CASCOR-CLIENT              CANOPY ADAPTER              DASHBOARD
                   ────────────                     ─────────────              ──────────────              ─────────

Metrics:           {loss, accuracy,         →    Raw JSON           →    _normalize_metric()     →    _to_dashboard_metric()
                    validation_loss, ...}          (ResponseEnvelope)       {train_loss, ...}            {metrics: {loss: ...},
                                                                            (flat canonical)              network_topology: {...}}
                                                                                                          (nested dashboard)

Topology:          {input_size,             →    Raw JSON           →    _unwrap_response()      →    _transform_topology()
                    hidden_units: [{...}],         (ResponseEnvelope)       (envelope removed)           {input_units,
                    output_weights: [...]}                                                                 hidden_units: int,
                                                                                                           nodes: [...],
                                                                                                           connections: [...]}

Status:            TrainingStatus.STARTED    →    "Started" or      →    (via relay callback)    →    _normalize_status()
                   (enum)                          "STARTED"               status string                 → "Started"
                                                   (varies by path)                                       (title-case canonical)

Parameters:        {learning_rate,           →    Raw JSON           →    _unwrap_response()      →    Reverse param map
(cascor → canopy)   epochs_max, ...}               (ResponseEnvelope)                                    {nn_learning_rate,
                                                                                                           nn_max_total_epochs, ...}

Parameters:        ← {learning_rate,         ←    PATCH /v1/...      ←    _CANOPY_TO_CASCOR_      ←    {nn_learning_rate,
(canopy → cascor)     epochs_max, ...}                                       PARAM_MAP                    nn_max_total_epochs, ...}
```

### C.2 State Machine Transition Diagram

```bash
                    ┌─────────────────────────────────────┐
                    │                                     │
                    ▼                                     │
              ┌──────────┐    START    ┌────────────┐     │
  ──────────► │ STOPPED  │ ──────────► │  STARTED   │     │
              └──────────┘             └────────────┘     │
                    ▲                    │    │    │      │
                    │              PAUSE │    │    │      │
                    │                    ▼    │    │      │
                    │           ┌──────────┐  │    │      │
                    │  RESUME   │  PAUSED  │  │    │      │
                    │  ◄────────┤          │  │    │      │
                    │           └──────────┘  │    │      │
                    │                         │    │      │
                    │    RESET ◄──────────────┘    │      │
                    │                              │      │
                    │         ┌──────────────┐     │      │
                    │         │  COMPLETED   │◄────┘      │
                    │         └──────┬───────┘            │
                    │                │ RESET              │
                    │                ▼                    │
                    │    ┌──────────────────┐             │
                    └────┤  (Auto-reset?)   │─────────────┘
                         │  CR-007: NOT YET │
                         └──────────────────┘

              ┌──────────┐
              │  FAILED  │ ← Exception during training
              └──────────┘
                    │ RESET (or auto-reset per CR-007 fix)
                    └──────► STOPPED
```

### C.3 Ingress Path Diagram (All Data Into Dashboard)

```bash
                              ┌───────────────────────────────┐
                              │      CANOPY DASHBOARD         │
                              │                               │
    ┌──────────────────────┐  │  ┌──────────────┐             │
    │ DemoMode (simulation)│──┼──│ MetricsPanel │  Nested     │
    │ Nested format ✓      │  │  │ Nested access│  format     │
    └──────────────────────┘  │  └──────────────┘  required   │
                              │                               │
    ┌──────────────────────┐  │  ┌──────────────┐             │
    │ REST /api/metrics/*  │──┼──│ MetricsPanel │  Nested ✓   │
    │ _to_dashboard_metric │  │  │ via Interval │  (FIX-A)    │
    └──────────────────────┘  │  └──────────────┘             │
                              │                               │
    ┌──────────────────────┐  │  ┌──────────────┐             │
    │ REST /api/network/   │──┼──│ NetworkViz   │  Graph ✓    │
    │ _transform_topology  │  │  │ via Interval │  (FIX-B)    │
    └──────────────────────┘  │  └──────────────┘             │
                              │                               │
    ┌──────────────────────┐  │  ┌──────────────┐             │
    │ REST /api/status     │──┼──│ Status Bar   │  Flat ✓     │
    │ Fresh REST calls     │  │  │ via Interval │  (works)    │
    └──────────────────────┘  │  └──────────────┘             │
                              │                               │
    ┌──────────────────────┐  │  ┌──────────────┐             │
    │ WS relay (broadcast) │──┼──│ websocket-   │  Raw ✗      │
    │ Raw CasCor format    │  │  │ data div     │  (unused)   │
    └──────────────────────┘  │  │ NOT consumed │  P5-RC-05   │
                              │  └──────────────┘  P5-RC-14   │
                              │                               │
    ┌──────────────────────┐  │  ┌──────────────┐             │
    │ State sync on connect│──┼──│ Initial state│  Normalized │
    │ Through adapter ✓    │  │  │ population   │  ✓ (FIX-E)  │
    └──────────────────────┘  │  └──────────────┘             │
                              └───────────────────────────────┘
```

---

*End of Canopy-Cascor Interface Analysis Document*:
