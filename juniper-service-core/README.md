# juniper-service-core

[![PyPI](https://img.shields.io/pypi/v/juniper-service-core)](https://pypi.org/project/juniper-service-core/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)

**The shared FastAPI service-tier framework every Juniper model service is built on.**

Standing up a model as a service means writing the same plumbing every time: an app factory,
settings, health probes, API-key auth, Docker-secret loading, security middleware, a training
lifecycle with status tracking and event streaming, the HTTP routes that drive it, live WebSocket
streams, and — for distributed training — a worker pool. `juniper-service-core` is that plumbing,
factored out of [`juniper-cascor`](https://github.com/pcalnon/juniper-cascor) into one
**model-agnostic** package. **You bring the model; it brings the service.**

The `-core` suffix marks it as genuinely shared: it carries no model, training, or domain logic —
those stay in the owning service and are injected. A new Juniper model service (regression,
classification, whatever the model does) wires its model into the lifecycle and gets a consistent
HTTP + WebSocket surface for free.

## Dependency-free top-level import

`import juniper_service_core` pulls in **no** third-party runtime dependency — only `__version__`
loads eagerly. The rest of the public surface (`create_app`, `SettingsBase`, and the security /
secrets / middleware / lifecycle / routes / websocket / worker helpers) resolves lazily on attribute
access (PEP 562 `__getattr__`), so `fastapi` / `pydantic-settings` / `starlette` / `numpy` load only
when you touch a name that needs them. That's what lets a `--no-deps` publish-verify import the
package cleanly.

## Install

```bash
pip install juniper-service-core
```

## What's in the box

| Subsystem | Import surface | What it gives you |
|---|---|---|
| App factory | `create_app` | Model-agnostic FastAPI app: mounts the health router, then any service-supplied routers. |
| Settings | `SettingsBase` | `pydantic-settings` base (`service_name`, `host`, `port`, `log_level`); subclass and set your own `env_prefix`. |
| Health | *(mounted by `create_app`)* | `GET /v1/health` (liveness) + `GET /v1/health/ready` (readiness). |
| Security | `APIKeyAuth`, `RateLimiter`, `build_api_key_auth`, … | `X-API-Key` authentication + rate limiting. |
| Secrets | `get_secret` | Docker `_FILE` secret-indirection reader. |
| Middleware | `SecurityMiddleware`, `SecurityHeadersMiddleware`, `RequestBodyLimitMiddleware` | Drop-in ASGI middleware. |
| Launcher | `ManagedService`, `start_service`, `wait_for_health` | Subprocess service launcher (stdlib-only). |
| Lifecycle | `TrainingLifecycle`, `ServiceLifecycleManager`, … | Drives a [`juniper-model-core`](https://github.com/pcalnon/juniper-ml) `TrainableModel` through a status FSM + a `TrainingEvent` monitor; synchronous and threaded-orchestrator bodies, with snapshots + replay. |
| Generic routes | `build_routers`, `ResponseEnvelope`, … | Training-control, metrics, dataset, network, and snapshot HTTP routes over the injected lifecycle. |
| WebSocket | `attach_websocket`, `training_stream_handler`, `control_stream_handler`, … | Live training + control streams, plus a worker channel (`/ws/workers`). |
| Worker pool | `WorkerCoordinator`, `WorkerRegistry`, … | Distributed-worker registration, coordination, and task dispatch (stdlib-only foundations). |

Import cost tracks the subsystem: `.security`, `.secrets`, `.middleware`, `.launcher`, and `.workers`
are stdlib-/lightweight; `.lifecycle` needs `juniper-model-core`; `.routes` and `.websocket` need
`fastapi`.

## Quick start

A minimal, health-only service:

```python
from juniper_service_core import create_app, SettingsBase
from pydantic_settings import SettingsConfigDict


class MyServiceSettings(SettingsBase):
    model_config = SettingsConfigDict(env_prefix="JUNIPER_MYSVC_")


app = create_app(title="My Service", version="1.0.0")
# GET /v1/health       -> {"status": "ok"}
# GET /v1/health/ready -> {"status": "ready"}
```

To **serve a model**, wrap it in a `ServiceLifecycleManager`, mount the generic routers, and expose
the lifecycle on `app.state` — the routes read it from there:

```python
from juniper_service_core import create_app, ServiceLifecycleManager, build_routers

manager = ServiceLifecycleManager(MyModel())   # MyModel = any juniper-model-core TrainableModel
app = create_app(title="My Model Service", version="1.0.0", routers=build_routers())
app.state.lifecycle = manager
# -> POST /v1/train, GET /v1/training/status, and the metrics / dataset / network / snapshot
#    routes, all driving your model. (Routes return 503 until app.state.lifecycle is wired.)
```

[`juniper-recurrence`](https://github.com/pcalnon/juniper-recurrence) is the canonical worked
example — its FastAPI service is essentially this wiring around an LMU regressor.

## Who uses it

- **[juniper-recurrence](https://github.com/pcalnon/juniper-recurrence)** — the first real consumer;
  its service is `create_app` + a lifecycle around the LMU regressor.
- **[juniper-cascor](https://github.com/pcalnon/juniper-cascor)** — the framework was extracted *from*
  cascor's service tier; cascor's own cutover onto it is in progress.

Any new Juniper model service should build on this rather than re-implementing the plumbing.

## Status

**Live** on PyPI (Beta). The current version is shown by the badge above; see
[`CHANGELOG.md`](./CHANGELOG.md) for history. Pin with `juniper-service-core>=0.2.0,<0.8.0` —
the range the `juniper-ml` meta-package uses for its `tools` / `all` extras.

### Compatibility policy — pinning, not deprecation cycles

This package ships **no deprecation machinery**: no `DeprecationWarning`, no
`PendingDeprecationWarning`, no legacy aliases. That is deliberate, not an oversight
(defect-register `APD-ECO-007`).

While pre-1.0, compatibility is managed by **external pinning**: consumers pin
`>=floor,<next-minor`, so each `0.x` is a compatibility boundary and a breaking change
is absorbed by a ceiling raise the consumer performs deliberately. That works because
the consumer set is a known, enumerable handful of first-party repositories — and it
has been exercised: the two changes this package has shipped marked *"potentially
breaking"* were both cleared by **censusing the consumers** and verifying zero were
affected, which a deprecation cycle would only have made slower.

**What would change this.** A deprecation cycle is the right tool the moment the
consumer set stops being enumerable — a third-party dependant, or 1.0. At that point
do **not** invent machinery: two implementations already exist in this ecosystem and
should be reused rather than re-derived, since re-derivation is precisely how the
env-var lookup drifted across three services before it was consolidated.

| Need | Use |
|---|---|
| Env-var rename | `juniper_config_tools.env_with_legacy_alias` |
| API/argument rename | the `juniper-data-client` alias pattern (`warnings.warn(..., DeprecationWarning, stacklevel=N)` plus a **dated** removal window) |

A dated window is the part that matters: it turns a deprecation from a permanent tax
into a plan. See `juniper-cascor-client`'s `AUTO_PONG_REMOVAL_VERSION` for a worked
example, including how to verify `stacklevel` attributes the warning to the caller
rather than to library code.

## Development

```bash
pip install -e ".[test]"
pytest tests/ -v
```

## Design

Part of the [Juniper](https://github.com/pcalnon) ML research platform. The architecture and the
cascor extraction plan are the model/middleware refactor design of record
(`notes/JUNIPER_2026-05-31_JUNIPER-ECOSYSTEM_MODEL-MIDDLEWARE-REFACTOR-DESIGN-AND-PLAN.md` in `juniper-ml`).

## License

MIT — see [LICENSE](./LICENSE).
