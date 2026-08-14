# API Design and Implementation — A Practitioner's Primer

**Date**: 2026-08-13
**Author**: Paul Calnon
**Status**: Reference primer — living document
**Scope**: Web/HTTP APIs (breadth), REST/HTTP semantics (depth), and library/SDK API design
**Worked examples**: Grounded in the Juniper ecosystem; all example code is executable

---

## Reading Guide

This primer is organised into three parts that answer three different questions.

| Part                                           | Question it answers                                                                                      | Read it when                                                        |
|------------------------------------------------|----------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------|
| **Part I — The Web API Landscape**             | *Which kind of API should this be, and what cross-cutting concerns apply regardless?*                    | You are choosing a style, or you need the map before the territory. |
| **Part II — REST and HTTP Semantics in Depth** | *Given that it is an HTTP API, what exactly do the specifications require and permit?*                   | You are designing or reviewing concrete endpoints.                  |
| **Part III — Library and SDK API Design**      | *How do I design an in-process API — a package other code imports — that can survive its own evolution?* | You are publishing a library, or curating a public surface.         |

Every major section follows the same internal shape: **Overview → Background → Topics and Subtopics → Expert-Level Detail → Judgement Calls → Tradeoffs → Best Practices → Common Failure Modes → Error Handling → Controversy (where it exists) → Worked Examples**. Where a section has no genuine controversy, the block is omitted rather than manufactured — an invented dispute is worse than an absent one.

Code appears at two scales, and the distinction is deliberate:

- **Inline snippets** within each section illustrate a single point. They are chosen for clarity in prose and are not expected to run standalone.
- **Each part ends with a complete, executable program** — application, client, and passing test suite — that exercises the part's ideas together. These are extracted from this document and run by the harness in [Appendix D](#appendix-d--running-the-examples); they are the "fully functional" code, and they were verified by execution rather than by inspection.

### How claims in this document were verified

API writing is unusually prone to confident-but-wrong assertions: half-remembered RFC section numbers, status codes that "feel right", and folklore repeated until it sounds normative. Three deliberate countermeasures were applied.

1. **Primary sources on disk, not from memory.** Every specification cited here was downloaded and grepped locally rather than recalled. The fetch script is committed at [`util/ad-hoc/2026-08-13_fetch_api_specs.bash`](../util/ad-hoc/2026-08-13_fetch_api_specs.bash) and reproduces the cache. Where this document quotes normative wording, the quote came out of that cache.
2. **Executable examples.** Every code example was run — not merely written — in a clean virtual environment against the pinned versions in [Appendix D](#appendix-d--running-the-examples). Examples that did not run were fixed or removed.
3. **Independent adversarial review.** The draft was re-checked by independent reviewers whose brief was to *disprove* its claims: re-probing every repository citation, re-reading every cited specification section, and flagging any assertion that outran its evidence.

Two honesty conventions are used throughout:

- **Standard vs. convention.** Where common practice is *not* standardised, this document says so explicitly. `X-RateLimit-*` headers, for instance, are a widespread vendor convention, not a standard (see [I.6](#i6-rate-limiting-quotas-and-backpressure)).
- **Draft vs. published.** Internet-Drafts are labelled as drafts, with the understanding that a draft may change or expire.

### Notation

- `RFC 9110 §9.2.2` means section 9.2.2 of that RFC. Section numbers are as published; RFC citations use the [RFC Editor](https://www.rfc-editor.org/) canonical text.
- Repository citations use `path/to/file.py:LINE` relative to the repository named in the surrounding prose.
- Juniper repositories referenced: `juniper-data`, `juniper-cascor`, `juniper-canopy`, `juniper-recurrence`, and the shared in-repo packages `juniper-service-core` and `juniper-observability`. The ecosystem map is in the parent [`AGENTS.md`](../AGENTS.md).

---

## Contents

- [Reading Guide](#reading-guide)
  - [How claims in this document were verified](#how-claims-in-this-document-were-verified)
  - [Notation](#notation)
- [Overview: What an API Actually Is](#overview-what-an-api-actually-is)
  - [Why "API" is three different topics wearing one name](#why-api-is-three-different-topics-wearing-one-name)
  - [The Juniper ecosystem as a worked example](#the-juniper-ecosystem-as-a-worked-example)
- [Part I — The Web API Landscape](#part-i--the-web-api-landscape)
  - [I.1 What Part I Covers](#i1-what-part-i-covers)
  - [I.2 The HTTP Substrate](#i2-the-http-substrate)
  - [I.3 Architectural Styles: REST, RPC/gRPC, GraphQL](#i3-architectural-styles-rest-rpcgrpc-graphql)
  - [I.4 Real-Time and Streaming](#i4-real-time-and-streaming)
  - [I.5 Authentication and Authorization](#i5-authentication-and-authorization)
  - [I.6 Rate Limiting, Quotas, and Backpressure](#i6-rate-limiting-quotas-and-backpressure)
  - [I.7 Idempotency, Retries, and the Exactly-Once Illusion](#i7-idempotency-retries-and-the-exactly-once-illusion)
  - [I.8 Versioning and Evolution](#i8-versioning-and-evolution)
  - [I.9 Caching](#i9-caching)
  - [I.10 Observability for APIs](#i10-observability-for-apis)
  - [I.11 Testing APIs](#i11-testing-apis)
  - [I.12 Part I Worked Example — Making a Non-Idempotent POST Safe to Retry](#i12-part-i-worked-example--making-a-non-idempotent-post-safe-to-retry)
- [Part II — REST and HTTP Semantics in Depth](#part-ii--rest-and-http-semantics-in-depth)
  - [II.1 What Part II Covers, and What REST Actually Means](#ii1-what-part-ii-covers-and-what-rest-actually-means)
  - [II.2 Resource Modelling and URI Design](#ii2-resource-modelling-and-uri-design)
  - [II.3 Methods: Safety, Idempotency, and the Complete Table](#ii3-methods-safety-idempotency-and-the-complete-table)
  - [II.4 Status Codes](#ii4-status-codes)
  - [II.5 Representations, Content Negotiation, and Media Types](#ii5-representations-content-negotiation-and-media-types)
  - [II.6 Conditional Requests, ETags, and Optimistic Concurrency](#ii6-conditional-requests-etags-and-optimistic-concurrency)
  - [II.7 Pagination, Filtering, Sorting, and Partial Responses](#ii7-pagination-filtering-sorting-and-partial-responses)
  - [II.8 Error Models](#ii8-error-models)
  - [II.9 Hypermedia and HATEOAS](#ii9-hypermedia-and-hateoas)
  - [II.10 OpenAPI and Contract-First Design](#ii10-openapi-and-contract-first-design)
  - [II.11 Part II Worked Example — Conditional Requests and Optimistic Concurrency](#ii11-part-ii-worked-example--conditional-requests-and-optimistic-concurrency)
- [Part III — Library and SDK API Design](#part-iii--library-and-sdk-api-design)
  - [III.1 What Part III Covers](#iii1-what-part-iii-covers)
  - [III.2 Designing the Public Surface](#iii2-designing-the-public-surface)
  - [III.3 Naming, Signatures, and Ergonomics](#iii3-naming-signatures-and-ergonomics)
  - [III.4 Errors and Exception Hierarchy Design](#iii4-errors-and-exception-hierarchy-design)
  - [III.5 Versioning, SemVer, and Deprecation](#iii5-versioning-semver-and-deprecation)
  - [III.6 Typing and the Type-Checked Contract](#iii6-typing-and-the-type-checked-contract)
  - [III.7 Extension Points and Plugin APIs](#iii7-extension-points-and-plugin-apis)
  - [III.8 Packaging and the Distribution Boundary](#iii8-packaging-and-the-distribution-boundary)
  - [III.9 Part III Worked Example — A Client Library That Does Not Lose Information](#iii9-part-iii-worked-example--a-client-library-that-does-not-lose-information)
- [Appendix A — Common Interview Questions](#appendix-a--common-interview-questions)
  - [A.1 How to use this appendix](#a1-how-to-use-this-appendix)
  - [A.2 Fundamentals and HTTP](#a2-fundamentals-and-http)
  - [A.3 REST semantics — the deep cuts](#a3-rest-semantics--the-deep-cuts)
  - [A.4 Reliability — idempotency, retries, and failure](#a4-reliability--idempotency-retries-and-failure)
  - [A.5 Security and authentication](#a5-security-and-authentication)
  - [A.6 Caching and performance](#a6-caching-and-performance)
  - [A.7 Evolution and versioning](#a7-evolution-and-versioning)
  - [A.8 Library and SDK design](#a8-library-and-sdk-design)
  - [A.9 Open-ended design prompts](#a9-open-ended-design-prompts)
  - [A.10 Code-reading and debugging prompts](#a10-code-reading-and-debugging-prompts)
  - [A.11 Questions worth asking your interviewer](#a11-questions-worth-asking-your-interviewer)
- [Appendix B — Reference Tables](#appendix-b--reference-tables)
  - [B.1 Method properties](#b1-method-properties)
  - [B.2 Status codes that carry design decisions](#b2-status-codes-that-carry-design-decisions)
  - [B.3 Headers that carry API-design weight](#b3-headers-that-carry-api-design-weight)
  - [B.4 Retry decision table](#b4-retry-decision-table)
- [Appendix C — Cited Specifications](#appendix-c--cited-specifications)
  - [C.1 Non-RFC references](#c1-non-rfc-references)
- [Appendix D — Running the Examples](#appendix-d--running-the-examples)
  - [D.1 Why this appendix exists](#d1-why-this-appendix-exists)
  - [D.2 Pinned toolchain](#d2-pinned-toolchain)
  - [D.3 Running them](#d3-running-them)
  - [D.4 The extraction convention](#d4-the-extraction-convention)
  - [D.5 Reproducing the specification cache](#d5-reproducing-the-specification-cache)

---

## Overview: What an API Actually Is

An API is a **contract that outlives the code that first implemented it**. That single property explains nearly every difficulty in the field.

A function you can freely rename is not an API. A function that three teams import, that a customer's build pins to, or that a mobile client shipped eighteen months ago still calls, is an API — and the cost of changing it is no longer proportional to the effort of editing it. It is proportional to the number of independent parties who must be persuaded, coordinated, or broken. Design decisions that appear local at authoring time become distributed-systems problems at deprecation time.

Three consequences follow, and they organise this entire primer.

**First, the interface is a liability as much as an asset.** Every field you expose is a field someone will depend on, including fields you exposed by accident. This motivates the discipline of curating a public surface deliberately ([Part III](#part-iii--library-and-sdk-api-design)) rather than letting it accrete from whatever happened to be importable.

**Second, the boundary is where failure semantics are defined.** Inside a process, a failed call raises and the stack unwinds. Across a network, a failed call may have succeeded.

The caller cannot distinguish "the request never arrived" from "the request was processed and the response was lost". This ambiguity — not bandwidth, not latency — is the fundamental difficulty of network API design. Idempotency, retries, and error models ([I.7](#i7-idempotency-retries-and-the-exactly-once-illusion)) are all responses to this one problem.

**Third, evolution must be designed before it is needed.** Versioning strategies adopted after the first breaking change are always worse than those adopted before it, because by then the compatibility constraints are already in production. This is why [I.8](#i8-versioning-and-evolution) and [III.5](#iii5-versioning-semver-and-deprecation) exist as first-class topics rather than appendices.

### Why "API" is three different topics wearing one name

The word covers at least three distinct design problems, and conflating them is the most common source of bad advice.

|                               | **Network API**                | **Library/SDK API**           | **Platform/OS API**         |
|-------------------------------|--------------------------------|-------------------------------|-----------------------------|
| Call mechanism                | Serialised over a transport    | In-process function call      | Syscall / ABI               |
| Failure modes                 | Partial, ambiguous, retryable  | Deterministic exceptions      | Error codes, signals        |
| Versioning unit               | Endpoint / media type / schema | Package version               | Kernel or ABI version       |
| Breaking change cost          | Coordinated client migration   | Dependency resolution         | Effectively unbounded       |
| Latency budget                | Milliseconds to seconds        | Nanoseconds                   | Nanoseconds to microseconds |
| Can the caller see internals? | No                             | Often yes (Python especially) | No                          |

Advice that is correct for one column is frequently wrong for another.

"Return errors as values, not exceptions" is reasonable for a network boundary and contentious inside a Python library. "Never break compatibility" is achievable for a library with a deprecation window and impossible for a network API whose clients you do not control. This primer keeps the columns separate: Parts I and II address the first column, Part III the second. The third column is out of scope except where it illuminates the others.

### The Juniper ecosystem as a worked example

Rather than invent a toy domain, this primer draws its examples from a real system: the Juniper Cascade-Correlation research platform. It is a useful teaching subject because it exhibits, in one codebase, most of the design tensions the primer discusses.

- A **dataset-generation service** (`juniper-data`) that serves both JSON metadata and large binary artifacts — a content-negotiation and caching problem.
- A **training service** (`juniper-cascor`) that manages long-running, stateful, non-idempotent jobs — the hardest case for REST resource modelling.
- A **real-time dashboard** (`juniper-canopy`) that needs push updates — a WebSocket-vs-SSE-vs-polling decision made under real constraints.
- **Shared middleware** (`juniper-service-core`) implementing body limits, authentication, and rate limiting — cross-cutting concerns whose *ordering* is load-bearing.
- **Client libraries** (`juniper-data-client`, `juniper-cascor-client`) — the library-API column, with the added constraint of wrapping a network API.

Where the Juniper implementation makes a debatable choice, this primer says so and explains the alternative. The goal is a primer that teaches judgement, not a brochure.

---

## Part I — The Web API Landscape

### I.1 What Part I Covers

Part I maps the ground an API sits on before any of your own design decisions apply. Four layers, each of which constrains the one above it:

1. **The HTTP substrate** (I.2) — which wire protocol carries your bytes, and what that changes about latency, concurrency, and per-request overhead. The central teaching point is that HTTP *semantics* (methods, status codes, header fields, caching rules) are defined once, version-independently, in [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html), and each major version defines only a syntax for carrying them.
   Almost everything you know about "HTTP" is version-independent; the parts that are not are exactly the parts that matter for performance tuning.
2. **The architectural style** (I.3) — REST, RPC/gRPC, or GraphQL. This is the choice that determines your contract format, your caching story, your tooling, and how your errors are shaped. It is also the choice most often made by fashion rather than by requirement.
3. **The interaction model** (I.4) — request/response is the default, but a large class of APIs needs the server to speak first. Polling, long-polling, Server-Sent Events, WebSockets, and webhooks are five different answers with five different failure profiles.
4. **Authentication and authorization** (I.5) — who is calling, and what are they allowed to do. Separate questions, routinely conflated, with different failure modes and different places to enforce them.

The decision this part equips you to make is a compound one, and the layers are not independent:

| Layer       | The question                   | Where it binds the layers above                                                |
|-------------|--------------------------------|--------------------------------------------------------------------------------|
| Substrate   | HTTP/1.1, HTTP/2, HTTP/3?      | Sets per-request overhead, and whether "fewer, bigger requests" is good advice |
| Style       | REST, gRPC, GraphQL?           | gRPC *requires* HTTP/2 framing; GraphQL's default POST discards HTTP caching   |
| Interaction | Poll, SSE, WebSocket, webhook? | WebSockets bypass your HTTP middleware entirely — auth must move               |
| Auth        | Key, token, mTLS, signature?   | Browser transports cannot set headers, which forces the credential elsewhere   |

Two cross-cutting sources anchor the whole part. [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html) defines what HTTP *means*, independent of version. [RFC 9205](https://www.rfc-editor.org/rfc/rfc9205.html) (BCP 56, "Building Protocols with HTTP") defines what you may and may not do when you build an application protocol on top of HTTP — it is short, normative, directly on point for every API design decision in this primer, and almost never cited in practitioner writing.

Throughout, the worked examples come from the Juniper ML platform: a research stack of eight repositories built by one author over roughly a year. It is a useful teaching corpus precisely because it is neither a textbook nor a disaster — it contains careful, well-reasoned implementations sitting next to divergent copies of the same idea, and the divergence is documented in the code. Where a Juniper claim appears below it carries a `file:line` citation into a real repository.

---

### I.2 The HTTP Substrate

#### Overview

There are three deployed major versions of HTTP, and they do not replace one another. RFC 9110 §1.2 is explicit: "All three major versions of HTTP rely on the semantics defined by this document. They have not obsoleted each other because each one has specific benefits and limitations depending on the context of use."

That sentence is the most important thing in this section. The 2022 revision of the HTTP specifications split the protocol into **semantics** (RFC 9110), **caching** (RFC 9111), and three separate **syntaxes** — [RFC 9112](https://www.rfc-editor.org/rfc/rfc9112.html) for HTTP/1.1, [RFC 9113](https://www.rfc-editor.org/rfc/rfc9113.html) for HTTP/2, [RFC 9114](https://www.rfc-editor.org/rfc/rfc9114.html) for HTTP/3.
RFC 9110 §1.2 states the intent: the split exists "to allow each major protocol version to progress independently while referring to the same core semantics."

For an API designer this means your `GET`, your `404`, your `ETag`, and your `Retry-After` are the same objects on every version. What changes between versions is how many of them you can have in flight at once, how much each one costs on the wire, and how a stalled one affects its neighbours.

#### Background

HTTP/1.0 allowed one outstanding request per TCP connection. HTTP/1.1 added two things to fix that: persistent connections and pipelining.

**Persistent connections** worked. RFC 9112 §9.3 makes persistence the default: for an HTTP/1.1 message, "the connection will persist after the current response" unless the `close` connection option is present. The cost of a new TCP handshake (and a TLS handshake on top of it) is amortized across many requests.

**Pipelining** did not work. RFC 9112 §9.3.2 permits a client to "send multiple requests without waiting for each response", and permits a server to process a sequence of pipelined requests in parallel *if they all have safe methods* — but it "MUST send the corresponding responses in the same order that the requests were received."
That ordering requirement is the whole problem: one slow response blocks every response queued behind it, even if those were ready first. This is **application-layer head-of-line blocking**, and RFC 9113 §1 names it as the reason pipelining "only partially addressed request concurrency."

Pipelining carries a second hazard. RFC 9112 §9.3.2 warns that a user agent "SHOULD NOT pipeline requests after a non-idempotent method, until the final response status code for that method has been received", because recovering from a mid-pipeline connection failure means replaying requests — safe only for idempotent methods (RFC 9110 §9.2.2).
Browsers largely gave up and disabled pipelining; the workaround the whole web adopted instead was to open six or so parallel connections per origin. RFC 9112 §9.4 acknowledges this awkwardly: it declines to mandate a maximum, and merely "encourages clients to be conservative when opening multiple connections."

#### HTTP/2: binary framing, streams, and the blocking that survived

HTTP/2 keeps HTTP's semantics and replaces its syntax. RFC 9113 §2 gives the model in four moves:

- **Frames.** The basic protocol unit is a binary frame with a typed header. `HEADERS` and `DATA` frames carry requests and responses; `SETTINGS`, `WINDOW_UPDATE`, `PING`, `GOAWAY`, `RST_STREAM`, and `PUSH_PROMISE` carry protocol machinery.
- **Streams.** "Multiplexing of requests is achieved by having each HTTP request/response exchange associated with its own stream... Streams are largely independent of each other, so a blocked or stalled request or response does not prevent progress on other streams."
- **Flow control.** Per-stream and per-connection windows (RFC 9113 §5.2), advanced by `WINDOW_UPDATE`. Without it, multiplexed streams would destructively contend for one TCP connection.
- **Field compression.** HPACK (RFC 9113 §4.3, referencing the separate HPACK specification). Each endpoint keeps an encoder and a decoder context with a dynamic table whose size starts at 4,096 bytes (§4.3.1). Repeated header fields — `authorization`, `user-agent`, `accept`, a fixed `host` — collapse to table references after their first appearance on a connection.

Concurrency is bounded, not unlimited: `SETTINGS_MAX_CONCURRENT_STREAMS` (RFC 9113 §5.1.2, §6.5.2) lets each peer cap how many streams the *other* side may open. There is initially no limit, and the specification recommends the value "be no smaller than 100, so as to not unnecessarily limit parallelism."

Two consequences bite API designers directly.

First, **connection-specific header fields are banned.** RFC 9113 §8.2.2: an endpoint "MUST NOT generate an HTTP/2 message containing connection-specific header fields", naming `Connection`, `Proxy-Connection`, `Keep-Alive`, `Transfer-Encoding`, and `Upgrade`. `TE` survives only with the exact value `trailers`. A message carrying any of them "MUST be treated as malformed."
The same section notes that "HTTP/2 purposefully does not support upgrade to another protocol" — which is precisely why the WebSocket handshake in I.4 is an HTTP/1.1 story.

Second, and most importantly: **TCP head-of-line blocking is not fixed.** RFC 9113 §1 says so in one sentence: "Note, however, that TCP head-of-line blocking is not addressed by this protocol." HTTP/2 removed application-layer ordering constraints, but all its streams still ride one TCP connection, and TCP delivers bytes in order. A single lost segment stalls delivery of *everything* behind it — every multiplexed stream — until the retransmission arrives.
On a clean network HTTP/2 is a large win; on a lossy one, multiplexing over a single TCP connection can be worse than six independent connections, because six connections lose only one-sixth of the traffic to any given drop.

#### HTTP/3: what QUIC actually fixes

HTTP/3 is HTTP/2's design re-hosted on a transport that can honour it. RFC 9114 §1.2: QUIC "incorporates stream multiplexing and per-stream flow control, similar to that provided by the HTTP/2 framing layer. By providing reliability at the stream level and congestion control across the entire connection, QUIC has the capability to improve the performance of HTTP compared to a TCP mapping."

The decisive line is in RFC 9114 §2: "Each request-response pair consumes a single QUIC stream. Streams are independent of each other, so one stream that is blocked or suffers packet loss does not prevent progress on other streams." Reliability moved down one layer and became per-stream. That is the head-of-line blocking fix, and it is the main reason HTTP/3 exists.

Three more properties follow from the transport change:

- **TLS is not optional and not layered on top.** RFC 9114 §1.2: QUIC "incorporates TLS 1.3 at the transport layer, offering comparable confidentiality and integrity to running TLS over TCP, with the improved connection setup latency of TCP Fast Open."
- **HPACK could not survive.** RFC 9114 §2: "Because HPACK relies on in-order transmission of compressed field sections (a guarantee not provided by QUIC), HTTP/3 replaces HPACK with QPACK." QPACK moves table updates onto separate unidirectional streams so an encoder can trade compression efficiency against the risk of blocking.
- **The client's address can change mid-connection.** RFC 9114 §10.10 warns that implementations using the client address "for logging or access-control purposes" must "either actively retrieve the client's current address or addresses when they are relevant or explicitly accept that the original address might change." Any rate limiter or audit log keyed on client IP is on notice.

Discovery is different too. A client may connect directly using the ALPN token `h3` (RFC 9114 §3.1), or learn about an HTTP/3 endpoint from an `Alt-Svc` response header field or an HTTP/2 `ALTSVC` frame (§3.1.1). And there is an explicit fallback requirement: "Connectivity problems (e.g., blocking UDP) can result in a failure to establish a QUIC connection; clients SHOULD attempt to use TCP-based versions of HTTP in this case" (§3.1). HTTP/3 runs over UDP, and plenty of corporate networks still drop it.

#### TLS's role, and where it sits per version

TLS is not a version of HTTP; it is what makes the `https` scheme mean anything. Its placement differs:

| Version  | TLS relationship                                      | ALPN token | Minimum                           |
|----------|-------------------------------------------------------|------------|-----------------------------------|
| HTTP/1.1 | TLS below HTTP, negotiated separately (RFC 9112 §9.7) | `http/1.1` | not specified by RFC 9112         |
| HTTP/2   | TLS below HTTP, ALPN-selected (RFC 9113 §3.2)         | `h2`       | TLS 1.2 or higher (RFC 9113 §9.2) |
| HTTP/3   | TLS 1.3 *inside* QUIC (RFC 9114 §1.2)                 | `h3`       | TLS 1.3                           |

RFC 9113 §3.2 also bans the cleartext identifier over TLS: the `h2c` token "MUST NOT be sent by a client or selected by a server."

Compression interacts with TLS in a way that concerns anyone putting secrets in headers. RFC 9113 §10.6: "Implementations communicating on a secure channel MUST NOT compress content that includes both confidential and attacker-controlled data unless separate compression dictionaries are used for each source of data", citing the BREACH class of attack, and "Generic stream compression, such as that provided by TLS, MUST NOT be used with HTTP/2."

#### Connection reuse and pooling as a client concern

This is where the substrate stops being abstract. On HTTP/1.1, throughput is a function of how many connections you keep warm and how well you reuse them; a client that opens a fresh TCP+TLS connection per call pays two round trips of handshake before sending a byte.

Every Juniper client library builds a pooled session. In `juniper-data-client`, `juniper_data_client/client.py:209-227` constructs a `requests.Session`, wraps a `urllib3` `Retry` in an `HTTPAdapter` with `pool_connections=10, pool_maxsize=10` (`juniper_data_client/constants.py:68-69`), and mounts it on both URL schemes.
`juniper-cascor-client` does the same at `juniper_cascor_client/client.py:87-97`, but passes only `pool_maxsize=DEFAULT_POOL_MAXSIZE` (`constants.py:38`) and leaves `pool_connections` at the library default — a difference that matters only when a client talks to several hosts, which these do not, but which shows how easily two copies of one idea drift.

`pool_connections` is the number of distinct host pools cached; `pool_maxsize` is the number of connections kept per pool. Setting `pool_maxsize` below your worker-thread count silently serialises requests, or discards connections after use, depending on the adapter's blocking configuration — a performance bug that looks like a slow server.

A small illustrative version:

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def build_session(retries: int = 3, backoff_factor: float = 0.5) -> requests.Session:
    """One warm pool per (scheme, host, port), reused across every call."""
    session = requests.Session()
    retry = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "PUT"],  # idempotent only -- RFC 9110 §9.2.2
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session
```

The `allowed_methods` line is not cosmetic. `juniper-data-client` restricts retries to `HEAD, GET, PUT` (`constants.py:67`) and documents why in the six lines above it (`constants.py:59-66`): retry is "restricted to idempotent HTTP methods per RFC 9110 §9.2.2. POST, PATCH and DELETE were previously included, which could cause duplicate dataset creation (on POST) or repeated side-effects (on DELETE)".
`juniper-cascor-client` never received that fix — `constants.py:37` still reads `["GET", "POST", "DELETE", "PUT", "PATCH"]`, so a transient 502 on `POST /v1/training/start` is silently replayed. Part II returns to this; here the point is that connection-level retry policy is a *substrate* decision with *semantic* consequences, and the specification that governs it (RFC 9110 §9.2.2) is version-independent.

Under HTTP/2 and HTTP/3 the pooling question changes shape rather than disappearing. One connection now carries up to `SETTINGS_MAX_CONCURRENT_STREAMS` concurrent exchanges, so client-side pools shrink to one or two connections per origin.
But RFC 9113 §9.1.1 permits a single connection to be reused for *multiple different URI authorities* when the server is authoritative for all of them — and warns that "reusing a connection for multiple origins can result in requests being directed to the wrong origin server", for instance when a middlebox routes by TLS SNI. The server's escape hatch is the `421 (Misdirected Request)` status code.

#### What each version changes for API *design*

Three pieces of common advice are version-dependent, and knowing which is which prevents both cargo-culting and premature optimisation.

**"Minimise header bloat."** Strongly true on HTTP/1.1, where every request re-sends every header field in full text — and where, as RFC 9113 §1 notes, verbose fields cause "the initial TCP congestion window to quickly fill." Much weaker on HTTP/2 and HTTP/3: after the first request on a connection, a stable `authorization` or `user-agent` costs a table reference.
Note the limits are still real and still advisory — `SETTINGS_MAX_HEADER_LIST_SIZE` in HTTP/2 (RFC 9113 §10.5.1) and `SETTINGS_MAX_FIELD_SECTION_SIZE` in HTTP/3 (RFC 9114 §4.2.2) are both explicitly non-binding hints, and a server that receives an oversized field block "can send an HTTP 431 (Request Header Fields Too Large) status code."

**"Batch endpoints to reduce round trips."** This was strong advice under HTTP/1.1, where concurrency cost you a connection each. RFC 9205 §4.11 states the modern position: "HTTP/2 and HTTP/3 offer multiplexing to applications, removing the need to use multiple connections."
A hand-rolled batch endpoint buys you much less than it used to, and costs a great deal: it invents a second error model (per-item success/failure inside a 2xx envelope), and it is uncacheable, because a batch response is a composite of many resources with no single identity.
`juniper-data` illustrates the tax — `POST /v1/datasets/batch-create` returns `201` regardless of per-item failure, with per-item `success`/`error` envelopes (`juniper_data/core/models.py:206-214`), so a caller must parse the body to learn whether anything worked.

**"Assume request order."** Never safe, on any version. RFC 9205 §4.11 is unambiguous: "In all versions of HTTP, requests are made independently — you can't rely on the relative order of two requests to guarantee their processing order... If two requests need strict ordering, the only reliable way to ensure the outcome is to issue the second request when the final response to the first has begun."
And normatively: "Applications MUST NOT make assumptions about the relationship between separate requests on a single transport connection."

#### Judgement Calls

**Do you specify a version at all?** RFC 9205 §4.1 says you almost certainly should not: "it is NOT RECOMMENDED that applications using HTTP specify a minimum version of HTTP to be used", because "a connection can be handled by implementations that are not controlled by the application; for example, proxies, CDNs, firewalls." And absolutely: "Applications using HTTP MUST NOT specify a maximum version, to preserve the protocol's ability to evolve."
The permitted middle ground is a note — "if an application's deployment benefits from the use of a particular version of HTTP (for example, HTTP/2's multiplexing), this ought be noted."

**Where do you terminate TLS?** Terminating at a gateway gives you one place to manage certificates and lets the gateway speak HTTP/2 to browsers while speaking HTTP/1.1 to your service. It also means the connection your application sees is not the connection the client opened — which breaks any authentication scoped to the transport (client certificates), and is the exact scenario [RFC 9421](https://www.rfc-editor.org/rfc/rfc9421.html) §1 was written for.

**Is HTTP/3 worth enabling?** If your clients are mobile or on lossy links, the per-stream reliability is a real win and connection migration is a real feature. If your clients are servers in the same datacentre, TCP loss is rare and HTTP/2 already gives you multiplexing; the UDP-blocking fallback path (RFC 9114 §3.1) is then pure added complexity.

**Do you need to know the client's IP?** If yes, HTTP/3's address migration (RFC 9114 §10.10) and any TLS-terminating proxy in front of you are both problems, and you need a deliberate answer — not `request.client.host` and hope.

#### Tradeoffs

| Dimension                   | HTTP/1.1                                  | HTTP/2                         | HTTP/3                          |
|-----------------------------|-------------------------------------------|--------------------------------|---------------------------------|
| Concurrency                 | multiple connections; pipelining unusable | streams on one TCP connection  | streams on one QUIC connection  |
| Head-of-line blocking       | application layer *and* TCP               | TCP only (RFC 9113 §1)         | neither, within a connection    |
| Header cost                 | full text, every request                  | HPACK, stateful per connection | QPACK, out-of-order safe        |
| Transport                   | TCP                                       | TCP                            | UDP (blocked on some networks)  |
| TLS                         | optional, layered                         | required in practice, TLS 1.2+ | TLS 1.3, inside QUIC            |
| Debuggability               | trivially readable on the wire            | binary; needs tooling          | binary and encrypted end-to-end |
| Upgrade to another protocol | yes (`Upgrade`)                           | no (RFC 9113 §8.2.2)           | no                              |

The debuggability row is worth dwelling on. HTTP/1.1's greatest engineering virtue is that you can read it. RFC 9205 §4.1 leans on this: when writing examples, "applications should document both the request and response messages with complete header sections, preferably in HTTP/1.1 format." Your documentation should show HTTP/1.1 wire format regardless of what you deploy.

#### Best Practices

- Write your API against RFC 9110 semantics and let deployment choose the version. Do not pin a version in your specification (RFC 9205 §4.1).
- Reuse connections. Build one pooled client per process and share it; do not construct a session per call.
- Size the pool to your concurrency. `pool_maxsize` below your worker count silently serialises.
- Restrict automatic retry to idempotent methods unless you have implemented idempotency keys (RFC 9110 §9.2.2). `juniper-data-client/juniper_data_client/constants.py:59-67` is the pattern: the restriction *and* the reason, in the code.
- Add jitter to retry backoff. None of the three Juniper clients does; a synchronized retry storm after a restart is the failure this prevents.
- Prefer many small resources over batch endpoints on HTTP/2+. You regain caching, per-resource authorization, and one error model.
- Document examples in HTTP/1.1 wire format with complete header sections (RFC 9205 §4.1).
- Never assume ordering between separate requests (RFC 9205 §4.11).

#### Common Failure Modes

**A new connection per request.** Usually a client constructed inside a request handler or a loop. Symptom: latency dominated by handshakes, and a server-side socket count that tracks request rate instead of concurrency.

**Retrying a non-idempotent request.** The transport-level retry is invisible to application code, so the duplicate looks like a client bug or a mystery. `juniper-cascor-client` retries `POST /v1/training/start` and `POST /v1/snapshots` on 502/503/504 (`constants.py:36-37`) with no idempotency key anywhere in the system — a duplicate training start is one dropped connection away.

**Pool exhaustion presenting as server slowness.** Requests queue on a client-side semaphore; server latency metrics look fine while client latency climbs. Distinguishable only by instrumenting the pool.

**Assuming HTTP/2 fixed everything.** A single TCP retransmission stalls every multiplexed stream. Teams that consolidate onto one HTTP/2 connection and then see tail-latency regressions on lossy links have found TCP head-of-line blocking, exactly as RFC 9113 §1 warns.

**Sending connection-specific headers to an HTTP/2 peer.** A hand-built client, or a translating intermediary that forgets RFC 9113 §8.2.2, produces a message the peer "MUST" treat as malformed. The failure is a protocol error, not a 4xx — often surfacing as an unexplained connection reset.

**Rate limiting or auditing by client IP behind a proxy or on HTTP/3.** You are keying on the proxy's address, or on an address that may change mid-connection (RFC 9114 §10.10).

#### Error Handling

Substrate errors are *not* HTTP status codes; that is the trap. A connection reset, a TLS handshake failure, a DNS failure, and a read timeout all occur before any status code exists, and application code must distinguish them from a `503`.

The most important distinction is **whether the request was applied**. RFC 9110 §9.2.2 draws the line: if a client sends a `PUT` and the connection closes before any response arrives, it "can establish a new connection and retry the idempotent request. It knows that repeating the request will have the same intended effect."
For a non-idempotent method it cannot know, and the specification is direct: "A client SHOULD NOT automatically retry a request with a non-idempotent method unless it has some means to know that the request semantics are actually idempotent... or some means to detect that the original request was never applied."

Three practical rules:

1. **Separate transport failure from application failure in your exception types.** A caller must be able to distinguish "could not reach the server" from "the server said no". All three Juniper clients collapse retry exhaustion into a generic error: `urllib3`'s `RetryError` surfaces as a `requests.RequestException` and is mapped to the base exception (`juniper-data-client/juniper_data_client/client.py:295-297`), losing which status caused it.
2. **Preserve the status code as structured data, not prose.** The clients do map *some* statuses to typed leaves — cascor-client sends 409 to `JuniperCascorConflictError` and 503 to `JuniperCascorServiceUnavailableError` (`juniper-cascor-client/juniper_cascor_client/client.py:404-414`), and recurrence-client maps 409 the same way (`juniper-recurrence-client/juniper_recurrence_client/client.py:260-266`) — so a caller *can* branch on exception **type** for a mapped status.
   What is genuinely lost is everything outside that map: no exception carries `.status_code`, `.response_body`, or `.headers`, so 401, 413, 429, 500 and 501 all collapse into one base exception distinguishable only by parsing the message string, and a 429's `Retry-After` is unreachable even when the server sent one.
   That cascor 503 leaf is also **dead code**. 503 sits on the retry forcelist (`juniper_cascor_client/constants.py:36`) and the `Retry` is constructed without `raise_on_status=False` (`client.py:89-94`), so an exhausted 503 arrives as urllib3's `RetryError` wrapped in a `requests.RequestException` and lands on the base branch at `client.py:371` — never on the leaf. The repo's own test has to mount a retry-free adapter to reach it (`tests/test_client.py:299-311`).
3. **Set a timeout, and split it.** A single scalar timeout conflates connect, read, write, and pool-acquisition, which have completely different meanings. All three Juniper clients use one flat 30-second value with no public per-call override (`juniper-data-client/juniper_data_client/client.py:248`; `juniper-cascor-client/juniper_cascor_client/client.py:363`).
   For `juniper-recurrence-client` that scalar is also the socket timeout on a *synchronous long-running training call* (`client.py:311`), which makes the timeout an operational limit on model size.

---

### I.3 Architectural Styles: REST, RPC/gRPC, GraphQL

#### Overview

Three styles dominate. They differ less in capability than in *where they put the contract* and *what infrastructure they can reuse*.

- **REST** puts the contract in resources, URLs, and HTTP's own generic semantics. It reuses everything HTTP already has — caches, proxies, conditional requests, content negotiation — and gets no schema unless you add one.
- **gRPC** puts the contract in a `.proto` file and generates both ends. It reuses HTTP/2's framing and nothing else; caches and proxies see opaque POSTs.
- **GraphQL** puts the contract in a typed schema and lets the client compose the query. It reuses one HTTP endpoint and, by default, discards HTTP caching entirely.

RFC 9205 §3.1 states the principle that separates the first from the other two: "Much of the value of HTTP is in its generic semantics — that is, the protocol elements defined by HTTP are potentially applicable to every resource and are not specific to a particular context."
That genericity "allows an HTTP message to be handled by common software (e.g., HTTP servers, intermediaries, client implementations, and caches) without requiring those implementations to understand the application in use." gRPC and GraphQL both deliberately trade some of that away for a stronger contract.

#### Background

**REST** is an architectural style from Roy Fielding's 2000 dissertation, defined by a set of constraints — client/server, statelessness, cacheability, uniform interface, layered system, and optional code-on-demand. The uniform-interface constraint is the load-bearing one, and it includes hypermedia as the engine of application state: responses carry links that tell the client what it can do next.

Almost nothing marketed as REST implements that. What the industry calls REST is "JSON over HTTP with resource-shaped URLs and conventional method usage" — which is a perfectly good design, just not the thing Fielding described. It is worth saying plainly rather than pretending: the constraint most APIs drop is hypermedia, and dropping it means clients hardcode URL templates and the server can never move a resource.

RFC 9205 §3.2 makes the case for links in normative terms, and identifies exactly what you lose: "Instead of statically defining URI components like paths, it is RECOMMENDED that applications using HTTP define and use links to allow flexibility in deployment."
Links let a request be "routed to a different server without the overhead of a redirection", let applications be mixed on one server, and offer "a natural mechanism for extensibility, versioning, and capability management."
`juniper-data` hardcodes its `/v1` prefix as a repeated string literal in three `include_router` calls (`juniper_data/api/app.py:140-142`) and again inside emitted payload URLs (`juniper_data/api/routes/datasets.py:138`, `:253`), with no `API_VERSION` constant anywhere — the ordinary consequence of building paths rather than links.

**gRPC** is Google's RPC framework: Protocol Buffers for the message format, HTTP/2 for the transport, and code generation for both client and server. It is not an IETF standard; its wire protocol is specified in the gRPC project's own "gRPC over HTTP2" document.

**GraphQL** is a query language and execution model, originally from Facebook, now specified at `spec.graphql.org` and governed by the GraphQL Foundation. It is also not an IETF standard. Notably, the core GraphQL specification says nothing about HTTP at all — the transport binding lives in a separate **GraphQL over HTTP** document that is, at the time of writing, still a working draft.

#### gRPC: what it actually is

Four call types, all expressed as one HTTP/2 stream:

| Call type               | Client sends | Server sends | Typical use                      |
|-------------------------|--------------|--------------|----------------------------------|
| Unary                   | one message  | one message  | ordinary RPC                     |
| Server-streaming        | one message  | a sequence   | subscriptions, large result sets |
| Client-streaming        | a sequence   | one message  | uploads, telemetry ingest        |
| Bidirectional streaming | a sequence   | a sequence   | interactive sessions             |

The mechanism is worth understanding because it explains gRPC's single biggest deployment constraint. A gRPC call is an HTTP/2 `POST` whose body is a sequence of length-prefixed protobuf messages carried in `DATA` frames. The RPC's final status is *not* the HTTP status code — it is delivered in a `grpc-status` **trailer**: a `HEADERS` frame sent *after* all `DATA` frames. That design is what lets a server stream a thousand records and only then report failure.

Trailers are why gRPC does not work in browsers. HTTP/2 supports them (RFC 9113 §4.3 notes that messages "can optionally include a field block that carries a trailer section"), but the browser Fetch API exposes `response.headers` and not response trailers; the proposed trailer API was removed from the Fetch specification in late 2019 and is implemented in no major browser.
**gRPC-Web** works around this by moving the status metadata to the end of the response *body* instead of into trailers, which requires a translating proxy (Envoy's gRPC-Web filter, or a native gRPC-Web server implementation).
**Connect** is a later protocol that speaks gRPC, gRPC-Web, and a plain HTTP/JSON dialect over the same handlers.

The same trailer dependency bites outside the browser. Intermediaries with weak trailer support — some CDN configurations, some load balancers, older nginx builds — silently drop them, producing the classic symptom: a `200` response with no `grpc-status`, which client libraries surface as a confusing internal error.

#### GraphQL: single endpoint, typed schema, resolvers

A GraphQL server exposes one endpoint. The client sends a query naming exactly the fields it wants; the server returns exactly those fields. The schema is a type system — object types, fields, arguments, interfaces, unions, enums — and is introspectable at runtime, which is what powers GraphQL's genuinely excellent tooling (GraphiQL, editor completion, typed client codegen).

Execution is per-field. Each field has a **resolver**: a function that produces that field's value given its parent value and arguments. The engine walks the query tree calling resolvers. This is the source of GraphQL's expressive power and of its two characteristic pathologies.

**The N+1 problem.** Consider `{ datasets(limit: 50) { id generator { name } } }`. The `datasets` resolver runs one query returning 50 rows. Then the `generator` resolver runs *once per row* — 50 more queries. Nesting one level deeper multiplies again. The query looks trivial; the database sees 51 round trips, or 2,551.

The standard fix is **dataloader batching**: instead of resolving immediately, each `generator` resolver registers a key with a per-request loader and returns a promise. At the end of the event-loop tick, the loader dispatches one batched fetch for all 50 keys and fulfils every promise. Two properties matter:

- The loader must be **per request**, not per process. A process-lifetime loader is a cache that leaks one user's data into another user's response — an authorization bug, not a performance bug.
- Batching does not compose with per-field authorization automatically. If `generator` is visible only to some callers, the batch must still be filtered per caller.

**Unbounded query cost.** Because the client composes the query, a client can compose an expensive one. Given a cyclic schema (a dataset has generators, a generator has datasets), a query can recurse arbitrarily deep and cost exponentially, from a request that is a few hundred bytes long. The GraphQL specification's validation phase checks structural and type correctness; it does not check cost. Cost control is entirely an implementation concern, and there are three usual guardrails:

1. **Depth limiting** — reject queries nested beyond N levels. Cheap, crude, and easy to defeat with a wide shallow query.
2. **Complexity/cost analysis** — assign each field a cost, multiply through list arguments, reject above a budget. More accurate, requires schema annotation and maintenance.
3. **Persisted queries** — the server accepts only query documents registered ahead of time, identified by hash. This eliminates the attack surface entirely, at the cost of GraphQL's ad-hoc flexibility. It also, usefully, makes the request small enough to send as a `GET` — which brings caching back.

#### Caching: the mechanism, not the slogan

"GraphQL breaks HTTP caching" is true, and the mechanism is specific enough to be worth spelling out.

HTTP caching is keyed on the request method and target URI. RFC 9110 §9.3.1 states plainly that "The response to a GET request is cacheable." For `POST`, RFC 9110 §9.3.3 imposes two conditions that essentially never hold in practice: "Responses to POST requests are only cacheable when they include explicit freshness information... and a `Content-Location` header field that has the same value as the POST's target URI."
And even then, "a POST request cannot be satisfied by a cached POST response because POST is potentially unsafe."

A GraphQL client by default sends `POST /graphql` with the query in the body. Two different queries are therefore *the same cache key* — same method, same URI — differing only in a body that no HTTP cache inspects. There is nothing a CDN, a reverse proxy, or a browser cache can safely do with that. RFC 9111 §3 lists what a cache needs before it may store a response at all, and a bodiless-key `POST` fails at the first hurdle.

The consequences ripple outward. Conditional requests (`ETag` / `If-None-Match`) become meaningless because there is no stable resource identity to validate. `Vary` cannot help, because it varies on headers, not bodies. A CDN in front of a GraphQL API is a routing device, not a cache.

The escapes are real but narrow: persisted queries plus `GET` (which restores a cacheable method and a query-string cache key), or an application-level cache inside the resolvers keyed on your own identifiers. The second is the common choice, and it means rebuilding — in your process, without shared infrastructure — the thing RFC 9205 §4.9 calls "one of the primary benefits of using HTTP for applications."

REST's position here is the strong one, and most REST APIs waste it.
`juniper-data` is a clean example of the waste: `GET /v1/datasets/{id}/artifact` serves large, **immutable**, content-addressed blobs whose SHA-256 digest is already computed and stored (`juniper_data/core/artifacts.py:50-63`), and the service emits no `ETag`, no `Last-Modified`, no `Cache-Control`, and never returns `304` — the only `max-age` string in the codebase is inside its HSTS header value (`juniper_data/api/constants.py:69`).
The hard part of caching, having a stable strong validator, was already done; the easy part was skipped.

#### Honest comparison

| Dimension            | REST (JSON over HTTP)                                                                         | gRPC                                                           | GraphQL                                                             |
|----------------------|-----------------------------------------------------------------------------------------------|----------------------------------------------------------------|---------------------------------------------------------------------|
| Contract strength    | none by default; OpenAPI is bolt-on and often drifts                                          | strong: `.proto` is the source of truth, codegen both ends     | strong: typed schema, introspectable at runtime                     |
| Tooling              | universal (curl, browsers, every proxy)                                                       | excellent codegen; needs `grpcurl`-class tools to poke by hand | excellent explorer/IDE tooling; typed client codegen                |
| HTTP caching         | full (if you use it)                                                                          | none — opaque POSTs                                            | none by default; recoverable via persisted queries + `GET`          |
| Over/under-fetching  | both, unless you add field selection                                                          | under-fetching common; fixed response shape                    | solved by construction — this is its reason to exist                |
| Versioning           | URL or media-type versioning; RFC 9205 §4.16 prefers links, media types, or new header fields | field numbers give wire compat; add fields, never renumber     | schema evolution by additive change plus `@deprecated`; no versions |
| Streaming            | SSE or WebSockets, bolted on                                                                  | native, four call types                                        | subscriptions, transport unspecified by the core spec               |
| Browser reachability | native                                                                                        | **no** — needs gRPC-Web or Connect plus a proxy                | native                                                              |
| Error model          | HTTP status codes plus a body (RFC 9457 problem details, ideally)                             | `grpc-status` code in trailers plus `grpc-message`             | `errors` array in the body                                          |
| Observability        | status codes are the metric                                                                   | status codes are the metric                                    | see below — status codes are *not* the metric                       |

RFC 9205 §4.16 deserves quoting on versioning because it contradicts the default instinct. For backwards-incompatible change it names three mechanisms: "Using a distinct link relation type to identify a URL for a resource that implements the new functionality", "Using a distinct media type to identify formats that enable the new functionality", and "Using a distinct HTTP header field to implement new functionality outside the message content." A `/v2/` path prefix is not on the list.

#### Operational observability: why GraphQL breaks naive monitoring

Every standard HTTP monitoring setup — load balancer dashboards, CDN analytics, `http_requests_total{status}` in Prometheus, SLO burn-rate alerts, log-based error rates — computes error rate from the response status code. It is the one field every layer of infrastructure understands without knowing anything about your application.

A GraphQL server using the conventional `application/json` binding returns `200 OK` when a query fails. The failure is in the body:

```json
{
  "data": { "dataset": null },
  "errors": [
    {
      "message": "Dataset not found",
      "path": ["dataset"],
      "extensions": { "code": "NOT_FOUND" }
    }
  ]
}
```

Every dashboard in the building reports 100% success. Partial failure is worse still: a query touching ten fields where one resolver throws returns `200` with nine populated fields, one `null`, and one entry in `errors` — a response that is simultaneously a success and a failure, and that no status code can express.

This is not an accident or an oversight; it follows from GraphQL's execution model, in which a single request can partially succeed at field granularity, and HTTP has exactly one status code per response. But note the tension with RFC 9205 §3.1, which requires that applications "MUST NOT redefine, refine, or overlay the semantics of generic protocol elements such as methods, status codes, or existing header fields."
Returning `200` for a failed operation is arguably compliant in the letter (the HTTP request *was* successfully processed; the GraphQL operation was not) and clearly at odds with the spirit.

The GraphQL over HTTP working draft addresses this with a new media type, `application/graphql-response+json`, under which a server uses the full range of HTTP status codes: a response with a non-null `data` entry must carry a 2xx status, a document that fails to parse should be `400`, and a request that fails before execution gets an appropriate 4xx/5xx.
The legacy `application/json` behaviour — always `200` — is retained for compatibility with clients written before the draft. Because that document is still a working draft and the legacy binding remains widespread, you must assume both behaviours exist in the wild.

The operational consequence, whichever binding you serve: **your GraphQL error rate must be instrumented in the resolver layer**, emitted as its own metric, and alerted on separately. If you learned about your outage from the `errors` array only because a customer complained, this is the mechanism that hid it.

#### Judgement Calls

**Is HTTP even being used?** RFC 9205 §2 gives a crisp test. If your application "uses the transport port 80 or 443", or "uses the URI scheme `http` or `https`", or "uses an ALPN protocol ID that generically identifies HTTP (e.g., `http/1.1`, `h2`, `h3`)", or makes registrations in HTTP's IANA registries — then you are using HTTP, and "all of the requirements of the HTTP protocol suite are in force."
§2.1 gives the alternative: an application may build on HTTP's message format while changing its operation, but then it "MUST NOT use HTTP's URI schemes, transport ports, ALPN protocol IDs, or IANA registries" and loses "at least a portion of the benefits" plus "the benefit of mindshare." There is no third option where you keep the ports and redefine the semantics.

**Who are your clients?** Browsers rule out plain gRPC. Third-party integrators with unknown tooling favour REST heavily — curl works, and every language has an HTTP client. Internal services in a monorepo with a shared build make gRPC's codegen nearly free. A single first-party frontend with many screens and volatile data needs is GraphQL's home ground.

**Is caching load-bearing?** If a meaningful fraction of your traffic is repeated reads of slowly-changing data, REST's caching is worth more than GraphQL's flexibility, and you should not give it up without a plan to replace it.

**Do you have the discipline for a schema?** All three styles can be schema-first. Only gRPC and GraphQL *enforce* it. A REST API whose OpenAPI document is generated but never asserted against will drift. `juniper-data` shows the class: it declares no `responses={...}` anywhere, so **none** of its 404 / 400 / 501 / 401 / 429 / 413 responses appear in the generated schema — only the success code and FastAPI's automatic 422.

**Do you want per-field authorization?** GraphQL makes it necessary (a client can ask for any field it can name) and hard (authorization logic distributes across resolvers). REST concentrates it at the resource, which is coarser but far easier to audit.

#### Tradeoffs

The trade is consistently **contract strength and client flexibility against infrastructure reuse**.

REST buys the entire HTTP ecosystem — caching, conditional requests, range requests, content negotiation, proxies, CDNs, browser devtools, every debugging tool ever written — at the price of having no enforced contract and no field selection.

gRPC buys a rigorously enforced contract, efficient binary framing, and genuinely first-class streaming, at the price of opacity: no caching, no browser access without a proxy, no reading the wire without tooling, and an error model that intermediaries do not understand.

GraphQL buys exact client-driven fetching and outstanding developer tooling, at the price of the caching layer, a monitoring model that must be rebuilt, and a class of performance and DoS problems (N+1, unbounded cost) that do not exist in the other two.

A fourth option is under-considered: **REST with a well-maintained OpenAPI document plus generated clients**. It recovers a large share of gRPC's contract strength while keeping HTTP's genericity. It fails only when nobody maintains the document — which is a process problem, not a technology one.

#### Best Practices

- Choose one primary style per API surface and be honest in the documentation about which it is. An API that calls itself REST but ignores caching, status codes, and links should say "JSON over HTTP".
- Do not overlay application semantics on HTTP's generic elements (RFC 9205 §3.1). Application-specific meaning belongs in the message content and in fields you define, not in redefined status codes.
- Avoid over-specifying protocol behaviour. RFC 9205 §3.1 gives the anti-pattern verbatim — a specification saying "A POST request MUST result in a 201 (Created) response" forms an expectation the deployment cannot keep, because "there might be a proxy that requires authentication, or a server-side error, or a redirection."
- Use links rather than hardcoded path construction where you can (RFC 9205 §3.2).
- If you serve GraphQL: use a per-request dataloader, enforce a depth *and* complexity budget, consider persisted queries, and instrument the `errors` array as a first-class metric.
- If you serve gRPC and any client is a browser, plan the gRPC-Web or Connect layer up front — it is not a late addition.
- If you serve REST over immutable or slowly-changing resources, emit `ETag` and honour `If-None-Match`. If you already compute a content digest, you have already done the hard part.

#### Common Failure Modes

**"REST" that is RPC in disguise.** `POST /api/doThing` with a verb in the path and a `200 {"error": "..."}` body. Harmless if labelled honestly; corrosive when documented as REST, because clients then expect caching and status-code semantics that do not exist.

**Adding GraphQL to reduce round trips on an HTTP/2 backend.** The round-trip cost that motivated the change was already largely gone (RFC 9205 §4.11), and the caching that gets discarded was load-bearing. Measure before migrating.

**The GraphQL N+1 that only appears in production.** Development datasets are small enough that 51 queries feel instant. Detection requires query-count instrumentation per request, not latency alone.

**A process-wide dataloader.** Caches across users; leaks data between requests. This is a security incident with a performance-optimisation origin story.

**gRPC behind an intermediary that drops trailers.** `200` with no `grpc-status`. The client library's error message rarely names the real cause.

**Monitoring GraphQL by HTTP status code.** Covered above. The dashboard is green during the outage.

**Batch endpoints as a substitute for an async job pattern.** `juniper-data` has no `202`, no job resource, and no `BackgroundTasks` anywhere; long work is offloaded per-request with `asyncio.to_thread` (`juniper_data/api/routes/datasets.py:150`) and batch endpoints with fixed per-operation caps of 50 to 100 items (`juniper_data/core/constants.py:33-37`) stand in for concurrency. That works until one item in the batch is slow.

#### Error Handling

Each style has a native error channel, and they are not interchangeable.

**REST** uses status codes plus a body. The body should be [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457.html) problem details (`application/problem+json`) — a registered media type with `type`, `title`, `status`, `detail`, and `instance` members, extensible with your own. Most APIs use an ad-hoc shape instead.
`juniper-data` has zero occurrences of `problem+json` repo-wide; it uses FastAPI's default `{"detail": ...}` and, because it never overrides the framework's 422 handler, ships **two incompatible `detail` shapes** — a string from every hand-raised `HTTPException`, and an array of objects from validation failures. A client parsing `detail` must type-check it.

**gRPC** uses a status code from a fixed enumeration in the `grpc-status` trailer, plus `grpc-message` and an optional details payload. The enumeration is smaller and less ambiguous than HTTP's, which is a real advantage — but it is invisible to every HTTP intermediary, so nothing between client and server can act on it.

**GraphQL** uses the `errors` array, with `message`, `path` (which field failed), and a conventional `extensions.code`. Partial success is expressible, which HTTP status codes cannot do; this is a genuine capability and simultaneously the monitoring problem above.

Two rules that hold across all three:

- **Do not leak internals in error text.** `juniper-data` shows both the fix and the inconsistency in adjacent lines: `routes/datasets.py:433-447` replaces raw exception text with a 12-hex correlation id, documented because raw strings "can leak filesystem paths or internal type details" — while the adjacent branch at `:429` passes `HTTPException.detail` through verbatim.
- **Choose the status code for what the *client* should do next.** `juniper-data` documents a good instance of this reasoning: a generator whose optional dependency is missing returns `501`, not `503`, because (`routes/datasets.py:158-168`) "503 is deliberately avoided: it invites client retries and health-tooling misreads for a condition that will not clear on its own."

#### Controversy: REST vs GraphQL vs gRPC — choosing a style

**The controversy is real and unresolved.** It is not a matter of one style being technically superior; it is a genuine disagreement about which costs are acceptable, and the disagreement persists because the three styles optimise for different and legitimately incompatible things. Advocacy in this space is unusually strong, and much of it is written by people whose context does not resemble yours.

**The camps.** REST advocates hold that HTTP's generic semantics are a decades-deep investment in shared infrastructure and that discarding them is almost never worth it. gRPC advocates hold that untyped, undocumented JSON contracts are the dominant source of integration defects and that generated code eliminates a whole class of bugs.
GraphQL advocates hold that server-defined response shapes force clients into over-fetching, under-fetching, and endless bespoke endpoints, and that client-driven queries fix the actual bottleneck in product work.

**Where the split came from.** REST's dominance in the 2000s was a reaction to SOAP's complexity, and it succeeded partly by being *less* specified. gRPC emerged from Google's internal Stubby, in an environment of thousands of services in a monorepo with a shared build system — where codegen is nearly free and browsers are not clients.
GraphQL emerged from Facebook's mobile clients, where a single screen needed data from many resources over a slow, expensive network and the round trips were the dominant cost. Each style is an excellent solution to the problem its origin faced. The controversy is largely about how far each generalises.

##### The REST camp

**Strengths.** Reuses the entire HTTP ecosystem — RFC 9205 §3.3 enumerates it: message framing, multiplexing, TLS integration, intermediaries, client authentication, content negotiation, "caching for server scalability, latency and bandwidth reduction, and reliability", granularity of access control through a rich URL space, partial content, and "the ability to interact with the application easily using a Web browser". Universally understood.
Zero client-side toolchain requirement. Debuggable with curl. Degrades gracefully across versions and intermediaries.

**Weaknesses.** No enforced contract; OpenAPI is optional and drifts. No field selection, so over-fetching and under-fetching are structural. Endpoint proliferation as client needs diversify. Hypermedia — the thing that makes REST properly REST — is nearly always dropped, which forfeits its deployment flexibility. Streaming is not native.

**Risks.** The contract rots silently: the schema says one thing, the server does another, and nothing fails until a client breaks in production. Caching benefits are claimed and not implemented (as in `juniper-data`). Status-code usage becomes idiosyncratic, and clients start pattern-matching on error strings.

**Guardrails.** Generate the OpenAPI document *and* assert it in CI against the running app. Declare `responses={...}` for every non-success code. Set stable `operation_id`s so generated client method names survive a rename. Adopt RFC 9457 problem details. Emit `ETag` where you have a validator. Treat "we will document it later" as a decision not to have a contract.

##### The gRPC camp

**Strengths.** The `.proto` file is the single source of truth, and codegen makes drift structurally impossible for both ends. Binary framing is compact and fast to parse. Streaming is first-class in all four directions, not bolted on. Field numbering gives disciplined forward and backward wire compatibility. Deadlines and cancellation propagate through the stack. The error enumeration is small and unambiguous.

**Weaknesses.** No HTTP caching whatsoever — every call is an opaque POST. Browsers cannot speak it without gRPC-Web or Connect plus a proxy. The wire is unreadable without tooling. Intermediaries that mishandle trailers break it in ways that are hard to diagnose. Load balancing needs to be connection-aware, since long-lived HTTP/2 connections pin a client to a backend. It imposes a build-system dependency on every consumer.

**Risks.** Third-party integrators cannot use it without adopting your toolchain, which turns a public API into a closed one. Debugging in production is materially harder — you cannot read a capture. A proto change that is wire-compatible can still be semantically breaking, and nothing catches that. Teams sometimes adopt it for performance without measuring, and pay the opacity cost for a benefit they never needed.

**Guardrails.** Keep protos in a versioned, reviewed repository with a breaking-change linter (Buf or equivalent) in CI. Never renumber or reuse a field number. Consider Connect if any browser or curl-wielding human is a client. Verify trailer handling through every intermediary in your path, in a test, before you depend on it. Publish a JSON/REST gateway for third parties.

##### The GraphQL camp

**Strengths.** Over- and under-fetching are solved by construction — the client asks for exactly what it needs, once. One endpoint, one round trip, for a screen that touches many resources. The type system is enforced and introspectable, which yields the best interactive tooling of the three. Schema evolution is additive with `@deprecated`, so versioned endpoints are unnecessary. Frontend teams can iterate without backend changes, which is a real organisational velocity gain.

**Weaknesses.** HTTP caching is gone by default, for the specific mechanical reason above. Server-side performance is opaque — a cheap-looking query can be catastrophic. N+1 is the default behaviour, not an anti-pattern you have to work at. Authorization distributes across every resolver and is correspondingly hard to audit. Rate limiting by request count is meaningless when requests have unbounded cost.
The `200`-with-errors convention breaks all standard monitoring. File uploads and streaming need out-of-band conventions.

**Risks.** A single client-composed query becomes a denial-of-service vector from a few hundred bytes. A per-field authorization gap exposes data the REST equivalent would never have routed. The performance cliff arrives in production, because development datasets hide N+1. Teams often adopt GraphQL for one demanding client and then maintain it for all clients, most of which would have been better served by three REST endpoints.

**Guardrails.** Enforce depth *and* complexity limits before launch, not after the first incident. Use per-request dataloaders, never process-scoped. Prefer persisted queries for first-party clients — they eliminate the cost attack and restore `GET` caching. Instrument resolver-level errors as a distinct metric with its own alert. Audit per-field authorization deliberately; it will not emerge from testing. Track queries-per-request and rows-fetched-per-request, not just latency.

##### Recommendation

**This is a recommendation, not a rule**, and it is contingent on the audience of your API.

For a **public or third-party-facing API**: REST, with a maintained and CI-asserted OpenAPI document, RFC 9457 problem details, and real cache headers. The genericity argument in RFC 9205 §3.1 is at its strongest when you do not control your clients, and universal tooling is worth more than contract enforcement when your integrators are unknown.

For **internal service-to-service traffic** in an organisation that already has a shared build system: gRPC. Its costs — opacity, browser unreachability, toolchain coupling — land almost entirely on client populations you do not have, and the codegen benefit compounds with service count.

For a **first-party frontend with many screens and volatile data requirements**: GraphQL is a defensible choice, provided you budget for the guardrails above as part of the initial build rather than as follow-up work. If your data is mostly read-mostly and cacheable, reconsider — you are trading away your best scaling lever for flexibility you may not need.

For most teams most of the time, **REST done properly beats GraphQL done hastily**, and "done properly" mostly means using the HTTP features you already have. The version of REST that loses to GraphQL is the one that ships no schema, no cache headers, and no error contract.

---

### I.4 Real-Time and Streaming

#### Overview

HTTP's default is client-initiated request/response. A large class of APIs needs the reverse: the server has news, and the client should learn about it promptly. There are five practical answers, and they are not interchangeable.

| Option             | Direction                  | Transport                              | Reconnect                             | Browser API            |
|--------------------|----------------------------|----------------------------------------|---------------------------------------|------------------------|
| Polling            | client pulls               | ordinary HTTP requests                 | trivial (it is just the next request) | any HTTP client        |
| Long-polling       | client pulls, server holds | ordinary HTTP requests                 | client re-issues after each response  | any HTTP client        |
| Server-Sent Events | server pushes              | one long-lived HTTP response           | **automatic**, built into the API     | `EventSource`          |
| WebSockets         | bidirectional              | its own protocol after an HTTP upgrade | manual, you write it                  | `WebSocket`            |
| Webhooks           | server pushes              | a fresh HTTP request to *your* server  | server-side retry policy              | n/a (server-to-server) |

The most consequential structural fact, and the one this section builds toward: **a WebSocket connection is not an HTTP request, and middleware written against the request/response abstraction never sees it.**
The qualifier is load-bearing. Starlette's `BaseHTTPMiddleware` returns immediately for any non-HTTP scope (`starlette/middleware/base.py:102`, Starlette 1.6.0), so anything built on it is blind to the upgrade — and every middleware in Juniper is built on it.
Pure-ASGI middleware, which inspects `scope["type"]` itself, *can* act on a WebSocket, and several of Starlette's own do: `AuthenticationMiddleware` accepts both scopes and closes the socket on failure (`authentication.py:30`, websocket branch at `:39`), as do `SessionMiddleware`, `TrustedHostMiddleware`, and `HTTPSRedirectMiddleware`. `CORSMiddleware` genuinely bails (`cors.py:79`), and so does any body-size cap — neither concept has a WebSocket meaning.
So the question is not "does middleware apply" but "which kind is mine". Because Juniper's are all `BaseHTTPMiddleware` subclasses, its authentication, rate limiting, message-size caps, and request logging *must* be re-implemented inside each WebSocket handler — and, as the code below shows, largely are.

#### Background

**Polling** is a timer and a `GET`. Its cost is a function of interval and client count, and it is wrong in both directions simultaneously: too slow to be timely, too fast to be cheap. At a 5-second interval with 1,000 clients, that is 200 requests per second to discover that nothing changed. It is nonetheless the right answer more often than its reputation suggests — it needs no special infrastructure, survives every proxy, is trivially cacheable with `ETag`/`If-None-Match`, and fails safe.

**Long-polling** improves timeliness by having the server hold the request open until it has something to say (or a timeout fires). The client re-issues immediately on each response. It delivers near-push latency over ordinary HTTP, at the cost of one held server connection per client and a permanent argument with every intermediary's idle timeout.

**Server-Sent Events** is a one-way server-to-client stream over a single long-lived HTTP response. It is defined in the **WHATWG HTML Living Standard, §9.2 "Server-sent events"** — *not* an RFC. This matters for citation hygiene: there is a retired W3C `EventSource` Working Draft from 2011, and SSE has no RFC number at all.

**WebSockets** is a full-duplex protocol defined in [RFC 6455](https://www.rfc-editor.org/rfc/rfc6455.html). Its relationship to HTTP is narrow and explicit — RFC 6455 §1.7: "The WebSocket Protocol is an independent TCP-based protocol. Its only relationship to HTTP is that its handshake is interpreted by HTTP servers as an Upgrade request."

**Webhooks** invert the direction entirely: the server makes an HTTP request to a URL you registered. They are the only option here that works across organisational boundaries without a persistent connection, and they turn you into a server with all that implies — you need an endpoint, request authentication, replay protection, and idempotency.

#### Server-Sent Events: mechanism and constraints

The server responds with `Content-Type: text/event-stream` and never closes the body. Events are newline-delimited field blocks:

```text
event: metrics
id: 42
data: {"epoch": 17, "loss": 0.0231}

retry: 5000

data: {"epoch": 18, "loss": 0.0219}

```

Four fields carry the semantics:

- `data:` — the payload. Multiple `data:` lines in one block are joined with newlines.
- `event:` — the event name the client dispatches on; absent, it defaults to `message`.
- `id:` — sets the connection's *last event ID*.
- `retry:` — sets the reconnection delay in milliseconds. Absent, the delay is user-agent-defined (browsers commonly use a few seconds).

The `id:` field is what makes SSE genuinely good at resumption, and it is the single feature that most distinguishes it from a hand-rolled stream. When the connection drops, the browser reconnects **automatically** and sends the last received id back in a `Last-Event-ID` request header. A server that honours that header can replay exactly the missed events. You get at-least-once delivery across reconnects without writing a line of reconnection logic.

The constraints are equally definite:

- **Text only, UTF-8.** Binary payloads must be encoded (base64), inflating them by a third.
- **One direction.** The client cannot send anything on the stream; it makes ordinary HTTP requests for that. In practice this is fine — most "real-time" needs are read-heavy.
- **No custom request headers — in the browser `EventSource` API.** This is a constraint of that API, not of SSE as a protocol. The `EventSource` constructor takes a URL and an optional dictionary whose only standard member is `withCredentials`, with no header parameter, so a browser using it must carry the credential in a cookie or a query parameter — and a query parameter puts it in access logs, browser history, and `Referer` headers.
  Nothing in `text/event-stream` itself forbids headers: a server-side or CLI consumer sets `Authorization` like any other request, and a browser can too by dropping to `fetch()` and reading the `ReadableStream`. The real cost of that escape is what `EventSource` was giving you for free — you now own the event parser *and* the reconnect-with-`Last-Event-ID` logic, which is most of the reason to pick SSE at all.
- **HTTP/1.1 connection budget.** Each open `EventSource` occupies one of the browser's ~6 connections per origin. Several tabs on one origin can exhaust the budget and stall ordinary page requests. Under HTTP/2 and HTTP/3 the stream is one multiplexed stream among many, and the problem evaporates — this is a case where the substrate choice from I.2 directly determines whether an interaction model is viable.

#### WebSockets: the handshake, the framing, and the security model

The client sends an ordinary HTTP `GET` with `Upgrade: websocket`, `Connection: Upgrade`, `Sec-WebSocket-Key`, and `Sec-WebSocket-Version: 13`; the server answers `101 Switching Protocols` with a `Sec-WebSocket-Accept` derived from the key. After that the connection carries WebSocket frames, not HTTP messages.

RFC 6455 §1.6 explains the `Sec-` prefix: those fields exist so that "the server prove that it read the handshake", and "at the time of writing of this specification, fields starting with `Sec-` cannot be set by an attacker from a web browser using only HTML and JavaScript APIs" — the handshake is deliberately designed to be un-forgeable by a cross-origin form post or `XMLHttpRequest`.

**Masking.** RFC 6455 §5.3 requires every client-to-server frame to be XOR-masked with a per-frame key. §10.3 gives the reason, and it is a good piece of protocol history: an experiment demonstrated cache-poisoning attacks in which an upgraded connection was used to send bytes that looked like a `GET` request for a popular resource, which non-conformant intermediaries then cached.
Masking makes it impossible for script to control the bytes on the wire, and the specification is explicit that "Clients MUST choose a new masking key for each frame, using an algorithm that cannot be predicted by end applications that provide data."

**Origin.** RFC 6455 §10.2: "Servers that are not intended to process input from any web page but only for certain sites SHOULD verify the `Origin` field is an origin they expect." The security caveat is stated just as plainly in §1.6: "when the WebSocket Protocol is used by a dedicated client directly (i.e., not from a web page through a web browser), the origin model is not useful, as the client can provide any arbitrary origin string."
`Origin` constrains browsers. It constrains nothing else. Treating it as an authentication mechanism is a category error.

**Close codes.** RFC 6455 §7.4.1 defines 1000 (normal), 1001 (going away), 1002 (protocol error), 1003 (unacceptable data type), 1007 (inconsistent data), 1008 (policy violation), 1009 (message too big), 1010 (client expected extensions), and 1011 (unexpected server condition).
Three values are reserved and **must never be sent in a Close frame** — 1005 (no status present), 1006 (closed abnormally), and 1015 (TLS handshake failure); they exist for applications reporting what happened locally. 1004 is reserved with no meaning.

The ranges (RFC 6455 §7.4.2) are the part most often misremembered:

| Range     | Reservation                                                                            |
|-----------|----------------------------------------------------------------------------------------|
| 0-999     | not used                                                                               |
| 1000-2999 | the protocol, its revisions, and extensions in a permanent public specification        |
| 3000-3999 | libraries, frameworks, and applications — **registered directly with IANA**            |
| 4000-4999 | private use, **cannot be registered**, meaning by prior agreement between applications |

So an application inventing its own codes should use 4000-4999 unless it intends to register them.

**Authentication.** RFC 6455 §10.5 declines to specify one: "This protocol doesn't prescribe any particular way that servers can authenticate clients during the WebSocket handshake. The WebSocket server can use any client authentication mechanism available to a generic HTTP server, such as cookies, HTTP authentication, or TLS authentication."
And the protocol explicitly permits arbitrary headers — §4.1 item 12: "The request MAY include any other header fields, for example, cookies and/or authentication-related header fields such as the `Authorization` header field."

**But the browser cannot send them.** The WHATWG WebSockets Standard's constructor takes a URL and an optional subprotocol list — there is no parameter for request headers, and the request to add one has been open against the specification for years. A browser client therefore cannot set `Authorization` or `X-API-Key` on the handshake. That forces one of four workarounds, each with a real cost:

1. **Cookies.** Sent automatically, work well — and are exactly what makes cross-site WebSocket hijacking possible, because the handshake is not protected by CORS. Requires strict `Origin` checking and `SameSite` cookies.
2. **A token in the query string.** Simple, and it lands in server access logs, proxy logs, and browser history.
3. **Abusing `Sec-WebSocket-Protocol`.** The subprotocol list is the one client-controllable header, so some designs smuggle a token through it. It works; it is a misuse of a negotiation field, and the value still appears in logs.
4. **Authenticate after connect.** Accept the socket, require an auth message as the first frame, close if it does not arrive within a timeout. The most flexible option, and it means you accept unauthenticated connections — so the pre-auth state must be resource-bounded.

#### Grounding: the Juniper WebSocket surface

`juniper-service-core` (this repository's `juniper-service-core/` subdirectory) implements three WebSocket endpoints, mounted by `juniper_service_core/websocket/router.py:46-54` (`/ws/training`, `/ws/control`) and `:79-81` (`/ws/workers`). `juniper-cascor` registers the same three at `src/api/app.py:664-666`, with the worker channel at `/ws/v1/workers`.

**Middleware does not run — and the code says so.** The shared authenticator carries the reason in its docstring: `juniper_service_core/websocket/manager.py:60-61` — "``BaseHTTPMiddleware`` cannot intercept WebSocket upgrades, so each WS endpoint must authenticate independently." The function reads `APIKeyAuth` off `app.state`, checks the `X-API-Key` header, and closes with **4001** on failure (`manager.py:69-75`).
This is the single most portable lesson in the whole section: every HTTP protection you have is off by default on the WebSocket path, and you must re-add each one by hand.

**Origin, with opposite polarity on two endpoints of the same service.** This is the detail worth memorising, because it shows that "validate Origin" is not one rule:

- `/ws/control` is a **browser** endpoint. `websocket/control_security.py:34-50` normalises the header (`rstrip("/").lower()`), rejects a **missing** Origin fail-closed — `:43-45`, logging "no Origin header -- rejecting (fail-closed)" — and otherwise requires membership in an allowlist. The rejection closes **4003** at `control_stream.py:118`.
- `/ws/workers` is a **machine-to-machine** endpoint. `websocket/worker_stream.py:121-124` rejects **any** Origin at all: "Reject connections with an Origin header (workers are machine-to-machine, not browsers)", closing **4003**.

Same close code, opposite predicate. A browser presenting no Origin is a forgery; a worker presenting one is a browser that has no business here. Both use the 4000-4999 private-use range correctly per RFC 6455 §7.4.2.

**Parse success is not shape success.** `control_stream.py:196-209` handles two distinct failures. A `json.JSONDecodeError` acks `"Invalid JSON"` and closes 1003. But `json.loads("[]")` *succeeds*, and `[].get(...)` would raise `AttributeError` inside the command handler — tearing down the receive loop instead of rejecting one message.
So a JSON-valid non-object is explicitly rejected: `:206-209` acks `"Invalid control message"` and closes 1003, with the comment at `:203-205` naming the mechanism. The worker channel does the same at `worker_stream.py:219-222`, closing **4008** rather than registering. Two different acknowledgement strings for two different failures is the right level of precision: a client can distinguish "your bytes were not JSON" from "your JSON was not a command".

**A rejection path that must not itself fail.** `control_security.py:80-92` is a small masterpiece of defensive reasoning. The leaky bucket's `retry_after` property divides the token deficit by the refill rate. Configuring `ws_control_rate_limit_per_sec=0` builds `refill_rate=0.0` — and the comment at `:86-88` records what happened without the guard: dividing "the deficit by that crashed the control handler instead of acking `rate_limited`".
A `ZeroDivisionError` raised inside the command handler propagates out of the receive loop and kills the connection. The guard at `:89-90` returns `3600.0` — back off hard — so a configuration that means "deny everything" denies commands instead of destroying the channel. **The code path that handles rejection must be more robust than the code path it protects**, because it runs precisely when the system is under stress.

**Authorization before deserialization.** On the worker channel, `juniper_service_core/workers/coordinator.py:305-318` checks that the result belongs to this worker and that the task was assigned to it *before* calling `self._protocol.parse_result(...)` at `:321`. An unauthorized envelope therefore cannot burn a parse side-effect on a task it does not own.

**A size cap that allocates first.** `worker_stream.py:322-333` receives one binary frame per declared attachment and checks `len(raw_bytes) > _MAX_BINARY_SIZE` (100 MB, `:72`) — *after* `await websocket.receive()` has fully materialised the frame in memory. And the cap is per frame, so total memory for one result is `len(attachment_names) × 100 MB`.
This is exactly the bypass that HTTP streaming caps exist to prevent, reappearing on the other transport: `juniper_service_core/middleware.py:107-118` carefully stream-caps HTTP bodies rather than trusting `Content-Length`, and the WebSocket path then trusts the frame it already read.

And the cleanest instance of that failure class is not on the WebSocket path at all — it is on the HTTP path of this primer's main example. juniper-data does not use the shared middleware; it carries its own `RequestBodyLimitMiddleware` (`juniper_data/api/middleware.py:72-83`) whose entire check is `if content_length is not None and int(content_length) > self._max_bytes` (`:81`).
A chunked request that sends no `Content-Length` makes the first conjunct false, so the comparison never runs and the body streams straight past the 10 MB limit. Confirmed by running it: an 11 MB chunked body was read in full and surfaced as a 422 JSON-decode error, never a 413. The unguarded `int(...)` is a second defect on the same line — `Content-Length: abc` raises `ValueError` inside the middleware and becomes a 500, where the shared copy returns a 400.
Read the two side by side and the shape is a diverged fork: service-core's version carries the fix *and* a comment naming this exact bypass — a chunked stream with no `Content-Length` "must still hit the cumulative cap; skipping the stream when CL is present-and-small is the classic bypass" — and the local copy never received it. Two copies of one security control, only one fixed, is worse than a single unfixed copy — because the fixed one is what a reviewer finds when they go looking.

**Reconnection done properly.** `websocket/training_stream.py:222-263` implements a resume handshake worth copying. The client sends `{"type": "resume", "data": {"last_seq": N, "server_instance_id": "..."}}`.
The server (i) rejects a malformed frame (`:228-234`), (ii) compares the instance id and fails with reason `server_restarted` on mismatch (`:237-243`) — because a restarted server's sequence numbers mean something different, (iii) replays from the bounded buffer or fails with `out_of_range` if the client fell too far behind (`:245-253`), and (iv) on success sends `resume_ok` with a replayed count before the events.
The manager assigns monotonic sequence numbers under a lock and buffers into a bounded `deque` (`websocket/manager.py:120-124`, `:349-362`).

Three properties make this correct rather than merely present: the sequence numbers are server-assigned and monotonic; the buffer is bounded, so a slow client cannot exhaust memory; and falling off the end of the buffer is an *explicit, named* failure rather than a silent gap. A resume protocol that silently returns whatever it still has is worse than none, because the client believes it is up to date.

#### Heartbeats, and one place the Juniper implementation departs from the specification

RFC 6455 §5.5.2 defines a Ping control frame (opcode 0x9) — "A Ping frame may serve either as a keepalive or as a means to verify that the remote endpoint is still responsive" — and it is §5.5.2, not §5.5.3, that carries the obligation to answer one: "Upon receipt of a Ping frame, an endpoint MUST send a Pong frame in response, unless it already received a Close frame."
§5.5.3 defines the Pong (0xA) and adds only the identical-payload rule — a Pong "must have identical" application data, lowercase, not a normative MUST — and permits an unsolicited Pong as "a unidirectional heartbeat".

`juniper-service-core` implements its heartbeat at the **JSON application layer** instead: `control_stream.py:159-176` sends `{"type": "ping", "ts": ...}` every `ws_heartbeat_interval_sec` (default 30) and waits `ws_heartbeat_pong_timeout_sec` (default 10) for a `{"type": "pong"}` message routed at `:211-213`.
This is a defensible choice — the browser `WebSocket` API exposes no way to send a protocol-level ping or observe a pong, so a browser client *cannot* participate in RFC 6455 heartbeats. An application-level heartbeat is the only kind a browser can implement.

The departure was in the close code. On heartbeat timeout, `control_stream.py` called `websocket.close(code=1006, ...)` — at two sites, the control and training streams.

RFC 6455 §7.4.1 says of 1006: "1006 is a reserved value and **MUST NOT** be set as a status code in a Close control frame by an endpoint. It is designated for use in applications expecting a status code to indicate that the connection was closed abnormally." A conforming choice is 1011 (unexpected condition), 1001 (going away), or a private-use 4xxx code.

**This was found by writing this section, and is now fixed** (juniper-ml#1081, which closes both sites with 1011 and the timeout in the reason). It is worth keeping as a worked example for two reasons.

First, `juniper-cascor` had already hit this in production and fixed its own copies months earlier — the shared implementation simply never received the fix. That is the same propagation failure [I.7](#i7-idempotency-retries-and-the-exactly-once-illusion) describes for retry policy, in a different subsystem.

Second, the practical consequence is worse than the spec violation: the `websockets` server under uvicorn refuses to serialize 1006, so the close frame never reached the peer at all, and the client was left on a silent half-open socket with no code and no reason string.
(`control_stream.py:100` also uses 1013, which is not among RFC 6455 §7.4.1's defined codes — it is a later IANA registration in the 1000-2999 protocol range, which §7.4.2 reserves for exactly that purpose, so this one is fine.)

This is the kind of defect that never shows up in testing: most client libraries treat any close as a close, and 1006 is what they would have reported anyway. It bites a client that branches on the code — and, more sharply, a supervisor waiting for a *reason* it will now never receive. Note what actually caught it: not a test, but reading the code against the specification while writing this section. The tests all passed, because they asserted the code the handler sent rather than the code the wire could carry.

#### Judgement Calls

**Do you actually need push?** Ask what latency the user perceives. If a 10-second delay is invisible, poll; you will keep `ETag` caching, every proxy will work, and there is no connection state to manage. Push infrastructure is a real operational commitment.

**One direction or two?** If the client only needs to *receive*, SSE gives you automatic reconnection with resumption and works over plain HTTP. Choosing WebSockets for a one-way stream means writing reconnection, backoff, and resumption yourself — which is exactly what `training_stream.py:222-263` had to do.

**Is the client a browser?** It determines the authentication design (no custom headers) and the heartbeat design (no protocol-level ping). Both constraints vanish for a server-side client.

**Server-to-server across an organisational boundary?** Webhooks, almost always. Persistent connections across a boundary you do not control are fragile; a retried HTTP POST is not.

**What is the fan-out?** SSE and WebSockets both hold one connection per client. Ten thousand concurrent clients is a capacity design problem, not a code problem, and the answer usually involves a pub/sub tier rather than more application processes.

#### Tradeoffs

| Concern                 | Polling            | Long-poll        | SSE                                                               | WebSocket                                           | Webhook              |
|-------------------------|--------------------|------------------|-------------------------------------------------------------------|-----------------------------------------------------|----------------------|
| Latency                 | interval/2 average | near-immediate   | near-immediate                                                    | near-immediate                                      | near-immediate       |
| Server connections held | none               | one per client   | one per client                                                    | one per client                                      | none                 |
| Direction               | pull               | pull             | server → client                                                   | both                                                | server → client      |
| Binary payloads         | yes                | yes              | no (encode)                                                       | yes                                                 | yes                  |
| Automatic reconnect     | n/a                | client re-issues | **built in**                                                      | you write it                                        | server retries       |
| Resumption              | n/a                | none             | `Last-Event-ID`                                                   | you build it                                        | delivery attempt log |
| HTTP caching            | **yes**            | no               | no                                                                | no                                                  | n/a                  |
| Middleware applies      | yes                | yes              | yes                                                               | **request/response middleware: no**; pure-ASGI: yes | yes                  |
| Proxy friendliness      | perfect            | timeout fights   | good                                                              | needs upgrade support                               | perfect              |
| Auth from a browser     | headers fine       | headers fine     | cookie/query with `EventSource`; headers if you drop to `fetch()` | cookie/query/subprotocol/post-connect               | n/a                  |

#### Best Practices

- Start with polling. Move up only when a measurement, not an intuition, says the latency matters.
- Prefer SSE for one-way streams to browsers. `Last-Event-ID` resumption for free is worth more than most teams expect.
- Send a heartbeat, and make it bidirectional. A TCP connection through a NAT can be dead for minutes before either end notices. `control_stream.py:159-176` is the pattern: ping on an interval, close on missing pong.
- Set an idle timeout independent of the heartbeat. `control_stream.py:183-190` closes with 1000 and reason "Idle timeout" after `ws_control_idle_timeout_sec` (default 120) with no inbound frame.
- Re-implement every middleware protection inside the WebSocket handler: authentication, rate limiting, message-size caps, origin checking, logging. `control_stream.py:218-223` documents its gate order explicitly — "kill switch -> handshake cooldown (IP block) -> API-key auth -> Origin allowlist -> per-connection leaky-bucket rate limiting -> bidirectional idle timeout".
- Bound the message size *before* you allocate. The 64 KB JSON cap at `control_stream.py:192-194` is checked on a string already in memory; a genuinely defensive implementation caps at the framing layer.
- Reject a JSON-valid non-object explicitly. `json.loads("[]")` succeeds and the next `.get()` raises.
- Use 4000-4999 for application-defined close codes unless you are registering them with IANA (RFC 6455 §7.4.2).
- Add jitter to reconnect backoff. Every client reconnecting at exactly 5 seconds after a deploy is a self-inflicted thundering herd.
- Never trust `Origin` from a non-browser client (RFC 6455 §1.6).
- For webhooks: sign the request body, include a timestamp, reject stale signatures, and make delivery idempotent with an event id — the receiver *will* get duplicates.

#### Common Failure Modes

**Proxy idle timeouts killing quiet connections.** The single most common WebSocket and SSE deployment problem. A load balancer with a 60-second idle timeout drops any connection with nothing to say. Fixed by heartbeats at an interval below the shortest timeout in the path — which means knowing what that is.

**Reconnect storms.** Server restarts; every client reconnects simultaneously; the server falls over; repeat. Requires jittered exponential backoff on the client and connection-rate limiting on the server. `control_stream.py:103-108` implements the server half: a `HandshakeCooldown` blocks an IP after repeated rejected handshakes (default 10 rejections in 60 s → a 300 s block, `control_security.py:106`).

**Silent message loss on reconnect.** The client reconnects and misses everything sent while disconnected, without knowing. Only fixable with sequence numbers plus a replay buffer plus an explicit out-of-range failure — the `training_stream.py` design.

**No backpressure.** A slow consumer causes the server's send queue to grow without bound until memory is exhausted. The server must bound per-connection queues and decide what to do when full: drop oldest, drop newest, or close the connection. Choosing nothing means choosing "run out of memory".

**Authentication on the HTTP path only.** Middleware protects `/v1/*` and the WebSocket endpoint is wide open, because nobody realised the upgrade skips *request/response* middleware. A pure-ASGI authentication layer would have covered both scopes; a `BaseHTTPMiddleware` subclass never will, however carefully it is written.

**Ordering assumptions across reconnects.** Messages are ordered *within* a connection. Across a reconnect, ordering is whatever your resume logic makes it.

**A memory cap enforced after allocation.** `worker_stream.py:322-333`, discussed above. The check is correct and the allocation already happened.

#### Error Handling

WebSocket error handling has three distinct layers, and conflating them produces the classic "connection keeps dropping and we don't know why".

1. **Handshake failures** happen while it is still HTTP, so they are HTTP status codes. RFC 6455 §10.2 recommends `403 Forbidden` for an unacceptable Origin. In practice many frameworks — Juniper included — accept the socket and then close it with a code instead, which is easier to implement and harder for the client to distinguish from a network failure. `control_stream.py:97-121` closes rather than returning a status for every gate.
2. **Protocol failures** are Close frames with a status code. Use the specific one: 1003 for an unacceptable data type, 1009 for a message too large, 1008 for a policy violation, 1011 for an unexpected server condition. Never 1005, 1006, or 1015 (RFC 6455 §7.4.1).
3. **Application failures** should be messages, not closes. `control_stream.py:124-156` gets this right: an unknown command, a rate-limited command, a command timeout, and an executor exception all send a `command_response` ack and **keep the connection open**. Only malformed framing closes it. Tearing down a connection because one command was invalid forces a reconnect, which costs more than the error did.

One further distinction in the same handler is worth copying. `control_stream.py:150-156` splits expected control errors from unexpected ones: `ValueError` and `RuntimeError` — bad parameters, invalid state transitions — are surfaced to the client with their message, while a bare `Exception` is logged server-side and returned as the opaque string "Command execution failed". The caller learns what they can act on; internal detail stays internal.

RFC 6455 §10.7 states the general obligation: "Incoming data MUST always be validated by both clients and servers", and if invalid data arrives after a successful handshake, "the endpoint SHOULD send a Close frame with an appropriate status code... before proceeding to _Close the WebSocket Connection_. Use of a Close frame with an appropriate status code can help in diagnosing the problem."

---

### I.5 Authentication and Authorization

#### Overview

Two questions, routinely merged into one word:

- **Authentication (AuthN)**: who is making this request? Answered by a credential — a key, a token, a certificate, a signature.
- **Authorization (AuthZ)**: is this principal allowed to do this specific thing to this specific resource? Answered by a policy evaluated against the principal, the action, and the object.

HTTP encodes the distinction in its status codes. RFC 9110 §15.5.2: `401 (Unauthorized)` "indicates that the request has not been applied because it lacks valid authentication credentials for the target resource", and the server "MUST send a `WWW-Authenticate` header field... containing at least one challenge".
RFC 9110 §15.5.4: `403 (Forbidden)` "indicates that the server understood the request but refuses to fulfill it", and "If authentication credentials were provided in the request, the server considers them insufficient to grant access. The client SHOULD NOT automatically repeat the request with the same credentials."

So: 401 means "I don't know who you are, try again with credentials"; 403 means "I know who you are and the answer is no". A 401 without `WWW-Authenticate` is non-conformant, and it is extremely common.

RFC 9110 §15.5.4 adds a useful escape: "An origin server that wishes to 'hide' the current existence of a forbidden target resource MAY instead respond with a status code of 404 (Not Found)." When resource existence is itself sensitive, 404 is the correct answer, not a lie.

#### Background

The mechanisms, roughly in order of increasing capability and cost:

**API keys.** A long random string, sent in a header, compared against a stored set. There is no standard — no RFC defines `X-API-Key`; it is a widespread convention. What they are genuinely good for: identifying a *service* rather than a user; attributing usage for quotas and billing; enabling per-client revocation without touching a user database; and being trivially implementable by every client in every language.
What they are bad at: they are bearer credentials with no expiry, no audience restriction, no scope, and no proof of possession. Anyone who reads one has it, forever, until someone notices.

**HTTP Basic.** Base64 of `user:password` in the `Authorization` header. Base64 is encoding, not encryption. RFC 9205 §4.12 is blunt about it, though note that it is restating rather than imposing — the sentence opens "Per [RFC7617],": "the Basic authentication scheme is not suitable for protecting sensitive or valuable information unless the channel is secure (e.g., using the `https` URI scheme)."

**Bearer tokens.** [RFC 6750](https://www.rfc-editor.org/rfc/rfc6750.html) §2.1: `Authorization: Bearer <token>`. "Clients SHOULD make authenticated requests with a bearer token using the `Authorization` request header field with the `Bearer` HTTP authorization scheme. Resource servers MUST support this method." The token is opaque to the client. Its defining weakness is in the name — possession is sufficient.

RFC 6750 §2.3 also defines a URI query-parameter method, and immediately disowns it: "Because of the security weaknesses associated with the URI method... including the high likelihood that the URL containing the access token will be logged, it SHOULD NOT be used unless it is impossible to transport the access token in the `Authorization` request header field or the HTTP request entity-body."
[RFC 9700](https://www.rfc-editor.org/rfc/rfc9700.html) §4.3.2 upgrades this to a prohibition: "Clients MUST NOT pass access tokens in a URI query parameter in the way described in Section 2.3 of [RFC6750]."

**JWT.** [RFC 7519](https://www.rfc-editor.org/rfc/rfc7519.html) defines a compact, signed (JWS) or encrypted (JWE) claims format: three base64url segments separated by dots. Registered claims (§4.1) include `iss`, `sub`, `aud`, `exp`, `nbf`, `iat`, and `jti`. A JWT is a *format*, not a protocol — "JWT auth" describes a serialization, not an architecture.

**OAuth 2.0.** [RFC 6749](https://www.rfc-editor.org/rfc/rfc6749.html) is a *delegation* framework: it lets a resource owner grant a client limited access to their resources without sharing credentials. It is not a login protocol.

**OIDC.** OpenID Connect is an identity layer on top of OAuth 2.0, adding an `id_token` (a JWT about the *user*) and a `userinfo` endpoint. This is the login protocol. Using a raw OAuth access token as proof of identity is a known anti-pattern — the token says what the bearer may do, not who they are.

**mTLS.** Both sides present certificates during the TLS handshake. Strong, and the credential is bound to the connection rather than carried in the message — which is also its limitation. RFC 9205 §4.12: certificate authentication "is intrinsically scoped to the underlying transport connection. As a result, a client has no way of knowing whether the authenticated status was used in preparing the response... and the only way to obtain a specifically unauthenticated response is to open a new connection."

**HMAC request signing.** The client signs a canonicalised representation of the request; the server recomputes. [RFC 9421](https://www.rfc-editor.org/rfc/rfc9421.html) standardises this with `Signature-Input` and `Signature` fields.
Its motivating argument (§1) is precise: "TLS only guarantees these properties over a single TLS connection, and the path between the client and application may be composed of multiple independent TLS connections (for example, if the application is hosted behind a TLS-terminating gateway or if the client is behind a TLS Inspection appliance). In such cases, TLS cannot guarantee end-to-end message integrity or authenticity."
Signatures also give you replay protection and non-repudiation, which bearer tokens cannot.

#### OAuth 2.0: which grants survive

RFC 9700 (BCP 240, January 2025) **updates RFC 6749, RFC 6750, and RFC 6819** and is the current statement of best practice. Its §1 closes by noting that "OAuth 2.1, under development as [OAUTH-V2.1], will incorporate security recommendations from this document" — so RFC 9700 is the best available approximation of OAuth 2.1 today. Quote it rather than recalling folklore.

RFC 6749 §1.3 defines four grants. Their status under RFC 9700:

| Grant                               | RFC 6749     | RFC 9700 status                                                                                                                                                                                               |
|-------------------------------------|--------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Authorization code                  | §1.3.1, §4.1 | **Recommended**, with PKCE mandatory for public clients                                                                                                                                                       |
| Implicit                            | §1.3.2, §4.2 | **Discouraged** — "clients SHOULD NOT use the implicit grant... unless access token injection in the authorization response is prevented and the aforementioned token leakage vectors are mitigated" (§2.1.2) |
| Resource owner password credentials | §1.3.3, §4.3 | **Prohibited** — "MUST NOT be used" (§2.4)                                                                                                                                                                    |
| Client credentials                  | §1.3.4, §4.4 | Fine for machine-to-machine; there is no user to delegate                                                                                                                                                     |

The reasoning, quoted rather than paraphrased:

On **implicit** (§2.1.2): the grant and "other response types causing the authorization server to issue access tokens in the authorization response are vulnerable to access token leakage and access token replay".
Further, "no standardized method for sender-constraining exists to bind access tokens to a specific client... when the access tokens are issued in the authorization response. This means that an attacker can use the leaked or stolen access token at a resource endpoint."
The remedy: "Clients SHOULD instead use the response type `code`... This allows the authorization server to detect replay attempts by attackers and generally reduces the attack surface since access tokens are not exposed in URLs."

On **ROPC** (§2.4): "The resource owner password credentials grant MUST NOT be used. This grant type insecurely exposes the credentials of the resource owner to the client. Even if the client is benign, usage of this grant results in an increased attack surface (i.e., credentials can leak in more places than just the authorization server) and in training users to enter their credentials in places other than the authorization server."
It also notes the grant "is not designed to work with two-factor authentication" and is incompatible with origin-bound cryptographic credentials such as WebAuthn.

#### PKCE

[RFC 7636](https://www.rfc-editor.org/rfc/rfc7636.html) — Proof Key for Code Exchange — closes authorization-code interception. The client generates a high-entropy `code_verifier`, sends its hash as `code_challenge` with the authorization request, and presents the verifier at the token endpoint. An attacker who intercepts the code cannot redeem it.

RFC 7636 §4.1 specifies the verifier: "high-entropy cryptographic random STRING using the unreserved characters `[A-Z] / [a-z] / [0-9] / "-" / "." / "_" / "~"`... with a minimum length of 43 characters and a maximum length of 128 characters", and recommends deriving it from "a 32-octet sequence" base64url-encoded.
§4.2 defines two transformations — `plain` and `S256` (`BASE64URL-ENCODE(SHA256(ASCII(code_verifier)))`) — and requires: "If the client is capable of using `S256`, it MUST use `S256`, as `S256` is Mandatory To Implement (MTI) on the server."

RFC 9700 §2.1.1 hardens this considerably. "Public clients MUST use PKCE"; for confidential clients its use is "RECOMMENDED"; "Authorization servers MUST support PKCE"; and — the downgrade defence — "Authorization servers MUST mitigate PKCE downgrade attacks by ensuring that a token request containing a `code_verifier` parameter is accepted only if a `code_challenge` parameter was present in the authorization request."
It also disposes of the myth that PKCE is a mobile feature: "Note: Although PKCE was designed as a mechanism to protect native apps, this advice applies to all kinds of OAuth clients, including web applications."

Two more RFC 9700 §2.1 requirements are easy to get wrong: redirect URIs must be matched by "exact string matching except for port numbers in localhost redirection URIs of native apps", and clients "MUST prevent Cross-Site Request Forgery" — though "Clients that have ensured that the authorization server supports PKCE MAY rely on the CSRF protection provided by PKCE", which is why modern flows can drop the separate `state` CSRF token.

#### Token handling: storage, restriction, rotation

**Restrict the token.** RFC 9700 §2.3: "The privileges associated with an access token SHOULD be restricted to the minimum required... In particular, access tokens SHOULD be audience-restricted to a specific resource server or, if that is not feasible, to a small set of resource servers",
and "every resource server is obliged to verify, for every request, whether the access token sent with that request was meant to be used for that particular resource server. If it was not, the resource server MUST refuse to serve the respective request."

**Sender-constrain it.** RFC 9700 §2.2.1: "Authorization and resource servers SHOULD use mechanisms for sender-constraining access tokens, such as mutual TLS for OAuth 2.0 [RFC8705] or OAuth 2.0 Demonstrating Proof of Possession (DPoP) [RFC9449]... to prevent misuse of stolen and leaked access tokens." This is the structural fix for bearer semantics: the token alone stops being enough.

**Rotate refresh tokens.** RFC 9700 §2.2.2: "Refresh tokens for public clients MUST be sender-constrained or use refresh token rotation."
§4.14.2 describes rotation's detection property precisely: "the authorization server issues a new refresh token with every access token refresh response. The previous refresh token is invalidated... If a refresh token is compromised and subsequently used by both the attacker and the legitimate client, one of them will present an invalidated refresh token, which will inform the authorization server of the breach.
The authorization server cannot determine which party submitted the invalid refresh token, but it will revoke the active refresh token. This stops the attack at the cost of forcing the legitimate client to obtain a fresh authorization grant."
Note what rotation does and does not buy: it *detects* theft after the fact and limits the window. It does not prevent it.

**Browser storage.** There is no comfortable option. `localStorage` is readable by any script on the origin, so one XSS is total compromise and the token survives a tab close. `sessionStorage` narrows the lifetime, not the XSS exposure. An in-memory variable is the best of the script-accessible options and is lost on refresh. An `HttpOnly; Secure; SameSite` cookie is invisible to script but is sent automatically, which reintroduces CSRF for state-changing requests.
The pattern with the best properties today is the BFF (backend-for-frontend): tokens live server-side, the browser holds only a session cookie, and the frontend never sees a token at all. RFC 9700 §2.1 requires CSRF protection regardless of storage choice.

#### JWT validation: what libraries will not do for you

RFC 7519 §7.2 defines only *structural* validation — that the token parses, that the header is valid JSON, that the signature verifies. It ends with a warning that is easy to skim past: "note that it is an application decision which algorithms may be used in a given context. Even if a JWT can be successfully validated, unless the algorithms used in the JWT are acceptable to the application, it SHOULD reject the JWT."

The semantic checks are the application's job. [RFC 9068](https://www.rfc-editor.org/rfc/rfc9068.html) §4 enumerates them for OAuth access tokens, and it is the best available checklist:

- "The resource server MUST verify that the `typ` header value is `at+jwt` or `application/at+jwt` and reject tokens carrying any other value." This alone prevents ID-token-as-access-token confusion.
- "The issuer identifier for the authorization server... MUST exactly match the value of the `iss` claim."
- "The resource server MUST validate that the `aud` claim contains a resource indicator value corresponding to an identifier the resource server expects for itself. The JWT access token MUST be rejected if `aud` does not contain a resource indicator of the current resource server as a valid audience."
- "The resource server MUST reject any JWT in which the value of `alg` is `none`."
- "The current time MUST be before the time represented by the `exp` claim. Implementers MAY provide for some small leeway, usually no more than a few minutes, to account for clock skew."

The classic pitfalls map one-to-one onto that list:

**`alg: none`.** RFC 7519 §6 defines Unsecured JWTs — "a JWS using the `alg` Header Parameter value `none` and with the empty string for its JWS Signature value". Legitimate when the token is protected by other means; catastrophic when a verifier accepts it because it read `alg` out of the untrusted header and dispatched on it.

**Algorithm confusion.** A verifier configured with an RSA public key, asked to verify a token whose header says `HS256`, may use that *public* key as an HMAC secret. The public key is public. The attacker forges tokens at will. The fix is to pin the expected algorithm in your verifier configuration and never take it from the token.

**Missing `aud`.** A token minted for service A is replayed against service B. Both verify the signature — same issuer, same key — and both accept it. This is the most common real-world JWT failure, and it is why RFC 9700 §2.3 makes audience restriction a `SHOULD` at the issuer and RFC 9068 §4 makes checking it a `MUST` at the resource server.

**Missing `iss`.** With multiple identity providers configured, a token from the wrong one validates.

**Clock skew.** Rejecting a token issued two seconds ago because the issuer's clock is ahead. RFC 9068 §4's guidance — leeway of "no more than a few minutes" — is the right shape: some, bounded.

**Revocation.** The hard one. A signed, self-contained token is valid until `exp` by construction; there is no state to change. Every mitigation is a partial retreat from statelessness: short expiry plus refresh, a denylist of `jti` values, or introspection. See the controversy below.

```python
import time

REQUIRED_CLAIMS = ("iss", "aud", "exp")

class TokenError(Exception):
    """Raised when an access token fails a semantic validation check."""

def assert_access_token(header: dict, claims: dict, *, issuer: str, audience: str, leeway: int = 60) -> None:
    """The checks a JWT library will not make for you -- RFC 9068 §4."""
    alg = header.get("alg")
    if alg is None or alg == "none":
        raise TokenError("unsecured or missing alg")
    if header.get("typ") not in ("at+jwt", "application/at+jwt"):
        raise TokenError("not an OAuth 2.0 access token")
    missing = [name for name in REQUIRED_CLAIMS if name not in claims]
    if missing:
        raise TokenError(f"missing claims: {missing}")
    if claims["iss"] != issuer:
        raise TokenError("issuer mismatch")
    aud = claims["aud"]
    if audience not in (aud if isinstance(aud, list) else [aud]):
        raise TokenError("audience mismatch")
    if time.time() > float(claims["exp"]) + leeway:
        raise TokenError("expired")
```

Note that the algorithm is checked but not *selected* here — the caller must have pinned it before verifying the signature. Checking `alg` after verification is too late.

#### Grounding: API keys in Juniper

`juniper-service-core/juniper_service_core/security.py` is the shared implementation, and it gets three things right that are easy to get wrong.

**Constant-time comparison, and a divergence worth reading carefully.** A naive `api_key in self._api_keys` on a set leaks timing through hashing and comparison; `hmac.compare_digest` does not short-circuit on the first differing byte. Both Juniper implementations use it, but they differ in how they iterate — and the difference is a good test of whether you can reason about what a timing side channel actually reveals.

`juniper-service-core/juniper_service_core/security.py:65` short-circuits on a match:

```python
return any(hmac.compare_digest(api_key, k) for k in self._api_keys)
```

`juniper-data/juniper_data/api/security.py:80-84` deliberately does not, and its comment (`:75-79`) argues the point:

```python
matched = False
for candidate in self._api_keys:
    if hmac.compare_digest(api_key, candidate):
        matched = True
return matched
```

Which is right? The attack that matters is an attacker with no valid key trying to recover one. Against that attacker the two forms are identical: **every non-matching guess costs all N comparisons**, so there is no timing gradient to climb. `any()` returns early only when a key *does* match — which reveals the matched key's position in the server's list, to a caller who already holds that key. That is a weak information disclosure, not a credential leak.

So service-core's form is defensible and juniper-data's is belt-and-braces. The lesson is not "always accumulate"; it is that a side-channel argument has to name the attacker and the quantity leaked before it can be evaluated. A reviewer who flags `any()` here without that analysis is pattern-matching, and a reviewer who dismisses the concern without it is guessing.
The `juniper-data` copy makes the same choice for the same reason and *documents* it — `juniper_data/api/security.py:51-54` keeps keys in a list rather than a set specifically "because validate() compares against each key with hmac.compare_digest to eliminate the timing side-channel that a `value in set` membership test would leak".

**Blank keys must not enable auth.** `security.py:42-45` filters before enabling:

```text
self._api_keys: set[str] = {k for k in (api_keys or []) if isinstance(k, str) and k.strip()}
self._enabled = len(self._api_keys) > 0
```

The comment at `:42-43` names the failure it prevents: "``APIKeyAuth([""])`` must stay disabled, not authenticate a missing/empty header via compare_digest("", "")". An empty secrets file would otherwise switch authentication *on* in a mode that accepts an empty key — worse than leaving it off, because the deployment believes it is protected.

**The `juniper-data` copy has not adopted that fix.** `juniper_data/api/security.py:54` reads `self._api_keys: list[str] = list(dict.fromkeys(api_keys)) if api_keys else []` — de-duplication only, no blank filter. And the settings validator is inconsistent about it: `juniper_data/api/settings.py:159` filters blanks on the comma-separated-string branch (`[k.strip() for k in v.split(",") if k.strip()]`) while `:160` returns a list value untouched.
So `JUNIPER_DATA_API_KEYS='[""]'` parses to `['']`, enables authentication, and validates the empty string. This is a genuinely instructive bug shape: **the same input takes two code paths and only one sanitises it.**

**Auth runs before rate limiting — correct, and incomplete.** `juniper_service_core/middleware.py:176-180`:

```text
if self._api_key_auth.enabled:
    api_key = await self._api_key_auth(request)

if self._rate_limiter.enabled:
    await self._rate_limiter(request, api_key)
```

The ordering is right, and it is usually justified with two reasons that are really one. The limiter's bucket key *depends on the auth result* — `security.py:172-175` returns `f"key:{api_key}"` when authenticated and `f"ip:{client_ip}"` otherwise.

Limiting first would therefore force every caller into an IP-keyed bucket, collapsing everyone behind one NAT together *and* letting an unauthenticated attacker spend a legitimate caller's budget. Those are the same mechanism seen from two sides, not two independent arguments.

What the ordering *costs* is the part worth volunteering. Because an authentication failure raises before `self._rate_limiter(...)` is ever reached, **the entire 401 path was unthrottled**: credential guessing and garbage-credential floods consumed no tokens at all. This too was found by writing this section, and is now fixed (juniper-ml#1082) — but the gap is worth understanding, because the ordering that causes it is the ordering everyone recommends.

The fix is not to reorder — that trades a real protection for a worse one — but to run *two* limiters: a coarse IP-keyed one ahead of authentication so failed auth is throttled, and the identity-keyed one after. [I.6](#i6-rate-limiting-quotas-and-backpressure) develops this.

**A consequence of middleware-based auth: no OpenAPI security scheme.** Because authentication lives in middleware rather than in a FastAPI dependency, `juniper-data` instantiates `APIKeyHeader` at `juniper_data/api/security.py:26` and never wires it into any route. The generated OpenAPI document therefore contains no `securitySchemes` and no `security` requirement on any operation.
Authentication is invisible to schema consumers and to code generators — a client generated from the document will not send the key.

**And the documentation disappears when you secure the service.** `juniper_data/api/app.py:91` computes `docs_enabled = not settings.api_keys`, feeding `docs_url`, `redoc_url`, and `openapi_url` at `:97-99`. Configuring any API key removes `/docs`, `/redoc`, **and `/openapi.json`** entirely. There is no authenticated-docs path, so code generation against a secured deployment is impossible. The instinct — don't expose the schema publicly — is sound; the implementation conflates "public" with "existing".

#### Judgement Calls

**Do you need OAuth at all?** OAuth 2.0 solves *delegation*: a third party acting on a user's behalf. If your API is called only by your own frontend, or only by machines you operate, you do not have a delegation problem, and adopting an authorization server buys operational complexity for a scenario you do not have. Client credentials or a well-managed API key is the honest answer for internal service-to-service traffic.

**Where do you enforce authorization?** Middleware is the wrong layer for anything resource-specific — it sees the path, not the object. `juniper-service-core` puts authentication in middleware (correct: it is uniform) and has no authorization layer at all (correct for its threat model: a research service where every valid key is fully trusted). The moment two callers need different permissions, that must move to the handler or a dependency, where the resource is in scope.

**Stateless or stateful?** See the controversy below. The deciding question is how fast you must be able to revoke.

**Symmetric or asymmetric signing?** HMAC (`HS256`) requires every verifier to hold the signing secret — so every resource server can *mint* tokens. Asymmetric (`RS256`, `ES256`) lets verifiers hold only a public key. RFC 9068 §4 makes the recommendation for access tokens: "it is RECOMMENDED here that authorization servers sign JWT access tokens with an asymmetric algorithm."
RFC 9700 §2.5 extends the same reasoning to client authentication: asymmetric methods mean "authorization servers do not need to store sensitive symmetric keys, making these methods more robust against leakage of keys."

**Is the caller a browser?** It reshapes everything. No custom headers on WebSocket or `EventSource` (I.4). Token storage has no good option. CSRF becomes a live concern the moment credentials are ambient.

#### Tradeoffs

| Mechanism                     | Revocation                 | Scoping                | Replay protection               | Client complexity | Best fit                                    |
|-------------------------------|----------------------------|------------------------|---------------------------------|-------------------|---------------------------------------------|
| API key                       | immediate (delete it)      | none built in          | none                            | trivial           | machine-to-machine, quotas                  |
| HTTP Basic                    | change the password        | none                   | none                            | trivial           | legacy, internal, over TLS only             |
| Opaque bearer + introspection | immediate                  | server-side            | none                            | low               | when revocation must be fast                |
| JWT access token              | hard (see below)           | claims                 | none                            | low               | high-volume, short-lived                    |
| OAuth 2.0 + OIDC              | via refresh + short expiry | scopes, audience       | none by default                 | high              | third-party delegation, SSO                 |
| mTLS                          | CRL/OCSP; slow             | certificate attributes | connection-bound                | high (PKI)        | service mesh, high assurance                |
| HMAC signing (RFC 9421)       | rotate the key             | whatever you sign      | **yes**, with a timestamp/nonce | medium            | webhooks, non-repudiation, through gateways |

The row that surprises people is replay protection: *none* of the bearer mechanisms have it. A captured `Authorization` header is reusable until expiry. Only signing (and sender-constraining mechanisms such as mTLS or DPoP, per RFC 9700 §2.2.1) changes that.

#### Best Practices

- Use TLS everywhere. Every mechanism above except mTLS and message signing is a plaintext secret in a header.
- Send credentials in the `Authorization` header (RFC 6750 §2.1), never in a query string (RFC 9700 §4.3.2, "MUST NOT").
- Return 401 with a `WWW-Authenticate` challenge (RFC 9110 §15.5.2), 403 for an authenticated-but-refused request (§15.5.4), and consider 404 when existence is sensitive.
- Use RFC 6750 §3.1's error codes when you serve bearer tokens: `invalid_request` (400), `invalid_token` (401), `insufficient_scope` (403). Note the last one "MAY include the `scope` attribute with the scope necessary to access the protected resource" — actionable feedback.
- Compare secrets in constant time (`hmac.compare_digest`), as `juniper_service_core/security.py:65` does.
- Filter blank and whitespace-only keys *before* deciding whether authentication is enabled (`security.py:42-45`). An empty secret must never switch auth on.
- Run **two** limiters: a coarse IP- or prefix-keyed bucket *before* authentication, and the identity-keyed one after. Authenticating first is correct as far as it goes — it is what lets you key on identity at all (`middleware.py:175-186`) — but because the auth check *raises*, a single limiter placed after it never sees a failed authentication, leaving the entire 401 path unthrottled. Credential guessing then costs the attacker nothing. I.6 works through the mechanism.
- Pin the expected signing algorithm in the verifier. Never dispatch on the token's own `alg` header.
- Validate `iss`, `aud`, and `exp` on every request (RFC 9068 §4), with bounded leeway.
- Keep access tokens short-lived and audience-restricted (RFC 9700 §2.3); rotate refresh tokens for public clients (§2.2.2).
- Use PKCE with `S256` for every authorization-code flow, not just native apps (RFC 9700 §2.1.1).
- Declare your security scheme in OpenAPI. Auth enforced only in middleware is auth invisible to every generated client.
- Serve the schema behind authentication rather than not serving it — a secured deployment still needs to be code-generated against.
- Log authentication *decisions*, never credentials. Note that `RequestIdMiddleware` in `juniper-observability` propagates an inbound `X-Request-ID` verbatim with no length or charset validation (`juniper_observability/middleware/request_id.py:36-43`) — a header-injection surface if it reaches a non-JSON log sink.

#### Common Failure Modes

**401 without `WWW-Authenticate`.** Non-conformant per RFC 9110 §15.5.2, and it leaves a conforming client with no idea what scheme to use.

**401 and 403 swapped.** Returning 401 for an authorization failure invites the client to retry with the same credentials forever.

**Timing-unsafe key comparison.** `if key == stored` leaks the key one byte at a time to a patient attacker.

**A blank key enabling auth.** The `juniper-data` shape above: an empty secret file produces `enabled=True` and `validate("") == True`.

**Only one of two input paths sanitised.** Also the `juniper-data` shape: `settings.py:159` filters, `:160` does not.

**Accepting `alg: none`, or taking the algorithm from the token.** Both are total signature bypasses.

**Not checking `aud`.** Tokens minted for one service work on another. Invisible until someone tries it.

**Tokens in URLs.** Access logs, `Referer` headers, browser history, and error trackers all capture them. RFC 9700 §4.3.2 prohibits this.

**Long-lived access tokens with no revocation path.** A compromised token remains valid for its full lifetime and there is nothing you can do.

**Authorization in middleware only.** Middleware sees the path, not the object. `GET /v1/datasets/{id}` passes middleware whoever `{id}` belongs to.

**Auth invisible in the schema.** `APIKeyHeader` instantiated and never wired (`juniper_data/api/security.py:26`); generated clients omit the credential.

**Docs disabled by securing the service.** `app.py:91` — securing the deployment removes `/openapi.json`, so nobody can generate a client for the deployment that actually matters.

#### Error Handling

Authentication errors are security-relevant, so the response has two audiences with opposed interests: a legitimate client that needs to fix its request, and an attacker who wants to learn about your system.

**Be uniform to the caller, precise in the log.** "Invalid API key" and "Unknown API key" must be indistinguishable to the client; internally they are different events. `juniper_service_core/security.py:84-94` distinguishes only missing (`"Missing API key. Provide X-API-Key header."`) from invalid (`"Invalid API key."`), which is the right granularity — telling a caller the header is absent is not a leak, telling them a key exists but is expired might be.

**Do not leak existence.** RFC 9110 §15.5.4's 404-instead-of-403 option exists for this. A 403 on `/v1/datasets/{id}` confirms that dataset exists.

**Use the standard error codes when they apply.** RFC 6750 §3.1 defines exactly three for bearer tokens and pairs each with a status code.
It also handles the anonymous case explicitly: "If the request lacks any authentication information (e.g., the client was unaware that authentication is necessary or attempted using an unsupported authentication method), the resource server SHOULD NOT include an error code or other error information" — a bare `WWW-Authenticate: Bearer realm="example"` is the correct response to a request that carried no credential at all.

**Make 401 actionable and 403 final.** A 401 tells the client to acquire a credential and retry; a 403 tells it to stop. The distinction is what allows a client library to implement a token-refresh-and-retry loop safely, and it is exactly why the two must not be swapped.

**Preserve the status code as data.** The recurring Juniper client defect from I.2 applies here with sharper consequences: because status codes are formatted into exception message strings rather than attached as attributes, a caller cannot write `except AuthError as e: if e.status_code == 401: refresh()`. The refresh-and-retry loop that every OAuth client needs is not implementable against that surface.

#### Controversy: Stateless JWT vs opaque server-side sessions

**The controversy is real, long-running, and unusually heated.** It concerns whether an API's session state should live in a self-contained signed token the client carries, or in server-side storage that the client references with an opaque identifier. The heat comes from the fact that both sides are describing real production experience — of different systems.

**The camps.** The stateless camp holds that a signed JWT eliminates a network hop and a shared database from the hot path of every request, which is what makes horizontal scaling and multi-region deployment tractable. The stateful camp holds that authentication state is *inherently* mutable — users log out, get suspended, change password, have their access revoked mid-incident — and that a credential you cannot withdraw is a liability that no amount of latency saving justifies.

**Where the split came from.** Server-side sessions were the default for two decades: a session id in a cookie, session data in memory, then in a shared store as deployments scaled horizontally. That shared store became a scaling bottleneck and a single point of failure, and the mid-2010s microservices wave — where a request might traverse a dozen services, each needing to know the caller — made per-service session lookup look untenable.
JWTs, standardised as RFC 7519 in 2015, appeared to solve it: sign once, verify anywhere, no shared state. The backlash followed as teams discovered that "verify anywhere" also meant "revoke nowhere", usually during an incident. RFC 9700 §2.2 and §4.14 can be read as the standards community's considered response: keep tokens, but constrain, shorten, and rotate them.

##### The stateless (JWT) camp

**Strengths.** Verification is local — a signature check against a cached public key, no network call, no shared database. Scales horizontally without a session store, and works naturally across services and regions. Claims travel with the request, so a downstream service knows the caller without another lookup. Asymmetric signing means verifiers cannot mint tokens (RFC 9068 §4). Well-specified: RFC 7519 for the format, RFC 9068 for the OAuth access-token profile, and a mature library ecosystem.

**Weaknesses.** Revocation is genuinely hard — a valid signature is valid until `exp`. Tokens grow as claims accumulate, and they are sent on *every* request (a 2 KB token on an HTTP/1.1 API is 2 KB per request; HPACK amortises it on HTTP/2, which is a real interaction with I.2). Claims are stale by construction: a permission changed after issuance is not reflected until the next refresh.
The validation surface is wide and the failure modes are silent — `alg` confusion, missing `aud`, unpinned algorithms. Payloads are base64, not encrypted, so anything in a JWT is public unless you use JWE.

**Risks.** A compromised token is usable for its full lifetime with no way to stop it. A signing-key compromise invalidates every outstanding token and there is no incremental recovery. Teams routinely put too much in the token and then cannot change it without a re-login. The revocation problem is usually discovered during the incident where it matters.

**Guardrails.** Keep access-token lifetime short — minutes, not hours — and pair it with a refresh token; that bounds the revocation window without a lookup on the hot path. Rotate refresh tokens (RFC 9700 §2.2.2). Audience-restrict every token (§2.3). Pin the algorithm in the verifier. Validate `iss`, `aud`, `exp` per RFC 9068 §4. Keep claims minimal and stable. Plan key rotation with overlapping validity *before* you need it.
Consider sender-constraining via mTLS or DPoP (§2.2.1) so a stolen token is not enough on its own.

##### The stateful (opaque session) camp

**Strengths.** Revocation is immediate and total — delete the row, the session is gone, everywhere, now. State can change without re-issuing anything: permission changes, role changes, and forced logouts take effect on the next request. The credential is an opaque identifier carrying no information, so nothing leaks if it is logged or captured. The token is small. Server-side session data can hold whatever you need without bloating requests.
You can enumerate active sessions, which makes "sign out all devices" and per-session audit trivial. The security model is simple enough to reason about correctly — a much smaller validation surface than JWT.

**Weaknesses.** Every request needs a lookup, which is a network hop plus a store. That store is shared state: a scaling constraint, an availability dependency, and a failure domain. Cross-region deployments must replicate it or accept the latency. Cross-service architectures either share the store or add an introspection service, which reintroduces a network hop per service. Under load the session store becomes the bottleneck the JWT camp warns about.

**Risks.** Session-store outage is total authentication outage — every request fails. An under-provisioned store degrades every endpoint simultaneously. Caching session lookups to relieve the pressure quietly reintroduces the staleness the model existed to avoid, without the honesty of an explicit `exp`. Sessions that never expire accumulate indefinitely.

**Guardrails.** Use a store with a native TTL (Redis and equivalents) so expiry is not a background job you can forget. Make the store highly available and treat it as a tier-1 dependency, with explicit capacity planning. Cache lookups only with a short, deliberate, documented TTL — and understand that this converts your model into a hybrid with a bounded staleness window. Keep the session identifier high-entropy and opaque.
Bind sessions to a fingerprint (client IP, user agent) with care — RFC 9114 §10.10 warns that client addresses can change mid-connection on HTTP/3, and mobile clients change networks routinely.

##### Recommendation

**This is a recommendation, and it depends on one measurable requirement: your maximum acceptable revocation delay.**

If a compromised credential must be dead in **under a second**, use opaque server-side sessions or token introspection. No amount of JWT tuning gets you there; short expiry gives you a bounded window, not immediacy. Regulated environments, financial operations, and admin interfaces usually fall here.

If a revocation delay of **a few minutes** is acceptable, short-lived JWT access tokens plus rotated refresh tokens are an excellent fit, and this is what RFC 9700 §2.2 is shaped around. Most APIs are in this category and do not realise they have the choice.

The **hybrid** is what large systems converge on and is worth naming explicitly: a stateless JWT access token with a five-to-fifteen-minute lifetime, an opaque refresh token checked against server state at every refresh, and a revocation list consulted only on refresh — not on every request. Revocation takes effect within one access-token lifetime, the hot path stays lookup-free, and the store handles refresh traffic rather than request traffic, which is two or three orders of magnitude less.

What is not defensible in 2026 is the middle position that the ecosystem drifted into: **long-lived JWTs with no revocation path**. Multi-hour or multi-day access tokens that cannot be withdrawn combine the stateless model's weakness with none of its discipline. If you have those, shortening their lifetime and adding refresh is the single highest-value change available in this whole section.

### I.6 Rate Limiting, Quotas, and Backpressure

#### Overview

Rate limiting answers one question: given that this caller has already made N requests recently, may it make another? Everything else — algorithm, key, storage, headers — is implementation of that decision. It is cheap to describe and expensive to get right, because it sits on the hot path of every request, must be consistent across replicas that share no memory, and is the last line of defence between one badly written client and a shared outage.

#### Background

The status code is 429, defined not in the core semantics document but in [RFC 6585](https://www.rfc-editor.org/rfc/rfc6585.html) §4 (Standards Track, April 2012): "The 429 status code indicates that the user has sent too many requests in a given amount of time ('rate limiting')."

The same section is explicit that mechanics are out of scope — "this specification does not define how the origin server identifies the user, nor how it counts requests" — which is why every API you integrate against does it differently.

Two normative details in RFC 6585 §4 are widely missed. `Retry-After` is a *MAY*, not a MUST: responses "MAY include a Retry-After header indicating how long to wait before making a new request." And "Responses with the 429 status code MUST NOT be stored by a cache" — a 429 is a statement about the caller, not the resource, and caching one applies one caller's punishment to everyone behind a shared cache.

`Retry-After` itself is [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html) §10.2.3, with value `HTTP-date / delay-seconds` where `delay-seconds = 1*DIGIT` is "a non-negative decimal integer, representing time in seconds". Note the scope: §10.2.3 describes the field on 503 and 3xx responses and does not mention 429 at all. The 429 pairing comes from RFC 6585. Both are real; they live in different documents.

#### The Five Algorithms

##### Fixed window

Divide time into windows of length `W`; keep one counter per key per window; allow if below the limit `L`, then increment; reset on rollover. One integer, O(1) per request — and one flaw, worth a factor of two.

Take `L = 60`, `W = 60s`, window opening at `t = 0`. A client sends 60 requests at `t = 59.9`, all allowed inside `[0, 60)`. At `t = 60.1` the window rolls, the counter resets, and 60 more are allowed inside `[60, 120)`. That is **120 requests in 0.2 seconds** without ever violating "60 per 60 seconds". The advertised rate is 1 req/s; the achievable instantaneous rate at the boundary is `2L`. Every fixed-window limiter has this property — it is the algorithm, not a bug in one implementation.

Whether it matters depends on what you are protecting. For monthly billing, a 2x boundary burst is noise. For a downstream database, a burst synchronised across many clients at the same wall-clock boundary is exactly the event the limiter exists to prevent — and a globally aligned window (the top of each minute) *synchronises* every client's burst into one instant.

##### Sliding window log

Store every request timestamp within the last `W` seconds; drop the expired ones and count the rest. Exact: the invariant holds at every instant, with no boundary artefact. The cost is memory proportional to `L` per active key plus a prune-and-count per request. Right for small `L` and high-value limits; wrong at volume.

##### Sliding window counter

Keep the current and previous window counters and interpolate by position within the current window:

```text
estimate = current_count + previous_count * (1 - elapsed_fraction_of_current_window)
```

At `t = 60.1` with 60 requests in the previous window, `elapsed_fraction ≈ 0.0017`, so the estimate is about 60 before the first new request is counted — the boundary burst is suppressed for two integers per key. The estimate assumes uniform distribution within the previous window, so it is slightly wrong in both directions, but bounded rather than off by 2x. This is what most production limiters use.

##### Token bucket

A bucket holds up to `C` tokens and refills at `R` per second; each request removes one. This decouples what fixed-window conflates: `R` is sustained rate, `C` is permitted burst.

An idle client accumulates up to `C` tokens and may spend them at once — usually desirable, since a burst after idleness costs nothing you have not already sized for. Token bucket is also the natural fit for *cost-weighted* limits: an expensive request can consume 50 tokens instead of 1, which no counter-based algorithm expresses cleanly.

##### Leaky bucket

A queue drains at fixed rate `R`; full queue means refusal. The difference from token bucket is the output *shape*: token bucket passes bursts up to `C` through immediately, leaky bucket smooths output to exactly `R` regardless of input. Leaky bucket is a traffic shaper; token bucket is an admission controller.

In practice the two are implemented identically and named interchangeably. Read the code, not the class name — Juniper's own `LeakyBucket` (`juniper-service-core`, `juniper_service_core/websocket/control_security.py:53-78`) refills `capacity` tokens at `refill_rate` per second and decrements on acquire, which is a token bucket by the definition above. Misnamed, correctly implemented.

#### Where to Enforce, and What to Key On

| Layer       | Sees                                             | Cost of a rejection                   | Blind to                                     |
|-------------|--------------------------------------------------|---------------------------------------|----------------------------------------------|
| CDN / edge  | IP, path, coarse headers                         | Near zero; never reaches your network | Authenticated identity, tenant, request cost |
| Gateway     | Everything pre-routing                           | One hop; no app CPU                   | Per-operation cost, DB state                 |
| Application | Full auth context, resolved route, business cost | Full parse, auth, framework overhead  | Nothing — but pays for every rejection       |

The answer is usually "more than one": coarse IP limits at the edge to absorb volumetric abuse, identity-scoped limits in the application where identity is actually known.

The key is where designs go wrong. Keying on client IP alone breaks in three ways that all produce the same symptom — legitimate users throttled while abusers are not:

- **NAT and CGNAT.** An office, university, or mobile carrier region egresses through one address. A 60 req/min bucket shared by ten thousand people is not a rate limit; it is an outage with extra steps.
- **CDN and proxy collapse.** Behind a reverse proxy, `request.client.host` is the proxy unless you parse `X-Forwarded-For` — and parsing it is a security decision, because the client controls the left-hand entries. Trusting it unvalidated converts the limiter into a spoofable no-op.
- **IPv6.** A subscriber typically holds a /64 — 2^64 addresses. Per-address limits are free to evade. Limit on a prefix.

Keying on authenticated identity fixes all three, at the cost of only working *after* authentication — which forces an ordering decision, covered below.

#### Distributed Enforcement, and the Silent Failure

An in-memory counter enforces a limit **per process**. Run four replicas and "60 requests per minute" becomes, empirically, up to 240 — with no error, no log line, no test failure. The limit is simply four times looser than the number in your configuration, which is the number in your documentation.

That is the defining property: silent, scaling with replica count, invisible to any single-process test. It surfaces as "our rate limit doesn't seem to work" months later, usually during an incident.

Fixes, ascending in cost: divide the limit by the replica count (trivial, wrong the moment autoscaling moves); use a shared store with atomic increment (correct, adds a round trip and a dependency — and you must decide whether an unreachable store fails open, losing protection when you may need it, or fails closed, turning a Redis blip into a total outage); or run local buckets with periodic reconciliation (bounded overshoot, no per-request round trip, considerably more code).

Juniper's HTTP limiter is honest about being in the first category. `RateLimiter` (`juniper_service_core/security.py:99-104`) documents itself as an "In-memory fixed-window rate limiter … Thread-safe implementation suitable for single-process deployments."

The docstring is the deployment constraint. It holds a `dict` under a `threading.Lock` (`security.py:126-127`), prunes expired buckets every 100 calls, and hard-caps at 10 000 entries (`security.py:107-108`) so an attacker cycling keys cannot exhaust memory.

#### Response Semantics: 429, Retry-After, and the RateLimit Fields

The minimum viable rejection is 429 plus `Retry-After`. Everything beyond exists so a well-behaved client can *avoid* the rejection rather than discover it. Three header families are in circulation, with sharply different status:

| Form                                          | Status                                                    | Notes                                                                            |
|-----------------------------------------------|-----------------------------------------------------------|----------------------------------------------------------------------------------|
| `X-RateLimit-Limit` / `-Remaining` / `-Reset` | **De-facto vendor convention.** No RFC, no draft.         | Ubiquitous; `-Reset` semantics (epoch vs delta seconds) vary by vendor           |
| `RateLimit-Limit` / `-Remaining` / `-Reset`   | Historical IETF draft form (through revision -06)         | Superseded within the same draft; do not build on it                             |
| `RateLimit` + `RateLimit-Policy`              | **Internet-Draft** `draft-ietf-httpapi-ratelimit-headers` | Current form as of this writing; intended status Standards Track, **not an RFC** |

That last row is frequently misreported as a standard. It is an [Internet-Draft](https://datatracker.ietf.org/doc/draft-ietf-httpapi-ratelimit-headers/) of the IETF HTTPAPI Working Group.

Revision -06 defined four separate fields (`RateLimit-Limit`, `-Remaining`, `-Reset`, `-Policy`); revision -07 consolidated them into the two the current draft defines, both expressed as HTTP Structured Fields per [RFC 9651](https://www.rfc-editor.org/rfc/rfc9651.html) (Standards Track, September 2024, obsoleting RFC 8941). The consolidated form carries quota in parameters — `q` quota units, `r` remaining, `t` time remaining, `w` window — so one field expresses multiple simultaneous policies:

```http
HTTP/1.1 429 Too Many Requests
RateLimit-Policy: "sliding";q=12;w=1
RateLimit: "sliding";q=12;r=0;t=1
Retry-After: 1
```

Because it is a draft whose shape has already changed once, the pragmatic position is: emit `Retry-After` (RFC 9110 §10.2.3, unambiguous and universally understood), emit `X-RateLimit-*` if your ecosystem expects it, and add the draft fields when you are prepared to track revisions. Do not call any of them "the standard" in your documentation.

#### Backpressure Is Not Rate Limiting

- **Rate limiting** is a *policy* decision about a *caller*, evaluated against a quota: "you get 60 per minute because that is your plan." Enforced identically whether the server is idle or melting.
- **Backpressure** is a *capacity* signal about the *server*, evaluated against current load: "I am at my concurrency ceiling." Enforced only under pressure, and it applies to everyone.

They use different status codes for a reason. 429 says *you* did too much (RFC 6585 §4); 503 says *I* cannot cope (RFC 9110 §15.6.4 — "the server is currently unable to handle the request due to a temporary overload or scheduled maintenance, which will likely be alleviated after some delay"). Sending 429 for an overload tells the caller its quota is exhausted when it is not, and a client that trusts you backs off for the wrong duration.

Three capacity mechanisms deserve separate names. **Concurrency limits** — a semaphore bounding in-flight requests — are often more useful than a rate limit, because they bound *resource occupancy* rather than *arrival count*: ten concurrent minute-long requests are far more dangerous than a thousand millisecond ones, and no rate limit distinguishes them.

**Load shedding** means rejecting early and cheaply under overload; the counterintuitive rule is that recovery requires rejection to be *cheaper* than acceptance, or shedding consumes the capacity it was meant to free. **Queue bounds** matter because an unbounded queue converts overload into unbounded latency and then an OOM; a bounded queue converts it into fast, visible rejection.

#### Juniper in Practice

`juniper-service-core` (v0.5.1) carries the shared HTTP security tier and shows four decisions worth studying.

**The algorithm is fixed-window.** `RateLimiter.check` (`juniper_service_core/security.py:200-209`):

```python
import time

def check(self, key: str) -> tuple[bool, int, int]:
    """Excerpt of security.py:200-209; the lock and periodic prune are elided."""
    now = time.time()
    count, window_start = self._counters[key]
    if now - window_start >= self._window:
        self._counters[key] = (1, now)
        return (True, self._limit - 1, self._window)
    if count >= self._limit:
        reset_in = int(self._window - (now - window_start))
        return (False, 0, reset_in)
    self._counters[key] = (count + 1, window_start)
    return (True, self._limit - count - 1, int(self._window - (now - window_start)))
```

Defaults are 60 requests per 60 seconds (`security.py:112-113`). One nuance: the window is anchored to the key's *first* request rather than a global clock, because the `defaultdict` seeds `window_start = 0.0` and the first comparison against epoch time always rolls the window. Each key's boundary therefore drifts independently, so bursts from different callers do not synchronise — but the 2x boundary burst for a *single* caller is fully present.

**Auth runs before the limiter — correct, and incomplete.** `SecurityMiddleware.dispatch` (`juniper_service_core/middleware.py:175-186`) evaluates the API key first, and the ordering is load-bearing because the bucket key *depends on the auth result*:
`_get_key` (`security.py:172-175`) returns `key:{api_key}` when authenticated, falling back to `ip:{client_ip}`. Limiting first would leave `api_key` at `None` on every request, so every caller behind one NAT would share one `ip:` bucket — the CGNAT collapse above, self-inflicted by ordering.
This is one reason, not two: "an unauthenticated attacker exhausts a legitimate caller's quota" is that same shared-`ip:`-bucket mechanism described from the attacker's side.

The cost of the ordering is the part rarely stated. `APIKeyAuth` **raises** on failure, so with a single limiter placed after it the limiter is never reached (`middleware.py:175-186`) and **the entire 401 path goes unthrottled**. Credential guessing and garbage-key floods consume zero tokens and are bounded only by how fast the process can reject them — the limiter protects the authenticated surface and leaves the authentication surface itself open.

This was a live gap in `juniper-service-core` until it was found by writing this section; juniper-ml#1082 closed it by adding the pre-auth throttle described below, rather than by reordering. Keep the general lesson rather than the incident: *"authenticate before rate limiting"* is repeated everywhere as unqualified best practice, it is correct, and on its own it leaves the authentication surface unprotected. The complete rule needs two limiters, and the version of it you will usually be told names only one.
The fix is not to reverse the order but to run two limiters: a coarse IP- or prefix-keyed bucket before authentication, sized to absorb volumetric abuse, and the identity-keyed bucket after. The "Where to Enforce" table above already prescribes exactly that pairing — "coarse IP limits at the edge to absorb volumetric abuse, identity-scoped limits in the application" — and juniper-service-core ships only the second half. A single limiter, wherever you put it, leaves one of the two holes open.

**The 429 must be rebuilt by hand.** The limiter raises a FastAPI `HTTPException` carrying `X-RateLimit-Limit`, `-Remaining`, `-Reset`, and `Retry-After` (`security.py:231-240`). But it is invoked *directly from middleware*, not as a FastAPI dependency, so FastAPI's exception handlers never run and the exception would otherwise escape as a bare 500 with no headers. `SecurityMiddleware` therefore reconstructs the response explicitly (`middleware.py:181-186`):

```python
async def dispatch(self, request, call_next):
    """Excerpt of middleware.py:174-188; the exempt-path check is elided."""
    api_key = None
    try:
        if self._api_key_auth.enabled:
            api_key = await self._api_key_auth(request)
        if self._rate_limiter.enabled:
            await self._rate_limiter(request, api_key)
    except HTTPException as exc:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=exc.headers,
        )
    return await call_next(request)
```

Dropping `headers=exc.headers` yields a 429 with no `Retry-After` — correct status, useless response — and no unit test of the limiter would notice. Section I.11 returns to this.

**A rejection path that must never fail.** `LeakyBucket.retry_after` (`juniper_service_core/websocket/control_security.py:80-92`) carries a guard whose comment names the incident it prevents: a configured `ws_control_rate_limit_per_sec=0` builds `refill_rate=0.0`, so `deficit / self._refill_rate` would raise `ZeroDivisionError` *inside the rate-limit rejection path*, propagating out of the receive loop and tearing the whole connection down instead of denying one command.

The guard returns `3600.0` — back off hard — rather than dividing. The general lesson outweighs the specific bug: the code that runs when you are *rejecting* requests is the code that runs when you are under attack. It must be the most robust code in the service, and it is usually the least tested.

#### Judgement Calls

- **Which algorithm.** Fixed-window if the limit is commercial and a boundary burst is tolerable. Sliding-window counter if it protects a real capacity ceiling. Token bucket for burst-after-idle or cost-weighted requests.
- **Fail open or closed** when the backing store is unreachable — and the answer depends on what the limit is *for*. For quota and fairness limits, fail open with a loud alarm: the limiter's dependency should never be more critical than the service it protects. For limits that are a **security control** — authentication throttles, signup, password reset, anything standing in front of a guessable secret — failing open makes "take Redis down" the cheapest opening move in a credential-stuffing campaign.
  Degrade those to a conservative in-process bucket instead: it over-throttles by a factor of the replica count, which is the correct direction to be wrong. Failing open on a security limit hands an attacker a denial-of-protection primitive.
- **Per-endpoint or global.** One global limit is simple and lets one expensive endpoint eat a caller's whole quota; per-endpoint is precise and multiplies configuration by route count.
- **Whether to advertise remaining quota on success.** It lets good clients self-throttle and hands attackers a precise oracle.
- **Where the limit is configurable.** juniper-data makes the enabled flag and requests-per-minute settings (`juniper_data/api/settings.py:164-165`) but keeps the *window* a hardcoded module constant (`juniper_data/api/constants.py:79`) — defensible, as long as it is deliberate.

#### Tradeoffs

| Choice                  | Gain                                       | Cost                                            |
|-------------------------|--------------------------------------------|-------------------------------------------------|
| Edge enforcement        | Rejections never reach your infrastructure | No identity, no per-operation cost awareness    |
| Application enforcement | Full context: tenant, route, business cost | Every rejection costs a full request parse      |
| In-memory counters      | Zero dependencies, zero latency            | Limit silently multiplies by replica count      |
| Shared-store counters   | Correct across replicas                    | Round trip per request; new failure mode        |
| Key on IP               | Works pre-auth; stops volumetric abuse     | Breaks behind NAT/CDN; trivially evaded on IPv6 |
| Key on API key          | Accurate, fair, per-tenant                 | Only available after auth; needs an IP fallback |
| Advertise quota headers | Clients self-throttle; fewer 429s          | Discloses your limits to attackers              |

#### Best Practices

- Emit `Retry-After` on every 429 — the one header every client library already understands.
- Never cache a 429; RFC 6585 §4 requires this.
- Authenticate before rate limiting, and key the bucket on authenticated identity when you have one — but pair it with a coarse pre-auth limiter, or the 401 path itself is unlimited.
- Exempt health and readiness endpoints. `juniper-service-core` does so by path set (`juniper_service_core/middleware.py:23-36`); a throttled liveness probe reads to an orchestrator as a dead process, and its remedy is to restart you under load.
- Test the *rejection* path end to end through the middleware, not just the limiter object.
- Document the limit, window, key, and headers. An undocumented limit is discovered by your users in production.

#### Common Failure Modes

- **The 2x boundary burst.** Inherent to fixed-window; a synchronised thundering herd when windows align to a global clock.
- **The silent replica multiplier.** In-memory counters times N replicas. No error, no test failure.
- **NAT collapse.** IP-keyed limits throttling an entire office or carrier as one caller.
- **Spoofable forwarded headers.** Trusting `X-Forwarded-For` without a trusted-proxy allowlist makes the limiter a no-op for anyone who reads your docs.
- **Truncated `Retry-After`.** `security.py:205` computes `reset_in = int(...)`, truncating toward zero, so with 0.5 s remaining the client is told `Retry-After: 0` and retries immediately into another 429. Use ceiling arithmetic for backoff hints. (`Retry-After: 0` is syntactically valid — RFC 9110 §10.2.3 defines `delay-seconds` as *non-negative* — it is simply useless advice.)
- **Unbounded queueing instead of shedding.** Latency grows without bound until the process dies; the limiter never fires because arrival rate never exceeded the limit.

#### Error Handling

A rate-limit rejection is a normal, expected outcome, not an exceptional one.

- **Status:** 429 for quota; 503 for capacity.
- **Headers:** `Retry-After` always; quota headers applied consistently on both paths. Juniper emits three on success (`middleware.py:190-193`) and four on rejection (`security.py:234-239`); `Retry-After` is 429-only, which is correct.
- **Body:** enough to diagnose without leaking policy internals; a machine-readable problem document beats a prose string.
- **Logging:** rejections at INFO with the key *identifier*, never key material. A 429 storm is a signal, not an error; logging it at ERROR trains operators to ignore your error log.
- **Metrics:** count rejections labelled by route template and reason — see I.10 for why template and not raw path.
- **Client side:** treat 429 as retryable *only* with backoff respecting `Retry-After`, and only for requests safe to repeat. That constraint is the next section.

---

### I.7 Idempotency, Retries, and the Exactly-Once Illusion

#### Overview

A client sends a request. The connection drops. The client does not know whether the server processed it. This is the irreducible problem of distributed APIs, and every retry policy, idempotency key, and deduplication table exists to manage it.

The honest framing: **exactly-once *delivery* is impossible; exactly-once *effect* is achievable.** This section explains why the first half is true, how the second half is built, and what happens when three sibling client libraries — same author, same base library, same month — reach three different conclusions.

#### Background

The problem has a name — the two generals — and it starts here. The client sends and receives nothing back. Two worlds are consistent with that observation:

1. The request never reached the server. Nothing happened. Retrying is correct.
2. The request arrived, was fully processed, and the *response* was lost. Retrying duplicates the effect.

**The client cannot distinguish these.** Not with a longer timeout, not with a better library, not in principle — the information required is precisely the information that failed to arrive. This is the two generals problem, and no finite protocol of acknowledgements solves it, because the last message in any such protocol is itself unacknowledged.

What you can do is make guessing wrong harmless. If a duplicate produces no additional effect, the client can assume world 1 and retry, because if it was world 2 the retry costs only bandwidth. That is the entire idea, and it is why idempotency — not delivery guarantees — is load-bearing.

The failure is asymmetric in an underappreciated way: a lost response on a read is a wasted round trip, while a lost response on a charge is a support ticket. Severity scales with the side effect, not with the frequency of network failure.

#### What RFC 9110 Actually Says

RFC 9110 §9.2.2 defines idempotency precisely, and the precision matters:

> A request method is considered "idempotent" if the intended effect on the server of multiple identical requests with that method is the same as the effect for a single such request. Of the request methods defined by this specification, PUT, DELETE, and safe request methods are idempotent.

Three consequences are routinely misread.

**Idempotency is about the effect on the server, not the response.** §9.2.2 is explicit: "It knows that repeating the request will have the same intended effect, even if the original request succeeded, though the response might differ." A `DELETE` returning 204 then 404 is perfectly idempotent — server state is identical after one call or five. Treating a changed status code as evidence of non-idempotency misreads the definition.

**It is about the *intended* effect, not all observable effects.** Again: "the idempotent property only applies to what has been requested by the user; a server is free to log each request separately, retain a revision control history, or implement other non-idempotent side effects for each idempotent request." Five identical `PUT`s produce five access-log lines and remain idempotent.

**The method's classification is a default, not a guarantee about your resource.** §9.2.2 permits retrying a non-idempotent method "unless it has some means to know that the request semantics are actually idempotent, regardless of the method". A `POST` that upserts by a client-supplied natural key *is* idempotent in effect. Conversely, nothing stops you writing a `PUT` that increments a counter — and thereby breaking the contract every intermediary relies on.

§9.2.2 is unusually direct about client behaviour: "A client SHOULD NOT automatically retry a request with a non-idempotent method unless it has some means to know that the request semantics are actually idempotent … or some means to detect that the original request was never applied." For intermediaries the prohibition is absolute: "A proxy MUST NOT automatically retry non-idempotent requests.

A client SHOULD NOT automatically retry a failed automatic retry." And it acknowledges the practice it warns against: "Some clients take a riskier approach and attempt to guess when an automatic retry is possible. For example, a client might automatically retry a POST request if the underlying transport connection closed before any part of a response is received." That sentence is the whole controversy, written into the standard.

#### Idempotency Keys

##### How they work

The client generates a unique value — usually a UUIDv4 — and sends it with the request. The server maintains a store mapping key → outcome. On receipt: if the key is absent, claim it atomically, process, store the outcome, return. If present and complete, return the *stored response* without re-executing. If present and in-flight, it is a concurrent duplicate.

The header is conventionally `Idempotency-Key`, specified by [`draft-ietf-httpapi-idempotency-key-header`](https://datatracker.ietf.org/doc/draft-ietf-httpapi-idempotency-key-header/), an **Internet-Draft** of the IETF HTTPAPI Working Group — not an RFC.

As of this writing the draft is at intended status Standards Track and has not been published as an RFC; the datatracker was unreachable from this environment, so treat the exact revision number and expiry date as unverified. Treat the header as a widely adopted vendor convention with an in-progress standardisation effort, and say so rather than calling it a standard.

##### What must be stored

| Stored                                                      | Why                                                    |
|-------------------------------------------------------------|--------------------------------------------------------|
| The key                                                     | Lookup                                                 |
| A fingerprint of the request (hash of method + path + body) | To detect key reuse with different content             |
| Response status, headers, and body                          | So the replay is byte-identical, not merely successful |
| Processing state (in-flight / complete / failed)            | To handle concurrent duplicates                        |
| Creation timestamp                                          | To expire the entry                                    |
| Scope (which caller owns the key)                           | So one tenant's key cannot collide with another's      |

Scoping is not optional: a store keyed on the raw header value alone lets any caller guess another's key and receive their stored response — information disclosure with an unpleasant blast radius. A TTL is likewise mandatory, and its length is a real decision: it must exceed the longest plausible client retry horizon (hours, if clients retry from a durable queue) and it bounds storage growth. Expiry is not a correctness compromise; it is an explicit statement that after `T`, a repeat is a new intent.

##### Concurrency on the same key

Two identical requests can arrive simultaneously — the *normal* case when a client times out locally and retries while the original is still executing. The claim must therefore be atomic: a unique-constraint insert, `SETNX`, or equivalent compare-and-set. A read-then-write is a race, and the race window is exactly the window in which duplicates arrive.

For the loser there are two defensible answers: block until the winner completes and return its stored response (better experience, holds a connection, risks pile-up), or return `409 Conflict` immediately (cheap, correct, pushes the wait to the client). Pick one and document it. What you must not do is process both.

##### Same key, different body

Key `K` with body A, then `K` with body B. Something is wrong — a key-generation bug, a client reusing a constant, or an attack. The safest response is to **reject with `422` (or `409`) and not process**, because both alternatives are worse: returning A's stored response silently discards B, and processing B breaks the contract for anyone retrying A. This is why the request fingerprint must be stored; without it the case is undetectable.

#### Retry Strategy

##### Which statuses are safely retryable

| Status | Retryable? | Reasoning |
| --- | --- | --- |
| Connection error, DNS failure | Yes, if idempotent | May never have reached the server |
| Timeout with no response | Yes, if idempotent — the two-generals case exactly | Unknown outcome |
| 408 Request Timeout | Yes | Server explicitly did not complete the request |
| 429 Too Many Requests | Yes, honouring `Retry-After` | Explicitly transient (RFC 6585 §4) |
| 500 Internal Server Error | **Ambiguous** | May have partially applied before failing |
| 502 Bad Gateway | Yes, if idempotent | RFC 9110 §15.6.3: the gateway "received an invalid response from an inbound server it accessed" — the request *did* reach upstream, so the effect may already be applied. Many proxies also emit 502 on a failed connection, and the code alone does not distinguish the two |
| 503 Service Unavailable | Yes, if idempotent, honouring `Retry-After` | RFC 9110 §15.6.4: temporary overload, "likely be alleviated after some delay" |
| 504 Gateway Timeout | Yes, if idempotent | RFC 9110 §15.6.5: upstream did not respond in time — but may still be working |
| Other 4xx | **No** | Retrying a 400 or 404 produces a 400 or 404 |

The 500 row is where reasonable libraries disagree, and Juniper's siblings disagree exactly there. A 500 means the server *reached* your handler and something broke inside it — quite possibly after the first of three writes. 502 and 504 are widely *assumed* to mean the request never landed, and that assumption is where duplicate effects come from:
§15.6.3's 502 is a gateway that got a response it could not use, and §15.6.5's 504 is an upstream that did not answer *in time*. In both, the origin may well have done the work. The "if idempotent" qualifier on those rows is not decoration.

##### Exponential backoff, and why jitter is not optional

Backoff is straightforward: wait `base * 2^attempt`, capped, to give a struggling server time to recover. Jitter is the part that gets omitted, and omitting it turns a blip into an outage:

1. A server degrades for 500 ms. Every in-flight request across 1000 clients fails at approximately the same instant.
2. Every client computes the same first backoff — say 1 s.
3. At `T + 1s`, all 1000 retry **simultaneously**. The still-recovering server takes a perfectly synchronised spike far above steady-state load and fails again.
4. Every client computes the same second backoff. At `T + 3s`, all 1000 retry simultaneously again.

Deterministic backoff does not spread load; it *phase-locks* every client onto the same schedule and converts independent failures into a synchronised herd. Worse, each failure re-synchronises the herd more tightly, because clients that had drifted apart are pulled back onto the common schedule by their shared failure timestamp.

```python
import random

def backoff_delay(attempt: int, base: float = 0.5, cap: float = 30.0) -> float:
    """Full-jitter exponential backoff for retry attempt ``attempt`` (0-indexed).

    Returns a delay uniformly distributed in ``[0, min(cap, base * 2 ** attempt)]``.
    The randomisation is the point: deterministic backoff phase-locks every client
    onto one retry schedule, so a shared failure spikes at each backoff boundary.
    """
    ceiling = min(cap, base * (2**attempt))
    return random.uniform(0.0, ceiling)  # noqa: S311 - not a security context
```

"Full jitter" (uniform over `[0, ceiling]`) spreads load best; "equal jitter" (`ceiling/2 + uniform(0, ceiling/2)`) trades spreading for a guaranteed minimum wait. Either beats none. When the server supplies `Retry-After`, honour it as a *floor* and jitter on top — otherwise you have merely moved the synchronisation point to a time the server chose.

##### Retry budgets and circuit breakers

Per-request retry limits do not bound aggregate load. Three retries against a server failing every request means **4x traffic to a server that is already failing** — retries are an amplifier pointed at the broken thing. This is how partial degradation becomes complete outage: the server slows, clients retry, load rises, more requests time out, more retries fire.

**Retry budgets** cap retries as a fraction of total client requests — "no more than 10% of requests may be retries in any 10-second window". Untouched under normal conditions; under mass failure it caps amplification at 1.1x instead of 4x. This is the highest-leverage retry control and the one most often missing.

**Circuit breakers** track recent failure rate per upstream: above a threshold, *open* and fail fast locally with no network call; after a cooldown go *half-open* and admit a few probes; close on success, re-open on failure. The breaker converts a slow, expensive, amplifying failure into a fast, cheap one and gives the upstream actual idle time to recover. The two compose: the breaker stops traffic to a dead upstream, the budget bounds amplification while it is merely degraded.

#### Exactly-Once Delivery Versus Exactly-Once Effect

**Exactly-once delivery is impossible.** Delivery is an event in the network; guaranteeing it happened exactly once requires the sender to *know*, which requires an acknowledgement, which is a message that can be lost. Acknowledging the acknowledgement moves the problem — there is always a last message, and it is always unacknowledged.

This is not an engineering limitation to be overcome with better infrastructure; it is a theorem. You may choose **at-most-once** (send, never retry: never duplicates, loses messages) or **at-least-once** (retry until acknowledged: never loses, duplicates). There is no third option at the delivery layer.

**Exactly-once effect is achievable**, because "effect" is a property of *your state*, not of the network. Combine at-least-once delivery with an operation idempotent in effect and duplicates become invisible: the second delivery finds the key claimed, the row inserted, the state set, and returns the stored outcome unchanged.

Deliveries: one or more. Effects: exactly one. This is why "exactly-once" systems that genuinely work — including the ones advertising the phrase — are always at-least-once delivery plus server-side deduplication. The marketing describes the outcome; the mechanism is always the pair.

The practical consequence is where you invest. Do not try to make the network reliable; make the *operation* repeatable — content-addressed identifiers, client-supplied natural keys, upserts instead of inserts, and idempotency keys where none of those apply.

juniper-data illustrates the content-addressed variant. `generate_dataset_id` (`juniper_data/core/dataset_id.py:23-61`) hashes canonical JSON of `{generator, version, params}` with `sort_keys=True` and compact separators, producing `{generator}-{version}-{sha256[:16]}`. Identical parameters give an identical id, so a duplicate `POST /v1/datasets` collapses onto the existing resource — idempotent effect from the data model, no key header anywhere.

The escape hatch is equally instructive: when `params['seed']` is absent or `None` the generator is itself non-deterministic, so a UUID nonce is mixed in (`dataset_id.py:54-55`) specifically so a repeat does *not* collide onto a stale artifact. Content addressing is only idempotent when the content determines the result.

#### Juniper in Practice: Three Siblings, Three Answers

The most instructive example in the primer: three client libraries by the same author, on the same base stack (`requests` plus urllib3's `Retry`), within a few months of one another, reaching three incompatible conclusions. They were not written in parallel — data-client's policy comment is self-dated 2026-04-24, and recurrence-client's `constants.py` first landed on 2026-06-18 — which makes the divergence worse rather than better.
This is a fix that failed to propagate, not three simultaneous judgement calls.

|                         | juniper-data-client (v0.4.2)  | juniper-cascor-client (v0.7.0)      | juniper-recurrence-client (v0.2.0) |
|-------------------------|-------------------------------|-------------------------------------|------------------------------------|
| Retryable statuses      | `429, 500, 502, 503, 504`     | `429, 502, 503, 504` — **no 500**   | `429, 500, 502, 503, 504`          |
| Allowed methods         | `HEAD, GET, PUT`              | **`GET, POST, DELETE, PUT, PATCH`** | `HEAD, GET`                        |
| Retries non-idempotent? | No                            | **Yes**                             | No                                 |
| `backoff_factor`        | 0.5, constructor-configurable | 0.5, hardcoded (`client.py:91`)     | 0.5, configurable                  |
| Jitter                  | none                          | none                                | none                               |

Verified at `juniper_data_client/constants.py:58` and `:67`; `juniper_cascor_client/constants.py:36` and `:37`; `juniper_recurrence_client/constants.py:50` and `:54`.

**data-client carries the fix and the reasoning.** `juniper_data_client/constants.py:59-66`:

> XREPO-11 (2026-04-24): auto-retry is now restricted to idempotent HTTP methods per RFC 9110 §9.2.2. POST, PATCH and DELETE were previously included, which could cause duplicate dataset creation (on POST) or repeated side-effects (on DELETE) when transient 5xx responses retried a request that had already been applied server-side.

That is the two-generals problem, correctly diagnosed, in a source comment — and it prescribes the alternative: "Callers that need retry for mutations must implement their own idempotency layer (e.g., use client-supplied dataset names so POST collapses server-side via the existing dedupe path)."

**recurrence-client is stricter and says why.** `constants.py:51-53` restricts retries to `HEAD, GET` because "the recurrence POSTs (train / predict / crossval) carry server-side state — train and crossval are lock-guarded — so a transient-5xx retry must not silently re-issue them."

**cascor-client never received the fix.** It retries `POST`, `DELETE`, and `PATCH`. Its retried non-idempotent call sites are live duplicate-effect risks — `create_network` (`POST /network`, `juniper_cascor_client/client.py:154`), `delete_network` (`DELETE /network`, `:162`), `start_training` (`POST /training/start`, `:198`), `reset_training` (`POST /training/reset`, `:214`), and `save_snapshot` (`POST /snapshots`, `:295`).

A grep for `Idempotency-Key` across all three clients, `juniper-data`, and `juniper-service-core` returns nothing: no idempotency key exists anywhere in the stack, so nothing downstream deduplicates.

The scenario is concrete. `POST /training/start` returns 502 because a proxy hiccuped *after* the origin had already started a training run. urllib3 retries. The second request either starts a second run or returns a conflict — and either way the caller's view is wrong. Because the retry happens *inside* the HTTP adapter, the caller never learns it occurred.

A second-order defect compounds it: when retries are exhausted on a forcelist status, urllib3 raises `RetryError`, `requests` surfaces it as `RequestException`, and data-client's handler maps that to the **base** exception class (`juniper_data_client/client.py:295-297`) — losing the distinction between "connection refused" and "the server returned 503 five times". The caller receives a string, not a status.

The teaching point is not that cascor-client has a bug. It is that **retry policy is a genuine design decision with no obvious default**, that three competent attempts diverged, and that the divergence was invisible until someone read all three files side by side. If you ship more than one client library, retry policy belongs in one shared module with one comment explaining it.

#### Judgement Calls

- **Retry 500 or not.** cascor-client says no (the handler ran and may have partially applied); the others say yes (most 500s are transient dependency failures). Both defensible. Decide once, per organisation, and write down which.
- **Where retries live.** Inside the HTTP adapter they are automatic and invisible — uncountable, unloggable, no per-call opt-out. At the application layer they are explicit and verbose. All three Juniper clients chose the adapter, which is why the cascor `POST` retry is undetectable from calling code.
- **Client- or server-generated keys.** Client-generated is the only form that survives a lost response; a server-generated key you never received cannot be replayed.
- **Timeout versus retry budget.** A 30 s timeout with three retries is a 120 s worst case. All three Juniper clients use one flat 30 s timeout with three retries — and recurrence-client's `POST /v1/train` (`juniper_recurrence_client/client.py:311`) and `POST /v1/crossval` (`:405`) are *synchronous long-running server operations* sharing that socket timeout with no server-side cancellation. The client gives up while the server keeps working.

#### Tradeoffs

| Choice                      | Gain                                  | Cost                                                              |
|-----------------------------|---------------------------------------|-------------------------------------------------------------------|
| Retry aggressively          | Hides transient failures from users   | Amplifies overload; duplicates non-idempotent effects             |
| Retry conservatively        | No duplicates; no amplification       | Users see failures the network would have absorbed                |
| Idempotency keys            | Safe retries for any operation        | Storage, TTL policy, atomic-claim complexity, new failure surface |
| Content-addressed IDs       | Idempotency free from the data model  | Only works when content fully determines the result               |
| Retries in the HTTP adapter | Zero caller code                      | Invisible, unloggable, un-opt-out-able                            |
| Retries in the application  | Observable and controllable           | Every call site must implement it                                 |
| Circuit breaker             | Fast failure; upstream gets idle time | Rejects requests that might have succeeded                        |

#### Best Practices

- Default to retrying only idempotent methods; deviate only with an idempotency mechanism and a comment.
- Always jitter — full jitter unless you need a guaranteed minimum wait.
- Honour `Retry-After` as a floor, then jitter on top.
- Cap total elapsed time, not just attempt count; users and upstream timeouts care about wall clock.
- Enforce a retry budget across the client, not just per request.
- Preserve the status, body, and headers on exceptions — see **Error Handling** below for the precise statement of what the Juniper clients lose.
- Log every retry with attempt number and reason. A retry you cannot see is a retry you cannot debug.

#### Common Failure Modes

- **The retry storm.** No jitter, no budget; a 500 ms blip becomes a synchronised multi-minute outage.
- **Silent duplication.** Adapter-level retry of a non-idempotent `POST`: two training runs, two charges, two rows, and no log line saying a retry happened.
- **Storing only the key, not the response.** The replay returns 200 with an empty body.
- **TTL shorter than the client's retry horizon.** A client retrying from a durable queue an hour later gets a fresh execution.
- **Timeout shorter than the operation.** The client gives up and retries while the server is still working — the most common source of duplicates in practice, and exactly the recurrence-client shape above.
- **Retrying at multiple layers.** SDK 3x, gateway 3x, service mesh 3x: 27 requests from one call. Multiplicative, and each layer looks reasonable alone.

#### Error Handling

- **Distinguish "unknown outcome" from "known failure".** A timeout is not a failure; it is an absence of information. Code that treats them identically will either duplicate effects or report false failures.
- **Make the exception carry the status, the body, and the headers.** All three Juniper clients map 404 — and two of them 409 — to typed leaves, so a caller can branch on type for those. Everything unmapped (401, 413, 429, 500, 501) collapses into the base exception with the code only in the message string, and none of them exposes the response body or headers at all, so a 429's `Retry-After` cannot be honoured even when it is present.
- **On a duplicate-key hit, replay the stored response verbatim** — same status, same body. A different response teaches clients that retrying is unsafe.
- **Surface retry exhaustion distinctly.** "Failed after 4 attempts over 14 s" is actionable; "Request failed" is not.
- **Count idempotency-key hits.** It tells you whether clients are retrying — the earliest signal that something upstream is degraded.

#### Controversy: Should a Client Library Ever Auto-Retry POST?

**The controversy.** RFC 9110 §9.2.2 says a client "SHOULD NOT" automatically retry non-idempotent methods — a recommendation, not a prohibition — and in the same breath acknowledges that "some clients take a riskier approach and attempt to guess when an automatic retry is possible." The standard records the split. Juniper reproduces it: `juniper-cascor-client` retries `POST`, `DELETE`, and `PATCH`; the other two refuse, each citing §9.2.2 by number.

**The camps.** *Pragmatists* hold that most `POST` failures are connection-level and never reached the origin, that users experience unretried transients as outages, and that a library refusing to retry pushes the problem onto every application developer — who will implement it worse.

*Purists* hold that a library cannot know a resource's semantics, that silent duplication is worse than a visible error, and that the place to make an unsafe operation retryable is the protocol (an idempotency key), not the transport.

**The background.** urllib3's `Retry` originally allowed only idempotent methods by default, and its `allowed_methods` parameter makes widening the set a one-line change with no visible consequence in testing. Duplicate side effects appear only under real transient failures against real state — conditions a unit suite, and usually a staging environment, never produces. The pragmatist position is therefore very cheap to adopt and its cost is invisible until production.

**Pragmatist — auto-retry POST.**

- *Strengths.* Absorbs the large majority of failures, which genuinely are connection-level. One configuration line instead of retry logic at every call site. Better perceived reliability.
- *Weaknesses.* Cannot distinguish "never arrived" from "processed, response lost". Adapter-layer retries are invisible to the caller. The blast radius is proportional to the side effect, and the library does not know what that is.
- *Risks.* Duplicate resource creation; repeated charges; repeated state transitions — in cascor's case a duplicated `POST /training/start` or `POST /snapshots` with no server-side dedupe.
- *Guardrails.* Restrict to connection-level errors, never 5xx responses (a 5xx proves the request arrived). Require an idempotency key before enabling. Log every retry loudly. Make it opt-in per call, not a library-wide default.

**Purist — never auto-retry non-idempotent methods.**

- *Strengths.* Cannot duplicate an effect. Aligns with §9.2.2 and with the MUST NOT imposed on proxies. Failures stay visible, so they get fixed rather than masked. The application layer, which knows the semantics, decides.
- *Weaknesses.* Users see transient failures a retry would have hidden. Every application implements its own retry, and most will do so with no jitter and no budget — in practice often *worse* aggregate behaviour than a well-built library retry.
- *Risks.* Retry logic proliferates and diverges: the three-client divergence documented above, one layer up.
- *Guardrails.* Ship a documented retry helper the application can wrap around a mutation. Provide server-side idempotency so the application's own retry is safe. Preserve status codes so callers can decide correctly.

**Recommendation** (labelled as such): default to the purist position, and treat any deviation as requiring a server-side idempotency mechanism first. The asymmetry decides it — not retrying costs a visible error the caller can handle, while retrying wrongly costs a silent duplicate that surfaces as a data-integrity incident weeks later. Where retry-on-mutation is genuinely needed, add `Idempotency-Key` support to the server, then enable it in the client, in that order.

---

### I.8 Versioning and Evolution

#### Overview

Versioning is how an API changes without breaking its dependents. The mechanism choice — path, query, header, media type, or none — attracts most of the argument and is the least important part. What determines whether evolution works is whether you can answer three operational questions: what counts as a breaking change, who is still on the old version, and how do you turn it off.

#### Background

The discussion is usually framed as a choice between four transports. It is more useful as a choice between two philosophies — *version the interface* or *never break the interface* — with the transport an implementation detail of the first.

Two IETF documents supply the retirement machinery. [RFC 9745](https://www.rfc-editor.org/rfc/rfc9745.html) (Standards Track, March 2025) defines the `Deprecation` response header field. [RFC 8594](https://www.rfc-editor.org/rfc/rfc8594.html) (**Informational**, May 2019) defines `Sunset`. The status difference is real: one is a standard, the other an informational description of a convention.

#### The Strategies

**URI path** — `GET /v2/datasets/{id}`. Unambiguous, trivially routable, visible in every log line and curl command, cacheable with no `Vary` consideration because the URI *is* the cache key.

Its cost is conceptual: RFC 9110 §3.1 treats a URI as identifying a resource, and `/v1/datasets/42` and `/v2/datasets/42` are the same dataset presented differently, so the URI now identifies a representation format. It also forces clients to rewrite every URL, breaking stored links and making partial migration impossible.

**Query parameter** — `GET /datasets/{id}?version=2`. Easy to add and default. But the version participates in the cache key implicitly, is easy to omit (yielding a silent default), and mixes protocol metadata into a space used for resource selection. Rarely best; occasionally the only option available.

**Custom header** — `X-API-Version: 2`. Keeps URIs clean. In exchange the version is invisible in logs, address bars, and casual `curl`; it requires `Vary: X-API-Version` on every response or your CDN serves v1 bodies to v2 clients (see I.9); and intermediaries have no reason to preserve a custom header.

**Media type** — `Accept: application/vnd.example.dataset.v2+json`. The purist position: HTTP already has content negotiation, the version is a property of the *representation*, and `Vary: Accept` is standard and universally understood.

Its weaknesses are practical — verbose, awkward in browsers and API consoles, poorly supported by some tooling, and easy to get subtly wrong, since `Accept` is a preference list with qualities rather than a single value. Adoption is low relative to path versioning, so your users will need instructions.

**Never break (additive-only)** — do not version; make only changes that cannot break a conforming client. This is the strategy behind the longest-lived APIs in existence and the most demanding: it requires the first version to be right enough to live with, and it accumulates permanent scar tissue in the form of fields you regret. Its cost is paid by implementers, not callers.

#### What Actually Constitutes a Breaking Change

The obvious ones — removing an endpoint or field, renaming, changing a type — are rarely what breaks people, because they are obvious enough to catch in review. These are the ones that ship:

| Change                                        | Why it breaks a consumer                                                          |
|-----------------------------------------------|-----------------------------------------------------------------------------------|
| Adding a *required* request field             | Every existing caller's request becomes invalid                                   |
| Tightening validation (`maxLength` 500 → 100) | Previously accepted requests now 422                                              |
| Adding a value to a response enum             | Clients with exhaustive `match` on the old domain crash or fall through           |
| Removing a value from a *request* enum        | Callers sending it now fail                                                       |
| Changing an error code (400 → 422)            | Client error-handling branches silently stop matching                             |
| Changing the error *body shape*               | Any client parsing `detail` as a string breaks when it becomes an array           |
| Changing a default value                      | Callers relying on the old default get different behaviour with no request change |
| Changing result ordering                      | Any implicit "first item" assumption breaks                                       |
| Changing pagination page size                 | Fixed-size buffers and page-count logic break                                     |
| Making a sync operation async (200 → 202)     | Clients reading the body as the result get a job stub                             |
| Tightening rate limits                        | Working integrations start failing                                                |
| Adding a field a strict parser rejects        | `additionalProperties: false` or strict deserialisation fails                     |

That last row turns "additive-only is always safe" into a half-truth: adding a field is safe *only* if clients ignore unknown fields, which is a property of your consumers, not of your change.

The error-shape row is not hypothetical in Juniper. juniper-data emits two incompatible `detail` shapes: every hand-raised `HTTPException` uses a string, while FastAPI's un-overridden 422 handler emits an array of objects. A client writing `str(response.json()["detail"])` works until the first validation error.

#### Tolerant Readers and Their Limits

The robustness principle appears in API practice as the *tolerant reader*: ignore unknown fields, do not assume ordering, treat unknown enum values as a documented fallback, do not fail on extra data. It works, with two hard limits.

**It only helps if consumers implement it.** You cannot make third-party clients tolerant by declaring them so in your documentation. If any significant consumer deserialises strictly, adding a field is breaking for them regardless of policy.

**It hides errors as well as absorbing them.** A client silently ignoring an unknown enum value may be ignoring a state that matters — "payment failed" arriving as an unrecognised status that falls into the ignore branch is worse than a crash.

The workable synthesis: be tolerant about *structure* (unknown fields, ordering, extra data) and strict about *meaning* (unknown enum values in a semantically significant position should be surfaced, not swallowed).

#### Deprecation and Sunset

**`Deprecation`** — RFC 9745 §2 "allows a server to communicate to a client application that the resource in the context of the message will be or has been deprecated." The value is an Item Structured Header Field whose value MUST be a Date per RFC 9651 §3.3.7, so it uses the `@`-prefixed integer form. RFC 9745 §2.1 notes the date "may be in the future … or in the past".

**`Sunset`** — RFC 8594 §3 "allows a server to communicate the fact that a resource is expected to become unresponsive at a specific point in time." Its value is a plain HTTP-date.

RFC 9745 §4 covers the pairing and imposes an ordering constraint: "The timestamp given in the Sunset HTTP header field MUST NOT be earlier than the one given in the Deprecation header field." It also flags the format mismatch — "for historical reasons the Sunset HTTP header field uses a different data format for date" — which is a genuine trap: the two headers on one response are encoded differently.

**Link relations** connect these to documentation via the `Link` header of [RFC 8288](https://www.rfc-editor.org/rfc/rfc8288.html) (Standards Track, October 2017, obsoleting RFC 5988). RFC 9745 §3 *defines* the `deprecation` relation type and §6.2 registers it with IANA; RFC 8594 §6 defines `sunset` and §7.2 registers it.
The block below is a **combination**, not a quotation: RFC 9745 §3.1's examples pair `Deprecation` with `Link`, and §4 pairs `Deprecation` with `Sunset` — but §4's example carries no `Link`, so no single example in either RFC shows all three together.

```http
Deprecation: @1688169599
Sunset: Sun, 30 Jun 2024 23:59:59 UTC
Link: <https://developer.example.com/deprecation>; rel="deprecation"; type="text/html"
```

RFC 9745 §3.1 makes a point worth internalising: a `Link` with `rel="deprecation"` and *no* `Deprecation` header means the resource is not yet deprecated but its deprecation *policy* is discoverable.

Two constraints on expectations. RFC 8594 §3: "Clients SHOULD treat Sunset timestamps as hints: it is not guaranteed that the resource will, in fact, be available until that time and will not be available after that time." And RFC 9745 §5: "The act of deprecation does not change any behavior of the resource." A deprecated endpoint must keep working exactly as before. Deprecation is an announcement, not a behaviour change.

#### Migration Mechanics

Announcing is easy; completing requires four things.

**Dual-running** — both versions serve live traffic, backed by one implementation where possible (a translation layer at the edge) so behaviour cannot drift. Two independent implementations of "the same" API diverge, and users discover the divergence.

**Shadow traffic** — mirror a fraction of production v1 requests to v2, discard the responses, diff them against v1's. This finds behavioural differences under real traffic shapes no synthetic test generates, and costs nothing if the shadow path is genuinely side-effect-free (which requires care for mutations).

**Consumer-driven contracts** — each consumer publishes the subset it depends on; the provider verifies every contract in CI. This turns "is this change breaking?" from a judgement call into a test result. See I.11.

**Measuring who is left** — you cannot sunset what you cannot count. Instrument by version *and caller identity*, because "0.3% of traffic" and "one customer who will churn" are the same number and completely different decisions. Reach out to the named remainder; a broadcast announcement will not move them.

#### Juniper in Practice

juniper-data is versioned by URI path, and the version is a **string literal repeated across the codebase with no constant behind it**:

```python
app.include_router(health.router, prefix="/v1")
app.include_router(generators.router, prefix="/v1")
app.include_router(datasets.router, prefix="/v1")
```

That is `juniper_data/api/app.py:140-142`. It also appears hardcoded inside emitted payloads — `artifact_url` is built as `f"/v1/datasets/{dataset_id}/artifact"` at `juniper_data/api/routes/datasets.py:138` and again at `:253`. A repository-wide grep for `API_VERSION` in `juniper_data/` returns nothing.

The consequence is not that a `/v2` is impossible; it is that introducing one is a find-and-replace across an unbounded set of literals, including literals embedded in response bodies where a missed one produces a *working response containing a wrong URL* — a failure no type checker, linter, or router unit test catches.

The client libraries got this right: `juniper_data_client/constants.py:74` and `juniper_recurrence_client/constants.py:62` both define `API_VERSION_PATH_SUFFIX: str = "/v1"`. The consumers have the constant; the producer does not.

The cheap fix is one constant and a lint rule. The valuable insight is what the literal indicates: nobody has yet had to ship a v2, so the cost of the design has never been paid — and it will be paid all at once.

#### Judgement Calls

- **Whether to version at all.** For an internal API with a handful of known consumers and a shared deploy pipeline, never-break plus coordinated migration usually beats formal versioning.
- **Granularity.** Whole-API versions are simple and force unrelated consumers to migrate together; per-resource versions are precise and multiply your compatibility matrix.
- **How long to keep the old version.** Under six months is aggressive for a public API; over two years means maintaining it forever.
- **Whether to hard-cut at sunset.** A hard cut is honest and generates incidents. Brownouts — progressively higher error rates on a schedule — are kinder, notably effective, and notably unpopular.
- **Whether "adding a field" is breaking for you.** It depends entirely on your consumers' parsers, which is a fact about your ecosystem, not your API.

#### Tradeoffs

| Strategy        | Gain                                              | Cost                                                            |
|-----------------|---------------------------------------------------|-----------------------------------------------------------------|
| URI path        | Visible, routable, cacheable, trivially explained | URI stops identifying a resource; clients rewrite every URL     |
| Query parameter | Easy to add and default                           | Silent defaults; pollutes the query space; cache-key subtleties |
| Custom header   | Clean URIs                                        | Invisible in logs; needs `Vary`; poor tooling support           |
| Media type      | Uses HTTP as designed; `Vary: Accept` is standard | Verbose; awkward in browsers; low adoption; easy to get wrong   |
| Never version   | No migration ever; no version sprawl              | Permanent scar tissue; demands getting v1 nearly right          |

#### Best Practices

- Put the version in exactly one place in code. juniper-data's repeated `/v1` is the counter-example.
- Publish a written compatibility policy enumerating what you consider breaking; without one, every change is an argument.
- Send `Deprecation` and `Sunset` together with a `Link` `rel="deprecation"` to the migration guide, keeping `Sunset` no earlier than `Deprecation` per RFC 9745 §4.
- Instrument version usage by caller identity, not just percentage of traffic.
- Document the tolerant-reader expectation and test it: a consumer never sent an unknown field has never proven it tolerates one.
- Version error shapes as carefully as success shapes. They are parsed too.

#### Common Failure Modes

- **The version never retired.** v1, v2, and v3 in production forever, each with its own bugs.
- **Silent breaking change via validation tightening.** No schema field changed; previously valid requests now 422.
- **Enum expansion breaking exhaustive matches.** A new status value crashes strictly-typed clients.
- **The forgotten literal.** A `/v1` embedded in a response payload that migration misses — a 200 containing a dead URL.
- **Deprecating without measuring.** Sunset arrives, the endpoint is removed, and a customer nobody knew about goes down.
- **Two implementations of the same version.** They drift, and the drift is the migration bug.

#### Error Handling

- **Unknown version requested:** `400`, or `404` for a path version that does not route. Name the supported versions in the body.
- **Version present but retired:** `410 Gone` is more informative than `404`, and its permanence is the point.
- **During deprecation:** keep returning normal responses plus `Deprecation` / `Sunset` / `Link`. Do not degrade behaviour to encourage migration — RFC 9745 §5 says deprecation does not make behaviour changes.
- **Keep the error body shape stable across versions**, or version it explicitly. A client's error handler is the code least likely to have test coverage and most likely to run during an incident.

#### Controversy: URI Versioning vs Media-Type Versioning vs Never-Version

**The controversy.** There is no consensus on how — or whether — to version an HTTP API, and the disagreement is unusually sharp because it is partly technical and partly about what HTTP *is for*. The same three positions have been argued since the mid-2000s and none has won.

**The camps.** *URI versioners* put `/v1` in the path. *Media-type versioners* negotiate the version through `Accept`, treating it as a property of the representation. *Never-versioners* refuse to version at all and evolve additively.

**The background.** The split traces to a genuine ambiguity in the REST literature: a URI identifies a resource, and two versions of an API expose the *same* resources with different representations — which argues for content negotiation.

But content negotiation is comparatively unused, poorly supported in tooling, and invisible in a browser address bar, while path versioning is immediately legible to anyone who has ever read a URL. Practice diverged from theory and stayed there: the overwhelming majority of public APIs use path versioning, while the specification-literate minority regards that majority as wrong. Never-versioning grew out of watching organisations accumulate three live versions they could never retire.

**URI path versioning.**

- *Strengths.* Instantly legible; routable by any proxy; visible in logs, dashboards, and support tickets; cacheable with no `Vary` reasoning because the URI is the cache key; trivial to run two versions side by side; easy to explain to users.
- *Weaknesses.* The URI stops identifying a resource and starts identifying a representation format. Every client URL must be rewritten to migrate, breaking stored links. Partial migration is impossible — you move an entire client at once.
- *Risks.* Version sprawl, because adding `/v2` is cheap and retiring `/v1` is not. The version string leaks into payloads and documentation, as juniper-data's repeated `/v1` literal shows.
- *Guardrails.* One constant, never a literal. A written retirement policy before v2 ships. Per-version usage metrics from day one, keyed by caller.

**Media-type versioning.**

- *Strengths.* Uses a mechanism HTTP already defines for exactly this purpose. URIs stay stable and keep identifying resources, so links never break. `Vary: Accept` is standard and understood by every cache. Supports per-resource version granularity naturally.
- *Weaknesses.* Verbose vendor media types; awkward in browsers, consoles, and casual `curl`; uneven client-library support; and `Accept` is a preference list with qualities, so getting it exactly right is harder than it looks. Users need instructions, which means friction on every integration.
- *Risks.* A missing or wrong `Vary` turns it into a cache-poisoning bug (see I.9) — the failure mode is more severe than path versioning's. A default applied when `Accept` is absent silently pins clients to a version they never chose.
- *Guardrails.* Always emit `Vary: Accept`. Reject an unrecognised version explicitly rather than defaulting. Document the exact `Accept` string and provide copy-pasteable examples.

**Never-version (additive-only).**

- *Strengths.* No migration ever, no version sprawl, no dual-running, no sunset negotiation. Clients written years ago keep working. It sidesteps the entire mechanism argument.
- *Weaknesses.* Requires getting the first design close to right, which is rarely true of a first design. It accumulates permanent scar tissue: fields you regret, defaults you cannot change, enum values you cannot remove. "Additive-only is safe" is also only true if consumers tolerate unknown fields — a property of your ecosystem, not your policy.
- *Risks.* Pressure to smuggle breaking changes through as "clarifications" — tightening validation, changing a default — precisely the subtle class in the breaking-change table above. The discipline is easy to state and hard to hold over years.
- *Guardrails.* A written definition of breaking that includes the subtle cases. Consumer-driven contracts in CI so the definition is enforced rather than remembered. Schema diffing on every change. Accept that some mistakes become permanent, and design the first version knowing that.

**Recommendation** (labelled as such): for a public API with unknown consumers, use URI path versioning with a single constant and a retirement policy written before v2 exists — its legibility and operational simplicity outweigh its theoretical impurity, and the failure modes are visible rather than silent.

For an internal API with known consumers and a shared deploy pipeline, never-version plus coordinated migration is usually cheaper than any versioning scheme. Choose media-type versioning only when stable URIs are a genuine requirement (long-lived stored links, hypermedia navigation) *and* you are confident about `Vary` discipline across your whole cache hierarchy — because the cost of getting it wrong there is a data-disclosure incident rather than a 404.

---

### I.9 Caching

#### Overview

HTTP caching is the highest-leverage performance mechanism available to an API and the one most often left entirely unused — usually because the mental model is "caching is for static assets" and an API returns dynamic data. That model is wrong in a specific and expensive way: a great deal of API data is immutable, and immutable data is the easiest thing in the world to cache correctly.

This is the breadth treatment. Conditional requests — `ETag`, `If-None-Match`, `Last-Modified`, and the 304 flow — are covered in depth in Part II; this section cross-references rather than duplicates.

#### Background

[RFC 9111](https://www.rfc-editor.org/rfc/rfc9111.html) (Standards Track, June 2022, STD 98, obsoleting RFC 7234) defines HTTP caching. Two definitions from §1 anchor everything else:

> A "shared cache" is a cache that stores responses for reuse by more than one user; shared caches are usually (but not always) deployed as a part of an intermediary. A "private cache", in contrast, is dedicated to a single user; often, they are deployed as a component of a user agent.

That distinction — one user versus many — is the source of most caching security bugs. A response correctly cached in a browser is catastrophically wrong in a CDN.

RFC 9111 §2 defines the cache key as "composed from, at a minimum, the request method and target URI", noting that "many HTTP caches in common use today only cache GET responses and therefore only use the URI as the cache key." §2 also frames the specification's posture, which is easy to get backwards: "it can be assumed that reusing a cached response is desirable and that such reuse is the default behavior when no requirement or local configuration prevents it.

Therefore, HTTP cache requirements are focused on preventing a cache from either storing a non-reusable response or reusing a stored response inappropriately, rather than mandating that caches always store and reuse particular responses." Caching is the default; your headers *restrain* it. An API emitting no cache headers has not opted out — it has left the decision to heuristics.

#### Freshness Versus Validation

**Freshness** (§4.2) is time-based reuse with no network call: "A 'fresh' response is one whose age has not yet exceeded its freshness lifetime. Conversely, a 'stale' response is one where it has." This is the only path that eliminates latency entirely.

**Validation** (§4.3) is what happens when a response is stale but might still be usable: the cache asks the origin whether what it holds is still good, and a 304 confirms it without re-sending the body. This saves bandwidth, not round trips.

The implication: `max-age=0` plus an `ETag` gives correctness with a round trip on every request; `max-age=300` gives zero round trips for five minutes and up-to-five-minute staleness. Different products. Choose deliberately.

#### The Cache-Control Directive Families

##### `no-cache` versus `no-store` — the confusion that matters

These are constantly interchanged and mean nearly opposite things.

**`no-cache`** (§5.2.2.4) does **not** prevent storage. The response is stored; it simply cannot be *reused* without checking first — the directive "indicates that the response MUST NOT be used to satisfy any other request without forwarding it for validation and receiving a successful response".

Its purpose follows: it "allows an origin server to prevent a cache from using the response to satisfy a request without contacting it, even by caches that have been configured to send stale responses." `no-cache` means *always revalidate*, and it is entirely compatible with `ETag`: the cache stores the body, revalidates every request, and gets a cheap 304 most of the time.

**`no-store`** (§5.2.2.5) is the one that prevents storage: a cache "MUST NOT store any part of either the immediate request or the response and MUST NOT use the response to satisfy any other request", meaning it "MUST NOT intentionally store the information in non-volatile storage and MUST make a best-effort attempt to remove the information from volatile storage as promptly as possible after forwarding it."

The spec is equally precise about its limits: "This directive is not a reliable or sufficient mechanism for ensuring privacy. In particular, malicious or compromised caches might not recognize or obey this directive."

The rule: `no-store` for anything genuinely sensitive; `no-cache` when you want caching's bandwidth benefit with freshness guaranteed. Writing `no-cache` when you meant `no-store` leaves sensitive data on disk in every intermediary; writing `no-store` when you meant `no-cache` discards all of caching's benefit for no security gain.

##### `private`, `public`, `max-age`, `s-maxage`, `must-revalidate`

**`private`** (§5.2.2.7): "a shared cache MUST NOT store the response (i.e., the response is intended for a single user). It also indicates that a private cache MAY store the response … even if the response would not otherwise be heuristically cacheable." The spec attaches a warning worth quoting: "This usage of the word 'private' only controls where the response can be stored; it cannot ensure the privacy of the message content."

**`public`** (§5.2.2.9): "a cache MAY store the response even if it would otherwise be prohibited". Its main real use is overriding the default that responses to authenticated requests are not shared-cacheable — "public permits a shared cache to reuse a response to a request containing an Authorization header field". §5.2.2.9 also notes "it is unnecessary to add the public directive to a response that is already cacheable", so `public` on a plain unauthenticated GET is noise.

**`max-age`** (§5.2.2.1): "the response is to be considered stale after its age is greater than the specified number of seconds."

**`s-maxage`** (§5.2.2.10) overrides `max-age` *for shared caches only*, and carries a second implication easy to miss: "The s-maxage directive incorporates the semantics of the proxy-revalidate response directive … for a shared cache." It is the mechanism for "cache hard at the CDN, briefly in the browser" — `max-age=60, s-maxage=3600`.

**`must-revalidate`** (§5.2.2.2): once stale, a cache "MUST NOT reuse that response to satisfy another request until it has been successfully validated by the origin".

The spec is blunt about when it is warranted — it "ought to be used by servers if and only if failure to validate a request could cause incorrect operation, such as a silently unexecuted financial transaction" — and it has teeth: "if a cache is disconnected, the cache MUST generate an error response rather than reuse the stale response", with 504 suggested. It trades availability for correctness. Use it where you mean that trade.

##### The stale extensions

`stale-while-revalidate` and `stale-if-error` are **not** defined in RFC 9111. They come from [RFC 5861](https://www.rfc-editor.org/rfc/rfc5861.html) ("HTTP Cache-Control Extensions for Stale Content", May 2010), which is **Informational**, not Standards Track.

RFC 9111 §4.2.4 acknowledges them as an example of the permitted mechanism — a cache MUST NOT serve stale "unless it is disconnected or doing so is explicitly permitted by the client or origin server (e.g., … extension directives such as those defined in [RFC5861] …)" — and lists RFC 5861 in its **Informative** References, not its Normative ones.

`stale-while-revalidate=N` lets a cache serve stale immediately and revalidate in the background, hiding revalidation latency; `stale-if-error=N` lets it serve stale content when the origin errors, trading freshness for availability. Both are widely implemented by CDNs and genuinely valuable — but describe them as an Informational extension, not part of the caching standard.

#### `Vary`, and Why It Is the Usual Cause of Cache Bugs

`Vary` tells a cache that the key is not just the URI. RFC 9111 §4.1: a cache "MUST NOT use that stored response without revalidation unless all the presented request header fields nominated by that Vary field value match those fields in the original request".

**`Vary` too narrow (omitted) → poisoning and leakage.** You serve different content based on `Authorization`, `Accept-Language`, or a version header and do not declare it. A shared cache stores one user's response under a URI-only key and serves it to everyone.

Not a subtle performance issue — a data-disclosure incident. RFC 9111 §7.1 names the general class: "Storing malicious content in a cache can extend the reach of an attacker to affect multiple users … This is especially effective when shared caches are used to distribute malicious content to many clients."

**`Vary` too wide → zero hit rate.** `Vary: User-Agent` fragments the cache across every browser build; `Vary: *` "always fails to match" per §4.1, disabling reuse entirely. A cache with a 0% hit rate is pure added latency.

§4.1 documents a trap for the inconsistent case too: "Some resources mistakenly omit the Vary header field from their default response … with the effect of choosing it for subsequent requests to that resource even when more preferable responses are available." Emitting `Vary` on some responses from a URI and not others produces a cache that behaves differently depending on which response landed first.

The discipline: `Vary` must name **exactly** the request headers that change the body — every one, and no others. If you version by header, `Vary` on it. If you negotiate content, `Vary: Accept`. If you serve per-user data, prefer `private` or `no-store` over trying to `Vary` on `Authorization`.

#### Invalidation and Immutable URLs

Invalidation is genuinely hard when content at a stable URL changes: purge APIs are eventually consistent and per-CDN; TTL expiry is simple but slow. The way out is to make invalidation unnecessary.

**Content-addressed URLs** derive the identifier from the content, so different content has a different URL and the old URL never needs invalidating. This converts the hardest problem in caching into a naming convention. It is why asset pipelines emit `app.a3f8e12b.js`, and it applies to APIs whenever a resource is genuinely immutable.

#### Juniper in Practice: The Strongest Candidate, Unused

juniper-data (v0.11.0) has a textbook caching candidate and emits no cache headers at all.

`GET /v1/datasets/{id}/artifact` serves a dataset's NPZ blob. The `{id}` is content-addressed: `generate_dataset_id` (`juniper_data/core/dataset_id.py:23-61`) derives it from a SHA-256 over canonical JSON of generator, version, and parameters.

**The body for a given id cannot change.** A SHA-256 over the serialized artifact bytes is *already computed and stored* — `compute_checksum` (`juniper_data/core/artifacts.py:50-63`) returns `hashlib.sha256(arrays_to_bytes(arrays)).hexdigest()`, persisted on `DatasetMeta.checksum`. The response is large and clients download it repeatedly.

Every ingredient is present: an immutable resource, a stable content-derived URL, a precomputed strong validator, and a payload big enough to matter. None reaches HTTP. The artifact response (`juniper_data/api/routes/datasets.py:700-704`) sets exactly one header:

```python
import io

def artifact_response(dataset_id: str, artifact_bytes: bytes) -> StreamingResponse:
    """Excerpt of routes/datasets.py:700-704 — the only header it emits."""
    return StreamingResponse(
        io.BytesIO(artifact_bytes),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={dataset_id}.npz"},
    )
```

A repository-wide grep across `juniper_data/` for `ETag`, `Cache-Control`, `Last-Modified`, `If-None-Match`, `Vary`, and 304 handling returns nothing. The only `max-age` in the codebase is inside the HSTS header value (`juniper_data/api/constants.py:69`). The stored `checksum` is a strong `ETag` waiting to be emitted; three lines would enable both freshness and the conditional-request fallback:

```python
headers = {
    "Content-Disposition": f"attachment; filename={dataset_id}.npz",
    "ETag": f'"{meta.checksum}"',
    "Cache-Control": "private, max-age=31536000, immutable",
}
```

`private`, not `public`, and the reason is the endpoint's own authentication. This route is not on juniper-data's exempt list — `EXEMPT_PATHS` (`juniper_data/api/constants.py:33-41`) covers only health, docs,
and `/metrics` — so with API keys configured it requires `X-API-Key`. Because that credential is a *custom header* rather than `Authorization`, a shared cache has no way to tell the request was authenticated at all: §5.2.2.9's "public permits a shared cache to reuse a response to a request containing an Authorization header field" does not describe this situation, and no default protects it either.
`public` here instructs every intermediary to store the body and hand it to anyone requesting the same URI for a year, with `immutable` suppressing the revalidation that might have caught it. Reserve `public` for genuinely public resources; behind authentication use `private`, or `no-store` when the payload is sensitive.

Do not reach for `Vary: X-API-Key` as a substitute. `Vary` only binds a cache that already parses and honours it, and an intermediary has no reason to treat an unrecognised custom header as part of the cache key — which is the same reason §4.1's "too narrow" failure is a disclosure bug rather than a performance one.

The lesson generalises: a checksum in your data model is not an HTTP validator. Someone has to decide to put it on the wire, and in most codebases nobody has, because the data layer and the HTTP layer are owned by different people at different times.

#### Judgement Calls

- **Freshness or validation.** A long `max-age` is free but stale. `no-cache` plus `ETag` is always correct and always a round trip. Immutable content deserves the longest `max-age` you will write.
- **Where to cache.** Origin memory (fast, per-process, invisible to clients), a shared reverse proxy (one invalidation point), a CDN (closest to users, hardest to purge), or the client (free, entirely outside your control).
- **How stale is acceptable.** A product question dressed as a technical one; answer it per resource, not globally.
- **`private` or `no-store` for user data.** `private` allows browser caching, usually what you want; `no-store` is for data that must not touch disk anywhere.
- **`must-revalidate` or not.** It converts a cache outage into an error rather than stale data — correct for financial state, wrong for a product catalogue.

#### Tradeoffs

| Choice                               | Gain                                       | Cost                                                       |
|--------------------------------------|--------------------------------------------|------------------------------------------------------------|
| Long `max-age`                       | Zero round trips; maximum offload          | Stale for the full duration; no way to recall it           |
| `no-cache` + `ETag`                  | Always fresh; big bandwidth saving on 304s | A round trip on every request                              |
| `s-maxage` split                     | Hard CDN caching, fresh browsers           | Two lifetimes to reason about                              |
| `immutable` + content-addressed URLs | Invalidation becomes unnecessary           | Requires content-derived identifiers                       |
| `Vary` on a header                   | Correct negotiated caching                 | Every added header multiplies fragmentation                |
| No cache headers at all              | Nothing to get wrong                       | Full origin load; heuristic caching may still surprise you |

#### Best Practices

- Emit an explicit `Cache-Control` on every response; silence means heuristics, and heuristics are not your policy.
- Mark immutable, content-addressed resources aggressively — `public, max-age=31536000, immutable` when the resource is genuinely public, `private, ...` when it sits behind authentication. `public` on an authenticated endpoint tells every shared cache to serve one caller's body to the next.
- Emit a strong `ETag` whenever you already have a content digest — juniper-data's unused `checksum` is the case in point.
- Name every request header that affects the body in `Vary`, and nothing else.
- Split browser and CDN lifetimes with `max-age` plus `s-maxage` when they should differ.
- Verify cache behaviour in tests: assert the headers you expect and, at least once, assert a second request actually hits.

#### Common Failure Modes

- **`no-cache` written where `no-store` was meant.** Sensitive data stored throughout the hierarchy while the author believes it is not stored at all.
- **Missing `Vary` on a negotiated or header-versioned response.** One user's data served to another by a shared cache — the most serious caching bug there is.
- **A cached error.** A 500 with a long `max-age` outlives the outage that produced it.
- **Purge that does not propagate.** CDN purge is eventually consistent and per-POP; treat it as a hint.
- **The uncached immutable blob.** juniper-data's artifact endpoint: repeated full downloads of bytes that cannot have changed, with the digest already in the database.
- **Heuristic freshness surprising you.** With no explicit lifetime, RFC 9111 §4.2.2 permits caches to invent one. "We never set a cache header" is not "it is not cached".

#### Error Handling

- **Never cache 429** — RFC 6585 §4.
- **Cache 404 only deliberately and briefly.** RFC 9111 §2 permits storing negative results; a long-cached 404 for a resource about to exist is a support ticket.
- **Do not cache 5xx** unless you specifically want `stale-if-error` behaviour — which serves *previously good* content on error, the opposite of caching the error.
- **A cache miss is not an error.** Alert on hit *ratio*, not individual misses.
- **A disconnected cache holding `must-revalidate` content must error, not serve stale** (§5.2.2.2, 504 suggested). If that is unacceptable for your resource, you should not have used `must-revalidate`.
- **Failure to compute a validator is not a reason to omit caching.** Fall back to `Last-Modified` or time-based freshness. Emitting nothing is the worst option available.

---

### I.10 Observability for APIs

#### Overview

An API boundary is the one place where every request is visible, attributable, and comparable — the highest-value observability surface in the system, and the easiest to instrument badly, because the natural instrumentation (log the request, count it by URL) is precisely the one that takes production down.

#### Background

The three pillars map onto an API boundary with little friction. **Logs** are the per-request record: what was asked, by whom, what happened — high cardinality, high detail, expensive at volume. **Metrics** are aggregates: cheap, queryable, bounded, *provided* the label space is bounded.

**Traces** are causal chains across services: expensive per trace, usually sampled. They answer different questions and none substitutes for another. Metrics tell you *that* p99 tripled; traces tell you *where* the time went; logs tell you *what* the failing requests had in common.

#### Metrics: RED, and Why Histograms Beat Averages

RED — **R**ate, **E**rrors, **D**uration — is the canonical starting set: requests per second, error rate, and a latency *distribution*.

"Distribution" is load-bearing. A mean latency is nearly useless for a service: it is dominated by the bulk and blind to the tail. Where 99% of requests take 10 ms and 1% take 5 s, the mean is about 60 ms — a number no user experiences, and one that will barely move if the slow 1% becomes 3%.

Percentiles from a histogram fix this. p50 is the typical experience, p99 the bad one — and p99 matters more than its 1% weight suggests, for two compounding reasons. **Fan-out:** if a page makes 100 backend calls, the probability at least one hits the p99 is `1 - 0.99^100 ≈ 63%`, so the 99th-percentile backend latency is the *majority* case for the page.

**Queueing:** slow requests hold connections, threads, and memory, so the tail is where saturation begins and p99 degradation is the leading indicator of the outage p50 will only show once it is happening.

One caveat that is easy to get wrong: percentiles do not average across instances. Averaging four replicas' p99 values produces a number with no meaning. Aggregate the *histogram buckets*, then compute the percentile.

Juniper's shared middleware exports exactly the RED trio — `http_requests_total{method, endpoint, status}` and `http_request_duration_seconds{method, endpoint}` as a Histogram, plus an unmatched-route counter (`juniper-observability`, `juniper_observability/middleware/prometheus.py:49-66`).

#### Cardinality: The Classic Production Outage

Every distinct combination of label values creates a distinct time series, and each series costs memory. Label an HTTP metric by the **raw request path** and the label space becomes the set of URLs anyone can request — unbounded and, critically, **attacker-controlled**. Legitimate traffic alone produces one series per dataset id; a crawler hitting random 404 paths produces one series per request.

Series count grows without bound, memory follows, and the monitoring system dies — usually during the incident it exists to help you diagnose, because that is when unusual paths are most frequent.

The fix is to label by the **resolved route template**, bounded by the number of routes you wrote. Juniper's `PrometheusMiddleware` does exactly this (`juniper_observability/middleware/prometheus.py:77-84`):

```python
route = request.scope.get("route")
template = getattr(route, "path", None) if route is not None else None
method = request.method
if template:
    endpoint = template
else:
    endpoint = UNMATCHED_ENDPOINT_LABEL
    self._unmatched_count.labels(method=method).inc()
```

Two details worth copying. The template comes from `request.scope["route"]`, so `/v1/datasets/abc-123` and `/v1/datasets/def-456` both label as `/v1/datasets/{dataset_id}` — one series.

And anything matching no route collapses to a single `_unmatched` label (`juniper_observability/constants.py:22`) *and* increments a separate one-label counter, so scanning traffic stays visible as a signal without ever expanding the main metric's label space. The module docstring states the intent: "This bounds Prometheus label cardinality under attacker-controlled paths or path-parameter routes."

The same discipline applies to every label. User id, tenant id, session id, request id, full error message, and raw query string are all cardinality bombs. Identity belongs in logs and traces, which are built for high cardinality; metric labels must be drawn from a small, enumerable set.

#### Tracing and Correlation

Distributed tracing follows one logical request across services, and its load-bearing requirement is **context propagation**: each service must read the incoming context and pass it on. A service that drops it severs the trace and orphans every downstream span.

The interoperable format is [W3C Trace Context](https://www.w3.org/TR/trace-context/), a **W3C Recommendation**, defining `traceparent` (trace id, parent span id, sampling flags) and `tracestate` (vendor-specific data). Because it is a Recommendation rather than a vendor format, tracing systems from different vendors can participate in one trace.

A **correlation ID** is the cheaper cousin: one identifier on every log line for a request — the trace id when tracing exists, a UUID when it does not. It costs almost nothing and is the difference between "search the logs" and "filter by one field".

Juniper implements the cheap version. `RequestIdMiddleware` (`juniper_observability/middleware/request_id.py:36-43`) reads `X-Request-ID`, generates a UUID4 if absent, stores it in a `ContextVar`, echoes it on the response, and resets the token in a `finally`. The `ContextVar` is the right mechanism — per-task under `asyncio`, so concurrent requests cannot see each other's id — and the reset prevents leakage across tasks reusing a context.

One caveat, stated precisely because it is easy to overstate: the inbound header is propagated **verbatim, with no length or charset validation**. Within juniper-observability's own sinks this is contained — the JSON formatter serialises through `json.dumps` (`juniper_observability/logging.py:42-53`), which escapes control characters, and the plain-text formatter (`logging.py:25`, applied at `:81`) does not include `request_id` at all.

The exposure is at the *propagation contract*: the unvalidated value is echoed into a response header (`request_id.py:40`) and is available from the `ContextVar` to any consumer that writes it to a line-oriented sink, where CRLF forges log records. Validate on ingress — length cap and character allowlist — rather than relying on every downstream consumer to escape correctly.

#### Health Endpoints: Liveness Versus Readiness

- **Liveness** — "is this process broken beyond recovery?" Failure means *restart me*. It must depend on nothing external.
- **Readiness** — "should traffic be routed to me right now?" Failure means *stop sending traffic*, and may be temporary. It may legitimately check dependencies.

The failure mode when merged: a shared database slows, the combined check fails on every replica, the orchestrator concludes every replica is dead and restarts them all, restarts add cold-start load to the struggling database, and the cluster enters a restart loop that outlives the original problem. The database recovers; the cluster does not.

juniper-data separates them properly. `GET /health/live` (`juniper_data/api/routes/health.py:146-183`) runs an *in-process* tick against a strict budget and returns 503 `{"status": "unresponsive"}` only if the tick throws or exceeds `LIVENESS_TICK_BUDGET_MS` — no dependency consulted.

`GET /health/ready` (`:186-240`) probes storage and maps the result to a status code, documenting the contract in its docstring: 200 `ready`, 200 `degraded` (required deps healthy, an optional dep unhealthy), 503 `not_ready`. The `degraded`/`not_ready` distinction is the useful one — an optional dependency being down should not remove you from the load balancer.

Readiness probes run constantly, so their cost matters. juniper-data's readiness globs the storage directory, O(n) in dataset count, so it caches the result for 5 seconds (`health.py:63-104`) with the reasoning in the code: "orchestrators poll readiness every few seconds — a stale-tolerant 5s cache cuts the steady-state cost to one glob per cache window without instrumenting every dataset save / delete path".

The cache key includes the configured storage path so a tmpdir test fixture invalidates it, and the comment notes racing probes are benign. That is the right shape: bounded staleness, an explicit invalidation key, and the tradeoff documented where it is made. The probe also runs off the event loop via `asyncio.to_thread` (`health.py:208`), because a blocking `glob` in an async handler stalls every other request on that worker.

#### What to Log, and What Never To

Log per request: method, resolved route template, status, duration, correlation id, caller identity (an id, not credentials), and on errors an exception type and stack trace.

Never log: passwords, API keys, tokens, session identifiers, `Authorization` values, full request or response bodies from user-facing endpoints, PII beyond what you have a documented reason and retention policy for, or full query strings (which routinely carry tokens).

Two mechanisms make this hold. A **redacting formatter** enforces the rule in infrastructure rather than in every author's memory. **Structured logging** — key-value fields rather than interpolated strings — lets redaction operate on fields and frees queries from regex over prose.

Juniper's `JuniperJsonFormatter` (`juniper_observability/logging.py:31-53`) emits a fixed key set (`timestamp`, `level`, `logger`, `message`, `service`, `request_id`, plus `exception`), and its docstring gives the reason: "Always emits the same set of top-level keys so log shippers can parse every Juniper service's logs without per-service rules."

A related discipline is sanitising untrusted text before it reaches a log line. `juniper-service-core` strips `\r` and `\n` from any Origin or command text it logs on a WebSocket rejection (`juniper_service_core/websocket/control_security.py:30-31`, used at `:49`) precisely so a hostile value cannot forge additional records.

#### Judgement Calls

- **Trace sampling rate.** 100% is complete and expensive; 1% loses the rare failure you most want. Tail-based sampling — decide after the request, keep the slow and the failed — is best where tooling supports it.
- **Log level in production.** DEBUG is unaffordable at volume and indispensable during an incident; runtime-adjustable levels are worth the cost.
- **Whether to log request bodies.** Enormously useful and a direct route to logging credentials. If you do it, use an endpoint allowlist with field-level redaction.
- **Histogram bucket count.** Each bucket is a series per label combination; too few loses resolution, too many multiplies series.
- **Whether readiness checks dependencies.** Checking makes readiness meaningful and couples your availability to your dependency's; not checking keeps you in rotation while broken.

#### Tradeoffs

| Choice                      | Gain                                    | Cost                                         |
|-----------------------------|-----------------------------------------|----------------------------------------------|
| Label by route template     | Bounded cardinality; safe under attack  | Cannot see per-resource traffic in metrics   |
| Label by raw path           | Per-resource visibility                 | Unbounded, attacker-controlled series growth |
| 100% trace sampling         | Every request explicable                | Storage and ingest scale with traffic        |
| Tail-based sampling         | Keeps the interesting traces            | Requires buffering; more complex pipeline    |
| Structured logs             | Queryable, redactable, machine-parsable | Verbose; less pleasant to read raw           |
| Cached readiness            | Cheap under constant polling            | Up to TTL seconds of stale readiness         |
| Separate liveness/readiness | No restart loops on dependency failure  | Two endpoints and two semantics to maintain  |

#### Best Practices

- Label metrics by resolved route template, never raw path, with an explicit `_unmatched` bucket.
- Count unmatched requests separately so scanning stays visible without inflating cardinality.
- Use histograms for latency; aggregate buckets before computing percentiles.
- Propagate `traceparent` / `tracestate` unmodified through every service.
- Attach a correlation id to every log line and echo it in the response so users can quote it.
- Separate liveness from readiness; make liveness depend on nothing external.
- Alert on symptoms (error rate, p99) rather than causes (CPU). Users experience symptoms.

#### Common Failure Modes

- **Cardinality explosion.** Raw paths, user ids, or error strings as labels; kills monitoring during the incident.
- **Averages instead of percentiles.** The tail is invisible until it is an outage.
- **Broken trace propagation.** One service drops the context; every trace ends there.
- **Merged liveness and readiness.** Dependency slowness becomes a cluster-wide restart loop.
- **Expensive readiness probe.** An uncached O(n) probe polled every second becomes its own load problem.
- **Credentials in logs.** Usually via a logged full request, a logged exception carrying request context, or a logged query string.
- **Logging 429s at ERROR.** Trains operators to ignore the error log.

#### Error Handling

- **Log errors once, at the boundary where they are handled.** Logging at every level turns one failure into six lines and makes counting impossible.
- **Include the correlation id in the error response body**, not just headers, so a user can paste it into a ticket.
- **Never put internal detail in an error response.** Stack traces, file paths, and internal type names go to the log; the response gets a stable code and the correlation id. juniper-data does this in batch-create by replacing exception text with a 12-hex correlation id (`juniper_data/api/routes/datasets.py:433-447`).
- **Observability failures must never fail the request.** A metrics backend being down must not produce a 500.
- **Distinguish client from server errors in metrics.** A 4xx spike is a caller problem; a 5xx spike is yours. One combined "error rate" hides both.
- **Alert on the absence of signal.** Zero requests to an endpoint that normally receives thousands is a failure no error-rate alert will fire on.

---

### I.11 Testing APIs

#### Overview

Testing an API means testing a contract, not a function. The unit of correctness is what a caller observes over the wire — status, headers, body shape, side effects — and a test that verifies the handler while bypassing routing, middleware, serialisation, and auth is not testing the API. This section covers the layers, what each is good for, and the failure mode where a suite is entirely green over an application that cannot start.

#### Background

The pyramid holds at an API boundary, with layer-specific caveats. **Unit** tests a function in isolation — fast, precise, blind to composition; Juniper's `RateLimiter` tests (`juniper-service-core`, `tests/test_security.py:129-185`) drive `check()` and the properties directly.

**Integration** exercises the real application, middleware, and routing with external dependencies mocked; this is where API contracts live and where most effort belongs. **Contract** verifies that provider and consumer agree independently of either's internals. **End-to-end** runs the whole system with real dependencies: highest confidence, slowest, flakiest, and the layer to keep smallest.

#### In-Process ASGI Versus Over a Socket

**In-process.** `TestClient` (or `httpx.ASGITransport`) calls the ASGI application directly, with no socket. Fast and debuggable — a breakpoint in a handler is reachable from the test — and it faithfully exercises routing, middleware, dependency injection, and serialisation.

What it does not exercise: the HTTP server itself (uvicorn's parsing, header handling, timeouts), real connection management, TLS, HTTP/2, and anything depending on genuine chunked transfer.

Juniper's body-limit test hits this boundary directly: because `TestClient` and `httpx` rewrite `Content-Length` from the payload, testing an *under-declared* `Content-Length` requires driving the ASGI app manually with a hand-built scope and a fake `receive` channel (`tests/test_middleware.py:142-188`), and the test's docstring names the reason. When your test client is too helpful, drop a layer.

**Over a socket.** Start a real server, make real requests. Catches server-layer behaviour and nothing else does. Slower, needs port management, and produces a class of flakiness (startup races, port reuse) that in-process tests do not have.

The pragmatic split: everything in-process, plus a handful of socket-level smoke tests proving the server actually binds and serves.

#### Contract and Schema-Based Testing

**Consumer-driven contract testing** (Pact being best known) inverts the direction: each consumer writes the interactions it depends on, publishes them as contracts, and the provider verifies every published contract in CI. The provider then learns *before merging* that a change breaks a specific consumer, turning I.8's "is this breaking?" judgement into a test result.

Its limits are real — it covers only interactions consumers thought to declare, requires participation, and adds a broker to CI — and it is disproportionately valuable when consumers and providers ship independently.

**Schema-based testing** goes the other way: derive tests from the OpenAPI document, generating conforming requests and asserting conforming responses. Cheap, broad, and good at finding drift — but only to the extent the schema is accurate.

That qualification is where most codebases fail. juniper-data declares no `responses={...}` on any route, so none of its 404, 400, 401, 429, or 413 responses appear in the generated schema — only the success code plus FastAPI's automatic 422. Schema-based testing against that document would verify the happy path and nothing else, while reporting full coverage of the documented surface. A schema that omits error responses is not a weaker contract; it is a contract that makes the untested paths invisible.

#### Property-Based and Fuzz Testing

Example-based tests check the cases you thought of; property-based tests (Hypothesis) check properties over generated inputs and shrink failures to a minimal reproducer. Properties that hold at an API boundary:

- Any request accepted by the schema returns a schema-conforming response — never a 500.
- Round-trip: `POST` then `GET` returns what was posted, modulo documented normalisation.
- Idempotency: the same request with the same key twice yields identical responses.
- Pagination: concatenating all pages equals the unpaginated result, with no duplicates and no gaps.
- Ordering is stable across identical requests.

Fuzzing is the adversarial version — malformed JSON, deep nesting, enormous strings, wrong content types and methods, header injection. Its value is not finding logic bugs but finding *crashes*: any input that reaches your handler and throws unhandled is a finding, and 500s from malformed input are both a reliability and an information-disclosure problem.

Juniper has a good example of the class in the WebSocket path: `json.loads("[]")` succeeds, so a JSON-valid *non-object* passes the parse and then `[].get(...)` raises `AttributeError` inside the receive loop, tearing down the connection. The fix is an explicit shape check after the parse (`juniper_service_core/websocket/control_stream.py:203-209`). Parse success is not shape success — a property no example-based test was likely to have covered.

#### The Least-Tested, Highest-Risk Paths

Three categories are systematically under-tested, sharing a cause: they are inconvenient to provoke.

**Error paths.** Tests follow the happy path naturally. Error handling is the code that runs during an incident, and where inconsistencies hide — juniper-data's two incompatible `detail` shapes (string from hand-raised `HTTPException`, array-of-objects from FastAPI's 422) is exactly what a success-only suite never surfaces.

**Auth paths.** Test all four quadrants: no credential, invalid credential, valid credential with insufficient authority, valid credential with authority. Juniper's middleware suite covers the first three (`tests/test_middleware.py:204-221`) and also pins the *exemption* logic — that `/v1/health` stays reachable without a key when auth is on (`:223-228`) — the assertion that catches someone accidentally securing the liveness probe.

**Rate limits.** Awkward, because a correct test must exceed the limit without being timing-dependent. The technique is to construct a tiny limit rather than send many requests: Juniper builds `RateLimiter(requests_per_minute=1)` and sends two (`tests/test_middleware.py:252-273`). That test names its own reason for existing:

```python
def test_security_middleware_rate_limit_429_json_preserves_retry_after():
    """HTTPException from RateLimiter must surface as JSONResponse with Retry-After headers.

    Pins the middleware catch path (``except HTTPException`` -> ``JSONResponse(..., headers=)``)
    that unit tests of ``RateLimiter.__call__`` alone cannot exercise.
    """
```

This is the gap made concrete. `RateLimiter.__call__` raises an `HTTPException` carrying `Retry-After` and three `X-RateLimit-*` headers (`juniper_service_core/security.py:231-240`). Every unit test of the limiter can assert the exception carries the right headers and pass.

But because the limiter is invoked directly from middleware rather than as a FastAPI dependency, FastAPI's exception handlers never run — the middleware must catch and rebuild the response itself (`middleware.py:181-186`). Delete `headers=exc.headers` from that reconstruction and **every limiter unit test still passes** while the 429 goes out with no `Retry-After`. The bug lives in the seam between two correctly-tested components.

The generalisable rule: **test the composition, not just the components.** Wherever component A raises and component B translates that into a response, the translation needs its own test at the boundary — because both components are individually correct and the system is still broken.

#### The Masked-Seam Failure Mode

This is the failure that produces a fully green suite over an application that is dead on boot.

Some integration boundary is inconvenient in tests — a service client needing a live peer, a database connection, an HTTP session, a settings object reading the environment. Someone adds a broad fixture to mock it:

```python
@pytest.fixture(autouse=True, scope="session")
def _mock_upstream_client(monkeypatch_session):
    """Replace the upstream client everywhere so tests don't need a live peer."""
    monkeypatch_session.setattr("myapp.clients.UpstreamClient", FakeUpstreamClient)
```

`autouse=True` applies it to every test; `scope="session"` applies it for the entire run. From that moment, **no test ever exercises the real construction path.** If `UpstreamClient.__init__` raises on a missing environment variable, if its import fails, if the constructor signature changed, if the module no longer exists — the suite cannot tell you.

The mock is installed before anything real is touched. The suite stays green; the application fails on boot at the first real construction. Coverage tooling does not help: the mocked module may still be imported and report lines covered by other tests, and coverage measures execution, not realism.

How to detect it:

1. **Grep for the pattern.** `autouse=True` combined with `scope="session"` or `scope="module"` on a fixture patching a constructor, client, or transport is the signature. juniper-ml treats this as a first-class audit, shipping a dedicated read-only `mock-seam-auditor` agent (`.claude/agents/mock-seam-auditor.md`) whose only job is hunting fixtures that mask an integration boundary broadly enough that the real path is never exercised.
2. **Add one un-mocked construction test** that builds the real object graph — app factory, real client constructors, real settings — with no autouse fixture in scope. It need not make a network call; construction is where boot failures live.
3. **Add a boot smoke test in CI.** Start the real application against real configuration and hit `/health/live`. This is the socket-level test that earns its slowness.
4. **Scope mocks as narrowly as the test needs.** Function-scoped, explicitly requested fixtures confine masking to tests that asked for it.

The underlying principle: a mock at an integration boundary asserts that your understanding of the boundary is correct. If nothing checks that assertion against the real thing, the mock is not a test double — it is an unverified assumption with test coverage attached.

#### Backward Compatibility and Load Testing

**Backward compatibility** is testable, and mostly is not tested. Three mechanisms, ascending in strength: schema diffing in CI against the previous released OpenAPI document, flagging removals and tightenings; golden-file tests pinning exact response bodies so any shape change is a visible diff; and consumer contract verification, strongest because it encodes what consumers actually depend on rather than what the schema permits.

Test with *old* client versions too — the compatibility that matters is with the code your users are running.

**Load testing** answers where latency knees, what breaks first, whether the system degrades or collapses, and whether it recovers afterwards. That last question is the most valuable and least often asked.

What it does not tell you: behaviour under *real* traffic shape (synthetic load is uniform; real load is bursty and correlated), behaviour with a real cache hit ratio (a load test against a warm cache measures the cache), behaviour under partial failure, or behaviour with real data distributions. Results are a lower bound on trouble, not a capacity guarantee.

#### Judgement Calls

- **How much end-to-end.** Enough to prove the system composes; few enough that they are not why CI is slow and flaky. A single boot-and-health-check often carries most of the value.
- **Mock or real dependency.** Real dependencies find integration bugs and make tests slow and flaky; mocks are fast and can mask the seam; container-based real dependencies are a middle path with real setup cost.
- **Whether to test the framework.** Do not test that FastAPI routes correctly. Do test that *your* route, with *your* middleware stack, returns what you documented.
- **Coverage targets.** Useful as a floor, misleading as a goal — the masked-seam failure is invisible to coverage by construction.
- **Test the schema or the implementation.** Ideally both, asserting they agree; juniper-data's missing `responses={...}` means schema and implementation disagree about the entire error surface.

#### Tradeoffs

| Choice                    | Gain                                        | Cost                                                        |
|---------------------------|---------------------------------------------|-------------------------------------------------------------|
| In-process ASGI tests     | Fast, debuggable, faithful to app behaviour | Misses server-layer behaviour; client rewrites some headers |
| Socket-level tests        | Real server, real HTTP                      | Slow; port management; startup races                        |
| Broad autouse mocks       | Convenient; fast; no external setup         | Masks the real path entirely; green suite over dead app     |
| Narrow explicit mocks     | Real path stays exercised elsewhere         | More fixture code; more per-test setup                      |
| Consumer-driven contracts | Breaking changes caught before merge        | Requires consumer participation and a broker                |
| Schema-based testing      | Broad coverage cheaply                      | Only as good as the schema; blind to undeclared responses   |
| Property-based testing    | Finds cases nobody thought of               | Slower; failures need interpretation                        |

#### Best Practices

- Test through the full request path — routing, middleware, serialisation — not the handler in isolation.
- Test the composition wherever one component raises and another translates; the Juniper 429 header-passthrough test is the model.
- Keep at least one test that constructs the real object graph with no autouse mocks in scope.
- Scope mocks to the narrowest fixture that works; treat `autouse` plus session scope on a boundary as a finding requiring justification.
- Assert error responses — status, shape, headers — as rigorously as success responses.
- Pin response bodies with golden files so shape changes are visible in review.
- When the test client is too helpful, drop to the layer below rather than skipping the test.

#### Common Failure Modes

- **The masked seam.** Broad autouse/session mocks over an integration boundary; green suite, dead app.
- **Only the happy path.** Error handling, the code that runs during incidents, is the least covered.
- **Timing-dependent rate-limit tests.** `sleep`-based tests that pass locally and flake in CI.
- **Testing the schema instead of the behaviour.** Passes while the API returns undocumented shapes.
- **Coverage as a proxy for confidence.** High coverage over mocked seams is high coverage over nothing.
- **Load testing a warm cache.** Measures the cache; says nothing about origin capacity.
- **Never testing with old clients.** Backward compatibility verified only against the current client.

#### Error Handling

- **Assert on the whole error response** — status *and* body shape *and* headers. A test checking only the status will not notice that `Retry-After` vanished.
- **Test that unexpected exceptions become 500s with no internal detail leaked**, and that the correlation id is present so the response is diagnosable.
- **Test the error-shape contract explicitly.** If your API can return `detail` as both a string and an array, a test should either document that or fail.
- **Make test failures diagnostic.** `assert response.status_code == 200` says nothing about why; include the body in the assertion message.
- **Do not swallow exceptions in fixtures.** A teardown that catches and ignores turns a real failure into a passing test with a mysterious side effect.

### I.12 Part I Worked Example — Making a Non-Idempotent POST Safe to Retry

This example implements the idea at the centre of Part I: a client cannot tell a lost request from a lost response, so a `POST` that starts real work must be made replay-safe before it is safe to retry.

It is drawn directly from a live defect in this ecosystem. `juniper-cascor-client` retries `POST /v1/training/start` on transient 5xx (`juniper_cascor_client/constants.py:37`) with no idempotency key, so a dropped response can start a second training run on the same GPU. Its sibling `juniper-data-client` carries the fix and cites the specification for it (`juniper_data_client/constants.py:59-67`). This is what the corrected design looks like on both sides of the wire.

Three things are worth watching as you read it:

1. **The key is chosen by the client and reused across retries.** A server-generated key would be useless — the client needs it *before* it knows whether the first attempt survived.
2. **The stored record includes a fingerprint of the request.** Replaying a key with a different body is a client bug, and the server says so (422) rather than silently returning the wrong resource.
3. **The concurrent case is handled explicitly.** Two in-flight requests with one key is the interesting race, and the example reserves the key atomically before doing any work, so the loser gets a 409 rather than a second job.

The `_simulate_dispatch` helper deserves a note: real work always yields to the event loop, and without a yield the handler would be effectively atomic, making the 409 path unreachable in a test and misrepresenting production. The optional gate is a deliberate, documented test seam.

<!-- example-file: idempotent_jobs.py -->
```python
"""Making a non-idempotent POST safe to retry: server-side idempotency keys.

Motivation (a real defect, not a hypothetical)
----------------------------------------------
``juniper-cascor-client`` retries ``POST`` on 429/502/503/504 with no idempotency
key, so a transient gateway 502 automatically re-sends
``POST /v1/training/start``. If the first request succeeded and only its
**response** was lost, the retry starts a second training run on the same GPU.
Its sibling ``juniper-data-client`` carries the fix -- restrict retries to
idempotent methods, per RFC 9110 section 9.2.2 -- but it was never ported across.

That fix is only half an answer: it converts a duplicate-side-effect bug into an
availability bug, because the operation you most want to retry (submitting work)
is the one you may no longer retry. The complete fix is an **idempotency key**:
the client picks one key per logical submission and re-sends it unchanged on
every retry; the server stores the outcome under that key and replays it.
Retrying becomes safe by contract rather than by luck.

The four cases a server must handle
-----------------------------------
1. New key                      -> do the work, store the response, 201.
2. Known key, same body         -> replay the stored response verbatim.
3. Known key, different body    -> 422; the key was reused for another operation.
4. Known key, still in flight   -> 409; there is no stored response to replay yet.

Run the tests with::

    pytest test_idempotent_jobs.py
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import random
import time
import uuid
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, field
from typing import Annotated, Any, Final, Literal

import httpx
from fastapi import FastAPI, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "DEFAULT_RETRY_POLICY",
    "IdempotencyRecord",
    "IdempotencyStore",
    "Job",
    "JobRequest",
    "JobSubmissionError",
    "RetryPolicy",
    "create_app",
    "full_jitter_delay",
    "submit_job",
]

PROBLEM_JSON: Final = "application/problem+json"
#: How long a completed idempotency record stays replayable. Stripe uses 24h;
#: the right value is "longer than your slowest client's total retry budget".
DEFAULT_KEY_TTL_SECONDS: Final = 24 * 60 * 60
#: A reservation older than this is assumed to belong to a crashed worker and is
#: reclaimed, otherwise a process death would wedge that key until the TTL.
STUCK_RESERVATION_SECONDS: Final = 60.0


# --------------------------------------------------------------------------- #
# Problem details (RFC 9457)
# --------------------------------------------------------------------------- #
def problem(
    request: Request,
    *,
    status: int,
    title: str,
    detail: str,
    type_: str = "about:blank",
    headers: Mapping[str, str] | None = None,
    **extra: Any,
) -> JSONResponse:
    """Build an RFC 9457 ``application/problem+json`` response.

    ``instance`` is the request path so a support ticket can be tied to one call.
    """
    body: dict[str, Any] = {
        "type": type_,
        "title": title,
        "status": status,
        "detail": detail,
        "instance": str(request.url.path),
        **extra,
    }
    return JSONResponse(body, status_code=status, media_type=PROBLEM_JSON, headers=dict(headers or {}))


# --------------------------------------------------------------------------- #
# Domain models
# --------------------------------------------------------------------------- #
class JobRequest(BaseModel):
    """The request body. ``extra="forbid"`` makes a typo a 422 instead of a silent default."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["train", "evaluate"]
    dataset_id: str = Field(min_length=1, max_length=200)
    epochs: int = Field(default=10, ge=1, le=10_000)


@dataclass(slots=True)
class Job:
    id: str
    kind: str
    dataset_id: str
    epochs: int
    status: Literal["queued", "running", "succeeded", "failed"]
    created_at: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "dataset_id": self.dataset_id,
            "epochs": self.epochs,
            "status": self.status,
            "created_at": self.created_at,
        }


# --------------------------------------------------------------------------- #
# Idempotency store
# --------------------------------------------------------------------------- #
@dataclass(slots=True)
class IdempotencyRecord:
    """One key's lifecycle: reserved while in flight, then completed and replayable."""

    key: str
    fingerprint: str
    state: Literal["in_flight", "completed"]
    created_at: float
    status_code: int | None = None
    body: dict[str, Any] | None = None
    headers: dict[str, str] = field(default_factory=dict)


Outcome = Literal["proceed", "replay", "mismatch", "in_flight"]


class IdempotencyStore:
    """In-memory key store with an atomic check-and-reserve.

    A *single* guard lock protects the whole map rather than one lock per key.
    A per-key lock sounds tidier but is circular: you need a lock to safely
    create the per-key lock. One short-held lock around a dict lookup is both
    simpler and faster than the alternative, and it makes the reservation
    genuinely atomic -- two coroutines cannot both observe "no record" and both
    proceed to create a job.

    In a multi-process deployment this becomes a row in Postgres with a unique
    index on the key (``INSERT ... ON CONFLICT DO NOTHING`` is the same
    check-and-reserve) or a Redis ``SET key value NX PX ttl``. The state machine
    below does not change.
    """

    def __init__(
        self,
        *,
        ttl_seconds: float = DEFAULT_KEY_TTL_SECONDS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._ttl = ttl_seconds
        self._clock = clock
        self._guard = asyncio.Lock()
        self._records: dict[str, IdempotencyRecord] = {}

    def __len__(self) -> int:
        return len(self._records)

    def peek(self, key: str) -> IdempotencyRecord | None:
        """Read without locking -- for tests and diagnostics only."""
        return self._records.get(key)

    async def begin(self, key: str, fingerprint: str) -> tuple[Outcome, IdempotencyRecord | None]:
        """Atomically classify the request and reserve the key when it is new."""
        async with self._guard:
            self._sweep_locked()
            record = self._records.get(key)
            if record is None:
                self._records[key] = IdempotencyRecord(
                    key=key, fingerprint=fingerprint, state="in_flight", created_at=self._clock()
                )
                return "proceed", None
            # Fingerprint is checked before state: reusing a key for a different
            # operation is a client bug worth reporting even while in flight.
            if record.fingerprint != fingerprint:
                return "mismatch", record
            if record.state == "in_flight":
                return "in_flight", record
            return "replay", record

    async def complete(
        self, key: str, *, status_code: int, body: dict[str, Any], headers: Mapping[str, str] | None = None
    ) -> None:
        async with self._guard:
            record = self._records.get(key)
            if record is None:  # pragma: no cover - only reachable if swept mid-flight
                return
            record.state = "completed"
            record.status_code = status_code
            record.body = body
            record.headers = dict(headers or {})
            record.created_at = self._clock()  # TTL runs from completion

    async def abandon(self, key: str) -> None:
        """Release a reservation whose work failed, so the client may retry.

        Without this, an exception mid-handler would leave the key reserved and
        every retry would get 409 until the stuck-reservation horizon passed.
        """
        async with self._guard:
            record = self._records.get(key)
            if record is not None and record.state == "in_flight":
                del self._records[key]

    async def sweep(self) -> int:
        async with self._guard:
            return self._sweep_locked()

    def _sweep_locked(self) -> int:
        """Drop expired records. Caller must hold ``self._guard``."""
        now = self._clock()
        doomed = [
            key
            for key, rec in self._records.items()
            if (rec.state == "completed" and now - rec.created_at >= self._ttl)
            or (rec.state == "in_flight" and now - rec.created_at >= STUCK_RESERVATION_SECONDS)
        ]
        for key in doomed:
            del self._records[key]
        return len(doomed)


def fingerprint_body(payload: Mapping[str, Any]) -> str:
    """Hash the *validated* body so key order and defaults cannot cause a false mismatch."""
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# Server
# --------------------------------------------------------------------------- #
def create_app(*, ttl_seconds: float = DEFAULT_KEY_TTL_SECONDS, clock: Callable[[], float] = time.monotonic) -> FastAPI:
    """Build a fresh app. A factory (not a module-level singleton) keeps tests isolated."""
    app = FastAPI(title="Idempotent Jobs")
    app.state.jobs = {}
    app.state.keys = IdempotencyStore(ttl_seconds=ttl_seconds, clock=clock)
    # Test seam: an optional Event the create path awaits, so a test can hold one
    # request "in flight" and observe what a concurrent duplicate really gets.
    app.state.work_gate = None

    @app.post("/v1/jobs", status_code=201)
    async def create_job(  # noqa: D401 - route function
        request: Request,
        body: JobRequest,
        idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    ) -> JSONResponse:
        if not idempotency_key or not idempotency_key.strip():
            return problem(
                request,
                status=400,
                title="Missing Idempotency-Key",
                detail="POST /v1/jobs requires an Idempotency-Key header so retries cannot duplicate work.",
                type_="https://errors.example.com/idempotency-key-required",
            )

        store: IdempotencyStore = app.state.keys
        fingerprint = fingerprint_body(body.model_dump(mode="json"))
        outcome, record = await store.begin(idempotency_key, fingerprint)

        if outcome == "mismatch":
            return problem(
                request,
                status=422,
                title="Idempotency-Key reused for a different request",
                detail=(
                    "This Idempotency-Key was already used with a different request body. "
                    "Generate a new key for a new operation."
                ),
                type_="https://errors.example.com/idempotency-key-reuse",
            )

        if outcome == "in_flight":
            return problem(
                request,
                status=409,
                title="Request already in progress",
                detail="A request with this Idempotency-Key is still being processed. Retry shortly.",
                type_="https://errors.example.com/idempotency-key-in-flight",
                headers={"Retry-After": "1"},
            )

        if outcome == "replay":
            assert record is not None and record.status_code is not None and record.body is not None
            # Replayed verbatim: same status, same body. Only the advisory header
            # differs, so a caller that ignores it still sees a consistent world.
            return JSONResponse(
                record.body,
                status_code=record.status_code,
                headers={**record.headers, "Idempotency-Replayed": "true"},
            )

        # outcome == "proceed": we hold the reservation and must release it.
        try:
            job = Job(
                id=f"job-{uuid.uuid4().hex[:16]}",
                kind=body.kind,
                dataset_id=body.dataset_id,
                epochs=body.epochs,
                status="queued",
                created_at=time.time(),
            )
            await _simulate_dispatch(app)
            app.state.jobs[job.id] = job
        except Exception:
            await store.abandon(idempotency_key)
            raise

        payload = job.as_dict()
        headers = {"Location": f"/v1/jobs/{job.id}"}
        await store.complete(idempotency_key, status_code=201, body=payload, headers=headers)
        return JSONResponse(payload, status_code=201, headers=headers)

    @app.get("/v1/jobs/{job_id}")
    async def get_job(request: Request, job_id: str) -> JSONResponse:
        job: Job | None = app.state.jobs.get(job_id)
        if job is None:
            return problem(
                request,
                status=404,
                title="Job not found",
                detail=f"No job with id {job_id!r}.",
                type_="https://errors.example.com/job-not-found",
            )
        return JSONResponse(job.as_dict())

    return app


async def _simulate_dispatch(app: FastAPI) -> None:
    """Model the latency window in which a duplicate request can arrive.

    Real work (enqueueing, a DB write, a GPU reservation) always yields to the
    event loop. Without a yield here the handler would be effectively atomic and
    the 409 path would be unreachable -- untestable, and a lie about production.
    """
    gate: asyncio.Event | None = app.state.work_gate
    if gate is not None:
        await gate.wait()
    else:
        await asyncio.sleep(0)


# --------------------------------------------------------------------------- #
# Client: retry with a stable idempotency key
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class RetryPolicy:
    max_attempts: int = 4
    base_delay: float = 0.2
    max_delay: float = 20.0
    #: 500 is deliberately absent: a generic 500 may mean the write half-happened.
    #: With an idempotency key a 500 is in fact safe to retry, but keeping the set
    #: narrow makes the *reason* each status is here explicit.
    retry_statuses: frozenset[int] = frozenset({429, 502, 503, 504})


DEFAULT_RETRY_POLICY: Final = RetryPolicy()


class JobSubmissionError(RuntimeError):
    """Raised when every attempt was exhausted."""

    def __init__(self, message: str, *, attempts: int, last_status: int | None = None) -> None:
        super().__init__(message)
        self.attempts = attempts
        self.last_status = last_status


def full_jitter_delay(attempt: int, policy: RetryPolicy, rng: random.Random) -> float:
    """Full-jitter exponential backoff. ``attempt`` is 1-based.

    The delay is uniform over ``[0, ceiling]`` rather than ``ceiling`` itself.
    Equal-jitter and no-jitter schemes leave clients synchronised: every client
    that failed at T retries at T+base, re-colliding forever. Spreading each
    client uniformly across the whole window is what actually breaks the
    thundering herd, and it is strictly better than exponential-only backoff.
    """
    if attempt < 1:
        raise ValueError("attempt is 1-based")
    ceiling = min(policy.max_delay, policy.base_delay * (2 ** (attempt - 1)))
    return rng.uniform(0.0, ceiling)


async def submit_job(
    client: httpx.AsyncClient,
    payload: Mapping[str, Any],
    *,
    idempotency_key: str | None = None,
    policy: RetryPolicy = DEFAULT_RETRY_POLICY,
    rng: random.Random | None = None,
    sleeper: Callable[[float], Awaitable[None]] = asyncio.sleep,
) -> httpx.Response:
    """Submit one job, retrying transient failures under a single idempotency key.

    The key is generated **once**, outside the retry loop. That is the entire
    point: every attempt is the same logical submission, so the server can
    recognise attempts 2..N as duplicates of attempt 1 and replay rather than
    re-execute. Generating a key per attempt would be indistinguishable from
    having no key at all.

    ``sleeper`` and ``rng`` are injected so tests are deterministic and instant.
    """
    key = idempotency_key or f"jobsub-{uuid.uuid4().hex}"
    rng = rng if rng is not None else random.Random()
    last_status: int | None = None
    last_error: Exception | None = None

    for attempt in range(1, policy.max_attempts + 1):
        try:
            response = await client.post("/v1/jobs", json=dict(payload), headers={"Idempotency-Key": key})
        except httpx.TransportError as exc:
            # The most dangerous failure: the request may well have been applied.
            # Only the idempotency key makes retrying here correct.
            last_error, last_status = exc, None
        else:
            if response.status_code not in policy.retry_statuses:
                return response
            last_status, last_error = response.status_code, None

        if attempt == policy.max_attempts:
            break
        await sleeper(full_jitter_delay(attempt, policy, rng))

    detail = f"HTTP {last_status}" if last_status is not None else f"transport error: {last_error!r}"
    raise JobSubmissionError(
        f"job submission failed after {policy.max_attempts} attempts ({detail})",
        attempts=policy.max_attempts,
        last_status=last_status,
    )
```

<!-- example-file: test_idempotent_jobs.py -->
```python
"""Tests for idempotent_jobs.py.

The headline assertions are about *job count*, not status codes: an idempotency
implementation that returns the right status but creates two jobs has failed at
the only thing it exists to do.
"""

from __future__ import annotations

import asyncio
import json
import random
from collections.abc import Callable
from typing import Any

import httpx
import pytest

from idempotent_jobs import (
    IdempotencyStore,
    JobSubmissionError,
    RetryPolicy,
    create_app,
    full_jitter_delay,
    submit_job,
)

BODY: dict[str, Any] = {"kind": "train", "dataset_id": "spiral-v1-abc123", "epochs": 25}


def client_for(app: Any) -> httpx.AsyncClient:
    # httpx 0.28 removed the AsyncClient(app=...) shortcut; ASGITransport is the
    # supported way to drive an ASGI app in-process with no sockets involved.
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


async def wait_for(predicate: Callable[[], bool], *, timeout: float = 2.0) -> None:
    """Bounded poll on the event loop -- deterministic ordering without fixed sleeps."""
    deadline = asyncio.get_running_loop().time() + timeout
    while not predicate():
        if asyncio.get_running_loop().time() > deadline:  # pragma: no cover - failure path
            raise AssertionError("condition not reached before timeout")
        await asyncio.sleep(0.001)


class RecordingSleeper:
    """Async sleeper that records requested delays and never actually waits."""

    def __init__(self) -> None:
        self.delays: list[float] = []

    async def __call__(self, delay: float) -> None:
        self.delays.append(delay)


class LossyResponseProxy:
    """ASGI wrapper modelling a gateway that loses the response *after* the origin
    server has already committed the side effect.

    This is the failure that makes naive retries dangerous: the client sees 503
    and cannot tell "nothing happened" from "everything happened, and I lost the
    receipt". Failing before reaching the app would be a much easier case.
    """

    def __init__(self, app: Any, *, fail_times: int) -> None:
        self._app = app
        self._remaining = fail_times
        self.post_attempts = 0

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] != "http":  # pragma: no cover - no lifespan in these tests
            await self._app(scope, receive, send)
            return

        drop = False
        if scope["method"] == "POST":
            self.post_attempts += 1
            if self._remaining > 0:
                self._remaining -= 1
                drop = True

        async def maybe_send(message: dict[str, Any]) -> None:
            if not drop:
                await send(message)

        await self._app(scope, receive, maybe_send)

        if drop:
            body = json.dumps(
                {
                    "type": "https://errors.example.com/upstream-unavailable",
                    "title": "Service Unavailable",
                    "status": 503,
                    "detail": "upstream timed out",
                    "instance": scope["path"],
                }
            ).encode()
            await send(
                {
                    "type": "http.response.start",
                    "status": 503,
                    "headers": [
                        (b"content-type", b"application/problem+json"),
                        (b"content-length", str(len(body)).encode()),
                    ],
                }
            )
            await send({"type": "http.response.body", "body": body})


# --------------------------------------------------------------------------- #
# 1. Replay returns the identical response and creates exactly one job
# --------------------------------------------------------------------------- #
@pytest.mark.asyncio
async def test_replay_is_verbatim_and_creates_exactly_one_job() -> None:
    app = create_app()
    async with client_for(app) as client:
        headers = {"Idempotency-Key": "key-replay-1"}
        first = await client.post("/v1/jobs", json=BODY, headers=headers)
        second = await client.post("/v1/jobs", json=BODY, headers=headers)

    assert first.status_code == 201
    assert second.status_code == first.status_code
    assert second.json() == first.json()  # verbatim, including the job id
    assert second.headers["location"] == first.headers["location"]

    # Advisory only: a caller that ignores this header still sees a coherent world.
    assert "idempotency-replayed" not in first.headers
    assert second.headers["idempotency-replayed"] == "true"

    # The assertion that actually matters.
    assert len(app.state.jobs) == 1


@pytest.mark.asyncio
async def test_created_job_is_retrievable() -> None:
    app = create_app()
    async with client_for(app) as client:
        created = await client.post("/v1/jobs", json=BODY, headers={"Idempotency-Key": "key-get"})
        fetched = await client.get(created.headers["location"])
        missing = await client.get("/v1/jobs/job-does-not-exist")

    assert fetched.status_code == 200
    assert fetched.json() == created.json()
    assert missing.status_code == 404
    assert missing.headers["content-type"].startswith("application/problem+json")


# --------------------------------------------------------------------------- #
# 2. Same key, different body -> 422
# --------------------------------------------------------------------------- #
@pytest.mark.asyncio
async def test_same_key_different_body_is_rejected() -> None:
    app = create_app()
    async with client_for(app) as client:
        headers = {"Idempotency-Key": "key-conflict"}
        first = await client.post("/v1/jobs", json=BODY, headers=headers)
        second = await client.post("/v1/jobs", json={**BODY, "epochs": 99}, headers=headers)

    assert first.status_code == 201
    assert second.status_code == 422
    assert second.headers["content-type"].startswith("application/problem+json")
    assert second.json()["title"] == "Idempotency-Key reused for a different request"
    assert len(app.state.jobs) == 1  # the second request created nothing


@pytest.mark.asyncio
async def test_key_order_does_not_affect_the_fingerprint() -> None:
    """A reordered but semantically identical body must replay, not 422."""
    app = create_app()
    reordered = {"epochs": 25, "dataset_id": BODY["dataset_id"], "kind": "train"}
    async with client_for(app) as client:
        headers = {"Idempotency-Key": "key-order"}
        first = await client.post("/v1/jobs", json=BODY, headers=headers)
        second = await client.post("/v1/jobs", json=reordered, headers=headers)

    assert (first.status_code, second.status_code) == (201, 201)
    assert second.json() == first.json()
    assert len(app.state.jobs) == 1


@pytest.mark.asyncio
async def test_missing_key_is_rejected_with_problem_details() -> None:
    app = create_app()
    async with client_for(app) as client:
        response = await client.post("/v1/jobs", json=BODY)

    assert response.status_code == 400
    assert response.headers["content-type"].startswith("application/problem+json")
    assert set(response.json()) >= {"type", "title", "status", "detail", "instance"}
    assert app.state.jobs == {}


# --------------------------------------------------------------------------- #
# 3. Concurrency
# --------------------------------------------------------------------------- #
@pytest.mark.asyncio
async def test_concurrent_duplicates_create_exactly_one_job() -> None:
    """GUARANTEE: with a request genuinely in flight, the duplicate gets 409.

    The reservation is taken atomically under the store's guard lock *before* any
    work happens, so exactly one coroutine can ever see "new key". The loser
    cannot be served a replayed 201 because there is no stored response yet --
    the winner has not finished. 409 (rather than blocking until the winner
    completes) keeps the server's concurrency bounded: a stampede of duplicates
    is answered immediately instead of parking N coroutines on one lock.
    """
    app = create_app()
    store: IdempotencyStore = app.state.keys
    gate = asyncio.Event()
    app.state.work_gate = gate  # hold the winner mid-handler
    key = "key-concurrent"

    async with client_for(app) as client:

        async def fire() -> httpx.Response:
            return await client.post("/v1/jobs", json=BODY, headers={"Idempotency-Key": key})

        winner = asyncio.create_task(fire())
        await wait_for(lambda: store.peek(key) is not None)  # winner holds the reservation

        loser = asyncio.create_task(fire())
        await wait_for(loser.done)  # classified without ever touching the gate

        gate.set()  # release the winner
        first, second = await asyncio.gather(winner, loser)

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.headers["content-type"].startswith("application/problem+json")
    assert second.headers["retry-after"] == "1"
    assert len(app.state.jobs) == 1


@pytest.mark.asyncio
async def test_abandoned_reservation_is_released_after_a_409() -> None:
    """Once the winner completes, the same key replays instead of 409-ing forever."""
    app = create_app()
    store: IdempotencyStore = app.state.keys
    gate = asyncio.Event()
    app.state.work_gate = gate
    key = "key-then-replay"

    async with client_for(app) as client:

        async def fire() -> httpx.Response:
            return await client.post("/v1/jobs", json=BODY, headers={"Idempotency-Key": key})

        winner = asyncio.create_task(fire())
        await wait_for(lambda: store.peek(key) is not None)
        conflicted = await fire()
        gate.set()
        created = await winner

        app.state.work_gate = None
        replayed = await fire()

    assert (conflicted.status_code, created.status_code, replayed.status_code) == (409, 201, 201)
    assert replayed.json() == created.json()
    assert len(app.state.jobs) == 1


# --------------------------------------------------------------------------- #
# 4. Client retries a flapping endpoint, still exactly one job
# --------------------------------------------------------------------------- #
@pytest.mark.asyncio
async def test_client_retry_through_lost_responses_creates_one_job() -> None:
    app = create_app()
    proxy = LossyResponseProxy(app, fail_times=2)
    sleeper = RecordingSleeper()

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=proxy), base_url="http://test") as client:
        response = await submit_job(
            client,
            BODY,
            idempotency_key="key-flapping",
            rng=random.Random(1234),
            sleeper=sleeper,
        )

    assert response.status_code == 201
    assert proxy.post_attempts == 3  # two lost responses, then a delivered one
    assert len(sleeper.delays) == 2  # one backoff between each pair of attempts

    # Attempts 2 and 3 were replays of the work committed on attempt 1.
    assert response.headers["idempotency-replayed"] == "true"
    assert len(app.state.jobs) == 1

    # ...and the replayed job is the one that was actually created.
    (job,) = app.state.jobs.values()
    assert response.json()["id"] == job.id


@pytest.mark.asyncio
async def test_client_gives_up_after_max_attempts() -> None:
    app = create_app()
    proxy = LossyResponseProxy(app, fail_times=99)
    sleeper = RecordingSleeper()
    policy = RetryPolicy(max_attempts=3)

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=proxy), base_url="http://test") as client:
        with pytest.raises(JobSubmissionError) as caught:
            await submit_job(client, BODY, idempotency_key="key-doomed", policy=policy, sleeper=sleeper)

    assert caught.value.attempts == 3
    assert caught.value.last_status == 503
    assert proxy.post_attempts == 3
    assert len(sleeper.delays) == 2  # N attempts means N-1 waits, never a trailing one


@pytest.mark.asyncio
async def test_transport_errors_are_retried_under_the_same_key() -> None:
    """The hardest case: no response at all, so the client cannot know what happened."""
    attempts: list[httpx.Request] = []
    app = create_app()

    real = httpx.ASGITransport(app=app)

    class FlakyTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
            attempts.append(request)
            if len(attempts) == 1:
                raise httpx.ConnectError("connection reset", request=request)
            return await real.handle_async_request(request)

    async with httpx.AsyncClient(transport=FlakyTransport(), base_url="http://test") as client:
        response = await submit_job(client, BODY, idempotency_key="key-transport", sleeper=RecordingSleeper())

    assert response.status_code == 201
    assert len(attempts) == 2
    assert {r.headers["idempotency-key"] for r in attempts} == {"key-transport"}
    assert len(app.state.jobs) == 1


# --------------------------------------------------------------------------- #
# 5. Backoff maths, tested directly -- no sleeping
# --------------------------------------------------------------------------- #
def test_full_jitter_delay_is_bounded_increasing_and_capped() -> None:
    policy = RetryPolicy(base_delay=0.5, max_delay=4.0)
    rng = random.Random(20260813)

    for attempt in range(1, 8):
        ceiling = min(policy.max_delay, policy.base_delay * (2 ** (attempt - 1)))
        for _ in range(200):
            delay = full_jitter_delay(attempt, policy, rng)
            assert 0.0 <= delay <= ceiling

    # The ceiling doubles per attempt until it saturates at max_delay.
    ceilings = [min(policy.max_delay, policy.base_delay * (2 ** (a - 1))) for a in range(1, 7)]
    assert ceilings == [0.5, 1.0, 2.0, 4.0, 4.0, 4.0]
    assert all(b >= a for a, b in zip(ceilings, ceilings[1:]))


def test_full_jitter_actually_jitters() -> None:
    """Without jitter every client in a fleet would retry in lockstep."""
    policy = RetryPolicy(base_delay=1.0, max_delay=60.0)
    rng = random.Random(7)
    draws = {full_jitter_delay(3, policy, rng) for _ in range(50)}
    assert len(draws) > 40  # essentially all distinct


def test_full_jitter_delay_is_reproducible_under_a_seed() -> None:
    policy = RetryPolicy()
    a = [full_jitter_delay(i, policy, random.Random(99)) for i in range(1, 5)]
    b = [full_jitter_delay(i, policy, random.Random(99)) for i in range(1, 5)]
    assert a == b


def test_full_jitter_rejects_a_zero_attempt() -> None:
    with pytest.raises(ValueError):
        full_jitter_delay(0, RetryPolicy(), random.Random(0))


# --------------------------------------------------------------------------- #
# Key TTL
# --------------------------------------------------------------------------- #
@pytest.mark.asyncio
async def test_expired_keys_are_swept_and_stop_replaying() -> None:
    """After the TTL the key is forgotten, so the same key is a *new* operation.

    This is why the TTL must exceed the client's total retry budget: a client
    still retrying after expiry would silently duplicate work.
    """
    now = [1_000.0]
    app = create_app(ttl_seconds=10.0, clock=lambda: now[0])
    store: IdempotencyStore = app.state.keys

    async with client_for(app) as client:
        headers = {"Idempotency-Key": "key-ttl"}
        first = await client.post("/v1/jobs", json=BODY, headers=headers)
        now[0] += 11.0  # past the TTL
        second = await client.post("/v1/jobs", json=BODY, headers=headers)

    assert (first.status_code, second.status_code) == (201, 201)
    assert first.json()["id"] != second.json()["id"]
    assert len(app.state.jobs) == 2
    assert len(store) == 1  # the expired record was swept, the new one remains
```

Run this example, and the other two, with the harness described in [Appendix D](#appendix-d--running-the-examples).

## Part II — REST and HTTP Semantics in Depth

### II.1 What Part II Covers, and What REST Actually Means

#### Overview

Part I surveyed the landscape. Part II is the precise treatment of the layer everyone claims to already know: HTTP semantics as actually specified. The organising claim is that most "REST API design debates" are not about REST at all — they are about HTTP, conducted by people arguing from folklore rather than from the method and status-code definitions.

This section establishes vocabulary: what Fielding's REST is, what industry means by "REST", and why the gap changes what you do on a Tuesday afternoon. II.2 through II.5 then work through resources and URIs, methods, status codes, and representations, each grounded in specification text and in real Juniper code.

#### Background

REST was defined in Chapter 5 of Roy Fielding's 2000 UC Irvine dissertation, [*Architectural Styles and the Design of Network-based Software Architectures*](https://roy.gbiv.com/pubs/dissertation/rest_arch_style.htm). It is not a protocol, a format, or a URL convention. It is an *architectural style*: a named set of constraints, each chosen for the properties it induces, derived incrementally from
the "null style" (§5.1.1) — an empty constraint set.

That derivation matters because it explains why the constraints look arbitrary out of context. Each buys a property and costs something, and Fielding is explicit about the costs: statelessness "may decrease network performance by increasing the repetitive data (per-interaction overhead)" (§5.1.3); the uniform interface "degrades efficiency, since information is transferred in a standardized form
rather than one which is specific to an application's needs" (§5.1.5).

HTTP is not REST. HTTP/1.1 was designed alongside the dissertation and REST was the rationale for many of its choices, but the two are separable: you can build a non-RESTful system on HTTP (almost everyone does). Today HTTP semantics live in [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html), which in June 2022 obsoleted RFC 7230-7233 and 7235, with caching moving to RFC 9111 (STD 98) rather than into 9110; wire formats live separately in RFC 9112
(HTTP/1.1), RFC 9113 (HTTP/2), and RFC 9114 (HTTP/3). "HTTP says" below means RFC 9110 unless stated otherwise.

#### The six constraints, stated accurately

Fielding derives REST through these sections. Note §5.1.4 is titled "Cache", not "Cacheable", and there is no constraint called "resource identification" at this level.

| §     | Constraint        | What it requires                                                                                                                                                            | Property bought                                  |
|-------|-------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------|
| 5.1.2 | Client-Server     | Separate user-interface concerns from data-storage concerns                                                                                                                 | Portability, independent evolvability            |
| 5.1.3 | Stateless         | "each request from client to server must contain all of the information necessary to understand the request, and cannot take advantage of any stored context on the server" | Visibility, reliability, scalability             |
| 5.1.4 | Cache             | "data within a response to a request be implicitly or explicitly labeled as cacheable or non-cacheable"                                                                     | Reduced latency; costs staleness risk            |
| 5.1.5 | Uniform Interface | Four sub-constraints (below)                                                                                                                                                | Simplicity, visibility, independent evolvability |
| 5.1.6 | Layered System    | A component "cannot 'see' beyond the immediate layer with which they are interacting"                                                                                       | Bounded complexity, substrate independence       |
| 5.1.7 | Code-On-Demand    | Client functionality extensible by downloaded code                                                                                                                          | Extensibility; **optional**                      |

Code-on-demand is optional, and §5.1.7 says why in the same breath: "However, it also reduces visibility, and thus is only an optional constraint within REST." Fielding then meets the objection directly — "The notion of an optional constraint may seem like an oxymoron" — explaining that it lets an architecture gain the benefit within a realm where support is known while degrading gracefully
outside it.

The uniform interface distinguishes REST from every other network-based style, and is the constraint most often cited without its contents. Verbatim (§5.1.5):

> REST is defined by four interface constraints: identification of resources; manipulation of resources through representations; self-descriptive messages; and, hypermedia as the engine of application state.

Unpacked with the definitional material from §5.2.1:

1. **Identification of resources.** "Any information that can be named can be a resource" (§5.2.1.1). A resource is a *conceptual mapping* — formally "a temporally varying membership function M_R(t)" — not the bytes you get back. His illustration is an academic paper: the "authors' preferred version" and "the paper published in the proceedings of conference X" are "two distinct resources, even if they both map to the same value at some point in time".
   The version-controlled file reachable as "latest revision" or "revision number 1.2.7" follows as "A similar example".
2. **Manipulation of resources through representations.** You never operate on the resource directly; you exchange a representation — "a sequence of bytes, plus representation metadata to describe those bytes" (§5.2.1.2).
3. **Self-descriptive messages.** Each message carries enough metadata (media type, cache directives, method semantics) for any intermediary to process it without out-of-band knowledge. This is what makes shared caches and proxies possible at all.
4. **Hypermedia as the engine of application state (HATEOAS).** The client's next transitions come from links in the representation it just received, not from URL structure compiled into its source.

#### The gap: Richardson's maturity model, and industry usage

Essentially no commercial HTTP API satisfies constraint 4. Industry "REST" means roughly: JSON over HTTP, plural noun paths, several methods, sensible status codes. That is a real and useful thing; it is just not what the word denotes in its source.

The usual scaffold for the gap is the **Richardson Maturity Model**, proposed by **Leonard Richardson** in a 2008 QCon talk ("Justice Will Take Us Millions of Intricate Moves") and popularised by Martin Fowler's 2010 article [*Richardson Maturity Model*](https://martinfowler.com/articles/richardsonMaturityModel.html). Attribute it to Richardson — not Fowler, and certainly not Fielding. It is a
third-party descriptive model and appears nowhere in the dissertation.

| Level | Name                | Meaning                                          | Typical example                                     |
|-------|---------------------|--------------------------------------------------|-----------------------------------------------------|
| 0     | The Swamp of POX    | One URI, one method, verbs in the payload        | SOAP, XML-RPC, `POST /api` with `{"action": "..."}` |
| 1     | Resources           | Many URIs, still one method                      | `POST /getUser`, `POST /deleteUser`                 |
| 2     | HTTP Verbs          | Many URIs, correct methods, correct status codes | Nearly every "REST API" shipped since 2010          |
| 3     | Hypermedia Controls | Level 2 plus links driving state transitions     | HAL, Siren, JSON:API relationships, ActivityPub     |

juniper-data sits at Level 2 with one hypermedia-adjacent gesture: `CreateDatasetResponse` carries an `artifact_url` (`juniper_data/api/routes/datasets.py:138`, `:253`) so callers need not build the artifact path. That is a link — but a hand-rolled `f"/v1/datasets/{dataset_id}/artifact"`, not a typed link relation, and there is exactly one.

#### Why the gap matters practically, not pedantically

**Coupling to URL structure is real coupling.** Level 2 clients hardcode path templates. juniper-data emits `artifact_url` as an interpolated literal repeating the `/v1` prefix already declared three times in `juniper_data/api/app.py:140-142`; there is no `API_VERSION` constant anywhere, so moving to `/v2` is a multi-file edit with no compiler help and two independent places to drift. A hypermedia
client would have followed the link and not noticed.

**Generic-component behaviour is not optional.** Caches, proxies, and retry layers act on the self-descriptive-message constraint whether or not you meant them to. A GET that mutates state gets mutated by a prefetcher. A POST retried because a client library treats all 5xx alike produces duplicate side effects — Part I's three-sibling-clients problem, where `juniper-cascor-client` retries POST
while its two siblings do not.

**Vocabulary hygiene saves review cycles.** "Is this RESTful?" is unanswerable and generates unbounded argument. "Does a shared cache handle this response correctly?" and "Is this method safe to retry?" are answerable from the spec in ninety seconds. Prefer the second kind.

#### Judgement Calls

- **Aim for Level 2 deliberately.** It is right for most service-to-service APIs — but choose it explicitly and record that HATEOAS was considered and declined, so the next reader does not re-litigate it.
- **Adopt Level 3 only where evolvability pays.** Long-lived public APIs with uncontrolled clients, or workflow resources with genuinely state-dependent transitions ("this order can now be cancelled, but not refunded"). An internal service consumed by three clients you deploy yourself is not that.
- **Say "HTTP API" when you mean an HTTP API.** Reserve "REST" for claims you would defend against the dissertation.

#### Tradeoffs

| Choice                        | Gains                                                                        | Costs                                                                                    |
|-------------------------------|------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| Strict HATEOAS                | Server can restructure URLs freely; runtime capability discovery             | Larger payloads; every client needs a link-following layer; almost no tooling assumes it |
| Level 2 pragmatism            | Trivial OpenAPI codegen; every HTTP library works; the team already knows it | URL structure becomes public contract; capability discovery is out-of-band documentation |
| Verbs in payloads (Level 0/1) | Maps trivially onto existing RPC code; no method or status arguments         | Loses caching, intermediary visibility, and idempotency signalling entirely              |

#### Best Practices

- Read RFC 9110 §9 and §15 once, properly. Forty minutes, and it ends most design arguments outright.
- Write down which maturity level you target, and why, in the API's design doc.
- Derive emitted URLs from the same constant the router uses, so prefixes cannot drift.
- Prefer specification citations to blog citations in review. `RFC 9110 §9.2.2` is checkable; "REST best practice" is not.

#### Common Failure Modes

- **Cargo-cult pluralisation.** Renaming `/getUser` to `/users/{id}` while keeping a single POST changes nothing structural — Level 1 wearing Level 2's clothes.
- **HATEOAS theatre.** Emitting a `_links` block clients ignore because the templates are also documented and hardcoded. You pay the payload cost for none of the evolvability.
- **Assuming REST implies JSON.** Fielding's REST is format-agnostic; the media type is the extension point (§5.2.1.2). JSON is industry convention.
- **Reading "stateless" as "no server-side state".** The constraint concerns *session* state kept between requests on behalf of one client. A database is fine; a cookie-keyed server-side login session is what it excludes.

#### Error Handling

Errors are representations too. Fielding notes a representation may be "a representation of some error condition for a response" (§5.2.1.2), and RFC 9110 §15.5 says that, except when responding to HEAD, a server "SHOULD send a representation containing an explanation of the error situation, and whether it is a temporary or permanent condition." That is a SHOULD, not a MUST — advice with teeth, not a conformance requirement.

That last clause is the one implementations skip. juniper-data's global handlers return generic strings — `ValueError` → 400 and bare `Exception` → 500 at `juniper_data/api/app.py:152-166`, logging detail server-side only. A defensible security posture, but the body never tells the client whether the condition is temporary, which is exactly what the spec asks it to convey. II.4 returns to this.

#### Controversy: Is "REST" a useful term any more?

**That a controversy exists.** Two camps have argued since 2008, when Fielding published [*REST APIs must be hypertext-driven*](https://roy.gbiv.com/untangled/2008/rest-apis-must-be-hypertext-driven) — a post opening "I am getting frustrated by the number of people calling any HTTP-based interface a REST API", setting out six rules including "A REST API must not define fixed resource names or
hierarchies (an obvious coupling of client and server)". The line most often quoted from the post is not one of those rules but the framing that precedes them: "if the engine of application state (and hence the API) is not being driven by hypertext, then it cannot be RESTful and cannot be a REST API. Period." By that standard essentially every API called REST — juniper-data included — is not one.

**The camps.** The **purist** position: the term has a precise technical definition naming properties that matter, and diluting it destroys the ability to describe the difference between a hypermedia system and an RPC system. The **pragmatic** position: meaning is set by usage, "REST" has settled on a useful shared sense (resource-oriented HTTP with proper methods and status codes), and insisting
on the 2000 definition is a losing fight that mostly signals having read a dissertation.

**Background.** Between 2000 and 2008 REST spread as a reaction to SOAP/WS-\*, and what spread was what was easy to adopt: URLs as nouns, methods as verbs. Hypermedia constraints were harder, had no tooling, and solved a problem — uncontrolled client evolution — most in-house teams did not have. By the time Fielding objected, the usage was entrenched across an industry's documentation.

**Purist camp.** *Strengths:* precision; the constraints predict real properties (cacheability, intermediary transparency, evolvability under uncontrolled clients), and losing the word loses the ability to name them. *Weaknesses:* prescriptivism against near-universal usage rarely wins, and can devolve into gatekeeping that adds no engineering value to the API under review. *Risks:* reviews become
terminology fights and teams route around the pedant rather than engage the substantive coupling point. *Guardrails:* convert the objection into a testable question — "which clients break if we change this path?" — rather than a label dispute.

**Pragmatic camp.** *Strengths:* communicates efficiently with the whole industry; "REST API" reliably conveys a real shape, and Level 2 captures most of HTTP's practical benefits without the hypermedia cost. *Weaknesses:* blurs a distinction that occasionally matters a great deal, and lets teams believe they bought evolvability they did not; it also produces the "REST vs GraphQL" genre, comparing
an architectural style to a query language. *Risks:* cargo-culting, and surprise when a URL change breaks clients assumed to be loosely coupled. *Guardrails:* state the maturity level explicitly and document URL structure as contract if clients depend on it, rather than pretending it is an implementation detail.

**Recommendation** (labelled as such): use "HTTP API" as the default noun in specs, reserve "REST" for claims about the constraints, and when asked "is this RESTful?", answer the underlying operational question instead. That is a position on vocabulary hygiene, not on who is right — both camps describe something real.

---

### II.2 Resource Modelling and URI Design

#### Overview

URI design is where API design is most visible and least consequential, and where teams therefore spend disproportionate effort. The load-bearing decisions are: what your resources *are*, what the identifier's stability contract is, and whether clients construct URIs or follow them. Cosmetics — hyphens vs underscores, plural vs singular — matter only for consistency.

This section covers the resource/endpoint/representation distinction, the noun rule and where it honestly breaks, collection and item patterns, identifier design, and the syntactic details that produce real bugs. It grounds in two juniper-data mechanisms: a load-bearing route-ordering dependency, and a content-addressed identifier with a deliberate escape hatch.

#### Background

Three terms get conflated; Fielding's definitions separate them cleanly.

- A **resource** is the concept: "any information that can be named" (§5.2.1.1). "The latest version of dataset 'spiral-train'" is a resource.
- A **URI** identifies a resource. RFC 9110 §4 covers identifiers in HTTP; the syntax itself is RFC 3986.
- A **representation** is "a sequence of bytes, plus representation metadata" (§5.2.1.2) — one serialisation of current state. JSON metadata and an `.npz` artifact may be two representations of one resource, or representations of two related resources; that is a modelling decision.
- An **endpoint** is not a REST concept. It is an implementation word for "a route in my framework": the (method, path template) pair that dispatches to a handler. One resource typically has several endpoints, and using "endpoint" where you mean "resource" is how modelling discussions go wrong.

RFC 9110 §4.2.3 additionally specifies scheme-based normalisation for `http`/`https` URIs, with direct design consequences covered below.

#### Nouns not verbs — and the honest limits of that rule

The rule works because HTTP already supplies the verbs, and a uniform method set is what lets generic components reason about your traffic. `POST /datasets` plus `DELETE /datasets/{id}` beats `POST /createDataset` plus `POST /deleteDataset` because a cache, a proxy, and a retry layer all understand the former and none understand the latter.

It breaks for operations that are not state manipulation of a single named thing. The classic hard cases:

| Hard case | Options | Guidance |
| --- | --- | --- |
| **Search / query** | `GET /datasets?generator=spiral`; `GET /datasets/filter?…`; `POST /datasets/search` with a body | Prefer GET with query params — cacheable, linkable, safe. Fall back to POST only when the query exceeds URL limits or carries secrets; RFC 9205 §4.5.1 says applications needing POST queries "ought to consider allowing **both** methods" |
| **Batch operations** | `POST /datasets/batch-delete`; `PATCH /datasets` with a list; many parallel requests | A batch is a legitimate resource — a *job description*, not a verb. Name it as one and be explicit about partial-failure semantics |
| **State transitions** | `POST /orders/{id}/cancel`; `PATCH /orders/{id}` with `{"status":"cancelled"}`; `POST /orders/{id}/cancellations` | The sub-resource-as-noun form is most defensible: the transition becomes a thing with its own identity, timestamp, and reason |
| **"Send email"** | `POST /messages`; `POST /emails/send` | Model the artefact, not the act. Creating a `message` the server then delivers is more honest and more retryable |
| **Non-CRUD compute** | `POST /training/start`; `POST /trainings` | If it produces a durable thing, model the thing. If it genuinely does not, an action sub-resource is acceptable — just do not pretend otherwise |

Two honest admissions. `POST /resource/{id}/action` is extremely common and not a defect on its own; it recognises that HTTP's method set is small and some operations do not decompose — Fielding's own note that the uniform interface "is not optimal for other forms of architectural interaction" (§5.1.5) concedes exactly this. And noun purity is bounded by whether you control the domain model:
juniper-cascor's `POST /v1/training/start` and `POST /v1/training/reset` are verb-shaped because the operation genuinely is a control action on a long-lived singleton trainer, not a create.

#### Collections, items, sub-resources, singletons

```text
/datasets                    collection
/datasets/{id}               item
/datasets/{id}/artifact      sub-resource (a different representation-bearing resource)
/datasets/{id}/preview       sub-resource (a derived view)
/datasets/stats              singleton (aggregate over the collection)
```

juniper-data implements exactly this set: collection at `datasets.py:257`, item at `:651`, `artifact` at `:676`, `preview` at `:707`, `stats` singleton at `:338`.

**Singletons** — resources with no sibling and no identifier (`/stats`, `/health`, `/settings`, `/me`) — are legitimate. Treat them as items: GET, possibly PUT/PATCH, never POST-to-create.

**When nesting hurts.** Nest only when the child genuinely cannot be addressed without the parent. Three signals it has gone wrong: the nested path is not the *only* way to reach the item, so you now have two URIs for one resource (RFC 9110 §4.2.3: "distinct resources SHOULD NOT be identified by HTTP URIs that are equivalent after normalization"); depth exceeds two levels below the collection,
forcing clients to know IDs they do not care about; or the parent is a filter rather than an owner — `/users/{id}/orders` where orders have global IDs should be `/orders?user={id}`, because the relationship is a query, not containment.

#### Canonical URIs and aliases

Pick one canonical URI per resource and redirect everything else to it. Aliases that both return 200 are the problem: caches store two entries, validators diverge, analytics double-counts. If you need a friendly slug alongside an opaque ID, serve 301 or 308 from the alias rather than duplicating the representation.
When a resource is legitimately reachable at more than one URI, `Content-Location` (RFC 9110 §8.7) is often reached for — but be precise about what it does. It "references a URI that can be used as an identifier for a specific resource corresponding to the representation in this message's content"; it is explicitly "representation metadata" and
"not a replacement for the target URI". Nowhere does §8.7 give it canonicality semantics. Canonicality is a different mechanism: the `canonical` link relation of RFC 6596, carried in a `Link` header or a document element. RFC 6596 is not in the local spec cache, so it is named here by number only, with no section cited.

juniper-data has a mild case: `GET /v1/datasets/latest?name=X` and `GET /v1/datasets/{id}` can return the same `DatasetMeta` (`datasets.py:628`, `:651`). Neither redirects and neither sets `Content-Location` — but setting it would not have merged anything, because a cache key is "composed from, at a minimum, the request method and target URI" (RFC 9111 §2). Two URIs get two entries no matter what the bodies say about themselves; only a
redirect collapses them. Since juniper-data emits no cache headers at all, the duplication is latent rather than live.

#### Path vs query parameters

In priority order: **path** for identity (which resource — `/datasets/{dataset_id}`); **path** for sub-resource selection (the fixed name of a related resource — `/datasets/{id}/artifact`); **query** for anything that filters, sorts, pages, or shapes a collection response (`?limit=`, `?offset=`, `?generator=`); **query** for optional modifiers on an item (`?n=100` for preview size).

The test: if removing the parameter still names a resource that makes sense, it belongs in the query string. Remove `generator=spiral` from `/datasets?generator=spiral` and you still have "all datasets". Remove `{id}` from `/datasets/{id}` and you have a different resource entirely.

juniper-data follows this with one wrinkle. `/datasets/versions` and `/datasets/latest` both take a **mandatory** `name` query parameter (`datasets.py:606`, `:630`) — identity smuggled into the query string. `/dataset-names/{name}/versions` would model it more honestly. The consequence is concrete: `GET /v1/datasets/latest` with no `name` is a 422 rather than a 404, which is a strange result from
a URI that looks addressable.

#### URI opacity: clients should not construct URIs from inferred templates

This is the rule with the largest practical payoff and the least adoption. RFC 9205 §4.4 states it for protocol specifications: "in most cases, specifications for applications that use HTTP won't contain fixed application URLs or paths", and "An application cannot define a fixed prefix for its URL paths". The alternatives it recommends are a well-known URI (RFC 8615) as entry point, or a
server-supplied URI Template (RFC 6570) — not a template the client inferred by pattern-matching two example URLs.

The in-house version: **publish the templates you support and treat them as contract, or emit links and let clients follow them — but never let clients guess.** A client that observes `/datasets/{id}/artifact` and concludes `/datasets/{id}/preview` must exist has invented a surface you never promised, and it will break on a refactor you were entitled to make. juniper-data's `artifact_url` is the
good pattern applied once; `preview`, `tags`, and the item URI itself remain client-constructed.

#### Identifiers: slug vs opaque vs UUID, and the enumeration risk

| Style              | Example                         | Good for                                       | Costs                                                                                |
|--------------------|---------------------------------|------------------------------------------------|--------------------------------------------------------------------------------------|
| Sequential integer | `/users/42`                     | Compact, sortable, trivially indexed           | **Enumerable.** Leaks volume and ordering; makes IDOR trivially exploitable at scale |
| UUID               | `/users/9f2c…`                  | Non-enumerable, client-generatable, merge-safe | Opaque to humans, 36 chars, poor index locality unless UUIDv7                        |
| Slug               | `/posts/why-rest-is-hard`       | Human-readable, SEO-relevant                   | Mutable — renames break links unless you keep redirects forever                      |
| Content hash       | `/datasets/spiral-v1.0.0-a3f8…` | Deduplicating, immutable, cache-friendly       | Identity is a function of content — changing anything renames                        |

**Sequential integers are an information disclosure, not only an IDOR risk.** Two separate problems: an attacker reading `/users/42` trivially tries 41 and 43 (IDOR — the real defect is the missing authorisation check; the ID style only sets exploitability), and *even with* correct authorisation, exposing `/orders/10041` and `/orders/10098` a week later tells a competitor you processed 57 orders.
Opaque IDs do not fix authorisation bugs; they remove the enumeration and the side channel.

#### Ground truth: juniper-data's content-addressed dataset ID

A hybrid worth studying, in `juniper_data/core/dataset_id.py:23-61`:

```python
canonical_json = json.dumps(canonical_data, sort_keys=True, separators=(",", ":"))
hash_digest = hashlib.sha256(canonical_json.encode(CHARSET_UTF8)).hexdigest()
return f"{generator}-{version}-{hash_digest[:DATASET_ID_HASH_PREFIX_LENGTH]}"
```

with `DATASET_ID_HASH_PREFIX_LENGTH = 16` (`juniper_data/core/constants.py:25`). The result — `spiral-v1.0.0-a3f8e12b4c567890` — is a *readable prefix plus opaque suffix*: generator and version are legible in a log line, the digest is non-enumerable. Canonicalisation (`sort_keys=True`, compact separators) is what makes the hash stable across dict orderings, and it is the step people forget.

Content-addressing buys idempotent creation: re-POSTing identical parameters yields the same ID and hits the cache branch instead of regenerating. Which makes the escape hatch the interesting part (`dataset_id.py:52-55`):

```python
# BUG-JD-04: Seedless requests are non-deterministic; add a nonce so the
# hashed ID cannot collide with a previous (now-stale) seedless artifact.
if params.get("seed") is None:
    canonical_data["_nonce"] = uuid.uuid4().hex[:_DATASET_ID_NONCE_LENGTH]
```

This is a worked example of **when not to content-address**. Content-addressing assumes the name is a total function of the inputs. With `seed` absent the generator is itself non-deterministic — identical parameters produce *different* data — so hashing the parameters would name two different artifacts identically, and the second request would silently receive the first one's data. Mixing in a
nonce deliberately breaks content-addressing for exactly the case where its premise is false. The rule generalises: **content-address only over inputs that fully determine the output.** Wall-clock time, unseeded randomness, and upstream mutable state all violate that premise.

#### Ground truth: the route-ordering dependency

juniper-data declares these GET routes on the `/datasets` router, in this order:

| Line              | Route               | Kind      |
|-------------------|---------------------|-----------|
| `datasets.py:276` | `GET /filter`       | literal   |
| `datasets.py:338` | `GET /stats`        | literal   |
| `datasets.py:604` | `GET /versions`     | literal   |
| `datasets.py:628` | `GET /latest`       | literal   |
| `datasets.py:651` | `GET /{dataset_id}` | catch-all |

The order is **load-bearing**. Starlette matches routes in declaration order, and `/{dataset_id}` is an unconstrained single-segment parameter that matches the literal string `stats` perfectly well. Move `:651` above `:338` — a plausible outcome of an alphabetise-the-handlers refactor or a merge that reorders a file — and `GET /v1/datasets/stats` stops reaching `get_dataset_stats`, entering
`get_dataset_metadata` with `dataset_id="stats"`. The store lookup misses and the caller gets:

```http
HTTP/1.1 404 Not Found
Content-Type: application/json

{"detail": "Dataset 'stats' not found"}
```

the worst possible failure shape: a plausible, well-formed 404 that reads as a data problem rather than a routing problem. No test asserts the ordering; no path converter constrains `{dataset_id}`.

Two hardenings, either of which removes the dependency. **Constrain the parameter** — dataset IDs match `{generator}-{version}-{16 hex}`, so a regex or validated converter makes `stats` non-matching and turns the misroute into a clean routing-layer rejection. Or **segregate the namespace** — put aggregates under a prefix that cannot collide (`/datasets/-/stats`, or a sibling `/dataset-stats`). The
general rule: **a catch-all path parameter and a sibling literal segment in the same position are an ambient ordering dependency**, and ordering dependencies no test asserts are the ones that break.

#### Syntax details that produce real bugs

**Trailing slashes.** `/datasets` and `/datasets/` are different URIs. RFC 9110 §4.2.3's normalisation makes an *empty* path equivalent to `/`, but nothing merges `/x` and `/x/`. Pick one form, redirect the other with 308 (preserving the method — see II.4), never serve 200 from both. Starlette's `redirect_slashes` performs the redirect for you but emits **307**, not 308: the router constructs
`RedirectResponse(url=...)` with no `status_code` (`starlette/routing.py:716`, Starlette 1.6.0) and that class defaults to 307
(`responses.py:204-212`). Method-preserving, but *temporary* — so no cache, client, or crawler ever learns which form is canonical, and a POST to the wrong form gets a redirect your client may or may not follow with the body intact. Emitting 308 means handling the redirect yourself.

**Case sensitivity.** §4.2.3: "The scheme and host are case-insensitive and normally provided in lowercase; all other components are compared in a case-sensitive manner." So `/Datasets` differs from `/datasets`, and `?Limit=10` from `?limit=10`. Lowercase your paths; do not rely on middleware to fold case.

**Percent-encoding.** Same section: "Characters other than those in the 'reserved' set are equivalent to their percent-encoded octets: the normal form is to not encode them." The spec's own example makes `http://example.com:80/~smith/home.html`, `http://EXAMPLE.com/%7Esmith/home.html`, and `http://EXAMPLE.com:/%7esmith/home.html` all equivalent. Practically: do not build identifiers from
characters whose encoding is negotiable, and never put a `/` inside a path-segment value — encoded or not, some proxy between you and the client will decode it early and change your routing.

#### Judgement Calls

- **Slug or opaque?** Slug if humans type or read it, with permanent redirects on rename. Opaque if a machine passes it around. Never sequential integers on a public surface.
- **Nest or query?** Nest when the child cannot exist without the parent and has no global identity. Query otherwise.
- **Action sub-resource or PATCH?** If the transition has attributes worth recording (who, when, why), make it a resource. If it is a plain field flip, PATCH the field.
- **Emit links or publish templates?** Templates for a small controlled client set; links when clients are numerous or uncontrolled. Do not do neither and hope.

#### Tradeoffs

| Choice                              | Gains                                                         | Costs                                                                                      |
|-------------------------------------|---------------------------------------------------------------|--------------------------------------------------------------------------------------------|
| Content-addressed IDs               | Free deduplication, idempotent creation, immutable cache keys | Fails when generation is non-deterministic; long identifiers; any parameter change renames |
| Deep nesting                        | Expresses ownership; natural authorisation scoping            | Clients carry IDs they do not need; refactoring containment breaks every URL               |
| Literal segments beside a catch-all | Readable, conventional URLs                                   | Silent ordering dependency; needs a converter or a test to be safe                         |
| Mandatory query params for identity | Avoids inventing a parent collection                          | The URI without the param looks addressable but is not; yields 422 where 404 is expected   |

#### Best Practices

- One canonical URI per resource; aliases redirect (308/301), never duplicate.
- Constrain path parameters with a converter or regex whenever a literal sibling exists at the same position, and add a routing test asserting each literal reaches its own handler — three lines that pin the dependency permanently.
- Lowercase paths; pick a trailing-slash policy and enforce it with a redirect.
- Derive emitted URLs from the router's own constant. juniper-data repeats the `/v1` literal in `app.py:140-142` *and* in `datasets.py:138`/`:253` with no shared constant — four places, nothing to catch a miss.
- Never encode a `/` into a path-segment value.

#### Common Failure Modes

- **Catch-all shadowing.** The `/{dataset_id}` versus `/stats` case above: a reorder turns a working route into a convincing 404.
- **Two URIs, one resource.** Alias and canonical both serving 200; cache splits, validators diverge.
- **Verb creep.** `/datasets/create`, `/datasets/{id}/update` — Level 1 with extra steps, disabling method-based reasoning in every intermediary.
- **Identity in the query string.** `/latest?name=X` looks like a collection URI, behaves like an item URI, and 422s instead of 404s when identity is missing.
- **Inferred templates.** A client guessing `/datasets/{id}/preview` from `/datasets/{id}/artifact` couples itself to a surface you never published.

#### Error Handling

Routing errors deserve distinguishable responses. Three cases commonly collapsed into one 404:

| Condition                          | Correct code | Why                                                                                             |
|------------------------------------|--------------|-------------------------------------------------------------------------------------------------|
| Path matches no route              | 404          | Genuinely no such resource                                                                      |
| Path matches, resource absent      | 404          | Same code, but the body should name the identifier, as `datasets.py:670` does                   |
| Path matches, method not supported | 405          | RFC 9110 §15.5.6 — and the server **MUST** generate an `Allow` header listing supported methods |

FastAPI produces the 405-with-`Allow` behaviour automatically, worth knowing so you do not hand-roll a 404 in its place. The remaining gap in juniper-data is that hand-raised 404s use `detail: string` while FastAPI's automatic validation failures use `detail: [array of objects]`, so clients cannot parse errors uniformly — covered in II.4.

---

### II.3 Methods: Safety, Idempotency, and the Complete Table

#### Overview

Method semantics are the part of HTTP that generic components actually act on. A cache decides what to store from the method; a proxy decides what it may retry; a client library decides whether a connection failure is safe to repeat. Get the method wrong and you do not get a validation error — you get a duplicate charge, a lost update, or a prefetcher that deletes your data.

#### Background

RFC 9110 §9.1 defines the method set, §9.2 the common properties, §9.3 each method. §16.1.1 makes the IANA "Hypertext Transfer Protocol (HTTP) Method Registry" authoritative and requires every registration to declare "Safe ('yes' or 'no')" and "Idempotent ('yes' or 'no')" — so these are registry-level facts about a method, not per-implementation choices.

Two structural rules worth internalising, both from §9.1: "All general-purpose servers MUST support the methods GET and HEAD. All other methods are OPTIONAL"; and an *unrecognised* method gets 501 while a recognised-but-not-allowed method gets 405 — a distinction almost no framework makes correctly. PATCH is not in RFC 9110 at all: it is [RFC 5789](https://www.rfc-editor.org/rfc/rfc5789.html)
(March 2010), and its properties differ from every other write method.

#### The complete table

Every cell below was read out of the specification text, not recalled.

| Method  | Safe | Idempotent | Cacheable                                                             | Request body                | Response body               | Defined in      |
|---------|------|------------|-----------------------------------------------------------------------|-----------------------------|-----------------------------|-----------------|
| GET     | Yes  | Yes        | Yes                                                                   | SHOULD NOT                  | Yes                         | RFC 9110 §9.3.1 |
| HEAD    | Yes  | Yes        | Yes                                                                   | SHOULD NOT                  | **MUST NOT**                | RFC 9110 §9.3.2 |
| POST    | No   | No         | Only with explicit freshness **and** `Content-Location` == target URI | Yes                         | Usually                     | RFC 9110 §9.3.3 |
| PUT     | No   | Yes        | No                                                                    | Yes                         | 201, or 200/204             | RFC 9110 §9.3.4 |
| DELETE  | No   | Yes        | No                                                                    | SHOULD NOT                  | 200/202/204                 | RFC 9110 §9.3.5 |
| PATCH   | No   | **No**     | Only with explicit freshness and matching `Content-Location`          | Yes (the patch document)    | Usually                     | RFC 5789 §2     |
| OPTIONS | Yes  | Yes        | No                                                                    | Allowed, but no defined use | Optional                    | RFC 9110 §9.3.7 |
| TRACE   | Yes  | Yes        | No                                                                    | **MUST NOT**                | Yes (the reflected message) | RFC 9110 §9.3.8 |
| CONNECT | No   | No         | No                                                                    | **None**                    | No (a tunnel follows)       | RFC 9110 §9.3.6 |

Sourcing for the non-obvious cells. **Safe set**, §9.2.1: "Of the request methods defined by this specification, the GET, HEAD, OPTIONS, and TRACE methods are defined to be safe" — so POST, PUT, DELETE, CONNECT are not, and RFC 5789 §2 declares PATCH unsafe. **Idempotent set**, §9.2.2: "Of the request methods defined by this specification, PUT, DELETE, and safe request methods are idempotent" — so
POST and CONNECT are not, and PATCH is not (RFC 5789 §2, verbatim: "PATCH is neither safe nor idempotent"). **Cacheability**, §9.2.3: "This specification defines caching semantics for GET, HEAD, and POST, although the overwhelming majority of cache implementations only support GET and HEAD"; §9.3.4 through §9.3.8 each state explicitly that responses to PUT, DELETE, CONNECT, OPTIONS, and TRACE "are
not cacheable", and POST's conditions are spelled out in §9.3.3.

**GET/HEAD/DELETE request bodies** all carry the same paragraph: content "has no generally defined semantics, cannot alter the meaning or target of the request, and might lead some implementations to reject the request and close the connection because of its potential as a request smuggling attack", and a client "SHOULD NOT generate content" in them. Framing permits it; nothing sensible consumes
it. **HEAD response body**, §9.3.2: "identical to GET except that the server MUST NOT send content in the response." **CONNECT**, §9.3.6: "A CONNECT request message does not have content" — a 2xx switches the connection to tunnel mode immediately after the header section. **OPTIONS request body**, §9.3.7, permits it but adds: "Note that this specification does not define any use for such content."

#### What "safe" actually means

Safe is about **intent**, not a guarantee the server does nothing. RFC 9110 §9.2.1 is unusually direct:

> This definition of safe methods does not prevent an implementation from including behavior that is potentially harmful, that is not entirely read-only, or that causes side effects while invoking a safe method. What is important, however, is that the client did not request that additional behavior and cannot be held accountable for it.

The spec's own examples are access logging and an ad click that charges an advertising account. juniper-data has a textbook instance: both `GET /v1/datasets/{id}` and `GET /v1/datasets/{id}/artifact` schedule a write — `asyncio.get_event_loop().call_soon(lambda: store.record_access(dataset_id))` at `juniper_data/api/routes/datasets.py:672` and `:698`. Server state changes on every GET, and the
method is still safe, because the caller neither asked for nor is accountable for the access counter.

The rule that follows is the one that bites: "the purpose of distinguishing between safe and unsafe methods is to allow automated retrieval processes (spiders) and cache performance optimization (pre-fetching) to work without fear of causing harm." If your GET does something you would mind having done a thousand times unbidden, it is not merely unsafe — it is a defect, and §9.2.1 says so: if a
resource's purpose is to perform an unsafe action, "the resource owner MUST disable or disallow that action when it is accessed using a safe request method."

#### Idempotency, and the subtlety that idempotent ≠ same response

§9.2.2: "A request method is considered 'idempotent' if the intended effect on the server of multiple identical requests with that method is the same as the effect for a single such request."

The property concerns **server-side effect**, not the response. The spec makes this explicit for retries: a client retrying a PUT after a connection failure "knows that repeating the request will have the same intended effect, even if the original request succeeded, **though the response might differ**." The canonical illustration is DELETE: `DELETE /datasets/abc` returns 204 the first time and
404 the second — different responses, identical end state. DELETE is idempotent. Anyone who "fixes" the second call to also return 204 in the name of idempotency has misunderstood the property and destroyed a useful signal.

**Why PUT is idempotent and POST is not** comes straight from what each says about the enclosed representation (§9.3.4): "The target resource in a POST request is intended to handle the enclosed representation according to the resource's own semantics, whereas the enclosed representation in a PUT request is defined as replacing the state of the target resource. Hence, the intent of PUT is
idempotent and visible to intermediaries." PUT names *what the state should be*; applying that twice reaches the same state. POST names *a thing to process*; processing it twice processes it twice.

The operational consequences, all §9.2.2, are exactly the rules Part I's three retry policies disagree about: "A client SHOULD NOT automatically retry a request with a non-idempotent method unless it has some means to know that the request semantics are actually idempotent, regardless of the method, or some means to detect that the original request was never applied"; "A proxy MUST NOT
automatically retry non-idempotent requests"; "A client SHOULD NOT automatically retry a failed automatic retry."

`juniper-data-client` cites §9.2.2 by name in its retry constants and restricts retries to `HEAD,GET,PUT`. `juniper-cascor-client` retries `GET,POST,DELETE,PUT,PATCH` against endpoints including `POST /v1/training/start` and `POST /v1/snapshots`, with no idempotency key — the "some means to know" clause asserted without any means. Idempotency keys, the mechanism that legitimately makes a POST
retryable, are covered in Part I.7 and not repeated here.

#### PATCH

PATCH sends a *patch document*: "a set of instructions describing how a resource currently residing on the origin server should be modified to produce a new version" (RFC 5789 §2), against PUT where "the enclosed entity is considered to be a modified version of the resource stored on the origin server". Three properties catch people out.

1. **Not idempotent by default.** RFC 5789 §2, verbatim: "PATCH is neither safe nor idempotent." A patch saying `{"op":"add","path":"/tags/-","value":"x"}` appends a tag every time it runs. A patch saying `{"status":"cancelled"}` happens to be idempotent — but that is a property of that document, not the method, and no intermediary can tell them apart.
2. **Atomic.** "The server MUST apply the entire set of changes atomically and never provide (e.g., in response to a GET during this operation) a partially modified representation. If the entire patch document cannot be successfully applied, then the server MUST NOT apply any of the changes."
3. **Conditional by recommendation.** "Clients using this kind of patch application SHOULD use a conditional request such that the request will fail if the resource has been updated since the client last accessed the resource. For example, the client can use a strong ETag in an If-Match header on the PATCH request."

**Patch document formats.** RFC 5789 deliberately defines none — "there is no single default patch document format that implementations are required to support." The two that matter are both Standards Track:

| Format           | RFC                     | Media type                     | Shape                                                                                    |
|------------------|-------------------------|--------------------------------|------------------------------------------------------------------------------------------|
| JSON Patch       | RFC 6902 (April 2013)   | `application/json-patch+json`  | An array of operations: `add`, `remove`, `replace`, `move`, `copy`, `test` (RFC 6902 §4) |
| JSON Merge Patch | RFC 7396 (October 2014) | `application/merge-patch+json` | A partial document; `null` means delete the member                                       |

Two accuracy notes. **JSON Merge Patch is RFC 7396, which obsoletes RFC 7386** — RFC 7386 is frequently cited and is the wrong number. And "PATCH with a partial JSON object and `Content-Type: application/json`" is *neither* format: it is an ad-hoc convention resembling merge patch with no specification, no `null`-means-delete guarantee, and no `test` operation. Defensible for an internal API —
just do not label it as either RFC. JSON Patch's `test` operation is the underrated one: it turns a patch into its own precondition, so `[{"op":"test","path":"/version","value":7},{"op":"replace",…}]` fails atomically if the resource moved, without an ETag round trip.

#### PUT vs PATCH vs POST

| Situation                                      | Method | Reasoning                                                                                                                                                                    |
|------------------------------------------------|--------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Client knows the full target state and the URI | PUT    | Idempotent, intermediary-visible, replaces state (§9.3.4)                                                                                                                    |
| Client knows a delta, not the whole document   | PATCH  | Sending the whole document would clobber concurrent edits to fields you did not touch                                                                                        |
| Server chooses the URI                         | POST   | §9.3.4: "A service that selects a proper URI on behalf of the client, after receiving a state-changing request, SHOULD be implemented using the POST method rather than PUT" |
| Operation is a process, not a state assignment | POST   | The catch-all by design; §9.3.3 lists "providing a block of data ... to a data-handling process" first                                                                       |
| Creating a resource at a client-chosen URI     | PUT    | §9.3.4: PUT MUST return 201 if it created, 200/204 if it replaced                                                                                                            |

The strongest signal is the third row's inverse: if you are writing PUT while thinking "but the server assigns the ID", you want POST.

#### Conditional requests: making an unsafe operation safe to retry

A precondition converts a blind write into a compare-and-swap — *provided the server evaluates the condition and performs the write as a single atomic operation*. RFC 9110 §13.1 defines the preconditions; §13.1.1 (`If-Match`) is the one for writes. The 412-or-write exchange is only the protocol half; II.6 covers the storage half, without which a precondition narrows the lost-update window rather than closing it.

```http
PATCH /v1/datasets/spiral-v1.0.0-a3f8e12b4c567890/tags HTTP/1.1
If-Match: "a3f8e12b4c567890"
Content-Type: application/merge-patch+json

{"tags": ["train", "validated"]}
```

If the representation changed since the client's copy, the server returns **412 Precondition Failed** (§15.5.13) and applies nothing. The write is now safe to retry: a repeat either fails cleanly or applies to the state it was written against. This is what makes PATCH's non-idempotency tolerable, and why RFC 5789 §2 recommends it directly.

The server-side half is a validator. juniper-data computes exactly the value it needs — a SHA-256 over the serialised NPZ bytes, stored on `DatasetMeta.checksum` — and never sends it as an `ETag`, so no client can make a conditional request against it. The material is there; the header is not. RFC 6585 §3's **428 Precondition Required** covers the other side: a server that *requires* conditional
writes can reject unconditional ones outright, "to avoid the 'lost update' problem". Validator generation, strong versus weak
comparison, and the full optimistic-concurrency pattern are II.6's subject; this section needs only the fact that a precondition
converts an unsafe write into a retryable one.

#### Method overriding

`X-HTTP-Method-Override: DELETE` on a POST, or `?_method=PUT`, is a tunnelling hack from an era when HTML forms and some corporate proxies supported only GET and POST. It is a de-facto convention with no RFC — do not cite one. It is a smell for mechanical, not aesthetic, reasons.

- **It defeats every generic component.** A cache, proxy, or WAF sees POST and reasons about POST. The point of a uniform interface (§5.1.5) is that intermediaries act on method semantics without application knowledge; overriding hides the semantics in a header they do not read.
- **It defeats retry logic in both directions.** A library that will not retry POST refuses to retry a method-overridden GET; one that retries POST happily retries a method-overridden DELETE.
- **It is an authorisation bypass surface.** Any perimeter rule written as "deny DELETE to this path" is evaded by POST-plus-header. This has been a real CVE class.

If you must support it for a legacy client you do not control, terminate the override at the very edge — before any security or caching layer — and allow it only for an explicit method allowlist on explicit paths.

#### Judgement Calls

- **PUT or PATCH for updates?** PATCH when partial updates are the common case or concurrent writers touch different fields. PUT when the client legitimately holds the whole document and you want free idempotency.
- **Is my POST really a POST?** If two identical requests should produce one resource, you want PUT at a client-chosen URI, content-addressing (juniper-data's approach), or an idempotency key. Plain POST plus retries is the bug.
- **204 or 200 for DELETE?** 204 unless the caller needs the deleted representation or a job handle; 202 if deletion is asynchronous. §9.3.5 lists all three explicitly.
- **Expose OPTIONS?** Rarely worth it. RFC 9205 §4.5.2 lists the reasons — not linkable, not cacheable, chatty, patchy server support — and recommends a well-known URI or a `Link` header instead.

#### Tradeoffs

| Choice                        | Gains                                                 | Costs                                                                                  |
|-------------------------------|-------------------------------------------------------|----------------------------------------------------------------------------------------|
| Retry only idempotent methods | Cannot duplicate side effects; matches §9.2.2         | Transient failures on POST surface to the caller                                       |
| Retry everything              | Fewer visible failures                                | Duplicate creates and repeated side effects — the live risk in `juniper-cascor-client` |
| PATCH with JSON Patch         | Precise; `test` gives free preconditions; spec-backed | Clients must build op arrays; harder to read in logs                                   |
| PATCH with merge patch        | Trivial for clients; looks like the resource          | Cannot express array insertion; `null` is overloaded as "delete"                       |
| Method override               | Works through hostile intermediaries                  | Blinds caches, proxies, WAFs; authorisation-bypass surface                             |

#### Best Practices

- Declare the retry policy per method, in code, with the RFC cited — `juniper-data-client` does this, and it is why its policy survived review.
- Never let a safe method perform an action the caller requested. Logging and counters are fine; anything the client asked for is not.
- Return 405 with `Allow` for a wrong method (§15.5.6 makes `Allow` mandatory) and 501 for an unrecognised one.
- Choose and document one patch format; put it in the media type, not the prose docs.
- Emit an `ETag` whenever you already compute a digest — juniper-data computes one and discards it — and support `If-Match` on every unsafe method that can lose an update.

#### Common Failure Modes

- **Retrying POST.** Duplicate datasets, charges, emails. The single most expensive method bug.
- **Non-idempotent PUT.** A handler that appends to a list, or stamps `updated_at` into the resource's identity, is no longer safe for intermediaries to retry.
- **PATCH without preconditions.** Two concurrent partial updates; last writer silently wins on the overlapping field.
- **GET with side effects the caller asked for.** `GET /orders/{id}/cancel` is the archetype; a prefetcher, link checker, or browser preconnect will eventually call it.
- **404 where 405 belongs.** Hides a client bug (wrong method) as a data problem, and drops the `Allow` header that would have told the client what to do.

#### Error Handling

RFC 5789 §2.2 gives PATCH's error mapping, and it generalises to all write methods:

| Condition                                             | Code | Source                                     |
|-------------------------------------------------------|------|--------------------------------------------|
| Patch document media type not supported               | 415  | RFC 5789 §2.2                              |
| Patch document malformed                              | 400  | RFC 5789 §2.2                              |
| Patch well-formed but not applicable to current state | 409  | RFC 5789 §2.2 — "Conflicting state"        |
| `If-Match` / `If-Unmodified-Since` failed             | 412  | RFC 5789 §2.2; RFC 9110 §15.5.13           |
| Resource concurrently modified, no precondition sent  | 409  | RFC 5789 §2.2 — "Conflicting modification" |
| Server requires conditional requests                  | 428  | RFC 6585 §3                                |

Note the 409/412 split precisely: **412 means a precondition you sent evaluated false; 409 means the request conflicts with current state and you sent no precondition.** RFC 5789 §2.2 makes the distinction explicit, and it is the most useful thing in that section.

---

### II.4 Status Codes

#### Overview

Status codes are a small, fixed, generic vocabulary that both your application and every intermediary between you and your client must interpret consistently. They are not an error taxonomy for your domain, and the most common design error is treating them as one.

#### Background

RFC 9110 §15 defines the status codes. §15.1 notes reason phrases "are only recommendations" and may be replaced or omitted — HTTP/2 does not carry them at all. §16.2 makes the IANA registry authoritative and requires IETF Review for new codes.

[RFC 6585](https://www.rfc-editor.org/rfc/rfc6585.html) (April 2012) adds four that RFC 9110 does not carry: 428 Precondition Required, 429 Too Many Requests, 431 Request Header Fields Too Large, and 511 Network Authentication Required. Note that 422 *did* move: RFC 9110 Appendix B.3 records "Status code 422 (previously defined in Section 11.2 of [WEBDAV]) has been added because of its general
applicability." It is now §15.5.21, renamed from "Unprocessable Entity" to **"Unprocessable Content"**.

The design advice that matters most is RFC 9205 §4.6: "applications using HTTP should define their errors to use the most applicable status code, making generous use of the general status codes (200, 400, and 500) when in doubt. Importantly, they should not specify a one-to-one relationship between status codes and application errors." The reason given is that the code space is finite and status
codes "are often generated by components other than the application itself" — a CDN, a captive portal, an overloaded proxy — so a client reading application meaning into a bare code can be misled by an intermediary that never saw your handler.

#### The classes

| Class | Meaning (RFC 9110) | Client's default reaction |
| --- | --- | --- |
| 1xx Informational | "an interim response for communicating connection status or request progress prior to completing the requested action and sending a final response" (§15.2). Cannot contain content or trailers | Parse and usually ignore; a final response follows |
| 2xx Successful | "the client's request was successfully received, understood, and accepted" (§15.3) | Proceed |
| 3xx Redirection | "further action needs to be taken by the user agent in order to fulfill the request" (§15.4) | Follow `Location` carefully — see the method-rewriting rules below |
| 4xx Client Error | "the client seems to have erred" (§15.5). Server SHOULD send a representation explaining the situation "and whether it is a temporary or permanent condition" | Do not blind-retry; fix the request |
| 5xx Server Error | "the server is aware that it has erred or is incapable of performing the requested method" (§15.6). Same representation requirement | Retry with backoff **only if the method is idempotent** |

The "n00 fallback" rule from RFC 9205 §4.6 is the one to build clients around: an unrecognised code should be handled as the generic code of its class — "499 can be safely handled as 400 (Bad Request) by clients that don't recognise it".

#### The codes that matter, precisely

| Code      | Name                                   | Use it when                                                                                     | RFC                    |
|-----------|----------------------------------------|-------------------------------------------------------------------------------------------------|------------------------|
| 200       | OK                                     | Success with a representation                                                                   | 9110 §15.3.1           |
| 201       | Created                                | One or more resources were created; identify the primary one via `Location`                     | 9110 §15.3.2           |
| 202       | Accepted                               | Accepted for later processing; "intentionally noncommittal"                                     | 9110 §15.3.3           |
| 204       | No Content                             | Success, nothing to send. Cannot contain content or trailers                                    | 9110 §15.3.5           |
| 206       | Partial Content                        | Successful range request                                                                        | 9110 §15.3.7           |
| 301 / 308 | Moved Permanently / Permanent Redirect | Resource has a new permanent URI                                                                | 9110 §15.4.2 / §15.4.9 |
| 302 / 307 | Found / Temporary Redirect             | Resource temporarily elsewhere                                                                  | 9110 §15.4.3 / §15.4.8 |
| 303       | See Other                              | The result of this operation is available elsewhere via GET                                     | 9110 §15.4.4           |
| 304       | Not Modified                           | Conditional GET/HEAD whose precondition made a transfer unnecessary                             | 9110 §15.4.5           |
| 400       | Bad Request                            | "malformed request syntax, invalid request message framing, or deceptive request routing"       | 9110 §15.5.1           |
| 401       | Unauthorized                           | Missing or invalid credentials. **MUST** send `WWW-Authenticate`                                | 9110 §15.5.2           |
| 403       | Forbidden                              | Understood, refused; credentials (if any) insufficient                                          | 9110 §15.5.4           |
| 404       | Not Found                              | No current representation, or unwilling to disclose one exists                                  | 9110 §15.5.5           |
| 405       | Method Not Allowed                     | Method known, not supported here. **MUST** send `Allow`                                         | 9110 §15.5.6           |
| 406       | Not Acceptable                         | No representation matches the negotiation fields and no default will be sent                    | 9110 §15.5.7           |
| 409       | Conflict                               | Conflicts with current resource state; user might resolve and resubmit                          | 9110 §15.5.10          |
| 410       | Gone                                   | Permanently unavailable, and the server knows it                                                | 9110 §15.5.11          |
| 412       | Precondition Failed                    | A condition in the request header fields evaluated false                                        | 9110 §15.5.13          |
| 413       | Content Too Large                      | Request content exceeds what the server will process                                            | 9110 §15.5.14          |
| 415       | Unsupported Media Type                 | Request content is in a format the resource does not support                                    | 9110 §15.5.16          |
| 422       | Unprocessable Content                  | Media type understood, syntax correct, instructions not processable                             | 9110 §15.5.21          |
| 428       | Precondition Required                  | Server requires the request to be conditional                                                   | 6585 §3                |
| 429       | Too Many Requests                      | "the user has sent too many requests in a given amount of time"                                 | 6585 §4                |
| 500       | Internal Server Error                  | "an unexpected condition that prevented it from fulfilling the request"                         | 9110 §15.6.1           |
| 501       | Not Implemented                        | "the server does not support the functionality required to fulfill the request"                 | 9110 §15.6.2           |
| 502       | Bad Gateway                            | Acting as gateway/proxy, got an invalid response from upstream                                  | 9110 §15.6.3           |
| 503       | Service Unavailable                    | "temporary overload or scheduled maintenance, which will likely be alleviated after some delay" | 9110 §15.6.4           |
| 504       | Gateway Timeout                        | Acting as gateway/proxy, no timely response from upstream                                       | 9110 §15.6.5           |

#### The commonly-misused pairs

**200 vs 201 vs 202 vs 204.** 201 requires that something was created and that the primary new resource is identified "by either a `Location` header field in the response or, if no `Location` header field is received, by the target URI" (§15.3.2). 202 is for work not yet done: "the processing has not been completed. The request might or might not eventually be acted upon" — and it "ought to
describe the request's current status and point to (or embed) a status monitor". 204 means success with nothing to say, and "cannot contain content or trailers", so a 204 with a JSON body is a protocol violation some clients surface as a parse error. *Wrong:* returning 200 with `{"created": true, "id": "…"}` from a create endpoint — the information sits in the body where no intermediary can see
it, and there is no `Location`.

**301 vs 302 vs 307 vs 308 — the method-rewriting fact.** The single most valuable redirect fact, and routinely stated backwards. RFC 9205 §4.6.1 tabulates it exactly:

|                                                          | Permanent | Temporary |
|----------------------------------------------------------|-----------|-----------|
| **Allows** change of the request method from POST to GET | 301       | 302       |
| **Does not allow** change of the request method          | 308       | 307       |

RFC 9110's own notes on 301 and 302 say "For historical reasons, a user agent MAY change the request method from POST to GET for the subsequent request. If this behavior is undesired, the 308 (Permanent Redirect) status code can be used instead" (§15.4.2; §15.4.3 says the same pointing at 307). §15.4.8 is unambiguous the other way: with 307 "the user agent **MUST NOT** change the request method".
The history is in §15.4's note — 301 and 302 were originally method-preserving, early user agents split on redirecting POST as POST or as GET, "prevailing practice eventually converged on changing the method to GET", and 307/308 were added later to express the preserving behaviour unambiguously.

*Wrong:* redirecting `POST /v1/orders` to `POST /v2/orders` with a 301. Clients may re-issue it as `GET /v2/orders`, dropping the body — and §15.4 step 5 says that once the method changes to GET, the agent removes `Content-Type`, `Content-Length`, and the rest of the content-specific fields. The order silently vanishes. Use 308.

**401 vs 403.** 401 means "you are not authenticated, or your credentials are not valid here" and **MUST** carry a `WWW-Authenticate` challenge (§15.5.2). 403 means "understood, refused"; if credentials were supplied "the server considers them insufficient to grant access", and "The client SHOULD NOT automatically repeat the request with the same credentials" (§15.5.4). Mnemonic: 401 says *try
again with credentials*, 403 says *do not bother*. A 401 without `WWW-Authenticate` is non-conformant and confuses generic clients that would otherwise prompt or refresh. And §15.5.4 explicitly blesses the hiding pattern: "An origin server that wishes to 'hide' the current existence of a forbidden target resource MAY instead respond with a status code of 404 (Not Found)."

**404 vs 410.** 404 "does not indicate whether this lack of representation is temporary or permanent". 410 asserts permanence — "if the origin server does not know, or has no facility to determine, whether or not the condition is permanent, the status code 404 ought to be used instead" (§15.5.11). Use 410 when you have actually recorded a tombstone, not as a fancier 404.

**409 vs 412.** The distinction turns entirely on whether the client sent a precondition. 412 means a condition in the request header fields evaluated false (§15.5.13). 409 means the request conflicts with current state, "in situations where the user might be able to resolve the conflict and resubmit" (§15.5.10), and the server "SHOULD generate content that includes enough information for a user
to recognize the source of the conflict". *Wrong:* returning 409 for a failed `If-Match` — the client sent a precondition and deserves 412, which its HTTP stack may already handle.

**429.** RFC 6585 §4: "the user has sent too many requests in a given amount of time ('rate limiting')". The response "SHOULD include details explaining the condition, and MAY include a `Retry-After` header". Two things people get wrong: RFC 6585 defines *no* rate-limit headers beyond `Retry-After` (`X-RateLimit-*` is a vendor convention; the `RateLimit` fields are
`draft-ietf-httpapi-ratelimit-headers`, an Internet-Draft, not an RFC), and "Responses with the 429 status code MUST NOT be stored by a cache."

**500 vs 502 vs 503 vs 504.** 500 is *your* unexpected failure. 502 and 504 are specifically about acting "as a gateway or proxy" — 502 an invalid response from upstream, 504 no timely response from upstream. If your service is not a gateway, emitting them tells operators to look at a proxy that does not exist. 503 asserts "temporary overload or scheduled maintenance, which will likely be
alleviated after some delay" — an assertion that the condition *clears*.

#### `Retry-After` on 429 and 503

RFC 9110 §10.2.3: "Servers send the 'Retry-After' header field to indicate how long the user agent ought to wait before making a follow-up request." Its grammar is `HTTP-date / delay-seconds`, where delay-seconds is "a non-negative decimal integer". Both `Retry-After: Fri, 31 Dec 1999 23:59:59 GMT` and `Retry-After: 120` are valid, and a client must handle both.

Which responses it applies to is worth stating carefully, because §10.2.3 names only two contexts: "When sent with a 503 (Service Unavailable) response, Retry-After indicates how long the service is expected to be unavailable to the client. When sent with any 3xx (Redirection) response, Retry-After indicates the minimum time that the user agent is asked to wait before issuing the redirected
request." The 429 pairing comes from RFC 6585 §4, and 413 mentions it too: "If the condition is temporary, the server SHOULD generate a Retry-After header field" (§15.5.14). Send it whenever you know the answer — a 503 without it forces every client into its own guess, which is how synchronised retry storms form.

#### Ground truth: juniper-data's deliberate 501, not 503

When a generator's optional dependency is missing, juniper-data returns **501 Not Implemented**, and the code says exactly why (`juniper_data/api/routes/datasets.py:158-168`):

```python
# D1 (I-5): a generator raising ImportError means an optional dependency
# is missing in this deployment — a deterministic capability gap, not an
# internal error. Surface it as 501 Not Implemented with the generator's
# actionable install hint (e.g. "pip install datasets") instead of letting
# the bare re-raise below mask it as a generic 500. 503 is deliberately
# avoided: it invites client retries and health-tooling misreads for a
# condition that will not clear on its own.
raise HTTPException(
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    detail=f"Generator '{request.generator}' is not available in this deployment: {e}",
)
```

The reasoning checks out against the spec and is worth spelling out as a reusable rule. 503 asserts a condition "which will likely be alleviated after some delay" (§15.6.4) and invites `Retry-After`-driven retry. A missing Python package will not install itself. Asserting 503 would make three things worse: clients would retry a permanently-failing request, health checkers would mark an
otherwise-healthy service degraded, and the operator would be reading a capacity dashboard for a packaging problem. 501 — "the server does not support the functionality required to fulfill the request" (§15.6.2) — says the true thing.

One nuance the code does not address: 501 is in §15.1's heuristically-cacheable list ("200, 203, 204, 206, 300, 301, 308, 404, 405, 410, 414, and 501"). It happens not to matter here because this 501 arises on a POST, and POST responses are cacheable only with explicit freshness and a matching `Content-Location` (§9.3.3), neither of which juniper-data emits. Worth knowing before reusing 501 on a
GET.

#### Ground truth: the cache hit that returns 201

`POST /v1/datasets` is declared `status_code=201` (`datasets.py:71`). Because the dataset ID is content-addressed, a repeat POST with identical parameters finds the existing metadata and returns it from the cache-hit branch (`:120-139`) — with the same 201. The endpoint therefore has **no way to signal "this already existed."** A genuine creation and an idempotent no-op are identical on the wire,
and a metrics pipeline counting 201 as "datasets created" over-counts every retry and every deterministic re-request.

There is a real tension here worth being fair about. Content-addressing makes the POST effectively idempotent — a property Part I praised — and one honest reading is that the request's *intent* ("ensure this dataset exists") was fulfilled either way, so 201 is not a lie. The counter-argument is that §15.3.2 ties 201 to the claim that the request "has resulted in one or more new resources being
created", which on a cache hit is false.

Three ways out, in increasing order of disruption: **200 on cache hit, 201 on creation** — minimal, spec-honest, a one-line change; clients checking only `2xx` are unaffected and clients that care gain the signal. **A response field** — `CreateDatasetResponse` already carries `dataset_id`, `generator`, `meta`, and `artifact_url`, so adding `created: bool` costs nothing and breaks nobody, though an
intermediary cannot see it. **303 See Other** pointing at the existing resource, which §9.3.3 explicitly blesses: "If the result of processing a POST would be equivalent to a representation of an existing resource, an origin server MAY redirect the user agent to that resource by sending a 303 (See Other) response" — most correct, most disruptive.

Notably, juniper-data *does* observe the distinction internally: the cache-hit branch records `cache=POST_CACHE_HIT` to Prometheus (`:129-133`) while the generation path records `cache=POST_CACHE_MISS` (`:181-185`). The information exists and is exported to operators; it is only withheld from the caller.

#### Judgement Calls

- **How many distinct codes?** Few. RFC 9205 §4.6 says be generous with 200/400/500 and put fine-grained information in the body rather than minting a per-error code.
- **404 or 403 for an unauthorised resource?** 404 when the resource's existence is itself confidential (§15.5.4 permits it), 403 otherwise — and be consistent, because an API that leaks existence through the 403/404 difference has an enumeration oracle.
- **202 or synchronous?** 202 the moment work outlives a sensible request timeout. juniper-data has no async job pattern at all — no 202, no job resource — and instead offloads blocking work per-request via `asyncio.to_thread`. That works until a generator outlives the client's socket timeout.
- **Custom codes?** Never. RFC 9205 §4.6: "Applications MUST only use registered HTTP status codes."

#### Tradeoffs

| Choice                                 | Gains                                                      | Costs                                                                                         |
|----------------------------------------|------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| Fine-grained codes (many distinct 4xx) | Clients branch on the status line alone                    | Exhausts the code space; intermediaries can forge the same codes; RFC 9205 advises against it |
| Coarse codes plus a typed body         | Unlimited error vocabulary; survives proxy-generated codes | Clients must parse the body; useless to generic intermediaries                                |
| 501 for a capability gap               | Honest, non-retryable, does not trip health checks         | Heuristically cacheable per §15.1 — check the method before reusing on GET                    |
| 503 for a capability gap               | Familiar to ops tooling                                    | Invites retries and health-tooling misreads for a condition that will not clear               |

#### Best Practices

- Always send `Allow` with 405 and `WWW-Authenticate` with 401 — both MUST-level.
- Always send `Retry-After` with 503, and with 429 whenever you know the window.
- Never put content in a 204 or a 304; both are terminated by the end of the header section.
- Send `Location` with 201; use 308/307 for any redirect that must preserve a method, reserving 301/302 for GET-shaped resources.
- Document the *whole* status set per operation. juniper-data declares no `responses={...}` anywhere, so none of its 404/400/501/401/429/413 responses appear in the generated OpenAPI — only the success code plus FastAPI's automatic 422. Every client generated from that schema is blind to the error surface.

#### Common Failure Modes

- **200 with an error body.** Defeats every generic retry, alerting, and monitoring layer; the request looks successful to everything except your own client code.
- **301 on a POST route.** Method rewritten to GET, body and `Content-Type` dropped per §15.4 step 5, request silently lost.
- **503 for permanent conditions.** Retry storms plus false alerts, exactly as juniper-data's comment anticipates.
- **500 for client errors.** Pages an on-call engineer for a malformed request.
- **Bare 401 with no challenge.** Clients that would have re-authenticated surface a hard failure instead.
- **Two `detail` shapes.** juniper-data's hand-raised errors use `detail: string`; FastAPI's automatic 422 uses `detail: [object]`. A client cannot write one error parser.

#### Error Handling

The status code is the coarse generic signal; the body carries detail. RFC 9205 §4.6 says applications "should convey finer-grained error information in the response's message content and/or header fields", adding that "[PROBLEM-DETAILS] provides one way to do so" — and its bibliography resolves that reference to **RFC 7807**, since RFC 9205 is a June 2022 BCP and could not cite a July 2023 document. Read it as pointing at Problem Details, now
[RFC 9457](https://www.rfc-editor.org/rfc/rfc9457.html), which obsoletes 7807: `application/problem+json`, with `type`, `title`, `status`, `detail`, and `instance` plus arbitrary extensions. juniper-data uses FastAPI's default `{"detail": ...}` and has zero occurrences of `problem+json`: defensible pre-1.0, but every consumer writes bespoke parsing. Whatever shape you choose, follow §15.5/§15.6's SHOULD that the representation explain
"whether it is a temporary or permanent condition" — the field clients most need and most rarely get.

#### Controversy: 400 vs 422 for semantic validation failures

**That a controversy exists.** When a request is syntactically valid JSON with the right `Content-Type` but semantically wrong — `"limit": -5`, a missing required field, an unknown enum value — practitioners split hard on 400 versus 422, and both sides cite the same two paragraphs.

**What the specs actually say.** RFC 9110 §15.5.1, in full: "The 400 (Bad Request) status code indicates that the server cannot or will not process the request due to something that is perceived to be a client error (e.g., malformed request syntax, invalid request message framing, or deceptive request routing)." The three examples are syntactic, but the governing phrase — "something that is
perceived to be a client error" — is unrestricted. RFC 9110 §15.5.21: "The 422 (Unprocessable Content) status code indicates that the server understands the content type of the request content (hence a 415 (Unsupported Media Type) status code is inappropriate), and the syntax of the request content is correct, but it was unable to process the contained instructions. For example, this status code
can be sent if an XML request content contains well-formed (i.e., syntactically correct), but semantically erroneous XML instructions."

**Background.** 422 originated in WebDAV — RFC 4918 §11.2 — describing XML request bodies that parsed but asked for something incoherent. For two decades it was formally a WebDAV extension code, which is why "422 isn't real HTTP" was a defensible objection. RFC 9110 Appendix B.3 ended that. Meanwhile frameworks picked sides — Rails and FastAPI return 422 for validation failures by default, Spring
and ASP.NET Core lean 400 — so most engineers' intuitions were set by their framework rather than either RFC.

**The 422 camp.** *Strengths:* 422's definition describes this situation almost word for word, it is now a core RFC 9110 code with general applicability, and it distinguishes "I could not parse your request" from "I parsed it and it asks for something impossible" — a distinction clients act on differently (fix your serialiser vs fix your data). Major frameworks already emit it, so a large body of
client code handles it. *Weaknesses:* 422's sentence is framed around request *content* instructions, so stretching it to a bad query parameter or header extends its plain reading; some older intermediaries do not recognise it, though the §4.6 n00 fallback means they should degrade to 400 anyway. *Risks:* teams draw a fine 400/422 line no client branches on, spending review time on a distinction
with no consumer. *Guardrails:* use 422 only when request content parsed successfully and its *instructions* were the problem, and document the rule once. Be aware that on FastAPI the body/non-body split is not free:
`RequestValidationError` covers query, path, header, and cookie parameters too, so "keep 400 for anything wrong outside the body" requires registering a handler that inspects each error's `loc[0]` and re-maps the non-body ones. Leave that handler unwritten and the split is a documented intention the framework silently overrides.

**The 400 camp.** *Strengths:* 400's definition is broad enough — "something that is perceived to be a client error" — and RFC 9205 §4.6 explicitly advises "making generous use of the general status codes (200, 400, and 500) when in doubt" while warning against one-to-one status/error mappings. Universal recognition, no intermediary surprises, and it forces the useful discipline of putting real
detail in the body. *Weaknesses:* collapses a distinction that occasionally matters, and puts the API at odds with frameworks that emit 422 by default — producing an API that returns *both*, which is worse than either. *Risks:* if the body's error detail is thin, clients cannot tell a malformed payload from a rejected value at all. *Guardrails:* if you standardise on 400, override your framework's
default so nothing leaks 422, and make the body carry a machine-readable discriminator.

**Recommendation** (labelled as such): pick one, apply it everywhere, and make the body carry the discrimination. If your stack already emits 422 — as FastAPI does — let it stand wherever it fires, which on FastAPI means *every* automatic validation failure: query, path, and header parameters as well as body fields. Hand-raise 400 only for
failures the framework never sees, such as a malformed pagination cursor or a rejected combination of individually-valid parameters. Fighting the framework produces exactly the mixed surface both camps want to
avoid. This primer follows that rule and states it once: II.7's over-cap `limit` and negative `offset` are 422, because that is what FastAPI already returns. juniper-data currently has the mixed surface without having chosen it: hand-raised parameter failures are 400 (`datasets.py:112`) while FastAPI's automatic body validation is 422, with two incompatible `detail` shapes between them. That inconsistency is a far larger practical problem than which code is "right".

---

### II.5 Representations, Content Negotiation, and Media Types

#### Overview

A representation is what actually crosses the wire: bytes plus metadata describing them. Content negotiation is how client and server agree which representation, out of several possible ones, this exchange uses. Most APIs negotiate nothing — they serve one format and ignore `Accept` — which is a legitimate choice that should be made knowingly, because the machinery costs real complexity in caches
and `Vary` handling.

#### Background

RFC 9110 §12 defines three patterns visible in the protocol: **proactive** (server selects from the client's stated preferences), **reactive** (server lists alternatives, client picks), and **request content** negotiation (server states, in a response, what it prefers in future requests — e.g. `Accept-Patch` from RFC 5789 §3.1).

§12.1 is blunt about proactive negotiation's costs: it is "impossible for the server to accurately determine what might be 'best' for any given user"; describing capabilities on every request "can be both very inefficient ... and a potential risk to the user's privacy"; "It complicates the implementation of an origin server"; and "It limits the reusability of responses for shared caching". A user
agent "cannot rely on proactive negotiation preferences being consistently honored." Reactive negotiation (§12.2) — 300 Multiple Choices, or a list of links — avoids those costs but needs a second round trip and has no standardised automatic-selection mechanism.

#### `Accept`, q-values, and how ranking actually works

`Accept` is a list of media ranges, each optionally weighted (§12.5.1):

```text
Accept = #( media-range [ weight ] )
media-range = ( "*/*" / ( type "/" "*" ) / ( type "/" subtype ) ) parameters
```

Quality values (§12.4.2) are "normalized to a real number in the range 0 through 1, where 0.001 is the least preferred and 1 is the most preferred; a value of 0 means 'not acceptable'. If no 'q' parameter is present, the default weight is 1." At most three digits after the decimal point.

The ranking rule people get wrong is **specificity before weight**: "Media ranges can be overridden by more specific media ranges or specific media types. If more than one media range applies to a given type, the most specific reference has precedence." For `Accept: text/*, text/plain, text/plain;format=flowed, */*` the spec's own precedence order is `text/plain;format=flowed`, then `text/plain`,
then `text/*`, then `*/*`. So in `Accept: text/*;q=0.3, text/plain;q=0.7, text/plain;format=flowed, text/plain;format=fixed;q=0.4, */*;q=0.5`, the weight assigned to `text/html` is **0.3** — not 0.5 — because `text/*` is more specific than `*/*` even though `*/*` carries the higher q. Sort by specificity first; read the q off the winning range.

Two more facts worth having exactly right. **Absence means no preference** (§12.4.1): a missing `Accept` implies no preference on that dimension, not `*/*` at some particular weight. And **a no-match is not automatically a 406**: §12.4.1 says the server "can either honor the header field by sending a 406 (Not Acceptable) response or disregard the header field by treating the response as if it is
not subject to content negotiation for that request header field."

**`Accept` versus `Content-Type` is the most common confusion here, and it is not subtle once stated.** `Content-Type` (§8.3) describes *the message you are currently reading* — the request body on a request, the response body on a response. `Accept` (§12.5.1) describes *what the sender would like back*. A request carries both, describing different messages. The failure it produces: a client sends
`Content-Type: application/json` on a bodyless GET expecting that to select a JSON response, the server correctly ignores it, returns XML, and the client blames negotiation.

| Field                       | Selects          | Notes                                                                                                                                                                           |
|-----------------------------|------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `Accept` (§12.5.1)          | Media type       | Specificity beats weight                                                                                                                                                        |
| `Accept-Language` (§12.5.4) | Natural language | Language tags per §8.5.1                                                                                                                                                        |
| `Accept-Encoding` (§12.5.3) | Content coding   | `identity` is "a synonym for 'no encoding'"; an uncoded representation is acceptable by default unless excluded by `identity;q=0` or `*;q=0`                                    |
| `Accept-Charset` (§12.5.2)  | Charset          | Effectively obsolete for new APIs; UTF-8 everywhere                                                                                                                             |
| `Vary` (§12.5.5)            | — (response)     | "describes what parts of a request message, aside from the method and target URI, might have influenced the origin server's process for selecting the content of this response" |

**If you negotiate, you must send `Vary`.** Without it a shared cache stores one representation and serves it to clients that asked for something else. `Vary: accept-encoding, accept-language` is the common minimum; a proxy `MUST NOT` generate `Vary: *`.

#### Media type design

`media-type = type "/" subtype parameters` (§8.3.1); type and subtype tokens are case-insensitive; parameters are semicolon-delimited name/value pairs whose case-sensitivity depends on the parameter. Media types "ought to be registered with IANA according to the procedures defined in [BCP13]".

| Choice            | Example                                | When                                                                  |
|-------------------|----------------------------------------|-----------------------------------------------------------------------|
| Generic           | `application/json`                     | Default. Every client, tool, and proxy handles it                     |
| Structured suffix | `application/problem+json`             | You need a distinct type but want generic JSON tooling to still apply |
| Vendor tree       | `application/vnd.example.dataset+json` | You want the media type to carry versioning or schema identity        |

The `+json` **structured syntax suffix** signals that a format is built on JSON, so a recipient can apply generic JSON processing when it does not need the specific semantics. The suffix is registered by RFC 6839, *Additional Media Type Structured Syntax Suffixes* (January 2013, updating RFC 3023), whose §3.1 is titled "The +json Structured Syntax Suffix". Note its category: RFC 6839 is **Informational**, not Standards Track — it registers suffixes, it does not standardise a media type.
Registration procedures for media types generally are BCP 13, which RFC 9110 §8.3.1 cites.

The `vnd.` tree is where "media type versioning" lives — `application/vnd.example.dataset.v2+json`. It works and keeps the version out of the URL, at the cost that every client must set `Accept` correctly, every cache must `Vary` on it, and browsers and curl one-liners get the wrong thing by default. One warning on **parameters**: they are part of the type for matching purposes in `Accept` ranges
(the `text/plain;format=flowed` example above), and the registry disallows a parameter named `q` precisely because it would collide with the weight parameter.

#### Charset, and why `application/json` has no charset parameter

Settled, and frequently gotten wrong. [RFC 8259](https://www.rfc-editor.org/rfc/rfc8259.html) §11 registers `application/json` with `Optional parameters: n/a` and closes the registration with an explicit note:

> Note: No "charset" parameter is defined for this registration. Adding one really has no effect on compliant recipients.

The reason is §8.1: "JSON text exchanged between systems that are not part of a closed ecosystem MUST be encoded using UTF-8." The encoding is fixed by the format, so a charset parameter has nothing to select. RFC 8259 also requires that implementations "MUST NOT add a byte order mark (U+FEFF) to the beginning of a networked-transmitted JSON text", while permitting parsers to ignore one.

So `Content-Type: application/json; charset=utf-8` is harmless but meaningless, and `charset=iso-8859-1` is meaningless *and* wrong. Send `Content-Type: application/json`. This does **not** generalise: `text/html` and `text/plain` do have meaningful charset parameters, and RFC 9110 §8.3.1's own example is `text/html;charset=utf-8`.

#### Compression, binary payloads, and range requests

Compression is a *content coding* (`Content-Encoding`, §8.4) applied "beyond those inherent in the media type", negotiated with `Accept-Encoding`. A server failing a request because of an unsupported content coding "ought to respond with a 415 (Unsupported Media Type) status and include an `Accept-Encoding` header field in that response" — and, to avoid ambiguity, a server returning 415 for
reasons *unrelated* to content codings "MUST NOT include the `Accept-Encoding` header field" (§12.5.3). `Content-Encoding` is not `Transfer-Encoding`: the former is a property of the representation and survives end-to-end, the latter is hop-by-hop framing. For JSON, gzip typically wins 70-90% on the wire for a few milliseconds of CPU; for already-compressed binary — NPZ, images, video — it wins
nothing and costs CPU on both ends.

Base64-inlining a binary blob in JSON costs roughly 33% size inflation, forces the payload through a JSON parser, and defeats range requests, resumable downloads, and byte-accurate caching. Use a separate resource with its own URI when the blob is large, independently cacheable, or optional to the caller — exactly juniper-data's shape: metadata at `/v1/datasets/{id}`, bytes at
`/v1/datasets/{id}/artifact`. Inline only when the blob is small, always needed with its metadata, and an extra round trip dominates. **`Content-Disposition`** controls inline rendering versus download and carries the suggested filename; it is defined for HTTP by RFC 6266, *Use of the Content-Disposition Header Field in the Hypertext Transfer Protocol (HTTP)* (Standards Track, June 2011, updating RFC 2616).

RFC 9110 §14 defines range requests, "an OPTIONAL feature of HTTP, designed so that recipients not implementing this feature (or not supporting it for the target resource) can respond as if it is a normal GET request without impacting interoperability." The pieces: `Range` on the request (§14.2), `Accept-Ranges` to advertise support (§14.3), `Content-Range` to describe what was sent (§14.4), and
**206 Partial Content** as the status (§15.3.7). Two precise facts: "For this specification, GET is the only method for which range handling is defined" (§14.2), and a server supporting no ranges for a resource "MAY send `Accept-Ranges: none`" (§14.3) — while a client "MUST NOT assume that receiving an `Accept-Ranges` field means that future range requests will return partial responses." Range
support is worth implementing for exactly juniper-data's case: large immutable content-addressed artifacts, where a download that died at 80% would otherwise start over.

#### Ground truth: two byte-delivery paths that look alike and are not

juniper-data has two endpoints returning a `StreamingResponse`. Only one of them streams.

**The artifact download is chunked delivery, not streaming production** (`juniper_data/api/routes/datasets.py:693-704`):

```python
artifact_bytes = await asyncio.to_thread(store.get_artifact_bytes, dataset_id)
if artifact_bytes is None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Dataset '{dataset_id}' not found")
return StreamingResponse(
    io.BytesIO(artifact_bytes),
    media_type="application/octet-stream",
    headers={"Content-Disposition": f"attachment; filename={dataset_id}.npz"},
)
```

The entire artifact is materialised into `artifact_bytes` before the response object exists. Wrapping it in `BytesIO` means the ASGI layer sends it in chunks, which bounds the *socket buffer*, not process memory. Peak memory is the full artifact, per concurrent request — fine for artifacts of known modest size, but calling it "streaming" invites the assumption that it is safe for arbitrarily large
ones, and it is not.

Two smaller notes on the same four lines. `application/octet-stream` is the maximally generic type; RFC 9110 §8.3 names it as the *fallback* a recipient may assume when no `Content-Type` is present. NPZ is a ZIP container, so `application/zip` would have been strictly more informative — and juniper-data already uses exactly that on its other binary endpoint (`datasets.py:584`), making the
inconsistency internal rather than theoretical. And with the SHA-256 checksum already computed and stored on `DatasetMeta.checksum`, this response could carry an `ETag` for free and support conditional GETs on an immutable blob; it carries no validator at all.

**The batch export genuinely is incremental** (`datasets.py:562-586`), and the constraint that makes it work is worth studying:

```python
# ZIP_STORED is required for streaming-friendly archives: with ZIP_DEFLATED
# the zipfile module would need to seek back to patch the local-file-header
# with the final size, which is not possible once chunks have been yielded.
with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_STORED, allowZip64=True) as zf:
    for dataset_id in present_ids:
        ...  # fetch the bytes; skip quietly on a concurrent-delete race
        zf.writestr(f"{dataset_id}.npz", artifact_bytes)
```

The mechanism: a ZIP local file header precedes each entry's data and contains that entry's compressed size. With `ZIP_DEFLATED` the compressed size is unknown until compression finishes, so `zipfile` writes a placeholder and seeks backwards to patch it. Once a chunk has been yielded to the ASGI transport it is gone — there is nothing to seek back into. With `ZIP_STORED` the stored size equals the
input size and is known before the header is written, so no back-patching is needed and each entry can be emitted and released. The generator drains a `_ChunkBuffer` after each entry (`:573-576`), keeping peak memory at one NPZ rather than the whole export.

That is a genuine, load-bearing tradeoff — no compression in exchange for bounded memory — and the comment at `:564-566` records it, which is why a future contributor "optimising" the export to `ZIP_DEFLATED` will hopefully stop first. It is also the counterexample to the artifact endpoint: same response class, entirely different memory profile, and only the code tells you which is which.

#### Judgement Calls

- **Negotiate at all?** Only if you genuinely serve more than one representation. One format plus a documented `Content-Type` is simpler and honest — and if you do negotiate, `Vary` is not optional.
- **Vendor media type or plain `application/json`?** Vendor types when the media type carries versioning or schema identity and clients are all first-party; plain JSON when curl-ability and generic tooling matter more.
- **Inline or separate URL for binary?** Separate once the blob exceeds a few hundred kilobytes, is independently cacheable, or is optional.
- **Compress?** Yes for JSON, no for already-compressed binary. Let `Accept-Encoding` decide rather than hardcoding.
- **Range support?** Worth it for large immutable artifacts; skip it for small JSON.

#### Tradeoffs

| Choice                     | Gains                                                        | Costs                                                                                                                 |
|----------------------------|--------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------|
| Proactive negotiation      | One URI per resource; preferred form on the first round trip | Complicates the origin server; "limits the reusability of responses for shared caching" (§12.1); needs correct `Vary` |
| Reactive negotiation       | Cache-friendly; no per-request preference parsing            | Extra round trip; no standardised automatic selection (§12.2)                                                         |
| One format, no negotiation | Simplest possible; nothing to get wrong                      | Adding a second format later becomes a breaking change or a new URI                                                   |
| `ZIP_STORED` streaming     | Bounded memory regardless of export size                     | No compression — larger transfer                                                                                      |
| `ZIP_DEFLATED` buffered    | Smaller transfer                                             | Whole archive in memory; OOM risk scales with request size                                                            |
| Inline base64 binary       | One round trip; atomic with metadata                         | +33% size, no ranges, no independent caching, parser pressure                                                         |

#### Best Practices

- Send `Content-Type` on every response with a body; §8.3 warns that its absence invites MIME sniffing, which "risks drawing incorrect conclusions about the data".
- Send `Vary` whenever the response depended on a request header.
- Use the most specific accurate media type — `application/zip` beats `application/octet-stream` for a ZIP container — and omit `charset` on `application/json` while keeping it on `text/*`.
- Emit `ETag` on immutable binary resources when you already hold a digest.
- Document whether a "streaming" endpoint streams *production* or merely *delivery*; they have different memory profiles and only one of them scales.
- Advertise `Accept-Ranges: bytes` if you support ranges, and `Accept-Ranges: none` if you deliberately do not.

#### Common Failure Modes

- **Negotiating without `Vary`.** A shared cache serves the German response to the next English client.
- **Confusing `Accept` with `Content-Type`.** Setting the wrong one and concluding negotiation is broken.
- **Ranking q-values before specificity.** A "correct" negotiator that picks the wrong representation for `Accept: text/*;q=0.3, */*;q=0.5`.
- **`charset=utf-8` on JSON.** Harmless, but a reliable tell the sender has not read RFC 8259 §11 — and the same reflex often produces `charset=iso-8859-1`, which is wrong.
- **`application/octet-stream` as a default.** Discards type information the server already had.
- **`ZIP_DEFLATED` on a streamed archive.** Either a seek error or silent full-buffering, depending on the sink.
- **Calling buffered delivery "streaming".** The name promises a memory profile the code does not provide.

#### Error Handling

| Condition                                                 | Code                           | Source            |
|-----------------------------------------------------------|--------------------------------|-------------------|
| No acceptable representation, and no default will be sent | 406                            | RFC 9110 §15.5.7  |
| Request content type unsupported by the resource          | 415                            | RFC 9110 §15.5.16 |
| Request content coding unsupported                        | 415 **with** `Accept-Encoding` | RFC 9110 §12.5.3  |
| Range unsatisfiable                                       | 416                            | RFC 9110 §15.5.17 |
| Successful range response                                 | 206 with `Content-Range`       | RFC 9110 §15.3.7  |

Two subtleties. 406 is optional — §12.4.1 lets the server disregard the negotiation header and send a default, and for machine APIs sending the one format you have is usually kinder than a 406 nobody can act on. And the `Accept-Encoding`-on-415 rule is bidirectional: including it when the 415 was about the *media type* actively misleads the client about what went wrong.

An error mid-stream is the hard case with no good answer: once the status line and headers are out, a failure during body generation cannot change the status. juniper-data's batch export handles the one case it can — pre-checking existence before committing to a response body and returning 404 if *none* of the requested datasets exist (`datasets.py:530-533`) — but a dataset deleted mid-export is
skipped silently (`:570-572`). The archive arrives with fewer entries than requested, under a 200, and the caller has no way to know. A trailer, a manifest entry, or a sentinel file inside the archive would close that gap; nothing at the HTTP level can.

### II.6 Conditional Requests, ETags, and Optimistic Concurrency

#### Overview

A conditional request carries headers stating a precondition the server tests before applying the method.
[RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html) §13 defines five — `If-Match`, `If-None-Match`,
`If-Modified-Since`, `If-Unmodified-Since`, `If-Range` — under one mandatory evaluation order, and names two payoffs:
on safe methods, bandwidth avoidance; on state-changing methods, prevention of "the 'lost update' problem: one client
accidentally overwriting the work of another client that has been acting in parallel." The second is the one most
designers skip, and the one that silently corrupts data.

#### Background

Conditional requests were built for caches, which is why guidance treats `ETag` as a CDN feature. That is wrong on the
concurrency half: §13.1.1 notes "a cache or intermediary MAY ignore If-Match because its interoperability features are
only necessary for an origin server." The material was split into RFC 7232 in 2014 and folded back into RFC 9110 in
2022 (Appendix B.4), so older references carry dead section numbers. Cite §13 for preconditions, §8.8 for validators.

#### Validators: strong, weak, and what `W/` means

Per §8.8.1 a strong validator "changes value whenever a change occurs to the representation data that would be
observable in the content of a 200 (OK) response to GET"; a weak one "might not change for every change to the
representation data". The decisive test, same section: a validator is weak if shared by two or more representations of
a resource at the same time, *unless* those representations have identical representation data. `W/` is a declaration,
not a hint — §8.8.3 makes an entity tag strong by default and requires the origin to **MUST** prefix `W/`
(case-sensitive, `weak = %s"W/"`) when generation falls short. Mislabelling has teeth, because the comparison function
differs by field:

| Field             | Comparison function | Source           |
|-------------------|---------------------|------------------|
| `If-Match`        | strong (MUST)       | RFC 9110 §13.1.1 |
| `If-None-Match`   | weak (MUST)         | RFC 9110 §13.1.2 |
| `If-Range` (etag) | strong (exact)      | RFC 9110 §13.1.5 |

§8.8.3.2: strong comparison matches only when both tags are non-weak and the opaque parts match
character-by-character; weak comparison matches on the opaque parts regardless. So `W/"1"` and `"1"` are a weak match
and a strong non-match, and a server emitting a bare `"abc"` for something genuinely weak will accept
`If-Match: "abc"` and write against a representation it never verified.

#### `Last-Modified` and the one-second problem

`HTTP-date` has one-second resolution, so §8.8.2.2 says a `Last-Modified` used as a validator "is implicitly weak
unless it is possible to deduce that it is strong" — practically, that the origin "reliably knows that the associated
representation did not change twice during the second covered by the presented validator." §8.8.1 states the failure:
the timestamp is weak whenever the representation can change twice in a second and be read between the writes, which
is every machine-written resource. Use it for revalidation and coarse "changed since" traversal, never for optimistic
concurrency; `If-Unmodified-Since` (§13.1.4) is explicitly a stand-in for `If-Match` when the caller has no entity tag
— a fallback, not a peer.

#### The evaluation order, precisely

RFC 9110 §13.2.2: "A recipient cache or origin server MUST evaluate the request preconditions defined by this
specification in the following order":

1. Origin server, `If-Match` present → true: go to 3; false: **412**, unless it can be determined the state-changing
   request already succeeded (§13.1.1).
2. Origin server, `If-Match` absent and `If-Unmodified-Since` present → true: go to 3; false: **412**, same escape
   (§13.1.4).
3. `If-None-Match` present → true: go to 5; false and GET/HEAD: **304**; false and any other method: **412**.
4. GET/HEAD, `If-None-Match` absent, `If-Modified-Since` present → true: go to 5; false: **304**.
5. GET with both `Range` and `If-Range` → true and range applies: **206**; otherwise ignore `Range`, respond **200**.
6. Otherwise, perform the method.

Three consequences people get wrong. Entity tags beat dates *normatively* — §13.1.3 and §13.1.4 say a recipient **MUST
ignore** the date field when the corresponding entity-tag field is present. The failure code depends on the method,
not the header: a false `If-None-Match` is 304 for GET/HEAD and 412 otherwise, so `If-None-Match: *` on a PUT (the
create-if-absent guard) fails with 412. And §13.2.1 requires evaluation just before performing the action, with the
server **MUST ignoring all preconditions** if the unconditioned response would have been anything other than 2xx or
412 — so 401s and 404s win, and a resource you cannot see never answers 412 and confirms its existence.

#### 304 Not Modified: what it must carry

§15.4.5: the server **MUST** generate any of `Content-Location`, `Date`, `ETag`, `Vary`, `Cache-Control` and `Expires`
that would have appeared in a 200 to the same request, and **SHOULD NOT** generate other representation metadata
unless it guides cache updates (`Last-Modified` is called out as useful when there is no `ETag`). "A 304 response is
terminated by the end of the header section; it cannot contain content or trailers." The commonest bug is omitting
`ETag`, which leaves the client unable to freshen its stored validator; the second is omitting `Vary` on a negotiated
resource, letting a shared cache freshen the wrong variant.

#### The lost-update problem, concretely

juniper-data's tag update (`juniper_data/api/routes/datasets.py:766-795`) is a read-modify-write across two thread
offloads: `store.get_meta` at `:785`, set arithmetic at `:789-792`, `store.update_meta` at `:794`.
`LocalFSDatasetStore.update_meta` (`juniper_data/storage/local_fs.py:262-298`) serialises the whole `DatasetMeta` and
atomically replaces the file — last writer wins, whole document, no version check. No lock spans the pair.

```text
Dataset D, tags = ["train"].
C1: PATCH .../tags {"add_tags": ["gold"]}     reads ["train"] -> writes ["gold","train"]
C2: PATCH .../tags {"add_tags": ["archive"]}  reads ["train"] -> writes ["archive","train"]
Final: ["archive","train"]. Both returned 200. "gold" is gone -- no error, no metric, no way
for C1 to detect it short of re-reading.
```

One header and one status fix it:

```text
C1: GET   D                 -> 200, ETag: "v7"
C2: GET   D                 -> 200, ETag: "v7"
C1: PATCH D If-Match: "v7"  -> strong compare true  -> 200, ETag: "v8"
C2: PATCH D If-Match: "v7"  -> strong compare false -> 412, nothing written
C2: GET   D                 -> 200, ETag: "v8"; recompute intent, retry with If-Match: "v8"
```

C2 now owns the merge, which is correct: only C2 knows whether "archive" still makes sense given that "gold" arrived.
§13.1.1 permits 2xx instead of 412 when the change "appears to have already been applied", but warns that for
resources used as semaphores "an origin server is better off being stringent in sending 412 for every failed
precondition **on an unsafe method**" — the scope qualifier matters. Default to stringent. The same hazard hides on a path nobody suspects: `record_access` (`juniper_data/storage/base.py:198-223`)
is a read-modify-write of the *same* document — bump `last_accessed_at` and `access_count`, write it all back — fired
on every metadata read and artifact download (`routes/datasets.py:672`, `:698`). It holds `_version_lock`;
`update_dataset_tags` never takes that lock, so reading a dataset can undo an edit to it.

#### 428 Precondition Required

[RFC 6585](https://www.rfc-editor.org/rfc/rfc6585.html) §3: "The 428 status code indicates that the origin server
requires the request to be conditional", with the lost-update case named as its typical use; responses **SHOULD**
explain how to resubmit (its own example body says `try using "If-Match"`) and **MUST NOT** be cached. Why require
rather than support: an optional precondition is one nobody sends. Clients are written against the happy path and
tested without contention, so if the server accepts an unconditional `PATCH` every client will send one, and the
concurrency control is dead code that passes its tests. Requiring it converts silent data loss into a loud
first-request 428 at integration time. §7.1 is honest about the limit: "The 428 status code is optional; clients
cannot rely upon its use to prevent 'lost update' conflicts."

#### ETag generation, and the fix already sitting in juniper-data

| Strategy                | Strong?      | Cost per response            | Fails when                                  |
|-------------------------|--------------|------------------------------|---------------------------------------------|
| Content hash            | yes          | O(body); free if precomputed | Body built per-request, or very large       |
| Version counter / rowid | yes          | O(1) read                    | Needs every writer to bump it               |
| `mtime` + size          | weak         | O(1) stat                    | Sub-second writes; restore resets mtime     |
| Hash of serialized JSON | usually weak | O(body) every response       | Field order, floats, embedded read counters |

The cost objection is answered in §8.8.1: a collision-resistant hash suffices as a strong validator "if the data is
available prior to the response header fields being sent **and the digest does not need to be recalculated every time
a validation request is received**." Hashing per response makes the 304 — the cheap case — cost a full-body hash.
Precompute at write time and store it.

juniper-data already does the hard half. `compute_checksum` (`juniper_data/core/artifacts.py:50-63`) is a SHA-256
digest over the NPZ serialisation, and `arrays_to_bytes` (`:33-47`) sorts the array keys first (`:44`, "Ensure a
stable serialization order") so it is stable across processes. The create path calls it once
(`routes/datasets.py:192`) and stores it on `DatasetMeta.checksum` (`:230`; field at `core/models.py:71`), on an
artifact that is immutable and content-addressed — `generate_dataset_id` (`core/dataset_id.py:23-61`) hashes canonical
JSON into `{generator}-{version}-{digest[:16]}`. That is the textbook strong-validator case, and §8.8.3.1 says an
origin **SHOULD** send an `ETag` wherever change detection is reasonably determinable.

It sends nothing. `download_artifact` (`routes/datasets.py:676-704`) returns a `StreamingResponse` with exactly two
headers (`:700-704`), and a grep across `juniper_data/` finds zero occurrences of `ETag`, `Last-Modified`,
`Cache-Control`, `If-None-Match`, `If-Match`, `Vary`, or 304 — the only `max-age` is the HSTS value at
`api/constants.py:69`. Every repeat download of a multi-megabyte immutable blob re-transfers it. The wiring is a few
lines: emit `ETag: "<checksum>.npz"` plus `Cache-Control: private, max-age=31536000, immutable`, and return a bodiless
304 when a weak comparison of `If-None-Match` matches. `private`, not `public`: the route sits behind `X-API-Key`
(`api/constants.py:33-41` exempts only health, docs, and `/metrics`), and because that credential is a custom header
rather than `Authorization` no shared cache can tell the request was authenticated — so `public` would license every
intermediary to serve one caller's artifact to the next for a year. (The `immutable` directive is from RFC 8246, **not** in the
local spec cache; §13.2.1 references it as instructing caches "to forgo forwarding conditional requests when they hold
a fresh response", but treat its own semantics as unverified.)

A trap sits on the neighbouring endpoint. `GET /v1/datasets/{id}` returns a `DatasetMeta` including `last_accessed_at`
and `access_count` (`core/models.py:84-85`), and the handler schedules `record_access` on every call — so a strong
ETag hashed over *that* body would change on every GET and never hit, while the artifact endpoint's would work
perfectly. The validator must cover the representation, and here read access is part of it. Either exclude read
counters and mark the tag weak, or split them into a sub-resource.

#### Compression and validator identity

§8.8.1 is flat: "if the origin server sends the same validator for a representation with a gzip content coding applied
as it does for a representation with no content coding, then that validator is weak." §8.8.3.3 works the example —
`ETag: "123-a"` uncompressed, `"123-b"` with `Content-Encoding: gzip`, both `Vary: Accept-Encoding` — and its note
explains why: content codings are a property of the representation *data*, so a strong tag for a content-encoded
representation has to be distinct, whereas transfer codings apply only during message transfer and yield no distinct
tag. A proxy or CDN that gzips origin responses while passing the `ETag` through unchanged has therefore made a strong
tag a lie, with range corruption and cache poisoning across `Accept-Encoding` to follow; the compressing hop must
rewrite the tag or leave the body alone. The converse also holds — two representations *may* share a strong tag when
they differ only in metadata such as media type.

#### The precondition is only half the mechanism

A 412-or-write endpoint is a compare-and-swap only if the comparison and the write are **one atomic operation**. The
protocol supplies the comparison; the storage layer has to supply the atomicity — a conditional `UPDATE ... WHERE
version = ?` that reports rows affected, a native compare-and-swap, or a transaction that holds the row from read to
commit. Evaluate `If-Match` against a value read a moment ago and then write in a separate step, and you have not
closed the lost-update window: you have narrowed it, and made it far harder to reproduce.

juniper-data is the worked negative, and it is the same endpoint used throughout this section.
`update_dataset_tags` (`routes/datasets.py:785-794`) is `get_meta` → mutate the tag set in Python → `update_meta`,
across two separate `asyncio.to_thread` hops with nothing held between them. `record_access`
(`storage/base.py:217-222`) then performs its own read-modify-write of the same `DatasetMeta` on every GET, under a
per-process `_version_lock` the tag path never takes. Adding an `If-Match` check to the top of that handler would buy a
correct 412 and change nothing about the race — a writer landing between the two hops still wins silently, and a
second process is not serialised at all. The storage layer is what would have to change first.

#### Judgement Calls

- Immutable content-addressed resource: `ETag` is nearly free. Hot per-request aggregate: it costs a hash on every
  response and saves nothing.
- Prefer an honest `W/` to a dishonest strong tag; a weak tag still enables 304.
- 412 or 2xx on an apparently-repeated write: choose 2xx only when you can *prove* it succeeded.
- If you content-negotiate, the tag is per-representation and you owe a correct `Vary`.

#### Tradeoffs

| Choice                   | Buys                                                        | Costs                                     |
|--------------------------|-------------------------------------------------------------|-------------------------------------------|
| Precomputed content hash | Strong validator, cheap 304s                                | A write-path field; backfill for old rows |
| Hash on every response   | No schema change                                            | CPU on the path meant to be cheapest      |
| Version counter          | O(1), obviously strong                                      | Every writer must bump it, migrations too |
| `Last-Modified` only     | Zero storage                                                | Weak; unusable for `If-Match`             |
| Requiring `If-Match`     | Lost updates impossible *if the check and write are atomic* | Breaking change; needs a CAS in storage   |

#### Best Practices

- Emit `ETag` on every cheaply-detectable representation, including on **201 Created** (§8.8).
- Compute the validator at write time and store it; never hash on the read path if avoidable.
- Implement §13.2.2 literally; the ignore rules in §13.1.3/§13.1.4 are normative.
- On 304, echo `ETag`, `Date`, `Vary`, `Cache-Control`, and send no body (§15.4.5).
- Use `If-None-Match: *` for create-if-absent instead of a check-then-PUT race.
- Document what changes the validator, and whether it survives a redeploy.

#### Common Failure Modes

- **Silent lost updates** — the default state of any read-modify-write API without preconditions.
- **A strong tag over a mutating representation** — read counters make hit rate zero, silently.
- **Compression rewriting the body but not the tag** — two representations, one tag.
- **304 without `ETag`** — the client can never freshen its entry.
- **A tag from unsorted JSON or dict order** — stable in one process, unstable across replicas; juniper-data avoided
  this deliberately (`core/artifacts.py:44`).
- **Preconditions evaluated before auth** — leaks existence; forbidden by §13.2.1.

#### Error Handling

- **412** (§15.5.13) — a condition evaluated false. Include the *current* `ETag` so the retry costs one round trip,
  not two.
- **428** (RFC 6585 §3) — unconditional request, conditionality required. Name the header.
- **304** is success, but SDKs routinely treat any non-2xx as failure. Say so in the docs.
- **409** (§15.5.10) is different: a conflict you detected, versus 412 for a precondition you were asked to test.

#### Controversy: should an API that supports `If-Match` also *require* it?

**The controversy.** Accept unconditional mutations with last-writer-wins semantics, or reject them with 428? RFC 6585
defines the status and takes no position; real APIs split. **The camps:** *mandatory-precondition* (unsafe methods on
mutable resources must carry `If-Match`) versus *optional-precondition* (honour it when present, accept the request
when absent).

**Background.** The split tracks who the caller is. Conditional requests were designed for browsers and authoring
tools, where a human merge prompt is natural; machine clients often have no merge story — a 412 is an unhandled
exception — and retrofitting breaks every deployed client at once.

**Mandatory — strengths.** Lost updates become structurally impossible *where the storage layer makes the check and the
write atomic*; the failure is loud and at integration time; each client author confronts concurrency once, while they
can still change their design. A replayed `PATCH` carrying a spent tag is rejected, so retries cannot double-apply.

**Mandatory — weaknesses.** A breaking change on existing endpoints, an extra round trip for callers not already
holding a validator, and awkwardness for commutative operations where serialising writers buys nothing. Every write
path must maintain the validator, migrations included.

**Mandatory — risks.** Under contention a naive retry loop turns a lost update into a retry storm — data correct,
service down. Clients that "handle" 412 by re-fetching and blindly re-applying have reintroduced the lost update with
a clean conscience.

**Mandatory — guardrails.** Ship on new endpoints, not by retrofit; return the current `ETag` on the 412; cap retries
with jitter; offer a genuinely commutative operation (set-add, numeric delta) where one fits; and test the 412 branch
in CI, because it never runs in development.

**Optional — strengths.** Backwards compatible; callers who care opt in per request; cheap for read-mostly resources
where contention is rare, with the simple case at one round trip.

**Optional — weaknesses.** Nobody opts in. The mechanism exists, passes its tests, and protects nothing, because the
unconditional call works. Corruption surfaces later, in production data, with no record of which write won.

**Optional — risks.** The design-review illusion: "we support `If-Match`" reads as "we have concurrency control", and
those are not the same sentence.

**Optional — guardrails.** Make unconditional writes *observable* — count them, log them at WARN with the caller
identity, publish the number. "83% of writes here are unconditional" is the argument that funds the mandatory version.

**Recommendation** (labelled as such): for new mutating endpoints on shared resources, require the precondition and
return 428 — one documented round trip, paid once per client author, against a failure that is silent and permanent.
Do not retrofit; instrument first, honour `If-Match` when sent, and let the measured unconditional-write rate justify
a versioned migration. For genuinely commutative operations, redesign the operation rather than serialising it.

---

### II.7 Pagination, Filtering, Sorting, and Partial Responses

#### Overview

Four levers on a collection: pagination (which window), filtering (which rows), sorting (what order), partial
responses (which fields). They interact — a pagination scheme is only correct with respect to a total order, so
sorting is a precondition, not a peer. The two decisions with real consequences are the window mechanism and whether
the response is enveloped.

#### Background

Offset/limit came from SQL and maps to a URL trivially, which is why everyone writes it first; its defects appear only
at scale or under concurrent writes, i.e. after shipping. Keyset ("seek") pagination is the database community's
answer, and cursor pagination is keyset with the boundary hidden behind an opaque token. Large APIs moved that way
largely because the alternative quietly loses and repeats rows.

#### Offset/limit and its two real defects

**Deep-offset cost.** `OFFSET m` is not a seek; it is "produce m+n rows and discard m".
`LocalFSDatasetStore.list_datasets` (`juniper_data/storage/local_fs.py:241-255`) is the pure form:

```python
from pathlib import Path

class Store:
    """Excerpt of LocalFSDatasetStore; constant defaults inlined (100 / 0)."""

    _base_path: Path

    def list_datasets(self, limit: int = 100, offset: int = 0) -> list[str]:
        meta_files = sorted(self._base_path.glob("*.meta.json"))
        dataset_ids = [f.stem.replace(".meta", "") for f in meta_files]
        return dataset_ids[offset : offset + limit]
```

Every request globs the directory, sorts it, and discards all but `limit` entries — O(N log N) per page whether the
offset is 0 or 10 000. `/filter` is worse in kind: `filter_datasets` (`juniper_data/storage/base.py:314-378`)
materialises every dataset's metadata, evaluates ten predicates per row in Python (`:351-374`), sorts the survivors
(`:376`), then slices (`:378`).

**Item drift.** This one corrupts results. The window is defined by *position*, and positions shift when the set
changes. Dataset IDs are `{generator}-{version}-{sha256[:16]}` (`core/dataset_id.py:61`), so a new ID's lexicographic
position is effectively random:

```text
Page 1: slice [0:100] of the sorted list -> rows A0..A99 returned.

A concurrent POST inserts a row sorting at index 40; everything from 40 shifts RIGHT by one,
so A99 is now at index 100.  Page 2 = slice [100:200] returns A99 again.  -> DUPLICATED.

Instead a concurrent DELETE removes index 40; everything shifts LEFT by one, so A100 is now
at index 99, inside page 1's consumed window.  Page 2 starts at A101.     -> A100 SKIPPED.
```

A skipped row in an export is a dataset that silently does not migrate; a duplicated row in a batch job is work done
twice. `/filter` makes it systematic rather than occasional: it sorts `created_at` descending (`base.py:376`), so
every new dataset lands at index 0 and shifts the whole list right, and deep pages re-serve rows continuously under
steady creation load.

One accidental mitigation is worth naming, because it is why this is hard to find. `filter_datasets` reads through
`_list_all_metadata_cached` (`base.py:47-77`), a stale-tolerant TTL cache with `_METADATA_CACHE_TTL_SECONDS = 5.0`
(`base.py:26`). Pages inside one 5-second window see a consistent snapshot; pages straddling a boundary do not. The
bug is intermittent, load-dependent, and invisible to a test that pages quickly — the profile of a defect that reaches
production.

#### Keyset, cursors, and page numbers

Keyset replaces "skip m rows" with "resume after this value":
`WHERE (sort_key, id) > (:last_key, :last_id) ORDER BY sort_key, id LIMIT n`. It fixes drift because the boundary is a
*value*, so inserting or deleting before it moves nothing; rows created after iteration begins may be missed, but none
is silently skipped or duplicated — the guarantee batch jobs actually need. With an index on `(sort_key, id)` every
page is a seek plus `n` rows, independent of depth. The price is expressiveness: no jump-to-page-17, backwards needs a
reversed query, and the sort key joins the contract. On `/filter` that means ordering by
`(created_at DESC, dataset_id DESC)` and accepting `?after_created_at=...&after_id=...` — note the tiebreaker,
mandatory and currently absent. **Page numbers** are offset with the arithmetic moved server-side, plus one defect:
the client cannot resume without knowing `per_page` did not change.

An **opaque cursor** is keyset with the boundary encoded into a blob. Inside belong the sort key values, the
tiebreaker id, the direction, and a fingerprint of the filter set it was issued for; not internal ids, tenant ids, or
row counts. Opacity is a contract, not an encoding — base64 is not opacity, and once one client decodes your cursor
its structure is public API. Sign it (HMAC over the payload) and reject unverifiable tokens: clients then cannot
hand-craft out-of-contract queries, you can rotate the format because old-key cursors are rejectable, and a cursor
issued for filter set A cannot be replayed against set B. Design expiry explicitly — a cursor whose boundary row was
deleted must still work, since the comparison is on the value, but one issued against a snapshot you no longer keep
must fail loudly with a distinct 400, never restart silently from page one.

#### Total counts

A total requires evaluating the filter over the entire population. juniper-data's `/filter` returns an exact `total`
(`base.py:377`, `core/models.py:151`) and pays by materialising and testing every dataset on every page request — the
count is the dominant cost, recomputed identically for page 1 and page 40. The compromises, in increasing order of
honesty: **omit it** (fetch `limit + 1`, report `has_more` — sufficient for load-more UIs and every batch consumer);
**approximate it** and *name* it `total_approx`; **cap it** and report `total_is_lower_bound`; or **make it opt-in**
(`?include_total=true`, default off). What not to do is ship a field called `total` that is sometimes exact, sometimes
stale, and documented as neither.

#### Sorting and stable ordering

Unstable sort plus pagination equals duplicates, and it looks like a sorting bug while being a pagination bug: if the
sort key has ties and the tie order is not deterministic, two adjacent-page requests can order the tied group
differently, so a row appears in the tail of page 1 under one ordering and the head of page 2 under another while its
neighbour appears in neither.

juniper-data's `/filter` sorts `created_at` alone (`base.py:376`) with no tiebreaker. Python's `list.sort` is stable,
so ties preserve *input* order — but the input comes from `LocalFSDatasetStore.list_all_metadata`
(`local_fs.py:300-312`), which iterates `self._base_path.glob("*.meta.json")` with **no sort**. Directory iteration
order is filesystem-dependent and shifts as files are created and removed, so the tie order is not stable across
requests. Meanwhile `list_datasets` (`local_fs.py:253`) *does* sort its glob, so the two endpoints disagree on
ordering determinism as well as shape. The rule: **the sort must be a total order.** `ORDER BY created_at DESC` is a
bug; `ORDER BY created_at DESC, id DESC` is a contract.

#### Filtering syntaxes, and sparse fieldsets

Filter designs sit on a spectrum: fixed typed parameters (`?generator=spiral&min_samples=1000`); structured field
operators (`?created_at[gte]=...`); or a query language (RSQL, OData `$filter`, a bespoke DSL). The risk in the third
is not primarily SQL injection — a competent implementation parameterises — but *resource* injection: an expressive
language lets an unauthenticated caller compose a predicate that is legal, correctly parameterised, and
computationally ruinous. A filter over an unindexed column forces a sequential scan; a leading-wildcard `LIKE` defeats
every index; nested `OR` defeats the planner. Mitigate with an allowlist of filterable fields, an allowlist of
operators per field, bounds on depth and term count, and a statement timeout — not with input sanitisation.
juniper-data sits firmly at the first: ten hand-written comparisons over typed fields (`base.py:351-374`), each a
validated `Query(...)`, so there is no expression language and no injection surface; the cost of that safety is the
O(N) scan.

**Sparse fieldsets** (`?fields=dataset_id,checksum`) pay when the representation is large relative to need.
`DatasetMeta` (`core/models.py:21-85`) has roughly two dozen always-returned fields, and the cheap alternative already
exists as a second representation (`GET /v1/datasets` returns bare strings). Projection parameters multiply the
response shapes your schema must describe and interact badly with caching, since each field set is a distinct
representation; prefer distinct representations — a summary resource and a full one — when the useful field sets are
few.

#### Judgement Calls

- Machine consumers, exports, anything over a few thousand rows: cursor. Human admin UI over a small, slow-changing
  set: offset is fine.
- Exact total, approximate, or none: "Showing 1–50 of 12,043" needs a number; a batch job needs `has_more`.
- The `limit` cap matters more than the default (juniper-data: 100 / 1000, `routes/datasets.py:259`, `:288`).
- If clients paginate, ordering is part of the contract whether you documented it or not.

#### Tradeoffs

| Scheme        | Deep-page cost    | Drift-safe | Random access | Client complexity |
|---------------|-------------------|------------|---------------|-------------------|
| Offset/limit  | grows with offset | no         | yes           | none              |
| Page number   | grows with page   | no         | yes           | none              |
| Keyset        | flat              | yes        | no            | low               |
| Opaque cursor | flat              | yes        | no            | low (token only)  |

#### Best Practices

- Make every paginated order total: sort key plus a unique tiebreaker, always.
- Return an envelope carrying the next-page token, and emit `Link` headers as well.
- Cap `limit` server-side and *reject* over-cap values — silent clamping makes a client's "give me 10 000" look like
  it worked.
- Keep expensive totals out of the default response; sign cursors and reject unrecognised ones.
- Document drift semantics: "rows created during iteration may or may not appear; no row is returned twice" is a
  contract. Silence is not.

#### Common Failure Modes

- **Skipped rows in an export** — offset plus concurrent deletes; discovered downstream, months later, unreproducible.
- **Duplicated rows in a batch job** — offset plus concurrent inserts, worst with newest-first order.
- **Ties without a tiebreaker** — intermittent duplicates that vanish under a debugger.
- **Two list endpoints that disagree.** `GET /v1/datasets` returns a bare `list[str]` (`routes/datasets.py:257-273`)
  while `GET /v1/datasets/filter` returns `DatasetListResponse{datasets,total,limit,offset}` (`:276-335`, model
  `core/models.py:147-153`) — same window parameters, incompatible shapes, no shared ordering guarantee.
- **A filter model that exists but is not wired.** `DatasetListFilter` (`core/models.py:132-144`) declares the ten
  criteria as a validated Pydantic model; the route ignores it and re-declares twelve loose `Query(...)` parameters
  inline (`routes/datasets.py:278-289`). A grep finds exactly two references to the class name in the package — its
  own definition and a comment in `core/constants.py:39` — so the duplicated constraints can drift silently, and the
  model is the one place a reviewer would check them.

#### Error Handling

- Over-cap `limit`, negative `offset`, unknown sort field: **422** on a FastAPI-shaped stack, naming the parameter and
  range. These are automatic query-parameter validation failures, so the framework answers before your handler runs —
  II.8's captured body shows exactly that, `loc: ["query", "limit"]`. Emitting 400 instead means registering a
  `RequestValidationError` handler and re-mapping by `loc[0]`; II.4's recommendation is to take the framework's code
  rather than fight it, so 422. On a stack that does not validate query parameters for you, 400 is the equivalent
  choice — what matters is that one code covers the whole class.
- The three below sit on the other side of that line. They are conditions *your own handler* detects and raises, not
  automatic validation failures the framework answers before your code runs, so 400 is the right code for them even on
  the FastAPI-shaped stack that returns 422 above. The 422/400 split here is deliberate, not drift.
- Malformed, unverifiable, or expired cursor: **400** with a distinct machine-readable code so the client restarts
  iteration deliberately rather than looping.
- Unknown filter parameter: **400**, listing valid fields. Silently ignoring it turns a typo into a full-collection
  scan that looks like it worked.
- Filter too expensive: **400** if statically detectable, else a statement timeout surfacing as **503** with
  `Retry-After` (RFC 9110 §10.2.3).

#### Controversy: envelope or bare array?

**The controversy.** Should a collection return `[{...}, {...}]` or `{"items": [...], "next": ...}`? **The camps:**
*bare array* (the resource is a list, so return a list; pagination goes in `Link` headers where HTTP already has a
place for it) versus *envelope* (an object with items under a key, alongside pagination and metadata).

**Background.** Bare arrays came from "the body is the resource" plus the fact that
[RFC 8288](https://www.rfc-editor.org/rfc/rfc8288.html) already gives links a home in headers. Envelopes came from
practice: clients needed a next token, then a total, then a warnings array, and each addition to a bare array is
breaking while each addition to an envelope is not.

**Bare array — strengths.** Minimal; the body is exactly the data. Metadata sits in headers where caches and
intermediaries see it without parsing. It composes with streaming, since a large array can be produced incrementally
while an envelope with trailing metadata cannot.

**Bare array — weaknesses.** Nowhere to put anything else. Adding a total, warning, or deprecation notice means a
header — invisible to most client code, stripped by browser CORS defaults unless explicitly exposed, and `Link`
parsing is nontrivial enough that most SDKs skip it — or a breaking body change.

**Bare array — risks.** The evolution trap: a year in you need one extra field and the options are a new endpoint, a
version bump, or a header nobody reads. (The historical JSON-array-hijacking concern is essentially obsolete for API
clients and should not drive the decision.)

**Bare array — guardrails.** Ship `Link` headers from day one, expose them via `Access-Control-Expose-Headers`,
document the relation types, and never add a *required* header.

**Envelope — strengths.** Additive extension without breaking clients; pagination state sits beside the data in the
format every client already parses; codegen models it naturally; and "empty page" and "no more pages" become explicit
rather than inferred.

**Envelope — weaknesses.** More typing (`resp["items"]` everywhere), obstructed incremental production when the
envelope carries trailing metadata, and the temptation of a bespoke envelope per endpoint — worse than either
consistent option.

**Envelope — risks.** Inconsistency: an API with three envelope shapes is harder to consume than one with none.
juniper-data is the live example, with a bare array and a full envelope in one router file.

**Envelope — guardrails.** Define exactly one envelope and apply it to every collection, including the ones that
"obviously don't need it yet". Fix the item key name and never deviate. Emit `Link` headers as well.

**Recommendation** (labelled as such): use an envelope, consistently, and emit `Link` headers in addition. The
decisive argument is evolution, not elegance — the envelope's additive extension path is the one that does not cost a
version bump. If you have already shipped bare arrays, do not churn existing endpoints; standardise new ones and
converge at the next major version.

---

### II.8 Error Models

#### Overview

An error response serves two audiences with incompatible needs: a human debugging at 2am wants prose and a thread to
pull; a program wants a stable token to branch on and a signal about retrying. Serving one with the other's format is
the root of most bad error design — prose that clients regex-match, or opaque codes nobody can act on. The status code
is the coarse machine signal and is not enough; [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457.html) fills the gap
in a standard way.

#### Background

RFC 9457, *Problem Details for HTTP APIs*, was published July 2023 and **obsoletes RFC 7807** (its header records
`Obsoletes: 7807`). Appendix D lists the changes: a registry of common problem type URIs (§4.2), clarification of
multiple problems (§3), and guidance on non-dereferenceable type URIs (§3.1.1); the wire format is compatible. Its
motivation (§1): "HTTP status codes cannot always convey enough information about errors to be helpful. While humans
using web browsers can often understand an HTML response content, non-human consumers of HTTP APIs have difficulty
doing so."

[RFC 9205](https://www.rfc-editor.org/rfc/rfc9205.html) §4.6 makes the same point from the other direction,
contradicting a widespread instinct: "mapping application errors to individual HTTP status codes one-to-one often
leads to a situation where the finite space of applicable HTTP status codes is exhausted... applications using HTTP
should define their errors to use the most applicable status code, making generous use of the general status codes
(200, 400, and 500) when in doubt... they should not specify a one-to-one relationship between status codes and
application errors." It then names the mechanism: convey finer-grained information in the content, and
"[PROBLEM-DETAILS] provides one way to do so."

#### RFC 9457 exactly

The media type is **`application/problem+json`** (§3); Appendix B defines `application/problem+xml`. Five members
(§3.1):

| Member     | Type                  | Semantics                                                                                                             |
|------------|-----------------------|-----------------------------------------------------------------------------------------------------------------------|
| `type`     | string, URI reference | Identifies the problem type. Consumers **MUST** use it as the primary identifier. Default when absent: `about:blank`. |
| `status`   | number                | The status the origin generated. **Advisory only**; generators MUST use the same code in the real response.           |
| `title`    | string                | Short human-readable summary of the *type*. **SHOULD NOT** change between occurrences except for localisation.        |
| `detail`   | string                | Human-readable explanation of *this occurrence*.                                                                      |
| `instance` | string, URI reference | Identifies the specific occurrence.                                                                                   |

Four points people get wrong. **`type` defaults to `about:blank`** (§3.1.1), which §4.2.1 registers as meaning "the
problem has no additional semantics beyond that of the HTTP status code", with `title` then **SHOULD** being the
status phrase — so a document with no `type` is well-defined, not incomplete. **`title` is per-type, `detail` is
per-occurrence**; a `title` interpolating a request-specific value breaks client-side grouping and log aggregation.
**`detail` is for humans**, and §3.1.4 says so twice: it "ought to focus on helping the client correct the problem,
rather than giving debugging information", and "Consumers **SHOULD NOT** parse the `detail` member for information;
extensions are more suitable and less error-prone ways to obtain such information." **`status` can disagree with the
real status** — §5 warns the duplication is "bringing the possibility of disagreement", that "their relative precedence is
not clear", and that generic HTTP software uses the real code.

**Extension members** (§3.2) carry machine-readable per-occurrence data, and clients **MUST ignore** unrecognised
ones, which is what makes the format evolvable. §4 recommends extension names start with a letter, use only
`ALPHA / DIGIT / "_"` (so they survive XML serialisation), and be three characters or longer; defining a new type
requires documenting a type URI, a short title, and the status code it is used with. The URI **SHOULD** resolve to
HTML documentation, but §3.1.1 says consumers **SHOULD NOT** automatically dereference it outside developer tooling —
it is an identifier that happens to be resolvable, not a fetch instruction.

#### Why a URI rather than an error code string

The case for a URI is namespacing. Error codes live in a flat global namespace, and every organisation independently
mints `INVALID_REQUEST` and `NOT_FOUND`; the moment two systems' errors flow through one gateway or SDK, the codes
collide with no way to disambiguate. A URI under a domain you control cannot, it is self-documenting when resolvable,
and §4.2's IANA registry exists so common problems get identical identifiers across APIs.

The practical objection is equally real. URIs are long and awkward as map keys, in a `switch`, and in log queries;
§3.1.1 warns a *relative* type URI resolves against the document base URI and so identifies different resources at
different endpoints; they tempt clients into dereferencing, an outage amplifier that fires hardest during an incident;
and embedding a hostname couples error identity to a domain, with the spec noting that switching scheme later
"creat[es] a new identity for the problem type and thus introduc[es] a breaking change." The resolution most APIs
reach: an absolute `https` type URI under a stable API-owned path as the normative identifier, plus a short flat
`code` extension for ergonomics, documented so the URI wins.

#### Taxonomy, field-level errors, and the three explicit signals

A usable taxonomy has three levels, and confusing them is the usual failure: **HTTP status** for generic HTTP
software; **problem type / code** for the client's branching logic; **`detail`** for humans. Rules that keep level 2
stable: codes are append-only (retire, never repurpose); codes are independent of status (`insufficient-quota` may
move 403 → 402 without changing a client branch); one code per distinguishable client *action*, since a code that
cannot be acted on differently from its neighbour is noise; and codes documented in the same artifact as the endpoints
(II.10).

Validation is where a flat error is insufficient, and RFC 9457 §3 works exactly this case with an extension member: an
`errors` array whose items pair a human `detail` with a JSON Pointer `pointer` such as `#/profile/color` locating the
offending field in the request content. Carry a per-item machine code too if clients branch per field, and never echo
a value that might be a secret. §3 also says that when problems of *different* types occur "it is RECOMMENDED that the
most relevant or urgent problem be represented", and warns that generic "batch" problem types "do not map well into
HTTP semantics".

Three signals must be explicit rather than inferred. **i18n**: §1 says human-readable strings can be negotiated with
`Accept-Language` (RFC 9110 §12.5.4) and §3.1.3 permits `title` to vary for localisation; localise `title` and
`detail`, never `type` or a code, and always emit `Content-Language`. **Correlation**: every error carries the
identifier tying it to the server log — `instance` (§3.1.5) when it is a URI, else a `request_id` extension — and the
same value belongs in a response header (so it survives an unparseable body) and in the log line. **Retryability**:
use `Retry-After` (RFC 9110 §10.2.3, an `HTTP-date` or `delay-seconds`; RFC 6585 §4 uses it with 429; RFC 9457 §4
notes a problem type **MAY** specify its use), plus an explicit extension member where the status is ambiguous — a 500
from a deterministic serialisation bug is not retryable, one from a dropped database connection is.

#### What must never appear in an error body

Stack traces and exception class names — §5: generators "are encouraged to avoid making implementation details such as
a stack dump available through the HTTP interface." SQL text or ORM errors, which name your tables. Filesystem paths,
internal hostnames, container ids. Whether an account exists — distinguishing "no such user" from "wrong password" is
an enumeration oracle, and the same applies to any resource whose existence is confidential (return the same 404 for
"absent" and "present but not yours"). The submitted value of a secret field, since validation errors love to echo
input. And upstream vendor error bodies verbatim, which carry the upstream's internals and sometimes your keys. The
principle: the error body is a public document; everything else goes to the log, keyed by the correlation id.

#### Ground: juniper-data's three error shapes

juniper-data does not use problem details — a repository-wide grep for `problem+json` returns zero matches. Its
surface is FastAPI's default `{"detail": ...}` as `application/json`, from three independent places: **hand-raised
`HTTPException`** (twelve sites, all string `detail`: 400 for an unknown generator at `routes/datasets.py:94-97`, 400
for invalid params at `:112`, 501 for a missing optional dependency at `:165-168`, 404s at `:533`, `:647`, `:670`,
`:695`, `:728`, `:763`, `:787`); **middleware `JSONResponse`** (413 at `api/middleware.py:82`; 401/429 rebuilt from
the raised exception so its headers survive, `:136-140`); and **app-level handlers** (`ValueError` → 400
`{"detail": "Invalid request parameters"}` at `api/app.py:152-158`, `Exception` → 500
`{"detail": "Internal server error"}` at `:160-166`, both logging the real detail server-side only — that pair is
genuinely good practice).

**Two mutually incompatible `detail` shapes.** Every hand-raised error puts a *string* in `detail`; FastAPI's
request-validation handler puts an *array of objects* there. Verified against the toolchain this primer targets
(FastAPI 0.141.1, Pydantic 2.13.4, Starlette 1.6.0):

```json
{"detail": "Dataset 'abc' not found"}
```

```json
{"detail": [{"type": "greater_than_equal", "loc": ["query", "limit"],
             "msg": "Input should be greater than or equal to 1", "input": "0", "ctx": {"ge": 1}}]}
```

Same field, same content type, same API, disjoint types — and the documentation says nothing. This is an unclosed
default rather than sloppiness: juniper-data registers no `RequestValidationError` handler (only the `ValueError` and
`Exception` ones at `app.py:152` and `:160`), and `RequestValidationError` is **not** a `ValueError` subclass —
verified MRO: `RequestValidationError → ValidationException → Exception` — so the app handler does not intercept it
and FastAPI's built-in 422 runs unchanged. Meanwhile `pydantic.ValidationError` **is** a `ValueError` subclass, which
is why the generator-parameter failure at `routes/datasets.py:105-112` is caught by the route's own
`except (ValueError, ValidationError)` and emerges as a 400 string.

**Redaction on one branch and not its neighbour.** The batch-create loop has two handlers ten lines apart.
`routes/datasets.py:423-431` catches `HTTPException` and puts `e.detail` into the per-item `error` field **verbatim**;
`routes/datasets.py:433-447` catches everything else, mints a 12-hex correlation id, logs the traceback, and returns
only `f"Dataset creation failed (ref: {error_id})"` — rationale stated in-comment: "ERR-08: do not surface raw
exception strings — they can leak filesystem paths or internal type details." That reasoning applies to the adjacent
branch too, which can carry the 501 detail from `:165-168`, a string interpolating an `ImportError` message that may
contain a module path. In fairness the 501 disclosure is *considered*: the comment at `:158-164` explains the install
hint is the actionable payload, and that 503 was deliberately rejected because "it invites client retries and
health-tooling misreads for a condition that will not clear on its own." That is exactly the reasoning an error
taxonomy should record; it was just not applied uniformly.

#### Ground: the clients lose the status code

All three Juniper clients map status to an exception type and then discard the code. The data-client's handler
(`juniper-data-client/juniper_data_client/client.py:302-320`) sends 404 to `JuniperDataNotFoundError`, 400/422 to
`JuniperDataValidationError`, and everything else to
`JuniperDataClientError(f"Request failed ({response.status_code}): {error_detail}")`. The exception classes
(`juniper_data_client/exceptions.py`) are bare — one base and five leaves, every body a `pass` or docstring, with no
`status_code`, no `response`, no parsed body. So a caller can distinguish 404 from 400/422 by *type*, but 401, 413,
429, 500 and 501 all collapse into the same base exception, telling a rate limit from a server bug means parsing
`str(e)`, and a 429's `Retry-After` is reachable nowhere.

Two knock-on effects are visible in the code. Because `error_detail` is assigned from `error_json["detail"]`
unconditionally (`client.py:306`), a 422 makes it a Python `list` that is then f-string-interpolated — the two server
shapes surface as one unparseable repr. And the sibling cascor-client carries a workaround for fleet-wide
inconsistency: `juniper-cascor-client/juniper_cascor_client/client.py:393-402` tries `body["error"]["message"]` first
and falls back to `body["detail"]`, because different services answer with different envelopes — a client paying
interest on a server-side decision nobody made deliberately. The fix is one line of state on the base exception:
`status_code`, `response_body`, `headers`.

#### Partial failure and batch errors

Options: **all-or-nothing** (the batch is a transaction; simplest, needs transactional storage); **per-item results
with an overall 200/207** (the status means "processed", not "everything worked"); **fail-fast** (stop at the first
error, report progress).

juniper-data takes the second with one flaw. `batch_create_datasets` (`routes/datasets.py:377-454`) returns per-item
`success`/`error` records (`core/models.py:206-222`) plus `total_created`/`total_failed`, but declares
`status_code=status.HTTP_201_CREATED` (`:377`) with no conditional downgrade — so a batch in which every item failed
still answers **201 Created**, and a client checking `response.ok` and moving on has lost fifty datasets. The per-item
envelope is right; the status must stop claiming creation.

#### Judgement Calls

- **Adopt problem+json or keep a house format?** With clients in the field, converting is breaking — content-negotiate
  (§4 allows adding it to an existing API via `Accept`). New APIs should just use it.
- **Granularity?** One code per distinguishable client action; finer creates a taxonomy nobody maintains, coarser
  forces string parsing.
- **How much detail?** The line is whether it is *actionable by the caller*. "Install this extra" is; "IntegrityError
  at line 402" is not.
- **Localise?** Only with a real translation pipeline. A half-localised API is worse than English.

#### Tradeoffs

| Decision                   | Buys                                   | Costs                                 |
|----------------------------|----------------------------------------|---------------------------------------|
| `application/problem+json` | Standard shape, tooling, extensibility | Negotiation for old clients           |
| URI `type` as identifier   | Global uniqueness, resolvable docs     | Verbose; awkward as a map key         |
| Flat `code` extension      | Ergonomic branching                    | A second identifier to keep in sync   |
| Correlation id in body     | Support can find the log               | Must be logged, must not be guessable |
| Generic 500 text           | No information disclosure              | Developers cannot self-diagnose       |

#### Best Practices

- One error envelope for the entire API. Write it down; lint for it.
- `type` (or a code) is the branch point; `detail` is prose — document it as unstable and unparseable.
- Always include a correlation id, in the body *and* a header, and log it.
- Signal retryability explicitly: `Retry-After` where the status defines it, an extension member where it does not.
- Redact by default at the boundary, and make the redacting helper the only way to build an error body so the safe
  path is the easy path.
- Enumerate error types in the API description (II.10); preserve status, body, and headers on client-side exceptions.

#### Common Failure Modes

- **Two shapes for one field** — `detail` as string and as array in the same API.
- **Redaction on some paths only** — adjacent `except` branches with opposite policies.
- **Status claiming more than the body delivers** — 201 for a batch where everything failed.
- **Errors clients must regex** — the only discriminator is a human-readable message.
- **Stack traces in production** — usually a debug flag that was true in staging.
- **User enumeration** — different status, message, or merely timing between "no such account" and "wrong password".
- **Clients that discard the status** — the error arrived intact and the SDK threw it away.

#### Error Handling

How the error system itself fails, in three parts. **The handler that raises**: error construction must be total — no
database lookups, no template loading, no network call for a message catalogue. **The unhandled-exception net**: every
API needs a final handler converting anything unexpected into a generic 500 with a correlation id; juniper-data has
one (`api/app.py:160-166`) but no matching net for validation errors, which is why the second `detail` shape leaks
through. **Errors raised outside the framework's reach**: middleware-produced responses bypass application exception
handlers entirely — juniper-data's 401/429/413 come from middleware (`api/middleware.py:82`, `:136-140`) — so adopting
problem+json means treating the middleware layer too, or auth and rate-limit errors will be the only ones left in the
old format.

#### Controversy: is a URI the right machine-readable discriminator?

**The controversy.** §3.1.1 makes the `type` URI normative — "Consumers **MUST** use the `type` URI (after resolution,
if necessary) as the problem type's primary identifier" — yet many APIs that otherwise adopt problem details branch on
a short string code instead. **The camps:** *URI-primary* (the URI is the identity) versus *code-primary* (a flat
enumerated string is the real discriminator and `type` is documentation).

**Background.** The URI choice inherits the web's approach to extensibility — namespace by domain, make identifiers
resolvable, let a registry emerge — which works when identifiers are read by tools and written by specifications.
Error codes are read by application code in a `match` statement and written in a hurry; the ergonomics genuinely
differ.

**URI-primary — strengths.** No collisions across organisations, gateways, or aggregators; self-documenting when
resolvable; it supports the §4.2 registry, the only path to a generic client that handles "out of credit" identically
everywhere; and it enforces documentation discipline.

**URI-primary — weaknesses.** Verbose in every log line, switch, and dashboard label; the relative-URI trap in §3.1.1;
and it couples error identity to a domain, with the spec's own note that changing scheme later is a breaking change
showing how sticky the choice is.

**URI-primary — risks.** Clients dereferencing type URIs on every error — **SHOULD NOT** outside developer tooling,
but nothing stops them, and it amplifies traffic exactly during an incident. And documentation drift: a resolvable URI
that 404s is worse than a non-resolvable one.

**URI-primary — guardrails.** Absolute `https` URIs under a path you will own indefinitely, with real documentation
served at them; never relative; version the documentation, not the URI; log the URI but index on a derived short name
so dashboards stay readable.

**Code-primary — strengths.** Ergonomic in every language: a natural map key, enum value, and log field; easy to
enumerate exhaustively in a test; easy to say out loud in support; trivially stable across a domain migration.

**Code-primary — weaknesses.** It collides — `NOT_FOUND` from service A and service B are indistinguishable, so the
aggregator invents a prefix, a namespace done badly. No shared registry can form, and a code extension alongside an
ignored `type` gives two identifiers that can drift apart.

**Code-primary — risks.** The prefix-invention trap: `svcA.NOT_FOUND` is a URI with the structure removed and the
guarantees lost. And clients written against codes grow tolerance for missing codes, at which point they fall back to
parsing `detail`.

**Code-primary — guardrails.** Still emit `type`, still make it absolute, and document that the URI is normative and
the code derived. Namespace the code with an owner segment from day one, and lint that every code maps to exactly one
URI and vice versa.

**Recommendation** (labelled as such): emit both and say which wins. Make `type` an absolute `https` URI under an
API-owned path — the identifier that survives merges, gateways, and the next reorganisation — and carry a short flat
`code` extension for the ergonomics your clients will otherwise invent themselves. Document the URI as normative. The
redundancy costs a few bytes per error and buys the option of consolidating later, which the code-only design
forecloses.

---

### II.9 Hypermedia and HATEOAS

#### Overview

HATEOAS — "Hypermedia As The Engine Of Application State" — is the constraint that a client navigates by following
links the server provides rather than by constructing URLs from out-of-band knowledge. It is part of REST's *uniform
interface* constraint and distinguishes REST in the dissertation's sense from what the industry calls REST. It is
also, empirically, the least adopted of the constraints, and that gap is what this section is about. Fielding's
dissertation is not in the local spec cache, so that attribution is working knowledge, not a citation. The cached
corpus gets close in two separate places: RFC 9110 §1.3 opens "HTTP provides a uniform interface for interacting with
a resource", while §1.1 separately describes HTTP as a family of protocols that "share a generic interface, extensible
semantics, and self-descriptive messages". The RFC cites `[REST]` in §3.2 and §9.1 — not in §1.

#### Background

The web works this way: a browser knows one URL and the semantics of `<a href>`, so servers restructure URL spaces
constantly without breaking clients. API clients almost never do — they are generated from a schema or written against
a documented template and build `f"{base}/v1/datasets/{id}/artifact"` from string parts, which is exactly what RFC
9205 §3.2 warns against: "Instead of statically defining URI components like paths, it is RECOMMENDED that
applications using HTTP define and use links to allow flexibility in deployment." The reason is structural, not
ideological: a standard has many independent deployments and cannot assume path layout, whereas a company's API has
one deployment and a team controlling both ends. RFC 9205 addresses the first case; most APIs are the second.

#### Link relations and the `Link` header

RFC 8288 defines a link as a typed connection comprising a context, a relation type, a target, and optional target
attributes (§2); the relation carries the semantics, so "a link with the relation type `copyright` indicates that the
current link context has a copyright resource at the link target" (§2.1). There are two kinds — **registered** types
(bare tokens, compared case-insensitively, held in IANA's "Link Relations" registry, §2.1.1) and **extension** types
(URIs you control, compared as case-insensitive strings, §2.1.2). RFC 8288 does not enumerate the registry; §4.2 says
it "updates the registration procedures" and points at IANA. Both examples below are from §3.5, unfolded onto one
line each but otherwise unaltered:

```http
Link: <http://example.com/TheBook/chapter2>; rel="previous"; title="previous chapter"
```

```http
Link: </TheBook/chapter2>; rel="previous"; title*=UTF-8'de'letztes%20Kapitel, </TheBook/chapter4>; rel="next"; title*=UTF-8'de'n%c3%a4chstes%20Kapitel
```

The second is §3.5's multi-link example, and the `title*=` parameters are the point of it: RFC 8288 uses it to show
the RFC 8187 encoding that carries non-ASCII characters and a language tag (here German) in a header parameter. Drop
them and the example stops being that example.

Note the spelling: the cached RFC 8288 text uses **`previous`**, and elsewhere shows `start`, `index`, and
`copyright`. The widely deployed pagination spelling is `prev`; `prev`, `first`, and `last` are, to my knowledge, in
the IANA registry (`first`/`last` via RFC 5005), but neither the registry nor RFC 5005 is in the local cache and
outbound fetches were blocked here, so **treat `prev`, `first`, and `last` as unverified**. Verified from cache:
`next` and `previous` appear in RFC 8288's own examples, multiple links may be comma-separated in one field, and one
link-value may carry several space-separated relation types (§3.5).

#### Hypermedia formats

**None of the five below is in the local spec cache and outbound fetches were blocked, so the media types and status
claims here are working knowledge and are unverified.** Treat them as pointers.

| Format          | Media type (unverified)           | Shape                                                                            | Status (unverified)                 |
|-----------------|-----------------------------------|----------------------------------------------------------------------------------|-------------------------------------|
| HAL             | `application/hal+json`            | `_links` map of rel → href; `_embedded`                                          | Expired I-D; widely implemented     |
| JSON:API        | `application/vnd.api+json`        | `data`/`included`/`links`/`errors`, typed resource identifiers, sparse fieldsets | Versioned community spec            |
| Siren           | `application/vnd.siren+json`      | `class`, `properties`, `entities`, `links`, `actions` (method, href, fields)     | Community spec, low adoption        |
| Collection+JSON | `application/vnd.collection+json` | `items`, `queries`, `template` for writes                                        | Community spec, very low adoption   |
| JSON-LD + Hydra | `application/ld+json`             | RDF linked data; Hydra adds an operations vocabulary                             | JSON-LD a W3C Rec; Hydra a CG draft |

The spread is instructive. HAL adds links and nothing else, which is why it is the one people ship. Siren is the only
one describing *state transitions* — an `actions` array naming method, target, and expected fields — which is what
full HATEOAS requires and which almost nobody adopts. JSON:API is less a hypermedia format than a complete document
convention, and its adoption owes more to the pagination, sparse-fieldset, and error conventions than to the links.

#### Where hypermedia pays, and why pagination links won

Three cases share one property: the available next steps depend on server state the client cannot compute. **Workflow
resources** — an order that is `pending` can be cancelled, one that is `shipped` cannot, and encoding that client-side
gives one state machine two owners that will diverge. **Long-running operations** — a 202 returning a `Location` or
status link is hypermedia everyone adopts without naming it. **Pagination.** The common thread: hypermedia pays when a
link's *presence* carries information, not merely its value; a link always present and always the same shape is a URL
template with extra steps.

Pagination `Link` headers are the one broadly adopted piece of hypermedia — GitHub's REST API is the best-known
example, though I could not fetch its documentation to verify that here. Four properties explain it, and they are
exactly what the rest of hypermedia lacks. The client genuinely *cannot* construct the URL, because a cursor token is
opaque and server-generated, whereas for `/datasets/{id}` it already has the id. The relation vocabulary is tiny and
fixed, so no general link-following engine is needed. Absence is meaningful and trivially handled: no `next` means no
more pages, one `if` replacing an error-prone calculation over `total` and `offset`. And it degrades gracefully —
ignore the header, fall back to offset parameters — so nothing forced adoption and adoption happened. The general
lesson: hypermedia succeeds where following the link is *easier* than not following it.

#### Judgement Calls

- **Is the link's presence informative?** If every link is always present, you added payload and removed nothing.
- **Who writes the client?** Your team, generated from your schema: the decoupling argument is weak. Thousands of
  uncoordinated integrators: it is strong.
- **Headers or body?** Headers are visible to intermediaries and cost no schema change; bodies are easier for SDK code
  to reach. Emitting both is cheap.
- **A whole format, or `Link` plus a few fields?** HAL or JSON:API is an API-wide commitment; a `Link` header is a
  header.

#### Tradeoffs

| Approach               | Buys                                       | Costs                                 |
|------------------------|--------------------------------------------|---------------------------------------|
| No links               | Simplest client; trivial codegen           | URL structure is frozen public API    |
| `Link` headers only    | Standard, incremental, degrades gracefully | Awkward to reach in some HTTP clients |
| `_links` in body (HAL) | Easy to consume; per-item links            | Payload growth; a format commitment   |
| Full actions (Siren)   | Server owns the state machine              | Client complexity; almost no tooling  |

#### Best Practices

- Emit pagination links — the best cost/benefit ratio in the topic, and what juniper-data's `/filter` is missing (no
  `Link` header appears anywhere in the package).
- Return a `Location` or status link from every asynchronous-operation response.
- Where a link's presence encodes permission or state, document it: "the `cancel` link is present if and only if
  cancellation is allowed" is what makes it worth following.
- Use a registered relation type where one fits, an absolute URI under your own domain otherwise (§2.1.2). Do not
  invent bare tokens.
- If you ship `Link` for browser clients, add it to `Access-Control-Expose-Headers`.
- Do not claim HATEOAS if clients still build URLs from templates; the claim costs credibility.

#### Common Failure Modes

- **Links present, clients ignoring them** — payload grew, coupling did not shrink, and the URLs are frozen anyway
  because someone hardcoded them.
- **Links that are just templates** — `"self": "/v1/datasets/{id}"` with the id already known.
- **Absolute links with the wrong host** — behind a reverse proxy, links built from the request `Host` or a hardcoded
  base leak internal hostnames or point at an unreachable origin. The single most common operational bug in hypermedia
  APIs.
- **Hardcoded prefixes in emitted links.** juniper-data emits `artifact_url` as
  `f"/v1/datasets/{dataset_id}/artifact"` at `routes/datasets.py:138` and `:253`. That it is a link at all is good — a
  client can follow it without knowing the path scheme. But `/v1` is a bare literal there and in the three
  `include_router(..., prefix="/v1")` calls at `api/app.py:140-142`, with no shared constant; changing the prefix
  means finding all five sites, and missing one produces links that 404 while the routes still work.
- **A `Link` header emitted but stripped** by a proxy or CORS configuration.

#### Error Handling

- A followed link that 404s is a *server* bug — the server asserted the target existed. Monitor broken self-links.
- A client that cannot find an expected relation should fail loudly with the relation name, not fall back to a
  constructed URL; a silent fallback re-establishes the coupling and hides the regression.
- RFC 9457 §4 notes a problem type "might use typed links to another resource that machines can use to resolve the
  problem" — e.g. a link to the quota-purchase resource on a 402.

#### Controversy: does HATEOAS earn its cost?

**The controversy.** HATEOAS is a defining REST constraint that the overwhelming majority of so-called REST APIs do
not implement, and the industry has argued since roughly 2008 about whether that is a failure of the industry or of
the constraint. **The camps:** *advocates* (an API without it is permanently coupled to its URL structure, so
evolution requires versioning) versus *pragmatists* (the decoupling is theoretical because no client follows links
dynamically, so the cost is real and the benefit is not).

**Background.** The split has a specific origin — Fielding's 2008 post "REST APIs must be hypertext-driven", asserting
that URL-template APIs are not REST. That post, like the dissertation cited in the Overview above, is not in the local
spec cache and carries the same caveat. The industry's answer over fifteen years was to keep the name and drop the
constraint. Meanwhile tooling consolidated around OpenAPI, which describes URL templates, so the dominant toolchain
assumes the thing HATEOAS forbids. That is the material fact keeping the argument alive: it is now a debate about
which ecosystem you are in.

**Hypermedia — strengths.** Clients decouple from URI structure, so servers can restructure, relocate resources across
hosts, and split services — the deployment flexibility RFC 9205 §3.2 cites. RFC 9205 §4.4.1 describes the entry-point
document pattern, which "ensures that the deployment is as flexible as possible (potentially spanning multiple
servers), allows evolution, and also gives the application the opportunity to tailor the discovery document to the
client." Server-driven state machines put transition rules in one place, and RFC 9205 §4.16 lists "using a distinct
link relation type to identify a URL for a resource that implements the new functionality" as its *first* mechanism
for backwards-incompatible change.

**Hypermedia — weaknesses.** A link-following client needs a state machine, relation handling, and missing-relation
error paths, versus a generated client that calls a method. No generic client ecosystem materialised in thirty years.
OpenAPI, codegen, mocks, and contract testing model operations and paths, not link graphs. Payload bloat is real where
per-item `_links` exceed the data. And it does not remove versioning: relation types, media types, and field semantics
still change.

**Hypermedia — risks.** The dominant one is cost without benefit — you pay payload, implementation, and review
overhead, and clients hardcode URLs anyway, the observed outcome in most deployments. A subtler one is false
confidence: believing you can restructure freely, then finding during a migration that three integrators parse your
links. A discovery document also adds a request to every client's critical path and a single point of failure.

**Hypermedia — guardrails.** Measure before claiming: log how many requests arrive at URLs that were emitted as links
versus constructed. Adopt incrementally — pagination, then async status, then state-dependent actions. Document the
rule wherever a link's presence encodes one, keep a machine-checkable list of relation types, and do not promise URL
instability you will never exercise.

**Pragmatist — strengths.** Matches how clients are really built: generated, typed, method-shaped. The whole toolchain
works, payloads stay small, and onboarding is faster — read an operation list rather than learn a navigation protocol.
URL stability is achievable in practice, since adding fields and endpoints is backwards-compatible.

**Pragmatist — weaknesses.** URL structure becomes permanent public API, pushing you toward URL versioning and its
duplication. Server-side state rules leak into clients — the client decides whether to show "cancel" — and the copies
drift. Multi-deployment scenarios suffer most: fixed paths across independent vendor implementations are precisely
what RFC 9205 §3.2 calls "squatting".

**Pragmatist — risks.** Discovering the coupling at the worst time — a migration, a service split, a new gateway —
where every client must update in lockstep. And state-machine drift producing 409s that look like bugs.

**Pragmatist — guardrails.** Treat URL structure as a versioned contract and say so. Return a machine-readable list of
currently permitted operations (an `allowed_actions` array, or `Allow` on `OPTIONS`) even without full hypermedia —
that recovers most of the state-machine benefit cheaply. Emit pagination and async-status links regardless, and never
*promise* URL stability beyond the documented version.

**Recommendation** (labelled as such): adopt hypermedia selectively, where a link's presence carries information the
client cannot compute — pagination cursors, long-running-operation status, state-dependent actions. Do not adopt a
full hypermedia format for a single-deployment API consumed by generated clients; the tooling cost is real and the
decoupling benefit stays theoretical until you have actually moved a resource. Do adopt it where there are many
independent deployments or uncoordinated integrators, since RFC 9205 §3.2 applies directly. And in either case stop
using "RESTful" as a synonym for "JSON over HTTP" — the precision is worth keeping even when the constraint is not
met.

---

### II.10 OpenAPI and Contract-First Design

#### Overview

OpenAPI is a machine-readable description of an HTTP API — paths, operations, parameters, schemas, security schemes,
servers, examples — in JSON or YAML. Its value is entirely derivative: a spec buys nothing by existing and everything
through what consumes it (codegen, mock servers, request validation, docs, contract tests, linting). The central
question is not whether to have a description but which artifact is authoritative — the document or the code. Both
fail, differently, and the failure modes are what you actually choose between.

#### Background

OpenAPI descends from Swagger, donated to the OpenAPI Initiative in 2015 — history which, like the specification text
discussed below, is working knowledge here and not something the local cache can confirm. The 3.0 line set the object
model; the 3.1 line aligned the Schema Object with JSON Schema. On that alignment, here is what is verifiable here — from the local
toolchain (FastAPI 0.141.1, Pydantic 2.13.4, Starlette 1.6.0):

```text
>>> app.openapi()["openapi"]
'3.1.0'
>>> pydantic.json_schema.GenerateJsonSchema.schema_dialect
'https://json-schema.org/draft/2020-12/schema'
```

The implementation side is verified: FastAPI emits an OpenAPI 3.1.0 document whose schemas are generated against JSON
Schema draft 2020-12. The OpenAPI specification text is **not** in the local cache and outbound fetches were blocked,
so the spec-level claims — that OAS 3.1 nominates 2020-12 as its dialect, and the exact default of `jsonSchemaDialect`
— are **unverified here**. The practical consequence stands either way: under 3.1 a Schema Object is a JSON Schema, so
`$ref`, `const`, and array-valued `examples` behave as JSON Schema defines them, while 3.0's divergences (`nullable`,
singular `example`, an incompatible `exclusiveMinimum`) are 3.0-only. Do not mix the idioms.

#### Design-first vs code-first

**Design-first**: write the document, review it, generate stubs and SDKs, implement against them. **Code-first**:
write annotated handlers; the framework derives the document.

|                  | Design-first                          | Code-first                                 |
|------------------|---------------------------------------|--------------------------------------------|
| Review artifact  | The contract, before code exists      | A diff of generated JSON, after the fact   |
| Parallel work    | Consumers start day one from a mock   | Consumers wait for the endpoint            |
| Drift direction  | Doc says X, code does Y (**doc-rot**) | Doc omits X entirely (**spec-drift**)      |
| Cost of a change | Edit doc, regenerate, implement       | Edit code                                  |
| Typical failure  | Describes an API nobody built         | Describes only what the framework can see  |
| Enforcement      | Needs runtime validation to bind them | Needs review discipline to catch omissions |

The asymmetry worth internalising: design-first's failure is *visible* (someone reads the spec and it is wrong) while
code-first's is *invisible* (the spec is internally consistent and silently incomplete). An incomplete spec passes
every linter, renders beautifully, and generates a client that compiles.

#### What a good spec buys, and the fields a framework cannot infer

A spec buys client codegen; server stubs and gateway-level request validation (the enforcement that makes the document
load-bearing); mock servers, design-first's largest concrete payoff; rendered documentation; contract tests asserting
recorded responses validate against declared schemas; and Spectral-style linting for house rules. The last two turn a
description into a contract — a spec nothing validates against is documentation with a schema-shaped syntax.

**`operationId`** is the identifier code generators use to name methods, so its *stability* is a public API concern.
FastAPI's auto-generated ids derive from the function name, path, and method; verified on FastAPI 0.141.1:

```text
def list_items(...)  on GET /items        -> operationId "list_items_items_get"
def get_item(...)    on GET /items/{iid}  -> operationId "get_item_items__iid__get"
```

Every component is unstable. Rename the handler and every generated SDK renames a public method — from a change that
looked purely internal, with nothing in review to suggest otherwise. Set `operation_id=` explicitly, treat it as
public API, and lint for presence and uniqueness.

**Error responses** are what codegen turns into result types and what contract tests check, and this is where
code-first drifts hardest, because the framework sees only what the type system encodes. Verified on FastAPI 0.141.1:
a handler raising `HTTPException(status_code=404)` in its body produces an operation whose `responses` object contains
exactly `200` and `422` — the 404 is invisible, because there is no annotation to read.

**Security schemes** belong in `components.securitySchemes` with a `security` requirement on the operations they
protect; that is what makes generated clients accept a credential, what makes "try it out" send the header, and what
tells a reviewer which endpoints are protected. The framework can emit it only if authentication is something it can
see — middleware-implemented authentication is invisible by construction, because middleware runs outside the routing
layer the generator inspects.

**Examples** are the highest-value, highest-decay part of a spec: what developers actually read, and what rots fastest
because nothing checks it. In increasing order of effectiveness: validate every example against its schema in CI;
generate examples from recorded integration traffic; or make the examples executable in the contract suite.
Hand-written examples never revalidated are worse than none.

#### Ground: juniper-data as a worked drift example

juniper-data is code-first with FastAPI and exhibits three compounding gaps.

**1. No response declarations at all.** A grep for `responses=` across `juniper_data/` returns zero matches in the API
layer. There are twelve `raise HTTPException` sites in the route modules, plus middleware-produced 401, 429 and 413,
plus app-level 400 and 500 handlers — none appear in the schema. A consumer generating a client sees, per operation,
the declared success code and FastAPI's automatic 422, and nothing else. The endpoint most in need of documentation is
the most absent: the deliberate 501 for a missing optional dependency (`routes/datasets.py:165-168`), whose entire
purpose is to be actionably distinguishable from a 500, does not exist as far as the schema is concerned. The same
grep shows no `summary=`, no `servers=`, no `operation_id=`, and no tag descriptions. FastAPI synthesises a `summary`
from the function name, so the rendered docs are not blank — they carry derived text that changes on rename, alongside
an `operationId` that changes with it.

**2. No security scheme.** `api/security.py:26` instantiates `APIKeyHeader(name=HEADER_X_API_KEY, auto_error=False)` —
the FastAPI object whose entire purpose is to appear in `components.securitySchemes`. A repository-wide grep for
`api_key_header` finds exactly one occurrence: that line. It is never used as a dependency and never passed to the
app. Authentication is enforced in middleware instead (`SecurityMiddleware` registered at `api/app.py:127-131`,
dispatching at `api/middleware.py:129-140`), which works at runtime and is invisible at schema time. The generated
document therefore has no `securitySchemes` and no `security` requirement on any operation: a generated SDK has
nowhere to put the API key, and a reviewer reading the schema sees an entirely open API.

**3. Securing the deployment deletes the schema.** `api/app.py:91` reads `docs_enabled = not settings.api_keys`, and
that value feeds all three documentation URLs (`app.py:97-99`) — `docs_url`, `redoc_url`, and `openapi_url` each
become `None` when it is false. Configuring any API key therefore removes `/docs`, `/redoc`, **and `/openapi.json`**.
Disabling the interactive explorer in production is a defensible instinct; taking the machine-readable description
with it is a different decision, and nothing in the code suggests it was made separately. The consequence is that only
unauthenticated deployments serve a schema — so you cannot generate a client against a secured deployment, cannot run
contract tests against staging, and cannot diff the schema across environments. There is no authenticated-docs path.

The three compound in a specific way: the schema is incomplete (no errors), incorrect (no auth, on an API that
requires auth), and unavailable exactly where it could be checked against reality. Each alone is a small omission;
together they mean the generated document describes an API that does not exist and nothing can notice. The fixes are
individually small — a shared `responses=COMMON_ERRORS` dict on each operation, auth expressed as a dependency,
explicit `operation_id=` values, and `openapi_url` decoupled from `docs_url`.

#### Judgement Calls

- **Design-first or code-first?** Multiple independent consumers, or a spec that is itself a deliverable:
  design-first. One team owning both ends: code-first plus a linter.
- **Where does auth live?** If you want it in the schema it must be a dependency or declared scheme, not middleware —
  an architectural constraint, not a style preference.
- **Serve the schema in production?** Gating the interactive UI while keeping the JSON behind the same auth as the API
  is usually the right split.
- **How many examples?** One realistic example per operation, kept honest, beats twenty stale ones.

#### Tradeoffs

| Decision                    | Buys                                         | Costs                                      |
|-----------------------------|----------------------------------------------|--------------------------------------------|
| Design-first                | Parallel consumer work; reviewable contract  | Doc-rot; slower iteration; second artifact |
| Code-first                  | Zero drift on what the framework sees        | Silent omissions it cannot see             |
| Explicit `operationId`      | Stable generated method names                | One more field per operation               |
| Declared error responses    | Typed error handling in generated clients    | Verbose; hand-maintained                   |
| Schema served in production | Codegen and contract tests against real envs | Discloses the full API surface             |

#### Best Practices

- Lint the spec in CI: require `operationId`, at least one declared error response per operation, a `security`
  requirement on every non-public operation, and no unbounded arrays.
- Set `operation_id=` by hand and treat changes as breaking.
- Declare every status the endpoint can return, including middleware-produced ones.
- Keep `openapi_url` and `docs_url` independent decisions.
- Validate recorded responses against the schema in integration tests — in a code-first project that is the only thing
  binding document to code.
- Version and publish the spec artifact so a consumer can diff v1.4 against v1.3, and pin the OpenAPI version you
  emit.

#### Common Failure Modes

- **The invisible-error spec** — only the success code and an auto-422 declared.
- **The unauthenticated-looking spec** — auth in middleware, absent from the schema.
- **Schema unavailable where it matters** — secured deployments serve none.
- **Auto-`operationId` churn** — a refactor renames every generated SDK method.
- **Examples that no longer validate** — nothing checks them, so nobody notices.
- **A spec nothing enforces** — generated, rendered, never validated against.
- **3.0/3.1 idiom mixing** — `nullable: true` in a 3.1 document is silently meaningless.

#### Error Handling

- Treat spec generation as a build step that can fail. An undescribable route (untyped response, duplicate
  `operationId`) should fail the build rather than emit a degraded document.
- A contract-test schema failure should name the operation, the status, and the offending JSON pointer — not "response
  did not match schema".
- If a gateway validates requests against the spec, its rejection must be a normal error response in your own format
  (II.8), not the validator's raw output — otherwise you have introduced a second error format at the edge, produced
  by a component your clients did not know existed.

#### Controversy: design-first or code-first?

**The controversy.** Which artifact is authoritative — the description or the implementation? The argument has run
since Swagger 2.0 and neither side has won, which is itself evidence the answer is contextual. **The camps:**
*design-first* (the API is a contract, contracts are negotiated before implementation, and a description derived from
code is not a contract but a report) versus *code-first* (the description must match the running system, and the only
guarantee of that is deriving it from the running system).

**Background.** Design-first came from organisations where the API crosses a team or company boundary and consumers
must start before the provider ships — the mock-server workflow is its killer feature. Code-first came from framework
generation making accurate derivation nearly free, which removed the historical argument that hand-maintained docs
always rot.

**Design-first — strengths.** The contract is reviewable before implementation, when changing it is cheap. Consumers
work in parallel against a mock. It forces explicit decisions about error responses, security schemes, and naming that
a code-first project defers indefinitely and therefore never makes. It is the only workable model when several teams
implement the same API.

**Design-first — weaknesses.** Two artifacts to align, manually unless enforced. Iteration is slower: a one-line
change touches doc, stubs, and implementation. Generated server stubs are often unidiomatic, and teams end up fighting
or abandoning them.

**Design-first — risks.** Doc-rot: the implementation diverges under delivery pressure and the spec becomes an
aspirational document new consumers trust — worse than no spec, because it is confidently wrong. Secondarily,
design-by-committee produces a spec optimised for the review meeting.

**Design-first — guardrails.** Enforce conformance at runtime — a gateway or middleware validating against the spec —
so divergence is a test failure, not a discovery. Keep the spec in the same repository and pull request as the
implementation, and prefer generating interfaces and models over full server stubs.

**Code-first — strengths.** The description cannot drift on anything the framework sees: paths, methods, parameter
names and types, request and response models. Iteration is one edit. It reuses the annotations the team writes anyway,
so accuracy is a side effect of ordinary work.

**Code-first — weaknesses.** The framework sees only what the type system encodes; everything else — error responses,
security schemes, examples, descriptions, `operationId` stability, servers — must be added by hand, and because the
spec *generates successfully* without them, nothing prompts anyone to do it. juniper-data is the case in point. Review
is weaker too, because reviewers read the code diff, not the JSON diff.

**Code-first — risks.** Spec-drift by omission, silent by construction. Accidental breaking changes: renaming a
handler changes an `operationId` and breaks every codegen consumer with nothing in review to signal it. And the spec
degrading into a rendering artifact, so nobody notices when it stops describing the API.

**Code-first — guardrails.** Commit the generated spec and diff it in CI — this single practice converts the invisible
failure into a visible one. Lint for the fields the framework cannot infer, express auth as a dependency so it
appears, set `operationId` explicitly, and publish the spec from a secured environment so it can be checked against
reality.

**Recommendation** (labelled as such): code-first plus a committed, diffed, linted artifact is the better default for
a single team owning both ends, because it eliminates the drift class that is hardest to detect and reduces the
remainder to a lint rule. Choose design-first when consumers are independent — different teams, different companies,
or multiple implementations of one description — where the mock-server workflow and pre-implementation review are
worth the second artifact. Either way the decisive practice is the same and orthogonal to the choice: something
automated must compare the description to the running system, or you do not have a contract, you have a document.

### II.11 Part II Worked Example — Conditional Requests and Optimistic Concurrency

This example builds the HTTP semantics of Part II into one small service: content-addressed identifiers, strong `ETag`s, conditional `GET` returning 304, optimistic concurrency with `If-Match` and 412, `428 Precondition Required` for writes that omit the precondition, keyset pagination with a `Link` header, and RFC 9457 `application/problem+json` for every error.

The motivation is again a real gap. `juniper-data` already computes a SHA-256 over every artifact and stores it on the metadata record (`juniper_data/core/artifacts.py:50-63`), and its dataset identifiers are already content-addressed (`juniper_data/core/dataset_id.py:23-61`) — so its artifacts are the strongest possible candidate for `ETag` plus `Cache-Control: immutable`. It emits neither, and supports no conditional requests at all. The validator it needs is already sitting in the codebase.

The headline test is `test_lost_update_is_prevented_by_if_match`. It spells out the interleaving explicitly, because the lost-update problem is easy to nod along to and hard to actually picture:

```text
A: GET   -> tags=["baseline"], ETag=E0
B: GET   -> tags=["baseline"], ETag=E0     (B now holds a snapshot of E0)
A: PATCH If-Match: E0 -> 200, ETag=E1
B: PATCH If-Match: E0 -> 412               (B's view is stale)
*: GET   -> A's write survived
```

Without the precondition, B's write succeeds and silently erases A's change: no error, no log line, and no way for A to discover it. That silence is what makes lost updates expensive to diagnose in production.

One deliberate divergence from the real service: this example returns **200** when a content-addressed dataset already exists, reserving **201** for genuine creation. `juniper-data` returns 201 either way (`juniper_data/api/routes/datasets.py:71`), so a client cannot tell whether it created anything.

<!-- example-file: conditional_datasets.py -->
```python
"""Conditional requests: ETags, 304s, optimistic concurrency, and a real error model.

Motivation (the fix is already sitting in the codebase)
------------------------------------------------------
``juniper-data`` computes a SHA-256 over every artifact's serialized bytes and
stores it on ``DatasetMeta.checksum`` -- then never uses it as an HTTP validator.
There is no ``ETag``, no ``Cache-Control``, no ``If-None-Match`` and no 304
anywhere in the service, so ``GET /v1/datasets/{id}/artifact`` re-transfers
large, **immutable, content-addressed** blobs in full on every request. The
identifier is already a hash of the inputs and the body is already hashed: the
validator exists and is simply not emitted.

The service also cannot reject a stale write. Tags are mutable, so two clients
that read the same dataset and both PATCH it produce a silent lost update -- the
second write wins and the first is gone, with no error anywhere.

This example wires up what that service is missing:

* **Strong ETags** derived from the exact representation, so equality of the
  validator implies equality of the bytes.
* **304 Not Modified** carrying the header fields RFC 9110 section 15.4.5
  requires (ETag, Cache-Control, Vary, Date), and no body.
* **Optimistic concurrency** via ``If-Match``: absent -> 428 (RFC 6585 section 3,
  whose stated purpose is precisely the lost-update problem), stale -> 412.
* **Keyset pagination** with an opaque cursor and an RFC 8288 ``Link`` header,
  which -- unlike ``limit``/``offset`` -- cannot skip or duplicate rows when the
  collection changes mid-walk.
* **RFC 9457 problem details** on every error path, including FastAPI's
  validation errors, which otherwise emit a differently shaped body.

Run the tests with::

    pytest test_conditional_datasets.py
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import time
from collections.abc import Mapping
from dataclasses import dataclass
from email.utils import formatdate
from typing import Annotated, Any, Final, Literal

from fastapi import FastAPI, Header, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "Dataset",
    "DatasetCreate",
    "ProblemException",
    "artifact_etag",
    "compute_dataset_id",
    "create_app",
    "decode_cursor",
    "encode_cursor",
    "metadata_etag",
]

PROBLEM_JSON: Final = "application/problem+json"
#: Metadata is mutable (tags change), so it must be revalidated every time -- but
#: revalidation is cheap because a 304 carries no body. "no-store" would be wrong
#: (it forbids caching entirely) and a positive max-age would serve stale tags.
METADATA_CACHE_CONTROL: Final = "public, max-age=0, must-revalidate"
#: The artifact is safe to cache forever *because* the id is content-addressed:
#: a different byte stream is necessarily a different URL, so a cached entry can
#: never go stale. "immutable" is only honest under that invariant.
ARTIFACT_CACHE_CONTROL: Final = "public, max-age=31536000, immutable"
DEFAULT_PAGE_SIZE: Final = 20
MAX_PAGE_SIZE: Final = 100


# --------------------------------------------------------------------------- #
# Problem details (RFC 9457)
# --------------------------------------------------------------------------- #
class ProblemException(Exception):
    """Raised by route code; rendered by a single registered handler.

    Centralising the rendering is what keeps *every* error path the same shape,
    including the ones FastAPI generates on your behalf.
    """

    def __init__(
        self,
        *,
        status: int,
        title: str,
        detail: str,
        type_: str = "about:blank",
        headers: Mapping[str, str] | None = None,
        **extra: Any,
    ) -> None:
        super().__init__(detail)
        self.status = status
        self.title = title
        self.detail = detail
        self.type_ = type_
        self.headers = dict(headers or {})
        self.extra = extra

    def to_response(self, request: Request) -> JSONResponse:
        body: dict[str, Any] = {
            "type": self.type_,
            "title": self.title,
            "status": self.status,
            "detail": self.detail,
            "instance": str(request.url.path),
            **self.extra,
        }
        return JSONResponse(body, status_code=self.status, media_type=PROBLEM_JSON, headers=self.headers)


# --------------------------------------------------------------------------- #
# Content-addressed identity
# --------------------------------------------------------------------------- #
def canonical_json(payload: Any) -> str:
    """Deterministic JSON: sorted keys, no incidental whitespace.

    Both properties are load-bearing. Without ``sort_keys`` two semantically
    identical requests hash differently depending on dict iteration order;
    without compact separators the digest changes if a client pretty-prints.
    """
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def compute_dataset_id(*, generator: str, version: int, params: Mapping[str, Any]) -> str:
    """``{generator}-v{version}-{digest16}`` -- the real juniper-data scheme.

    The generator and version are carried in the clear so an id stays legible in
    a log line; the digest makes it collision-resistant and reproducible. Note
    that identity depends on *inputs*, not on when the request arrived, which is
    what makes a re-POST naturally idempotent.
    """
    digest = hashlib.sha256(
        canonical_json({"generator": generator, "version": version, "params": dict(params)}).encode("utf-8")
    ).hexdigest()
    return f"{generator}-v{version}-{digest[:16]}"


# --------------------------------------------------------------------------- #
# Domain
# --------------------------------------------------------------------------- #
class DatasetCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generator: Literal["spiral", "two_moons", "checkerboard"]
    version: int = Field(default=1, ge=1, le=999)
    params: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)


class TagUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tags: list[str] = Field(max_length=50)


@dataclass(slots=True)
class Dataset:
    id: str
    generator: str
    version: int
    params: dict[str, Any]
    tags: list[str]
    artifact: bytes
    created_at: float
    n_samples: int = 0

    def metadata(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "generator": self.generator,
            "version": self.version,
            "params": self.params,
            "tags": sorted(self.tags),
            "n_samples": self.n_samples,
            "size_bytes": len(self.artifact),
            "created_at": self.created_at,
        }


def metadata_etag(dataset: Dataset) -> str:
    """A *strong* validator: a hash of the exact representation we would send.

    Because it covers the mutable fields too, changing a tag necessarily changes
    the ETag -- which is the property If-Match relies on to detect a stale write.
    """
    digest = hashlib.sha256(canonical_json(dataset.metadata()).encode("utf-8")).hexdigest()
    return f'"{digest[:32]}"'


def artifact_etag(dataset: Dataset) -> str:
    return f'"{hashlib.sha256(dataset.artifact).hexdigest()[:32]}"'


def _synthesize_artifact(dataset_id: str, n_samples: int) -> bytes:
    """Deterministic stand-in for a real NPZ payload (keeps the example dependency-free)."""
    seed = hashlib.sha256(dataset_id.encode("utf-8")).digest()
    return (seed * ((n_samples // len(seed)) + 1))[:n_samples]


# --------------------------------------------------------------------------- #
# Entity-tag comparison (RFC 9110 section 8.8.3, section 13.1.1, section 13.1.2)
# --------------------------------------------------------------------------- #
def parse_etag_list(value: str | None) -> list[str] | None:
    """Split an If-Match / If-None-Match field value. ``None`` means the header was absent."""
    if value is None:
        return None
    return [item.strip() for item in value.split(",") if item.strip()]


def _opaque(etag: str) -> str:
    return etag[2:] if etag.startswith("W/") else etag


def strong_match(candidates: list[str], current: str) -> bool:
    """If-Match uses the *strong* comparison: a weak tag never matches."""
    if "*" in candidates:
        return True
    return any(c == current and not c.startswith("W/") for c in candidates)


def weak_match(candidates: list[str], current: str) -> bool:
    """If-None-Match uses the *weak* comparison, so W/"x" matches "x"."""
    if "*" in candidates:
        return True
    return any(_opaque(c) == _opaque(current) for c in candidates)


# --------------------------------------------------------------------------- #
# Keyset cursors
# --------------------------------------------------------------------------- #
def encode_cursor(after_id: str) -> str:
    raw = canonical_json({"after": after_id}).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def decode_cursor(cursor: str) -> str:
    """Opaque to the client: the encoding is ours to change without breaking anyone."""
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded.encode("ascii")))
        after = payload["after"]
        if not isinstance(after, str):
            raise TypeError("after must be a string")
    except (ValueError, KeyError, TypeError, binascii.Error) as exc:
        raise ProblemException(
            status=400,
            title="Malformed cursor",
            detail="The cursor parameter is not a cursor previously issued by this API.",
            type_="https://errors.example.com/bad-cursor",
        ) from exc
    return after


# --------------------------------------------------------------------------- #
# Server
# --------------------------------------------------------------------------- #
def create_app() -> FastAPI:
    app = FastAPI(title="Dataset Registry")
    app.state.datasets = {}

    @app.exception_handler(ProblemException)
    async def _problem_handler(request: Request, exc: ProblemException) -> JSONResponse:
        return exc.to_response(request)

    @app.exception_handler(RequestValidationError)
    async def _validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        # Without this, FastAPI emits {"detail": [ ... ]} -- a second, undocumented
        # error shape that clients must special-case. RFC 9457 permits extension
        # members, so the field-level detail survives under "errors".
        return ProblemException(
            status=422,
            title="Request validation failed",
            detail="The request body or parameters did not satisfy the schema.",
            type_="https://errors.example.com/validation-failed",
            errors=json.loads(json.dumps(exc.errors(), default=str)),
        ).to_response(request)

    def _require(dataset_id: str) -> Dataset:
        dataset: Dataset | None = app.state.datasets.get(dataset_id)
        if dataset is None:
            raise ProblemException(
                status=404,
                title="Dataset not found",
                detail=f"No dataset with id {dataset_id!r}.",
                type_="https://errors.example.com/dataset-not-found",
            )
        return dataset

    @app.post("/v1/datasets", status_code=201)
    async def create_dataset(body: DatasetCreate) -> JSONResponse:
        dataset_id = compute_dataset_id(generator=body.generator, version=body.version, params=body.params)
        existing: Dataset | None = app.state.datasets.get(dataset_id)
        if existing is not None:
            # Content-addressing makes creation idempotent for free. Returning 200
            # rather than 201 lets the client tell "I created this" from "this
            # already existed" -- a distinction the real service throws away.
            return JSONResponse(
                existing.metadata(),
                status_code=200,
                headers={"Location": f"/v1/datasets/{dataset_id}", "ETag": metadata_etag(existing)},
            )

        n_samples = int(body.params.get("n_samples", 512))
        dataset = Dataset(
            id=dataset_id,
            generator=body.generator,
            version=body.version,
            params=dict(body.params),
            tags=list(body.tags),
            artifact=_synthesize_artifact(dataset_id, n_samples),
            created_at=time.time(),
            n_samples=n_samples,
        )
        app.state.datasets[dataset_id] = dataset
        return JSONResponse(
            dataset.metadata(),
            status_code=201,
            headers={"Location": f"/v1/datasets/{dataset_id}", "ETag": metadata_etag(dataset)},
        )

    @app.get("/v1/datasets")
    async def list_datasets(
        request: Request,
        limit: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
        cursor: str | None = None,
    ) -> JSONResponse:
        # Keyset pagination sorts by a UNIQUE, TOTAL key. A non-unique sort key
        # (created_at alone, say) is the classic keyset bug: rows sharing a
        # timestamp straddle the page boundary and get skipped or repeated.
        ordered = sorted(app.state.datasets.values(), key=lambda d: d.id)
        if cursor is not None:
            after = decode_cursor(cursor)
            ordered = [d for d in ordered if d.id > after]

        page = ordered[:limit]
        has_more = len(ordered) > limit
        headers: dict[str, str] = {"Cache-Control": "no-store"}
        if has_more and page:
            # RFC 8288 web linking: the client follows this rather than
            # constructing offsets, so the scheme can change without a break.
            next_url = f"{request.url.path}?limit={limit}&cursor={encode_cursor(page[-1].id)}"
            headers["Link"] = f'<{next_url}>; rel="next"'
        return JSONResponse({"items": [d.metadata() for d in page], "count": len(page)}, headers=headers)

    @app.get("/v1/datasets/{dataset_id}")
    async def get_dataset(
        dataset_id: str,
        if_none_match: Annotated[str | None, Header(alias="If-None-Match")] = None,
    ) -> Response:
        dataset = _require(dataset_id)
        etag = metadata_etag(dataset)
        headers = {
            "ETag": etag,
            "Cache-Control": METADATA_CACHE_CONTROL,
            "Vary": "Accept",
            # A real ASGI server adds Date; ASGITransport does not, and RFC 9110
            # section 15.4.5 lists it among the fields a 304 must carry.
            "Date": formatdate(usegmt=True),
        }

        candidates = parse_etag_list(if_none_match)
        if candidates is not None and weak_match(candidates, etag):
            # 304 is terminated by the end of the header section: no content.
            return Response(status_code=304, headers=headers)

        return JSONResponse(dataset.metadata(), headers=headers)

    @app.get("/v1/datasets/{dataset_id}/artifact")
    async def get_artifact(
        dataset_id: str,
        if_none_match: Annotated[str | None, Header(alias="If-None-Match")] = None,
    ) -> Response:
        dataset = _require(dataset_id)
        etag = artifact_etag(dataset)
        headers = {
            "ETag": etag,
            "Cache-Control": ARTIFACT_CACHE_CONTROL,
            "Vary": "Accept",
            "Date": formatdate(usegmt=True),
            "Content-Disposition": f'attachment; filename="{dataset_id}.npz"',
        }
        candidates = parse_etag_list(if_none_match)
        if candidates is not None and weak_match(candidates, etag):
            return Response(status_code=304, headers=headers)
        return Response(dataset.artifact, media_type="application/octet-stream", headers=headers)

    @app.patch("/v1/datasets/{dataset_id}/tags")
    async def update_tags(
        dataset_id: str,
        body: TagUpdate,
        if_match: Annotated[str | None, Header(alias="If-Match")] = None,
    ) -> JSONResponse:
        dataset = _require(dataset_id)
        current = metadata_etag(dataset)

        candidates = parse_etag_list(if_match)
        if candidates is None:
            # 428 rather than 400: the request is well-formed, it is merely
            # unconditional, and the fix is for the client to add a precondition.
            raise ProblemException(
                status=428,
                title="Precondition Required",
                detail="PATCH requires an If-Match header carrying the ETag you last read.",
                type_="https://errors.example.com/precondition-required",
                headers={"ETag": current},
            )
        if not strong_match(candidates, current):
            raise ProblemException(
                status=412,
                title="Precondition Failed",
                detail="The dataset changed since you read it. Re-read it, reapply your change, and retry.",
                type_="https://errors.example.com/precondition-failed",
                headers={"ETag": current},
            )

        dataset.tags = list(body.tags)
        return JSONResponse(
            dataset.metadata(),
            headers={"ETag": metadata_etag(dataset), "Cache-Control": METADATA_CACHE_CONTROL, "Vary": "Accept"},
        )

    return app
```

<!-- example-file: test_conditional_datasets.py -->
```python
"""Tests for conditional_datasets.py.

The headline test is ``test_lost_update_is_prevented_by_if_match``: it is the
whole reason optimistic concurrency exists, and it is the scenario the real
service silently gets wrong.
"""

from __future__ import annotations

from typing import Any

import httpx
import pytest

from conditional_datasets import compute_dataset_id, create_app, decode_cursor, encode_cursor

SPIRAL: dict[str, Any] = {
    "generator": "spiral",
    "version": 1,
    "params": {"n_samples": 512, "noise": 0.05, "seed": 42},
    "tags": ["baseline"],
}


def client_for(app: Any) -> httpx.AsyncClient:
    # httpx 0.28 removed AsyncClient(app=...); ASGITransport drives the app in-process.
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


# --------------------------------------------------------------------------- #
# 1. Content-addressed identity
# --------------------------------------------------------------------------- #
def test_identity_depends_only_on_generator_version_and_params() -> None:
    base = compute_dataset_id(generator="spiral", version=1, params={"n_samples": 512, "seed": 42})
    reordered = compute_dataset_id(generator="spiral", version=1, params={"seed": 42, "n_samples": 512})
    other_params = compute_dataset_id(generator="spiral", version=1, params={"n_samples": 512, "seed": 43})
    other_version = compute_dataset_id(generator="spiral", version=2, params={"n_samples": 512, "seed": 42})

    assert base == reordered  # canonical JSON: key order cannot matter
    assert base != other_params
    assert base != other_version
    assert base.startswith("spiral-v1-")
    assert len(base.rsplit("-", 1)[1]) == 16


@pytest.mark.asyncio
async def test_recreating_the_same_dataset_is_idempotent() -> None:
    app = create_app()
    async with client_for(app) as client:
        first = await client.post("/v1/datasets", json=SPIRAL)
        second = await client.post("/v1/datasets", json=SPIRAL)

    assert first.status_code == 201
    assert second.status_code == 200  # already existed -- a distinction worth signalling
    assert first.json()["id"] == second.json()["id"]
    assert first.headers["etag"] == second.headers["etag"]
    assert len(app.state.datasets) == 1


# --------------------------------------------------------------------------- #
# 2. Conditional GET
# --------------------------------------------------------------------------- #
@pytest.mark.asyncio
async def test_if_none_match_returns_304_with_no_body() -> None:
    app = create_app()
    async with client_for(app) as client:
        created = await client.post("/v1/datasets", json=SPIRAL)
        dataset_id = created.json()["id"]

        full = await client.get(f"/v1/datasets/{dataset_id}")
        etag = full.headers["etag"]
        revalidated = await client.get(f"/v1/datasets/{dataset_id}", headers={"If-None-Match": etag})

    assert full.status_code == 200
    assert etag.startswith('"') and etag.endswith('"')  # strong validator, quoted
    assert full.headers["cache-control"] == "public, max-age=0, must-revalidate"

    assert revalidated.status_code == 304
    assert revalidated.content == b""
    # RFC 9110 section 15.4.5: a 304 MUST carry the fields a 200 would have.
    assert revalidated.headers["etag"] == etag
    assert revalidated.headers["cache-control"] == full.headers["cache-control"]
    assert revalidated.headers["vary"] == "Accept"
    assert "date" in revalidated.headers


@pytest.mark.asyncio
async def test_if_none_match_accepts_a_weak_validator_and_a_wildcard() -> None:
    """If-None-Match uses the weak comparison, so W/"x" matches "x"."""
    app = create_app()
    async with client_for(app) as client:
        dataset_id = (await client.post("/v1/datasets", json=SPIRAL)).json()["id"]
        etag = (await client.get(f"/v1/datasets/{dataset_id}")).headers["etag"]

        weak = await client.get(f"/v1/datasets/{dataset_id}", headers={"If-None-Match": f"W/{etag}"})
        wildcard = await client.get(f"/v1/datasets/{dataset_id}", headers={"If-None-Match": "*"})
        listed = await client.get(f"/v1/datasets/{dataset_id}", headers={"If-None-Match": f'"stale", {etag}'})
        stale = await client.get(f"/v1/datasets/{dataset_id}", headers={"If-None-Match": '"stale"'})

    assert weak.status_code == 304
    assert wildcard.status_code == 304
    assert listed.status_code == 304  # matches any member of the list
    assert stale.status_code == 200  # no match -> full representation


@pytest.mark.asyncio
async def test_artifact_is_immutable_and_conditionally_cacheable() -> None:
    app = create_app()
    async with client_for(app) as client:
        dataset_id = (await client.post("/v1/datasets", json=SPIRAL)).json()["id"]
        artifact = await client.get(f"/v1/datasets/{dataset_id}/artifact")
        revalidated = await client.get(
            f"/v1/datasets/{dataset_id}/artifact", headers={"If-None-Match": artifact.headers["etag"]}
        )

    assert artifact.status_code == 200
    assert artifact.headers["content-type"] == "application/octet-stream"
    assert artifact.headers["content-disposition"] == f'attachment; filename="{dataset_id}.npz"'
    # "immutable" is only honest because the id is a hash of the inputs.
    assert artifact.headers["cache-control"] == "public, max-age=31536000, immutable"
    assert len(artifact.content) == 512

    assert revalidated.status_code == 304
    assert revalidated.content == b""


# --------------------------------------------------------------------------- #
# 3. THE HEADLINE TEST: the lost update, prevented
# --------------------------------------------------------------------------- #
@pytest.mark.asyncio
async def test_lost_update_is_prevented_by_if_match() -> None:
    """Two clients read the same version and both try to write.

    Interleaving, made explicit:

        A: GET  -> tags=["baseline"], ETag=E0
        B: GET  -> tags=["baseline"], ETag=E0      (B now holds a snapshot of E0)
        A: PATCH If-Match: E0 -> 200, tags=["baseline","approved"], ETag=E1
        B: PATCH If-Match: E0 -> 412               (B's view is stale)
        *: GET  -> A's write survived

    Without the precondition, B's PATCH would succeed and silently erase A's
    change -- no error, no log line, no way for A to find out.
    """
    app = create_app()
    async with client_for(app) as client:
        dataset_id = (await client.post("/v1/datasets", json=SPIRAL)).json()["id"]

        # Both clients read the same representation.
        read_a = await client.get(f"/v1/datasets/{dataset_id}")
        read_b = await client.get(f"/v1/datasets/{dataset_id}")
        etag_a = read_a.headers["etag"]
        etag_b = read_b.headers["etag"]
        assert etag_a == etag_b  # identical state -> identical validator

        # Client A writes first and wins.
        write_a = await client.patch(
            f"/v1/datasets/{dataset_id}/tags",
            json={"tags": ["baseline", "approved"]},
            headers={"If-Match": etag_a},
        )
        assert write_a.status_code == 200
        assert write_a.headers["etag"] != etag_a  # the validator moved

        # Client B writes second, holding the now-stale validator.
        write_b = await client.patch(
            f"/v1/datasets/{dataset_id}/tags",
            json={"tags": ["baseline", "rejected"]},
            headers={"If-Match": etag_b},
        )
        assert write_b.status_code == 412
        assert write_b.headers["content-type"].startswith("application/problem+json")
        # The 412 carries the current ETag so B can re-read, reapply, and retry.
        assert write_b.headers["etag"] == write_a.headers["etag"]

        # A's write survived; B's was rejected, not merged and not silently dropped.
        final = await client.get(f"/v1/datasets/{dataset_id}")

    assert final.json()["tags"] == ["approved", "baseline"]
    assert final.headers["etag"] == write_a.headers["etag"]


@pytest.mark.asyncio
async def test_b_can_recover_by_re_reading() -> None:
    """The 412 is not a dead end: re-read, reapply, retry against the fresh ETag."""
    app = create_app()
    async with client_for(app) as client:
        dataset_id = (await client.post("/v1/datasets", json=SPIRAL)).json()["id"]
        stale = (await client.get(f"/v1/datasets/{dataset_id}")).headers["etag"]

        await client.patch(
            f"/v1/datasets/{dataset_id}/tags", json={"tags": ["approved"]}, headers={"If-Match": stale}
        )
        rejected = await client.patch(
            f"/v1/datasets/{dataset_id}/tags", json={"tags": ["rejected"]}, headers={"If-Match": stale}
        )
        fresh = rejected.headers["etag"]
        retried = await client.patch(
            f"/v1/datasets/{dataset_id}/tags",
            json={"tags": ["approved", "reviewed"]},
            headers={"If-Match": fresh},
        )

    assert rejected.status_code == 412
    assert retried.status_code == 200
    assert retried.json()["tags"] == ["approved", "reviewed"]


# --------------------------------------------------------------------------- #
# 4. PATCH without If-Match
# --------------------------------------------------------------------------- #
@pytest.mark.asyncio
async def test_patch_without_if_match_is_428() -> None:
    app = create_app()
    async with client_for(app) as client:
        dataset_id = (await client.post("/v1/datasets", json=SPIRAL)).json()["id"]
        response = await client.patch(f"/v1/datasets/{dataset_id}/tags", json={"tags": ["nope"]})
        unchanged = await client.get(f"/v1/datasets/{dataset_id}")

    assert response.status_code == 428  # RFC 6585 section 3
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["title"] == "Precondition Required"
    assert "etag" in response.headers  # hands the client what it needs to succeed
    assert unchanged.json()["tags"] == ["baseline"]  # nothing was written


@pytest.mark.asyncio
async def test_weak_validator_is_rejected_by_if_match() -> None:
    """If-Match requires the strong comparison: a weak tag must not authorise a write."""
    app = create_app()
    async with client_for(app) as client:
        dataset_id = (await client.post("/v1/datasets", json=SPIRAL)).json()["id"]
        etag = (await client.get(f"/v1/datasets/{dataset_id}")).headers["etag"]
        response = await client.patch(
            f"/v1/datasets/{dataset_id}/tags", json={"tags": ["x"]}, headers={"If-Match": f"W/{etag}"}
        )

    assert response.status_code == 412


# --------------------------------------------------------------------------- #
# 5. Keyset pagination
# --------------------------------------------------------------------------- #
def test_cursor_round_trips() -> None:
    assert decode_cursor(encode_cursor("spiral-v1-abcdef0123456789")) == "spiral-v1-abcdef0123456789"
    assert "=" not in encode_cursor("x")  # padding stripped, still decodable


@pytest.mark.asyncio
async def test_keyset_pagination_covers_the_collection_exactly_once() -> None:
    app = create_app()
    async with client_for(app) as client:
        expected = set()
        for seed in range(11):
            body = {**SPIRAL, "params": {**SPIRAL["params"], "seed": seed}}
            expected.add((await client.post("/v1/datasets", json=body)).json()["id"])

        seen: list[str] = []
        pages = 0
        url: str | None = "/v1/datasets?limit=3"
        while url is not None:
            page = await client.get(url)
            assert page.status_code == 200
            pages += 1
            seen.extend(item["id"] for item in page.json()["items"])

            link = page.headers.get("link")
            if link is None:
                url = None
            else:
                assert link.endswith('; rel="next"')
                url = link[1 : link.index(">")]

    assert len(expected) == 11
    assert pages == 4  # 3 + 3 + 3 + 2
    assert len(seen) == len(set(seen))  # no duplicates
    assert set(seen) == expected  # no gaps
    assert seen == sorted(seen)  # walked in key order


@pytest.mark.asyncio
async def test_link_header_is_absent_on_an_exactly_full_final_page() -> None:
    """The boundary case: 6 items at limit=3 must not advertise an empty page 3."""
    app = create_app()
    async with client_for(app) as client:
        for seed in range(6):
            await client.post("/v1/datasets", json={**SPIRAL, "params": {**SPIRAL["params"], "seed": seed}})

        first = await client.get("/v1/datasets?limit=3")
        cursor = first.headers["link"]
        second = await client.get(cursor[1 : cursor.index(">")])

    assert "link" in first.headers
    assert len(second.json()["items"]) == 3
    assert "link" not in second.headers


@pytest.mark.asyncio
async def test_a_garbage_cursor_is_a_problem_not_a_500() -> None:
    app = create_app()
    async with client_for(app) as client:
        response = await client.get("/v1/datasets?cursor=not-a-real-cursor")

    assert response.status_code == 400
    assert response.headers["content-type"].startswith("application/problem+json")


# --------------------------------------------------------------------------- #
# 6. One error model everywhere
# --------------------------------------------------------------------------- #
REQUIRED_MEMBERS = {"type", "title", "status", "detail", "instance"}


@pytest.mark.asyncio
async def test_not_found_carries_every_standard_problem_member() -> None:
    app = create_app()
    async with client_for(app) as client:
        response = await client.get("/v1/datasets/spiral-v1-0000000000000000")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert REQUIRED_MEMBERS <= set(body)
    assert body["status"] == 404
    assert body["instance"] == "/v1/datasets/spiral-v1-0000000000000000"
    assert all(isinstance(body[m], str) for m in REQUIRED_MEMBERS - {"status"})


@pytest.mark.asyncio
async def test_framework_validation_errors_use_the_same_shape() -> None:
    """FastAPI's default 422 is a *different* body shape; the handler unifies it."""
    app = create_app()
    async with client_for(app) as client:
        bad_enum = await client.post("/v1/datasets", json={**SPIRAL, "generator": "not_a_generator"})
        bad_extra = await client.post("/v1/datasets", json={**SPIRAL, "typo_field": 1})
        bad_query = await client.get("/v1/datasets?limit=99999")

    for response in (bad_enum, bad_extra, bad_query):
        assert response.status_code == 422
        assert response.headers["content-type"].startswith("application/problem+json")
        assert REQUIRED_MEMBERS <= set(response.json())
    assert bad_enum.json()["errors"]  # field detail preserved as an extension member
```

Run this example, and the other two, with the harness described in [Appendix D](#appendix-d--running-the-examples).

## Part III — Library and SDK API Design

### III.1 What Part III Covers

#### Overview

Parts I and II dealt with APIs reached over a wire. This part deals with the API another engineer
reaches by typing `import`: the public surface of a Python package — which names exist, what shape
they have, what they raise, how they change, and what a type checker downstream can see of any of it.

#### Background

Almost every property flips when the boundary moves in-process. Caller and callee now share a heap, an
exception stack, and an interpreter that dies together.

| Property                       | Network API                                                                            | In-process library API                                                                        |
|--------------------------------|----------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| Failure mode                   | The *outcome* can be lost: the peer may have applied the request and lost the response | The outcome always arrives — a return or an exception — but the *effect* can still be partial |
| Unit of versioning             | The deployed service; one version serves all callers                                   | The installed distribution; every caller may pin a different one                              |
| Caller visibility of internals | None — only the wire format is reachable                                               | Complete — every module, attribute, and closure                                               |
| Compatibility enforcement      | The server validates and rejects                                                       | Nothing validates; a wrong call is a `TypeError` at best                                      |
| Cost of a call                 | Milliseconds — hundreds of microseconds at best, and observable                        | Nanoseconds, unobservable, so callers make millions                                           |

Two of those rows are usually stated more strongly than they survive. The in-process failure mode is
often given as "total or none", and it is not: a method that mutates two attributes and then raises
leaves half its work done, and exception safety is a long-standing in-process hazard. What you never
lose in-process is the *answer* — no partition can hide whether the call happened. The cost row is
understated by orders of magnitude at least as often. Measured here on CPython 3.13.13: an in-process
method call is ~60 ns, and a warm loopback HTTP GET with no TLS is ~615 µs per call over 2,000 calls —
four orders of magnitude before a real network is involved.

The third row shapes Python specifically. With no `private` keyword there is no enforcement:
`_lazy_cache` in `juniper-observability` is reachable — this section's research imported it directly —
and so is every function a package chose not to list in `__all__`.

What Python has instead is a social contract backed by tooling: a naming convention (the leading
underscore), a declaration (`__all__`), a marker file that tells type checkers to trust your
annotations (`py.typed`), and linters that complain when a consumer crosses the line. None stops
anyone. Together they suffice, because the real enforcement is that a consumer who reaches past the
contract owns the breakage.

The worked examples are the Juniper client libraries and shared packages — unusually good material
because three sibling HTTP clients (`juniper-data-client`, `juniper-cascor-client`,
`juniper-recurrence-client`) were written by one author against one base library and solved the same
problems three different ways, and because the two shared packages (`juniper-service-core`,
`juniper-observability`) took opposite positions on the most consequential decision in package design:
what a bare `import` costs.

#### Judgement Calls

The recurring question is how much of your freedom to trade for your callers' stability. Every
mechanism below buys the caller something and costs the author something; no setting of those dials is
right for all libraries.

#### Tradeoffs

Breadth of surface against cost of change. Every name you export is a name you must keep working;
every name you do not export is one a determined consumer will import anyway, then complain about when
it moves.

#### Best Practices

Decide in writing what is public before the first release. Retrofitting a boundary onto a package
whose consumers already reach everywhere is far harder than declaring one on day one.

#### Common Failure Modes

The surface that was never designed: `__init__.py` re-exports whatever was convenient, every module is
importable, nothing is underscored, and the first refactor breaks three downstream repositories.

#### Error Handling

Part III treats errors as part of the surface. An exception type is as much a published contract as a
function signature, and III.4 is devoted to it.

---

### III.2 Designing the Public Surface

#### Overview

The public surface is the set of names a consumer may rely on, plus the guarantee that importing your
package is cheap and side-effect-free. Both are design decisions, and the second is routinely
forgotten until someone measures a CLI taking 400 ms to print `--help`.

#### Background

Python's boundary markers, precisely. **The leading underscore** — `_name`, `self._attr`,
`_module.py` — means "not part of the contract". Nothing enforces it; `from pkg._internal import X`
works. Its teeth are that linters flag it and that you may break such a consumer without a major bump.
**`__all__`** controls exactly one language behaviour: which names `from pkg import *` binds. It is
also read by documentation generators, by linters deciding whether a re-export is "unused", and by
static analysis wanting your intended surface. It does not restrict `import`, hide anything, or affect
`getattr`.

That last point deserves demonstration. Against `juniper-observability` 0.4.0 on CPython 3.13.13:

```python
import juniper_observability
from juniper_observability import prometheus_helpers
from juniper_observability.testing import reset_prometheus_registry

ns: dict[str, object] = {}
exec("from juniper_observability import *", ns)
assert set(ns) - {"__builtins__"} == set(juniper_observability.__all__)  # exactly 29 names
assert callable(reset_prometheus_registry)               # not in __all__, imports fine
assert isinstance(prometheus_helpers._lazy_cache, dict)  # module-private, still reachable
```

All three hold. `__all__` gave the star-import an exact 29-name result — including `__version__`,
which the default rule (bind every non-underscore global) would have skipped — and prevented nothing
else. `reset_prometheus_registry` is a deliberate submodule-only surface
(`juniper_observability/testing.py`, absent from the package `__all__` at
`juniper_observability/__init__.py:52-90`); `_lazy_cache` is a genuine private
(`juniper_observability/prometheus_helpers.py:68`).

#### Module Layout and Re-Exports

Implementation in submodules, curated re-exports in `__init__.py`. This lets you move code between
modules without moving names — the main compatibility benefit of having a root surface at all.

`juniper-observability` does it at two levels: `juniper_observability/middleware/__init__.py` gathers
`metrics_auth.py`, `prometheus.py`, and `request_id.py` into one namespace with its own eight-name
`__all__`, and the package root re-exports from that (`juniper_observability/__init__.py:33-42`). A
consumer writes `from juniper_observability import RequestIdMiddleware` and never learns the class
lives in `middleware/request_id.py`; moving it is a non-event. The cost: two `__all__` lists must
agree, and a name added to the inner one but not the outer is silently invisible at the root. Nothing
checks this.

`juniper-data-client` shows the deliberate *sub*-surface:
`juniper_data_client/testing/__init__.py:39-45` exports `FakeDataClient` and four generators, and the
root re-exports none of them — so a production process that writes `import juniper_data_client` never
gets `FakeDataClient` in its namespace and never executes the test double's module body. Be precise
about what that buys: it is surface discipline, not import cost. `numpy` arrives regardless, because
`client.py:15` and `contract.py:27` both `import numpy as np` and the root imports both modules
(`__init__.py:7-8`). Verified: after a bare `import juniper_data_client`, `"numpy" in sys.modules` is
`True` and `"juniper_data_client.testing" in sys.modules` is `False`.

#### Eager and Lazy Imports, and PEP 562

Every top-level import in your `__init__.py` runs on your consumer's first import, transitively. If
you eagerly import `pydantic`, every consumer pays for `pydantic`, including one that wanted a
constant.

[PEP 562](https://peps.python.org/pep-0562/) — "Module `__getattr__` and `__dir__`", added in 3.7 and
cited by name in CPython's own documentation data (`pydoc_data/topics.py:641` in the 3.13 standard
library) — is the escape hatch. A module-level `__getattr__(name)` is called when normal attribute
lookup on the module fails; `__dir__()` controls `dir(module)`. Together they let a package advertise
names it has not imported.

#### Import-Time Side Effects

A module body that only defines things is safe to import. One that reads environment variables, opens
files, connects to services, or constructs an application is not — the consumer cannot control when it
happens, pass different inputs, or avoid it while importing anything else.

`juniper-data` carries the fixed version in its own docstring. The service exposes a factory plus a
cached accessor (`juniper_data/api/app.py:171-172`):

```python
@functools.lru_cache(maxsize=1)
def get_app() -> FastAPI:
    return create_app()
```

with the rationale at `juniper_data/api/app.py:185-188`: it "replaces the previous module-level
`app = create_app()` (CLN-JD-03), which read environment variables and registered middleware at import
time". That is the failure class in one sentence — a test wanting different settings could not have
them, because the app was built by the time the `import` returned. Import time is a user-facing
performance property, and `python -X importtime` measures it.

#### Optional Dependencies and Where to Put the Guard

The extras pattern (`pip install pkg[prometheus]`) declares a dependency the package can work without.
The design question is where the *import* goes, and all three placements appear in these repositories.

**Module top, with a fallback** — `juniper_service_core/dependency_floors.py:37-41`:

```python
try:  # ``packaging`` is near-universal (pip depends on it) but not a hard dep here.
    from packaging.version import InvalidVersion, Version
except ModuleNotFoundError:  # pragma: no cover
    Version = None  # type: ignore[assignment]
    InvalidVersion = Exception  # type: ignore[assignment,misc]
```

Cost paid once; `_below` then degrades to a numeric-tuple comparison (`dependency_floors.py:89`, built
by `_vtuple` at `:73-77`) rather than failing. Right when a genuine fallback exists — and note this is
a *swallow*, one of the narrow legitimate kinds III.4 enumerates: the failure is not the caller's
concern and the `except` wraps exactly the one import that may fail.

**Function body, raising on use** — `juniper-observability` throughout. `get_prometheus_app` imports
`prometheus_client` inside itself (`juniper_observability/prometheus.py:24`), with the consequence in
the module docstring (`prometheus.py:3-7`): "the package can be installed without the `[prometheus]`
extra and these helpers will simply raise at call time". The four collector helpers follow
(`prometheus_helpers.py:133`, `:193`, rationale `:37-40`).

**Function body, degrading on absence** — `juniper-cascor-client` uses the same placement for the
opposite outcome (`juniper_cascor_client/observability.py:52-55`): `ImportError` returns `None`, the
caller checks for `None` (`:109-111`), and the package emits its structured warning without the metric.
The docstring makes this the contract (`observability.py:10-13`): consumers skipping the extra "still
get the structured log line and all validation behaviour; they just don't get the metric."

The tradeoff is early-and-clear against importable-at-all. A module-top guard fails at import with a
traceback pointing at your package — the best possible diagnostic — but fails even for the consumer
who was never going to touch that path. A function-body guard always imports, at the price of
deferring the error to where the traceback is less obvious and the failure may be in production.

#### The Centrepiece: Two Opposite Strategies, Measured

`juniper-service-core` 0.5.1 and `juniper-observability` 0.4.0 share a repository, an author, and a
release cadence, and chose opposite strategies.

**`juniper-service-core` — a full PEP 562 lazy surface.** The package docstring states the guarantee
(`juniper_service_core/__init__.py:10-16`): "Importing this top-level package pulls **no** third-party
runtime dependency. Only `__version__` is exposed eagerly... This is what lets the TestPyPI
publish-verify run a clean `--no-deps` `import juniper_service_core` check." Four parts: one eager
import of `__version__` (`:36`); a `TYPE_CHECKING` block importing all 60 lazy names (`:38-110`),
whose in-comment reason (`:39-43`) is that `TYPE_CHECKING` is `False` at run time so these never
execute, and their purpose is "to make every lazily-exported name resolvable for type checkers and for
CodeQL's `py/undefined-export` query, which cannot see through `__getattr__`"; a 61-entry `__all__`
(`:112-186`) and a 60-entry `_LAZY_EXPORTS` name-to-module map (`:193-266`) across twelve submodules;
and the two dunders (`:269-281`, `:284-285`), the second returning `sorted(__all__)`.

```python
def __getattr__(name: str):
    module_name = _LAZY_EXPORTS.get(name)
    if module_name is not None:
        from importlib import import_module

        return getattr(import_module(module_name), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
```

The `AttributeError` on the miss path is not decoration: a module `__getattr__` that returns `None` or
raises something else breaks `hasattr`, `dir`-based tooling, and `from ... import` diagnostics.

**`juniper-observability` — eager and flat.** Nine top-level `from ... import` statements
(`juniper_observability/__init__.py:17-50`) pulling 29 names out of nine submodules, all written
absolute (`from juniper_observability.middleware import ...`, never `from .middleware import ...`); a
29-name `__all__` (`:52-90`); no `__getattr__`, no `__dir__`, no `TYPE_CHECKING` block. Its
optional-dependency problem is solved one level down.

Measured on CPython 3.13.13, seven runs each, warm cache, via
`PYTHONPATH=<pkg-dir> python3 -X importtime -c "import <pkg>"`. The module count is the number of
**new top-level, non-underscore entries in `sys.modules`** after the import, against the same
interpreter's own startup baseline:

|                            | `import juniper_service_core`        | `import juniper_observability`                       |
|----------------------------|--------------------------------------|------------------------------------------------------|
| New top-level modules      | 2 (`juniper_service_core`, `typing`) | 66                                                   |
| Third-party pulled         | none                                 | `pydantic`, `pydantic_core`, `starlette`, `anyio`, … |
| `-X importtime` cumulative | 2.8 – 3.5 ms (median 2.9)            | 156 – 196 ms (median 165)                            |
| `len(dir(module))`         | 61 (exactly `__all__`)               | 47                                                   |

The module count is environment-sensitive; the ratio is not. An interpreter whose startup already
imports `typing` and the `collections` family reports 2 new modules for `juniper-service-core`, one
that does not reports 10, and a single extra optional Starlette dependency moves the observability
count between 66 and 67. The ratio holds at ~57× on the medians. Quote the ratio, re-measure the
absolutes in your own environment.

Touching one lazy name pays the deferred cost: after `_ = m.SettingsBase`, `pydantic_settings` is in
`sys.modules`. All five dependencies `juniper-service-core` declares mandatory
(`juniper-service-core/pyproject.toml:24-38`) are absent from a bare import, `numpy` included — its
deferral explained in-line at `pyproject.toml:33-36`.

Both are defensible; they optimise different things. `juniper-service-core` is a framework substrate
that many consumers import, some only for `__version__` or the stdlib-only launcher, and its
`--no-deps` check is a real release gate. `juniper-observability` is a middleware kit whose every
consumer immediately instantiates a Starlette middleware or a Pydantic model, so deferring `pydantic`
would defer nothing while costing a 60-entry hand-maintained map.

The lazy scheme's real costs, none hypothetical: `__all__`, `_LAZY_EXPORTS`, and the `TYPE_CHECKING`
block are three parallel lists with no test asserting they agree; a typo in `_LAZY_EXPORTS` becomes an
`AttributeError` at first use rather than an `ImportError` at import; and `dir()` returning exactly
`__all__` means `__file__`, `__doc__`, and `__name__` vanish from the REPL listing — honest about the
public surface, less honest about the module.

#### Judgement Calls

- **Must a bare import be dependency-free?** Only if something depends on that property.
  `juniper-service-core` has one: a publish step that installs with `--no-deps` and imports. Without a
  concrete consumer of the guarantee, the 60-entry map is maintenance without payoff.
- **How much to re-export at the root?** Enough that consumers never need a submodule path for
  ordinary work; not so much that the root is the union of everything.
- **Support `from pkg import *`?** You do not decide that — only whether it produces a sensible
  result. `__all__` makes it sensible and costs one list.

#### Tradeoffs

| Choice                 | Buys                                                    | Costs                                                      |
|------------------------|---------------------------------------------------------|------------------------------------------------------------|
| Eager imports          | Simplicity; errors at import; tools see reality         | Every consumer pays full import cost and every dependency  |
| PEP 562 lazy surface   | Fast, dependency-free import; `--no-deps` verifiability | Three parallel name lists; deferred `AttributeError`s      |
| Guard at module top    | Clear failure, one place                                | Unimportable without the optional dependency, for everyone |
| Guard in function body | Always importable                                       | Failure deferred to a call site, possibly in production    |

#### Best Practices

- Declare `__all__` in every module in the surface, and in every `__init__.py`. Underscore everything
  else; a package where nothing is underscored has not decided anything.
- Keep module bodies to definitions; expose a factory when something must be built.
- Going lazy? Keep a `TYPE_CHECKING` block — but for the right reason. Checkers do not break without
  it: mypy 2.1.0 honours a module-level `__getattr__` and resolves every name through it, to `Any`. On
  a lazy package with no such block, `--strict` passes on `from lazypkg import Widget, Wodget`, reveals
  both as `Any`, and flags neither the misspelling nor a wrong-typed call on the result. What you lose
  is precision and typo detection, not resolution. The block also feeds the analyses that genuinely
  cannot follow `__getattr__` — CodeQL's `py/undefined-export`, which is what the service-core comment
  scopes itself to — and costs nothing at run time.
- Run `python -X importtime -c "import yourpkg"` before and after any `__init__.py` change.

#### Common Failure Modes

- **Accidental re-export.** A convenience import at the top of `__init__.py` joins the surface the
  moment someone imports it from there, listed or not.
- **The drifted `__all__`.** A name removed from the module but left in `__all__` raises only on
  `import *`, so name-based test imports never catch it.
- **Import-time environment reads.** Configuration captured at import cannot be overridden, and
  presents as "my test's monkeypatch does nothing".
- **Lazy-map typos.** A wrong module string in `_LAZY_EXPORTS` raises at first attribute access, with
  a traceback pointing at the map rather than the caller.

#### Error Handling

A module `__getattr__` must raise `AttributeError` for unknown names — that is what `hasattr`,
`getattr(m, x, default)`, and `from m import x` rely on. `juniper_service_core/__init__.py:281` does
exactly this. Returning `None`, raising `KeyError`, or letting the underlying `ImportError` escape all
break callers in hard-to-diagnose ways, because the failure surfaces at an attribute access rather
than at an import.

#### Controversy: Lazy Module Surfaces versus Eager Imports

**That there is a dispute.** Whether a library should defer imports via PEP 562 is actively contested;
several large ecosystem packages adopted module `__getattr__` for exactly the reason
`juniper-service-core` gives, and others rejected it as complexity buying milliseconds.

**The camps.** *Lazy* holds that import time is a real, compounding cost — a CLI or test suite
importing a hundred packages pays every one serially before doing work — and that a library has no
business deciding its consumers can afford `pydantic`. *Eager* holds that an import graph should be
readable off the source, that deferred failures are worse failures, and that the fix for slow imports
is fewer dependencies, not later ones. A third camp — call it *generated-lazy* — accepts the lazy
position and rejects the hand-maintained map: derive the whole surface from one declaration instead of
writing it three times.

**The background.** The split hardened as scientific and web stacks grew heavy transitive trees and
Python CLIs became slow enough to notice. PEP 562 made the pattern respectable in 3.7; the friction is
that completion, static analyzers, and `dir()` assume the eager model, and that a checker following
`__getattr__` gets `Any` rather than a real type — which is what the `TYPE_CHECKING` block at
`juniper_service_core/__init__.py:38-110` restores.

**Generated-lazy — the mechanism.** The scientific-Python community's answer is
[`lazy_loader`](https://pypi.org/project/lazy-loader/) (0.5), whose project home *is* the spec it
implements, [SPEC 1](https://scientific-python.org/specs/spec-0001/). Its `attach_stub(package_name,
filename)` parses the `.pyi` stub sitting next to your `__init__.py` and returns, in its own docstring's
words, "`__getattr__, __dir__, __all__`" — all three derived from one file, which "allows static type
checkers to find imports, while still providing lazy loading at runtime". The package's README uses
scikit-image's `__init__.py` as its worked example. Adopt it and `juniper-service-core`'s three parallel
lists collapse into one stub, drift becomes a parse error rather than a silent miss, and the stub does
the job the hand-written `TYPE_CHECKING` block was doing — so both the headline lazy weakness and the
guardrail below dissolve.

The rebuttal is proportionality, and it is a real one. `lazy_loader` is a third-party runtime dependency
(it pulls `packaging`) added to solve a bookkeeping problem that a 60-name package has and a 6-name
package does not; the stub is still a second copy of the name list, merely one a tool reads; and a
package whose whole selling point is a dependency-free `--no-deps` import now has a dependency at the
top of its `__init__.py`. That last objection is decisive for `juniper-service-core` specifically and for
nobody else — which is exactly the shape of an argument you should check against your own package rather
than adopt wholesale.

**Lazy — strengths.** Measurably faster imports (here ~57× on medians); a `--no-deps` check that catches
a real packaging error class; and heavy dependencies that an extra *can* then make genuinely optional.
Note the scoping: a lazy import does not by itself make a declared dependency optional.
`juniper-service-core` declares all five of its dependencies mandatory and a plain `pip install` brings
all five — see III.8, which is where this distinction is worked out. Laziness buys import *cost*;
optionality is a `[project.optional-dependencies]` decision that laziness makes *possible*.

**Lazy — weaknesses.** Duplicated name lists with no consistency check; tracebacks routed through
`__getattr__`; circular-import problems move from import time to first use, where they are harder to
spot.

**Lazy — risks.** A renamed submodule breaks only the lazy path, only at run time — tests that never
touch the affected name stay green.

**Lazy — guardrails.** Write a test looping `getattr(pkg, name)` over `__all__`, and one asserting
`set(__all__) == set(_LAZY_EXPORTS) | {"__version__"}`. Neither exists in `juniper-service-core`
today. Keep `__dir__` and the `TYPE_CHECKING` block. Or skip all of that and generate the surface from
a stub with `lazy_loader.attach_stub`, which makes the consistency test unnecessary rather than absent
— the right move for a package with a large surface and no `--no-deps` guarantee to protect.

**Eager — strengths.** The import graph is the source; failures happen at import in one place with a
good traceback; every tool works without special handling.

**Eager — weaknesses.** Costs are unbounded and transitive, and a consumer cannot opt out. Optional
dependencies must be handled in function bodies instead.

**Eager — risks.** Import cost creeps: one convenience `from .x import Y` can pull a multi-megabyte
dependency into every consumer's process, invisibly to review.

**Eager — guardrails.** Pin import time in CI. A three-line test asserting `import yourpkg` leaves a
named heavy module out of `sys.modules` catches the creep.

**Recommendation** (as a recommendation): default to eager. Adopt PEP 562 when you can name the
consumer of the guarantee — a `--no-deps` verification step, a measured CLI startup budget, extras
that genuinely bifurcate your dependency tree. `juniper-service-core` can name one; most packages
cannot. If you do adopt it and the surface is large, generate it: hand-writing the third parallel list
is the part of the lazy position that has an off-the-shelf answer, and the only good reason to decline
that answer is the one `juniper-service-core` has.

---

### III.3 Naming, Signatures, and Ergonomics

#### Overview

A signature is a contract with three audiences: the reader of a call site, the type checker, and
future-you adding a parameter without breaking anyone. Most advice addresses only the first. The
compatibility properties are what make `*` a design tool rather than a style preference.

#### Background

Python has five parameter kinds, and the boundaries between them are the API decision:

```python
def f(pos_only, /, pos_or_kw, *args, kw_only, **kwargs):
    ...
```

The compatibility rules follow directly. **Positional parameters are ordered forever**: once a caller
may write `f(a, b)`, you can never insert before `b`, reorder, or rename `b` — only append.
**Keyword-only parameters are an unordered set**: add, reorder, and deprecate freely, since callers
name what they pass; only removal and semantic change break them. **Positional-only (`/`)** frees you
to rename, because no caller can name it. That asymmetry is the whole argument: `*` costs one
character and converts a frozen sequence into an extensible set.

#### Three Points on One Axis

The three clients, same author, same problem — pass a batch of tuning parameters to a POST — reached
three different answers.

**Worst: no signature at all.** `juniper_cascor_client/client.py:138` is
`def create_network(self, **kwargs: Any) -> Dict[str, Any]:`. The eleven real arguments —
`input_size`, `output_size`, `learning_rate`, `candidate_learning_rate`, `max_hidden_units`,
`candidate_pool_size`, `correlation_threshold`, `patience`, `candidate_epochs`, `output_epochs`,
`epochs_max` — exist only in the docstring (`:141-152`), three marked "(required)", and the body
forwards blind (`:154`, `json=kwargs`). The consequences are not stylistic: a type checker cannot
check anything, completion offers nothing, `create_network(input_sixe=2)` is valid Python that reaches
the server as an unknown field, and a missing required argument is a 422 at best rather than a
`TypeError`. The docstring cannot even drift *detectably*, because there is nothing to drift from.

**Middle: named, but positional.** `juniper_data_client/client.py:412-423`:

```python
def create_dataset(
    self,
    generator: str,
    params: Dict[str, Any],
    persist: bool = True,
    name: Optional[str] = None,
    description: Optional[str] = None,
    created_by: Optional[str] = None,
    parent_dataset_id: Optional[str] = None,
    tags: Optional[List[str]] = None,
    ttl_seconds: Optional[int] = None,
) -> Dict[str, Any]:
    ...
```

Named and typed — a large improvement. But all nine are positional-or-keyword, so
`create_dataset("spiral", {"seed": 42}, False)` is legal, and that third argument is the boolean trap
in its natural habitat. The order is now frozen: a tenth option can only be appended, and `persist`
can never move.

**Best: keyword-only.** `juniper_recurrence_client/client.py:291-310` — `train` opens with `*,` on
line 293 and takes sixteen keyword-only parameters; `crossval` (`:381-404`) takes twenty, the first of
which, `n_folds: int`, has no default and is therefore *required and keyword-only*. There is exactly
one way to call these: `client.train(name="equities", d=16, theta=0.75, ridge="gcv", readout="rff")`.
At twenty parameters this is load-bearing — a twenty-parameter positional signature is unreadable at
the call site and unchangeable at the definition. The cost is small: no positional shorthand, even for
the obvious first argument.

#### Closed Sets and Numeric-or-Sentinel Parameters

`Literal` is scarce across the five packages: ten occurrences in two of them. Seven are in
`juniper-recurrence-client` (the import at `client.py:16` plus six annotation sites, all in `train` and
`crossval`); the other three are in `juniper-observability`, where `health/models.py:17` imports it and
`:26` and `:34` use it for exactly what this subsection recommends — two closed status enums,
`Literal["healthy", "unhealthy", "degraded", "not_configured"]` on `DependencyStatus` and
`Literal["ready", "degraded", "not_ready"]` on `ReadinessResponse`. The other three packages have none.
A closed enum (`client.py:302`, repeated `:396`),
`readout: Optional[Literal["linear", "rff", "mlp"]] = None`, makes `readout="mpl"` a type error rather
than a server-side 422 or a silent default. And a genuine union of a number and a magic string
(`:301`, `:395`):

```python
ridge: Optional[Union[float, Literal["gcv"]]] = None
```

This is the shape normally botched as `Any` or `Union[float, str]`. `ridge="gvc"` is a type error
while `ridge=1e-3` and `ridge="gcv"` both check. Same for
`rff_gamma: Optional[Union[float, Literal["median"]]]` (`:304`, `:398`). For contrast,
`juniper_data_client/contract.py:41` returns a plain `str` documented (`:50-52`) as exactly
`"tabular"` or `"sequence"`, with the constants at `juniper_data_client/constants.py:291-292` —
`-> Literal["tabular", "sequence"]` is the same information in a form the checker can use.

#### Defaults, Sentinels, and the Omit-if-None Idiom

Mutable defaults are a bug: `def f(items=[])` evaluates `[]` once, at definition, and every mutating
call mutates the same list. The fix is `items=None` plus `items = [] if items is None else items`.
None of the five packages has this bug.

`None` as "unset" works whenever `None` is not a meaningful value. When it is — when a caller must
distinguish "set this to null" from "leave it alone" — you need a distinct sentinel object, because
`None` is now overloaded. These clients need only the simple case and use it to drive the omit-if-None
request-body idiom (`juniper_recurrence_client/client.py:317-339`):

```python
body: dict[str, Any] = {"dataset": _dataset_ref(...)}
if d is not None:
    body["d"] = d
if ridge is not None:
    body["ridge"] = ridge
```

An omitted key and an explicit `null` are different messages: omitted means "use your default", `null`
means "this value is null". Building the body by comprehension over all parameters would send
`{"d": null, ...}` and force the server to treat null as absent — foreclosing ever sending a real
null. The cost is a wall of near-identical `if` statements: eleven in `train` (`client.py:317-339`) and
twelve in `crossval` (`:410-439`). Genuinely ugly, and the right call.

#### `**kwargs` as an API Surface

`**kwargs` is legitimate for forwarding to a callable whose signature you do not own, and for
decorators; `juniper_recurrence_client/client.py:208` uses it correctly, forwarding to
`requests.Session.request`. Using it for parameters you *do* own, as `create_network` does, costs
static checking, completion, typo detection, required-argument enforcement, and the ability to learn
the API from the signature. It buys forward-compatibility with server fields the client has not been
updated for — a real benefit, and why the pattern persists in thin wrappers. The compromise keeping
most of both: name every parameter you know about and add `**extra: Any` for the rest.

#### Constructors, Factories, and Fail-Fast Validation

A constructor that does work is hard to test and impossible to configure differently; the alternatives
are a plain factory or a `classmethod`. `juniper-service-core` exposes a factory and makes it entirely
keyword-only (`juniper_service_core/app.py:23-29`):

```python
def create_app(
    *,
    title: str = "Juniper Service",
    version: str = "0.1.0",
    routers: Iterable[APIRouter] = (),
    lifespan: Lifespan[FastAPI] | None = None,
) -> FastAPI:
    ...
```

Note `routers: Iterable[APIRouter] = ()` — an immutable default that sidesteps the mutable-default
trap rather than working around it.

Where a constructor *is* the API, the question is how much it validates, and the three clients diverge
on the same input. **Fail fast**: `juniper_recurrence_client/client.py:183-184` raises
`JuniperRecurrenceConfigurationError` when the parsed `base_url` has no netloc, reasoning at
`:175-177` — a hostless URL "would otherwise normalize to a broken, hostless URL and fail opaquely on
the first request". **Silently normalise**: `juniper_data_client/client.py:180-201` performs the same
parse, strips a trailing `/` and a `/v1` suffix, validates nothing. **Barely normalise**:
`juniper_cascor_client/client.py:82-83` is `self.base_url = base_url.rstrip("/")` followed by
`self.api_url = f"{self.base_url}{API_VERSION_PATH}"`, with `API_VERSION_PATH = "/v1"`
(`juniper_cascor_client/constants.py:24`). No `/v1`-suffix strip, so a caller passing the API root
they see in the docs — `http://localhost:8200/v1` — sends every request to `/v1/v1/...`. One line from
the data-client version, and it turns a natural input into a 404 storm.

#### Resource Lifetime, Iteration, and Return Types

Anything holding a socket, file, or pool should be a **context manager**.
`juniper_recurrence_client/client.py:481-489` implements `close`/`__enter__`/`__exit__`;
`juniper_cascor_client/ws_client.py:436-444` implements `__aenter__`/`__aexit__`/`__aiter__`, so a
caller writes `async with CascorTrainingStream(url) as stream: async for msg in stream:`.

**Iterators versus lists**: lists are simpler and re-iterable, generators are lazy and stream. The
rule that matters — never return a generator from a function whose name reads like an accessor,
because callers will iterate twice and silently get nothing the second time. If laziness matters, name
it (`iter_*`, `stream_*`).

**Return types**: 45 of the 61 public methods across the three clients return a bare
`Dict[str, Any]` / `dict[str, Any]`, and none of the five packages contains a single `TypedDict` or
`@overload`. Defensible for a thin HTTP wrapper (III.6 treats the dispute), but where a package returns
*its own* structure a named type costs nothing —
`juniper_service_core/dependency_floors.py:61-66` is the good version:

```python
class FloorViolation(NamedTuple):
    """One unsatisfied floor. ``installed`` is ``None`` when the dist is not installed."""

    distribution: str
    floor: str
    installed: str | None
```

A caller writes `v.installed`, not `v[2]`, and adding a field renumbers nothing.

#### Judgement Calls

- **Where does `*` go?** Parameters a reader would recognise unlabelled may be positional; everything
  else, and every boolean, keyword-only. The *default* is genuinely contested — the Controversy block
  at the end of this section argues both positions and the retrofit trap that makes the choice
  one-way.
- **Is a boolean the right parameter at all?** `persist=True`/`False` is often better as two
  functions, or an enum, when the paths differ in more than one branch.
- **Fail fast or normalise?** Fail fast when the input can be *proven* wrong locally, as a hostless
  URL can. Normalise only where the transformation is unambiguous.

#### Tradeoffs

| Decision                | Buys                                                 | Costs                                                     |
|-------------------------|------------------------------------------------------|-----------------------------------------------------------|
| Keyword-only everything | Free reordering and additions; readable call sites   | No shorthand even for the obvious argument                |
| Positional-friendly     | Matches the stdlib; shorter for recognised arguments | Order permanent from release one; booleans get misordered |
| `**kwargs` passthrough  | Forward-compatibility with an evolving server        | All static checking, completion, and typo detection       |
| Fail-fast constructor   | Errors at the configuration site, with the bad value | Rejects inputs a lenient version would coerce             |
| `NamedTuple` returns    | Named access; additive evolution                     | One more exported type to version                         |

#### Best Practices

- Put `*` before every optional parameter in new public functions — free now, impossible to retrofit
  compatibly — and never make a boolean positional.
- `Literal` for closed string sets; `Union[float, Literal["sentinel"]]` for numeric-or-magic-value.
- Immutable defaults (`()`, `None`) only. Build request bodies by omission, not by sending nulls.
- Validate what you can prove wrong at construction; say what was wrong and what was received.

#### Common Failure Modes

- **The docstring-only signature.** A typo becomes a server error or a silently missing field.
- **The frozen positional list.** A parameter added mid-list changes the meaning of existing
  positional calls, undetectably — the commonest real breakage of the positional style.
- **Null-versus-absent.** Sending explicit nulls forecloses ever sending a real null.
- **The doubled path prefix.** `rstrip("/")` without a version-suffix strip yields `/v1/v1/`.

#### Error Handling

Validation errors from a constructor should name the parameter and echo the value.
`juniper_recurrence_client/client.py:184` does both: `f"base_url must include a host; got {url!r}"`.
The `!r` matters — the failing input is often an empty string or one with invisible whitespace, and
`repr` is what makes that visible.

#### Controversy: Should Every Parameter Be Keyword-Only?

**That there is a dispute.** Nobody argues that keyword-only parameters are bad. The dispute is over
the *default*: whether a new public function should open with `*,` unless there is a reason not to, or
whether `*` should be introduced only where a specific parameter calls for it. The two positions
produce visibly different signatures for the same job, and this ecosystem contains both — `train`
(`juniper_recurrence_client/client.py:291-310`) and `create_dataset`
(`juniper_data_client/client.py:412-423`) are the same author solving the same problem two ways.

**The camps.** *Keyword-only by default* holds that parameter order is an accident of authoring that
should never have become a contract, and that one character buys permanent freedom to add, reorder,
and deprecate. *Positional-friendly* holds that the standard library's shape — `open(path)`,
`json.dumps(obj)`, `Session.request(method, url)` — is the shape readers have internalised, that
`client.get(url=url)` is noise at the call site, and that the evolution freedom is being bought for
functions that will never spend it.

**The background.** Keyword-only parameters have existed since Python 3.0, but positional-only `/`
arrived only in 3.8 ([PEP 570](https://peps.python.org/pep-0570/), named in CPython 3.13's
`pydoc_data/topics.py:2818` and `:5725`). For that decade the choice was binary and
"positional-or-keyword" was simply what a signature looked like — which is when the stdlib conventions
readers still pattern-match against were formed. The compatibility framing arrived later, with SemVer
and type checkers making "what exactly did I just break?" a question with a checkable answer.

The precision the argument usually misses: `*` does not remove the freeze, it *relocates* it.

| Parameter kind               | Frozen forever      | Free to change                  |
|------------------------------|---------------------|---------------------------------|
| Positional-or-keyword        | Order **and** names | Nothing except appending        |
| Keyword-only (after `*`)     | Names               | Order; insertions; deprecations |
| Positional-only (before `/`) | Order               | Names                           |

Keyword-only trades a frozen order for frozen *names* — usually the better trade, since a name is
easier to get right first time than an ordering that must anticipate parameters you have not thought
of. But it is a trade, and the camps disagree about which freeze costs more.

**Keyword-only by default — strengths.** It scales where positional does not:
`juniper_recurrence_client/client.py:381-404` takes twenty parameters, and `n_folds: int` (`:384`) is
required *and* keyword-only — which the positional style cannot express without making it the first
argument and freezing it there forever. Insertions become free rather than append-only, and booleans
cannot be misordered.

**Keyword-only by default — weaknesses.** Every parameter name becomes public API the day you publish
and can never be renamed. There is no shorthand even where a positional argument would be unambiguous,
and the result reads unlike the stdlib its users switch to and from all day.

**Keyword-only by default — risks.** The name freeze is invisible in a way the order freeze is not. A
tidy-up commit renaming `rff_gamma` to `gamma` is breaking, and nothing in your repository catches it,
because your tests were renamed in the same commit. An order freeze announces itself the moment you try
to insert a parameter; a name freeze announces itself in a stranger's `TypeError`.

**Keyword-only by default — guardrails.** Choose parameter names as deliberately as function names —
they are equally public and equally permanent. Use `/` on genuinely positional leading arguments to buy
back rename freedom there. Run a type checker in CI against a consumer-shaped probe file (III.6), where
a renamed keyword-only parameter is an error rather than a downstream bug report.

**Positional-friendly — strengths.** It matches what readers expect and what the stdlib does, and it is
shorter wherever the meaning is obvious unlabelled: `create_dataset("spiral", {"seed": 42})` genuinely
reads better than the keyword form. Combined with `/`, it is also the only style that leaves a
parameter free to be renamed later.

**Positional-friendly — weaknesses.** Order is permanent from release one, so a new parameter can only
be appended, however unrelated to the one it now sits beside. And it admits the boolean trap in its
natural habitat: `create_dataset("spiral", {"seed": 42}, False)` is legal, and nothing at the call site
says what `False` means.

**Positional-friendly — risks.** The retrofit is the serious one, and it makes the decision one-way:
adding `*` later breaks every positional caller, so "we'll add it when we need it" is not available.

```python
def create_dataset(generator, params, *, persist=True):  # `*` introduced in v2
    return persist


create_dataset("spiral", {}, persist=False)  # keyword callers unaffected
# create_dataset("spiral", {}, False)  -> TypeError: takes 2 positional arguments but 3 were given
```

The compatible ways out are a deprecation cycle designed in advance, or living with the order forever.

**Positional-friendly — guardrails.** Put `*` before the first *optional* parameter even when the
leading required ones stay positional — the hybrid, not the extreme.
`juniper_service_core/workers/coordinator.py:136-144` is the shape: `registry` and `protocol`
positional because a reader recognises them, `*` before the three tunables.

**Recommendation** (as a recommendation): adopt that hybrid rather than either extreme. Leading
arguments a reader recognises unlabelled may stay positional — mark them `/` if you want to keep the
freedom to rename them; everything optional goes after `*`. It is what `create_app`
(`juniper_service_core/app.py:23-29`) and `WorkerCoordinator.__init__` already do, and it is the
position that survives the retrofit asymmetry: `*` added later breaks callers, while a parameter that
starts keyword-only can usually be relaxed to positional-or-keyword without breaking anyone.

*Usually*, not always: if the function takes `*args`, there is no position to relax the parameter into
except in front of the variadic, which changes what every existing call means.
`def connect(*hosts, timeout=5)` cannot become `def connect(timeout=5, *hosts)` — under the second,
`connect("a", "b", timeout=1)` raises `TypeError: got multiple values for argument 'timeout'` and
`connect("a", "b")` silently returns `(("b",), "a")`, having rebound `timeout` to `"a"`. The silent one
is the worse outcome. Where the signature has no `*args`, the relaxation really is free.

---

### III.4 Errors and Exception Hierarchy Design

#### Overview

Exception types are part of your signature. A caller's `except` clause is a call site, and changing
what you raise breaks it as surely as changing what you return. This section covers designing the
tree, preserving the chain, and — most often skipped — attaching the data a caller needs to *act*.

#### Background

The standard shape is one package base class plus typed leaves. The base lets a caller write
`except PackageError:` and be sure nothing else escapes; the leaves let a caller who cares handle one
case. Both are necessary — a base without leaves forces message parsing, leaves without a base force
an ever-growing tuple in every `except`.

All three clients implement exactly this and nothing more: `juniper_data_client/exceptions.py:4-37`
(one base, five leaves), `juniper_cascor_client/exceptions.py:4-49` (one base, seven leaves),
`juniper_recurrence_client/exceptions.py:10-36` (one base, six leaves). The load-bearing property holds
in all three: not one of the twenty-one classes defines `__init__` or any attribute. The bodies differ
cosmetically — recurrence-client's seven are a docstring and nothing else, while data-client's six and
cascor-client's eight are a docstring followed by a redundant `pass`.

**Intermediate categories** — `TransientError` versus `PermanentError` — earn their keep when callers
genuinely branch on the category and membership is stable. They fail when categorisation is contested:
is a 429 transient? Usually. Is a 409 conflict? Entirely depends why. A category callers must
second-guess is worse than none, because it invites `except TransientError: retry()` on cases that
will never succeed. Flat is reasonable at five to seven leaves; at twenty, a middle layer starts
paying.

#### Inheriting From Builtins

Deriving from `ValueError`, `KeyError`, or `OSError` means callers with generic handlers catch you
without knowing about your package. Whether that is a feature is the section's live dispute — the
Controversy block at the end argues it — but the two halves of this ecosystem chose opposite answers,
which is worth having in front of you first.

`juniper-service-core` defines six exception classes and inherits from a builtin in four of them, from
two builtins. `SnapshotNotFoundError(KeyError)` (`juniper_service_core/lifecycle/snapshots.py:35`)
because the store is a mapping and `except KeyError` is the idiom a caller already has — and it is
raised with the bare id, `raise SnapshotNotFoundError(snapshot_id)` (`:82`), which is the mapping
convention followed properly. Three more derive from `RuntimeError`: `WorkerRegistryFullError`
(`workers/registry.py:31`), whose docstring gives the reason (`:34-37`) — "Distinct from a generic
`RuntimeError` so the websocket worker-handshake handler can catch this specific case and emit a
structured 'registry full' close frame rather than an opaque server error" — plus `DependencyFloorError`
(`dependency_floors.py:57`) and `AuthPostureError` (`auth_posture.py:51`). The remaining two derive
from bare `Exception`: `TrainingInterrupted` (`lifecycle/manager.py:59`) and `ReplayOutOfRange`
(`websocket/manager.py:53`).

There is no package base class anywhere in `juniper-service-core`, and the consequence needs stating
carefully, because the obvious phrasing is false. It is not that the six share no ancestor: three are
`RuntimeError`s, so `except RuntimeError:` really does catch all three. What they share no ancestor of
is anything *package-specific*, and `RuntimeError` is a builtin that any library in the process may
raise — so that clause does not mean "catch service-core", it means "catch a large, unbounded,
mostly-unrelated population that happens to include three of service-core's six". No `except` a consumer
can write means "this package failed". That is the cost of the inherit-from-builtins position adopted
without a base, and the partial ancestor makes it worse than none, because it invites a handler that
looks correct and is not.

The three clients took the opposite line — a package base derived from bare `Exception`, every leaf
under it, nothing else (`juniper_data_client/exceptions.py:4-37`,
`juniper_cascor_client/exceptions.py:4-49`, `juniper_recurrence_client/exceptions.py:10-36`) — with one
leak. `juniper_data_client/contract.py:41` `validate_npz_contract` is *public* (imported at
`juniper_data_client/__init__.py:8`, exported at `:15`) but its documented failure mode is a bare
`ValueError` (`contract.py:54-58`, raised at `:66`), not `JuniperDataValidationError` — so a caller
wrapping the client surface in `except JuniperDataClientError:` does not catch it.

#### Preserving Context

`raise X() from e` sets `__cause__` ("direct cause"). `raise X()` inside an `except` sets `__context__`
implicitly ("during handling"). Both keep the original traceback, and so — this surprises people —
does `raise X(str(e))`, as long as it is still inside the `except` block: the implicit `__context__`
does not care what arguments you passed. What `from e` adds is the explicit *cause* link and the
"direct cause" wording; what you lose without it is discussed under Common Failure Modes below. The
clients get this right on every transport path — `juniper_data_client/client.py:287-291`:

```python
try:
    response = self.session.request(method, url, **kwargs)
except requests.exceptions.ConnectionError as e:
    outgoing_error = JuniperDataConnectionError(f"Failed to connect to JuniperData at {self.base_url}: {e}")
    raise outgoing_error from e
```

The same at `juniper_cascor_client/client.py:367-372` and
`juniper_recurrence_client/client.py:239-247`, and on the malformed-JSON paths
(`juniper_data_client/client.py:345`, `juniper_cascor_client/client.py:387`,
`juniper_recurrence_client/client.py:287`). The `from e` is what lets an operator see the underlying
`urllib3` error rather than a one-line summary of it.

#### The Big One: Structured Data on Exceptions

Every one of these clients builds its HTTP exceptions from a single formatted string —
`juniper_data_client/client.py:312-320`:

```python
if response.status_code == HTTP_404_NOT_FOUND:
    outgoing_error = JuniperDataNotFoundError(f"Resource not found: {error_detail}")
    raise outgoing_error
elif response.status_code in (HTTP_400_BAD_REQUEST, HTTP_422_UNPROCESSABLE_ENTITY):
    outgoing_error = JuniperDataValidationError(f"Validation error: {error_detail}")
    raise outgoing_error
else:
    outgoing_error = JuniperDataClientError(f"Request failed ({response.status_code}): {error_detail}")
    raise outgoing_error
```

No `.status_code`, no `.response`, no `.detail`. The status exists at the raise site and is discarded
— in the 404 and 400/422 branches it is not even in the message.

`juniper_cascor_client/client.py:389-414` is worse: it drops the status from the message on four of its
five branches. Driving the real client against a stub server returning each status in turn:

```text
409 -> JuniperCascorConflictError    | message='service starting'
400 -> JuniperCascorValidationError  | message='service starting'
422 -> JuniperCascorValidationError  | message='service starting'
```

The 400 and the 422 are byte-identical: same type, same message, both echoing only the server's
`detail`. A caller cannot distinguish a malformed request from a semantically invalid one by type, by
attribute, or by parsing. The fix is small and entirely additive:

```python
class JuniperDataClientError(Exception):
    """Base exception for all JuniperData client errors."""

    def __init__(self, message: str, *, status_code: int | None = None, detail: object = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail
```

Existing `except` clauses keep working, `str(exc)` is unchanged, every subclass inherits the
attributes, and callers get `if exc.status_code == 429: back_off()` instead of a substring search.

The same defect appears one layer down, where the structured data demonstrably exists.
`juniper_service_core/dependency_floors.py:213-217` computes a `list[FloorViolation]` — the NamedTuple
from III.3, carrying `distribution`, `floor`, and `installed` — then formats it away into
`raise DependencyFloorError(message)`. A caller wanting the structure must call
`check_dependency_floors` directly, which is possible but not exported from the package root
(`juniper_service_core/__init__.py:112-186` exports only `enforce_dependency_floors` and the
exception). `self.violations = violations` would have cost one line.

**Messages as a semi-public API.** Once a caller cannot branch on type or attribute, they branch on
the message — which makes your message text load-bearing whether you intended it or not, and a
"clarify the wording" commit a breaking change for somebody. That is the strongest practical argument
for structured attributes: they are the only thing that makes message text safe to edit. The messages
are otherwise well-built; the malformed-JSON path truncates the body preview to 200 characters
(`juniper_data_client/client.py:344`, identically in the other two), keeping a 40 MB HTML error page
out of a log line while preserving enough to diagnose "the load balancer returned an HTML 502".

#### Losing a Distinction to the Retry Layer

The subtlest failure here is one no unit test catches, because it lives between the exception mapping
and the retry policy.

`juniper-cascor-client` defines a typed 503 leaf, `JuniperCascorServiceUnavailableError`
(`exceptions.py:40-43`), mapped at `client.py:411-412`. It also puts 503 on the urllib3 retry
forcelist (`constants.py:36`, `[429, 502, 503, 504]`) and allows retries on every method it uses
(`:37`, `["GET", "POST", "DELETE", "PUT", "PATCH"]`). When retries are exhausted on a forcelist
status, urllib3 raises rather than returning the response; `requests` surfaces that as `RetryError`, a
`RequestException`, which the client catches at `client.py:371-372` and maps to the **base** class.
Driving the shipped client against a server returning a persistent 503:

```text
retries=0: 503 -> JuniperCascorClientError
retries=3: 503 -> JuniperCascorClientError
# with the adapter's status_forcelist emptied:
503 -> JuniperCascorServiceUnavailableError
```

`JuniperCascorServiceUnavailableError` is unreachable through the client's own request path under the
shipped configuration, at every retry count including zero. The typed leaf exists, is correct, and is
dead. The `__cause__` chain is intact — it points at `RetryError` — so the information is recoverable
by an operator reading a traceback and entirely unavailable to code. The generalisable lesson: a retry
layer *below* your exception mapping can erase distinctions the mapping was written to preserve, and
only exercising the whole stack finds it.

#### Raise, Return, or Warn

Raise when the caller cannot proceed. Return a result object when "failed" is an expected outcome the
caller branches on anyway — a validator reporting every problem, not just the first.
`juniper_recurrence_client/client.py:462-468` shows the boundary handled well: a readiness probe
converts the exception into a `bool`, because "not ready" is the normal answer, and catches only the
package base class so unrelated failures still propagate. Warnings are for things a caller should
change but need not handle now (III.5); a warning the caller must act on immediately should have been
an exception.

#### Judgement Calls

- **How many leaves?** One per distinct caller response. Two types always handled identically are one
  type.
- **Inherit from a builtin?** Contested; see the Controversy block at the end of this section for both
  positions and the adjudication.
- **Attributes or message?** Attributes, whenever a caller could plausibly branch on the value.

#### Tradeoffs

| Choice                  | Buys                                                  | Costs                                                      |
|-------------------------|-------------------------------------------------------|------------------------------------------------------------|
| Flat base + leaves      | Simple; catch broadly or narrowly                     | Callers grow long `except` tuples as leaves multiply       |
| Intermediate categories | Category-level handling                               | Contested membership; miscategorisation is worse than none |
| Builtin base classes    | Interoperability with existing handlers               | Unintended capture by unrelated broad handlers             |
| Structured attributes   | Programmatic branching; message text becomes editable | Requires an `__init__`                                     |

#### Best Practices

- One package base class; every leaf derives from it; nothing else escapes.
- Always `raise ... from e` when re-raising in an `except`.
- Carry status codes, bodies, and correlation ids as attributes, not message text, and truncate
  anything potentially large before it reaches a message.
- Document what each public function raises — `Raises:` is part of the contract.
- Test the exception mapping through the whole client, retry layer included.

#### Common Failure Modes

- **`raise X(str(e))`** — not what it is usually accused of. Verified on CPython 3.13.13: inside an
  `except` block it still sets `__context__`, and the formatted traceback carries both frame sets under
  "During handling of the above exception, another exception occurred". What it drops is `__cause__`,
  which stays `None`. The chain therefore reads "during handling" rather than "direct cause" — a weaker
  claim about the relationship — and the original exception's *type* is recoverable only by reading a
  traceback, never by code, since `str(e)` flattened it to text. Frames are lost outright only when you
  re-raise *outside* the `except` block, where the exception state has already been cleared, or when you
  write `from None`.
- **The unreachable leaf** — a typed exception the retry or transport layer intercepts first.
- **Message-only status** — callers resort to `"429" in str(exc)`, which breaks on rewording.
- **Bare `except Exception: pass`** — the failure vanishes and returns later as corrupted state.
- **Leaking a foreign exception type** — a `json.JSONDecodeError` escaping an HTTP client makes `json`
  part of your public API. All three clients close this hole explicitly
  (`juniper_data_client/client.py:332-345` and siblings).

#### Error Handling

Swallowing an exception is legitimate under one rule with two halves: the failure must not be the
caller's concern, **and** the `except` must be narrowed to the single call that may fail. Three shapes
in these packages satisfy it, and they are the whole legitimate set — instrumentation that must never
break the path it observes; probing for an optional dependency
(`juniper_service_core/dependency_floors.py:37-41`, the `except ModuleNotFoundError` fallback from
III.2, and `juniper_cascor_client/observability.py:52-55`, whose `except ImportError: return None` the
caller then checks at `:109-111`); and converting an expected failure into a documented return value
(`juniper_recurrence_client/client.py:462-468`, the readiness probe from Raise, Return, or Warn above,
which catches only the package base class). Nothing else qualifies. The instrumentation case is the one
worth reading in full — `juniper_data_client/client.py:321-330`:

```python
try:
    ...  # issue the request; return on success, or raise one of the typed errors
finally:
    duration_ms = (time.monotonic() - start) * 1000.0
    status = response.status_code if response is not None else None
    try:
        self._on_request(method, url, status, duration_ms, outgoing_error)
    except Exception:  # noqa: BLE001 — instrumentation must not crash production paths
        logger.warning("on_request hook raised; suppressed to keep request path resilient", exc_info=True)
```

Four properties make this correct rather than lazy. The hook fires in `finally`, so every outcome —
success, transport failure, all typed-error branches — is observed exactly once. The swallow is
narrowed to the hook call, not wrapped around real work. It logs with `exc_info=True`, so the
suppressed exception remains recoverable. And the `# noqa` comment states *why*, which distinguishes a
decision from an oversight. `juniper_recurrence_client/client.py:272-278` is the same code with the
same comment.

The complementary detail is the default:
`self._on_request: RequestHook = on_request or _noop_request_hook`
(`juniper_data_client/client.py:174`) uses a *named* no-op (`:109-122`) rather than `None`, reasoning
at `:171-173` — the no-op default means "call sites don't need `if self._on_request: ...` guards — the
no-op call is a single attribute load + return". The recurrence copy adds the other half
(`juniper_recurrence_client/client.py:100`): "named so the default is a real callable", which also
makes the default satisfy the published `RequestHook` type.

Note the asymmetry inside `juniper-cascor-client`: `_dispatch_disconnect` (`ws_client.py:459-471`)
wraps each listener in `try`/`except` with the comment "isolate listener faults", while `_dispatch`
(`:453-457`) — the loop running the six message callbacks — has no guard, so one raising `on_metrics`
listener tears down the stream. Same file, same pattern, one hardened.

#### Controversy: Should Library Exceptions Inherit From Built-in Exception Types?

**That there is a dispute.** Whether a library's exceptions should derive from the closest matching
builtin — `KeyError`, `ValueError`, `OSError` — or from bare `Exception` and nothing else is not a
style preference: the choice decides whether code that has never heard of your package catches your
failures, and it is a behavioural contract you cannot change later without breaking someone. The two
shared packages and the three clients here disagree with each other about it.

**The camps.** *Inheritors* hold that an exception should say what *kind* of thing went wrong in the
vocabulary the language already has: a missing key is a `KeyError` whoever raises it, and
`except KeyError:` around a mapping lookup deserves to work. *Isolationists* hold that your exceptions
should be catchable only on purpose — one package base, everything under it, nothing a handler written
for an unrelated failure can capture by accident.

**The background.** The builtin hierarchy was designed for the interpreter's own failure modes, not as
a taxonomy for third-party libraries, and the split dates from the period when libraries began reusing
it for interoperability. `OSError` is the sharpest case, because the language itself consolidated it
into *the* I/O-failure vocabulary — on CPython 3.13.13, `IOError`, `EnvironmentError`, and
`socket.error` are all literally `OSError`, and `ConnectionResetError` and `TimeoutError` are its
subclasses. `requests` then deliberately joined that vocabulary:

```python
import socket

from requests.exceptions import RequestException

assert IOError is OSError and socket.error is OSError          # the stdlib consolidation
assert issubclass(RequestException, OSError)                   # True on requests 2.33.1
```

Because every Juniper client wraps `requests`, that one word in someone else's class statement decides
what a Juniper caller's `except OSError:` does.

**Inheriting — strengths.** The caller already has the idiom and need not learn yours.
`SnapshotNotFoundError(KeyError)` (`juniper_service_core/lifecycle/snapshots.py:35`) is the strongest
form: the store is a lookup, a miss really is a missing key, and `except KeyError:` around it is
correct code written by someone who never read your package. Generic retry, cache, and adapter layers
that catch builtins keep working — and the choice is additive, since you can derive from your base and
a builtin at once.

**Inheriting — weaknesses.** You inherit the builtin's behaviour along with its identity, and some of
it surprises. `KeyError.__str__` returns `repr(args[0])`, so a message passed to a `KeyError` subclass
renders quoted anywhere `str(exc)` is used — a logger `%s`, an f-string, a bare `print`:

```python
class SnapshotNotFoundError(KeyError):
    pass


assert str(SnapshotNotFoundError("no bundle for snapshot id-42")) == "'no bundle for snapshot id-42'"
```

Quotes are right for a key and wrong for a sentence, and nothing warns you which you passed.

**Inheriting — risks.** Unintended capture, invisible from your side of the boundary: a consumer's
`except OSError:` written around file I/O silently swallows every HTTP failure a `requests`-derived
exception carries, so the failure does not surface at all. The related risk is the one
`juniper-service-core` actually has — inheriting from builtins *instead of* a base, leaving its six
exception types with no package-specific shared ancestor and no way to catch the package as a unit.

**Inheriting — guardrails.** Inherit only where the builtin's contract is literally what happened, and
inherit from your package base as well: `class SnapshotNotFoundError(ServiceCoreError, KeyError)` gives
both the idiom and the catch-all. Pass a key, not a sentence, to anything deriving from `KeyError`.
`OSError` is a conditional, not a prohibition: derive from it only if your package genuinely *is* an
I/O boundary and you want `except OSError:` to keep working across it — which is precisely what
`requests` decided, and the reason its choice propagates through every client in this ecosystem.
Understand what you buy with it: you become invisible to callers using narrower handlers, and visible
to every broad one. For anything that is not I/O, refuse.

**Isolating — strengths.** Nothing catches you by accident, `except PackageError:` means exactly what
it says, and you may define `__init__` and attributes without negotiating with a builtin's `args`
semantics. It is also the position that stays correct as dependencies change: the three clients derive
from bare `Exception`, so what `requests` decided about `OSError` cannot reach them.

**Isolating — weaknesses.** Every caller must learn your types, and generic handlers stop working. Note
the direction — because `requests.RequestException` *is* an `OSError`, wrapping it in
`JuniperDataConnectionError(Exception)` **narrows** what an existing handler catches: code that caught
your transport failures via `except OSError:` stops catching them.

**Isolating — risks.** That narrowing lands at the version introducing the wrapper and is not obviously
breaking by signature-shaped tests — nothing in the public API changed shape, only what an unrelated
`except` clause lets through. Consumers discover it as an unhandled exception in production.

**Isolating — guardrails.** One base class, every leaf under it, and an audit that *every* public entry
point raises from your tree — `contract.py:66`'s bare `ValueError` is exactly the leak this catches.
Document the catchable base, since it is the only thing a caller can rely on, and treat introducing a
wrapper as a changelog compatibility note, because for someone it is one.

**Recommendation** (as a recommendation): isolate by default — one package base derived from
`Exception`, every leaf under it — and inherit from a builtin only where the builtin's contract is
*literally* what occurred, then by multiple inheritance so the package base survives. A mapping-shaped
store raising `KeyError` earns it; a validation helper raising `ValueError` usually does not, because
"invalid" is your domain judgement rather than the language's. `OSError` is the one to think hardest
about: refuse it for anything that is not an I/O boundary, and accept it — eyes open, in the changelog
— only if you are one and you want to stay catchable as one, the way `requests` did.

---

### III.5 Versioning, SemVer, and Deprecation

#### Overview

A version number is a promise about what changed. For a library nothing enforces it — no gate rejects
a wheel whose minor bump removed a function — so the discipline is convention plus whatever tests make
the convention checkable.

#### Background

**SemVer 2.0.0** ([specification](https://semver.org/spec/v2.0.0.html)) defines `MAJOR.MINOR.PATCH`:
increment MAJOR for incompatible API changes, MINOR for backward-compatible additions, PATCH for
backward-compatible fixes. Two provisions are load-bearing and routinely skipped. First, SemVer
requires you to *declare* a public API — the version means nothing until you have said what it is a
version of, and a package where every module is fair game cannot make a compatibility promise at all.
Second, the `0.y.z` escape clause: below `1.0.0` the specification treats the project as in initial
development and guarantees no stability. The de-facto convention filling that gap treats `0.y` as
major and `0.y.z` as minor, so `0.4.0 → 0.5.0` may break and `0.4.1 → 0.4.2` may not. Every package
here is pre-1.0 and follows that reading; nothing enforces it.

*Citation note:* this environment could not reach `semver.org` to re-verify the spec text, so the above
is a paraphrase and deliberately cites no clause numbers. The linked URL is canonical.

**PEP 440** ([Version Identification and Dependency Specification](https://peps.python.org/pep-0440/))
is what Python implements — the format `packaging` parses and `pip` orders, as that library's source
states repeatedly (`packaging/version.py:411`, `packaging/specifiers.py:70`). It overlaps SemVer
without being it. PEP 440 has an *epoch* (`1!2.0.0`) for a scheme change, which SemVer lacks;
pre-release spelling differs (`1.0.0rc1` versus `1.0.0-rc.1`); PEP 440 adds post-releases
(`1.0.0.post1`) and dev releases (`1.0.0.dev1`) with defined ordering, and SemVer has neither; PEP 440
permits any number of release segments (`1.2.3.4`) where SemVer requires three; and the ordering rules
differ enough that a string can sort one way under each. For a Python library, publish PEP 440
versions that also happen to be valid SemVer.

#### What Counts as Breaking for a Library

The network answer ("the response shape changed") does not transfer. The in-process set is larger and
less obvious.

| Change                                             | Breaking?               | Why                                              |
|----------------------------------------------------|-------------------------|--------------------------------------------------|
| Adding a keyword-only parameter with a default     | No                      | No existing call site is affected                |
| Adding a positional parameter anywhere but the end | Yes                     | Silently rebinds existing positional calls       |
| Renaming any positional-or-keyword parameter       | Yes                     | Breaks every caller that passed it by name       |
| Narrowing a return type (`dict` → `MyModel`)       | Yes                     | Callers doing `result["k"]` break                |
| Widening a return type (`str` → `str \| None`)     | Yes                     | Callers not handling `None` break                |
| Changing which exception type is raised            | Yes                     | `except` clauses are call sites                  |
| Removing an attribute, even undocumented           | Usually                 | Convention says no; reality says someone used it |
| Tightening validation                              | Yes                     | Inputs that used to work now raise               |
| Loosening validation                               | No                      | Strictly additive                                |
| Behaviour change with an unchanged signature       | Yes, and the worst kind | Nothing static detects it                        |

Tightening validation deserves emphasis because it feels like a bugfix. Had
`juniper-recurrence-client` added its hostless-URL check (`client.py:183-184`) in a patch release,
every deployment passing a URL that happened to work would start raising at construction — same code,
same signature, new exception, and a major-version change under any honest reading.

#### Single-Sourcing the Version

**Dynamic, from a `_version.py`.** `juniper-recurrence-client` is the exemplar: the literal exists in
exactly one place (`juniper_recurrence_client/_version.py:7`), and `pyproject.toml:7` declares
`dynamic = ["version"]` with `pyproject.toml:54-55`:

```toml
[tool.setuptools.dynamic]
version = { attr = "juniper_recurrence_client._version.__version__" }
```

The module docstring names the constraint this imposes (`_version.py:1-5`): it is "kept import-free so
setuptools can parse `__version__` statically at build time... without importing requests". That
matters — a `_version.py` importing the package would force the build backend to import the whole
distribution, dependencies included, to read a string.

**`importlib.metadata`** leaves no literal in the source at all, at the price of a runtime lookup and a
failure mode for uninstalled source trees. **Manual duplication** is what the other four do, and it is
where drift lives.

| Package                     | `pyproject.toml` | `__version__`              | Other copies                | Consistent?       |
|-----------------------------|------------------|----------------------------|-----------------------------|-------------------|
| `juniper-recurrence-client` | dynamic (`:7`)   | `_version.py:7` = `0.2.0`  | none                        | Yes, structurally |
| `juniper-cascor-client`     | `:7` = `0.7.0`   | `__init__.py:14` = `0.7.0` | `constants.py:14` = `0.7.0` | Yes, by hand      |
| `juniper-data-client`       | `:7` = `0.4.2`   | `__init__.py:11` = `0.4.2` | five file headers           | **No**            |
| `juniper-service-core`      | `:7` = `0.5.1`   | `_version.py:5` = `0.5.1`  | none                        | Yes, by hand      |
| `juniper-observability`     | `:7` = `0.4.0`   | `_version.py:3` = `0.4.0`  | none                        | Yes, by hand      |

Two findings need stating precisely, because this story is usually told wrong.
`juniper-cascor-client` *had* drifted and has been fixed: `__init__.py:11-13` carries the tombstone —
the constant is "kept in lockstep with `[project].version` in pyproject.toml (CL1 also fixed a
pre-existing drift where this constant had been left at 0.4.0 while the package shipped 0.5.x/0.6.x)"
— and both copies now read `0.7.0`. `juniper-data-client` has *three* copies and the third has
drifted: `pyproject.toml:7` and `__init__.py:11` agree at `0.4.2`, but `constants.py:12` reads
`Version: 0.4.0`, `contract.py:21` reads `0.4.1`, and `testing/__init__.py:7`,
`testing/generators.py:7`, and `testing/fake_client.py:7` all read `0.4.0`. The file-header convention
created a third, informal copy that nothing updates — `tests/test_versioning.py:7` reads `0.3.2`,
showing how far such a thing drifts once decorative.

None of the three clients tests that these agree. The mechanism exists one level up: the
meta-repository's `tests/test_release_train_registry.py:307` defines `VersionDunderLockstepTest`,
whose docstring names the incident it closes — "service-core 0.5.0, silent for five days because no
gate existed". It covers the in-repo packages; the clients live in their own repositories, outside its
reach. A convention with no test has already drifted somewhere you have not looked, and the test is
four lines:

```python
import tomllib
from pathlib import Path

import juniper_data_client

def test_version_lockstep() -> None:
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["project"]["version"] == juniper_data_client.__version__
```

#### Deprecation Mechanics

The cycle: keep the old thing working, warn on use, document the removal version, remove in a major
release, never reuse the name.

**`DeprecationWarning` is hidden by default, and the mechanism explains why `stacklevel` matters.**
CPython 3.13's default filters, read from a live interpreter:

```text
('default', None, <class 'DeprecationWarning'>, '__main__', 0)
('ignore',  None, <class 'DeprecationWarning'>, None, 0)
```

The first shows the warning *only when the module it is attributed to is `__main__`*; the second
ignores it everywhere else. Attribution comes from `stacklevel`, so a warning raised with the default
`stacklevel=1` is attributed to your library's module, matches the `ignore` filter, and is seen by
nobody — including a user running a script directly. Correct `stacklevel` is not politeness; it is the
difference between a warning that exists and one that does not.

`juniper-data-client` holds the only `warnings.warn` call in all five packages, and it is right
(`juniper_data_client/testing/fake_client.py:246-261`):

```python
def _resolve_generator_alias(name: str) -> str:
    canonical = _GENERATOR_LEGACY_ALIASES.get(name)
    if canonical is None:
        return name
    warnings.warn(
        f"Generator name {name!r} is deprecated; use {canonical!r} instead. "
        "The legacy alias will be removed in a future release.",
        DeprecationWarning,
        stacklevel=3,
    )
    return canonical
```

`stacklevel=3` is correct for this chain, and the frames are worth enumerating exactly, because getting
them one apart is the whole bug class. Level 1 attributes the warning to the `warnings.warn` call
itself, inside `_resolve_generator_alias`. Level 2 attributes it to `_resolve_generator_alias`'s
*caller* — that is, the line inside the public method where it invokes the helper (`fake_client.py:352`
and `:397`), still library code. Level 3 attributes it to the public method's caller, which is user
code, and is what you want. Run the same three-deep chain with `stacklevel` 1, 2 and 3 under
`warnings.catch_warnings(record=True)` and the reported `filename`/`lineno` walks up exactly one frame
per level; that is the only reliable check, and it takes ten lines. The
alias map above carries the removal window in a comment (`:237-240`): a "one-release-cycle
backward-compat map... Remove in the release after v0.5". A dated window turns a deprecation from a
permanent tax into a plan.

#### Two Flavours of Back-Compatibility

The alias is one flavour: warned, dated, loud. The other is `juniper_cascor_client/ws_client.py:249` —
a silent opt-out flag, `auto_pong: bool = True`, documented in the `CascorTrainingStream` class
docstring (`:219-242`, the relevant passage at `:224-230`): pings
are now answered automatically, and "Pass `auto_pong=False` to restore the legacy behaviour where ping
frames are yielded to the consumer, which must then reply itself... or be closed by the server ~40s
after connect". No warning fires either way, and no removal is stated.

Both are defensible. A warned alias is right when the old spelling is simply wrong and everyone should
move. A silent flag is right when the old behaviour stays legitimate for some callers — here, a relay
that wants to see and forward the pings. The risk is that the flag never goes away: nothing tells you
who still sets it. And `auto_pong` is the *fourth positional parameter*, so
`CascorTrainingStream(url, key, origin, False)` is legal — III.3's boolean trap, in a compatibility
flag, where it is most likely to be misread.

Neither shared package has any deprecation machinery: zero `DeprecationWarning`, zero
`PendingDeprecationWarning`, zero legacy aliases across `juniper_service_core/` and
`juniper_observability/`. Both are pre-1.0 and manage compatibility purely by external pinning — a
coherent position while the consumer set is a known handful of first-party repositories, and not one
the moment a third party depends on you.

#### Dependency Pinning: Floors and Ceilings

A *floor* (`>=0.3.1`) says "I need at least this" and is uncontroversial: you know what you use. A
*ceiling* (`<0.5.0`) says "I do not work above this", and is the fight, because you are asserting
something about software that does not exist yet. The Juniper tree contains both, plus a written
rationale in the comment block at the meta-package's `pyproject.toml:36-42`, which sits above the
`doc-tools` extra declared at `:43-44`. Of that pin it says (`:38-40`): "Pinned inside the 0.1.x range
so a future 0.2.x with breaking CLI changes doesn't auto-adopt before consumer repos have migrated."

| Pin                                              | Location                                      | Ceiling? |
|--------------------------------------------------|-----------------------------------------------|----------|
| `juniper-data-client>=0.4.1`                     | meta `pyproject.toml:30`                      | No       |
| `juniper-doc-tools>=0.1.0,<0.2.0`                | meta `pyproject.toml:44`, `:54`               | Yes      |
| `juniper-service-core>=0.2.0,<0.6.0`             | meta `pyproject.toml:57`                      | Yes      |
| `requests>=2.28.0`, `urllib3>=2.0.0`             | every client `pyproject.toml`                 | No       |
| `juniper-observability>=0.3.1,<0.5.0`            | `juniper-recurrence-client/pyproject.toml:46` | Yes      |
| `fastapi>=0.110`, `pydantic>=2.0`, `numpy>=1.24` | `juniper-service-core/pyproject.toml:24-38`   | No       |

The pattern is coherent even if never stated as policy: third-party runtime dependencies get floors
only; first-party pre-1.0 siblings get ceilings, because their `0.y` bumps are treated as major.

#### Judgement Calls

- **When do you go 1.0?** When you will accept the cost of a major bump for the next breaking change.
  Staying at `0.x` forever to keep the escape clause has consequences for consumers who cannot express
  a compatibility range.
- **Fix or break?** If any currently-working call stops working it is a break, regardless of whether
  the old behaviour was a bug.

#### Tradeoffs

| Choice                             | Buys                                   | Costs                                         |
|------------------------------------|----------------------------------------|-----------------------------------------------|
| Dynamic version from `_version.py` | Structurally impossible to drift       | `_version.py` must stay import-free           |
| `importlib.metadata`               | No literal in source                   | Runtime lookup; fails for uninstalled trees   |
| Manual duplication                 | Zero machinery                         | Drifts, and only a test catches it            |
| Warned deprecation                 | Callers learn before removal           | Needs correct `stacklevel` and a removal plan |
| Silent behaviour flag              | No noise; legacy path stays legitimate | Never removable — you cannot see who uses it  |

#### Best Practices

- One source of truth for the version, plus a test asserting every copy agrees.
- Treat `0.y` as major while pre-1.0, and say so in the README.
- Deprecate with `DeprecationWarning`, the right `stacklevel`, and a stated removal version.
- Keep a `CHANGELOG.md` with breaking changes at the top of their section.
- Floors always; ceilings by policy, with the policy written next to the pin.

#### Common Failure Modes

- **Silent version drift.** Multiple literals, no test, and a wheel reporting a version it is not —
  `juniper-cascor-client` shipped `0.5.x`/`0.6.x` announcing `0.4.0`.
- **The invisible deprecation.** Wrong `stacklevel`, warning filtered out, removal arrives unannounced.
- **The eternal shim.** A compatibility path with no removal date becomes permanent, and its
  interaction surface grows with every later change.
- **The accidental break in a patch.** Tightened validation or a changed exception type shipped as
  `0.4.1 → 0.4.2`.

#### Error Handling

A version-mismatch failure should be loud and specific. `juniper-service-core` implements this at
boot: `enforce_dependency_floors` compares every installed `juniper-*` distribution against the
declared floors and raises before the service binds
(`juniper_service_core/dependency_floors.py:213-217`). The module docstring names the incident it
prevents (`:10-13`) — "a client wheel below its `pyproject` floor passed unit tests but broke the live
app" — and it ships with an escape hatch, `JUNIPER_SKIP_DEP_FLOOR_CHECK` (`:46`, documented at
`:21-23`), so a false positive can never permanently block a legitimate start. Both halves matter: a
check with no bypass gets deleted the first time it is wrong.

#### Controversy: Should Libraries Cap Their Dependencies' Upper Versions?

**That there is a dispute.** Whether a library should publish `<2.0.0`-style upper bounds is among the
sharpest live disagreements in Python packaging, and it has produced ecosystem-wide incidents in both
directions.

**The camps.** *Cappers* hold that a library should express the range it has actually been tested
against, and that a resolver silently installing an untested major is how consumers get mystery
breakage. *Non-cappers* hold that upper bounds are predictions about unreleased software, usually
wrong, and that a cap in a widely-depended-upon library propagates into an unsolvable resolution graph
downstream.

**The background.** The dispute sharpened as Python's resolver became strict. A modern resolver
refuses to install rather than pick an inconsistent set, so a stale cap in one transitive dependency
can block an entire environment — and the consumer often cannot fix it, not controlling the capping
package. Meanwhile several high-profile majors broke large numbers of uncapped consumers, which is the
cappers' evidence.

**Capping — strengths.** Encodes tested reality rather than hope; prevents a silent upgrade into a
known-incompatible major; gives the maintainer a window to test and release before consumers are
exposed. For first-party pre-1.0 siblings — where `0.y` bumps really are major, as in
`juniper-service-core>=0.2.0,<0.6.0` — the cap is simply accurate.

**Capping — weaknesses.** A cap is a claim about software that does not exist. It goes stale the day
the next major ships, and until you release, every consumer is blocked. In a deep tree one stale cap
can make an environment unsolvable.

**Capping — risks.** Abandonment is the serious one: an unmaintained capping package becomes a
permanent ceiling on everything downstream, with forking or resolver overrides the only remedies.

**Capping — guardrails.** Cap only where you have a *reason*, and record it next to the pin — the
meta-package's `pyproject.toml:36-42` comment is the model. Automate the bump with a scheduled job
testing against the next major. Prefer capping first-party pre-1.0 dependencies, whose release you
control, over third-party ones you do not.

**Not capping — strengths.** Nothing goes stale; consumers adopt a new major immediately and pin in
their own application, which is where environment-level pinning belongs; the resolution graph stays
solvable.

**Not capping — weaknesses.** A breaking major reaches consumers before you have tested against it,
and the failure looks like *your* library breaking. You find out from bug reports.

**Not capping — risks.** For a wide API surface against a fast-moving dependency, the uncapped
position amounts to continuous unpaid integration testing performed by users.

**Not capping — guardrails.** Run CI against the dependency's pre-release and main branch on a
schedule, so you learn about a break before your users do. Publish a cap *reactively* the moment an
incompatibility is confirmed — a reactive cap is accurate by construction, where a speculative one is
a guess.

**Recommendation** (as a recommendation): floors always; no speculative upper bounds on third-party
dependencies; reactive caps the moment an incompatibility is proven; speculative caps only on
first-party pre-1.0 dependencies whose release you control — exactly the split the Juniper pins
arrived at.

---

### III.6 Typing and the Type-Checked Contract

#### Overview

Annotations in your source are not a contract with anyone until they are *shipped* in a form
downstream tools trust. That is a packaging decision, not a coding one, and it is possible to do all
the typing work and none of the shipping — exactly what happened to two of these five packages.

#### Background

**PEP 561** ([Distributing and Packaging Type Information](https://peps.python.org/pep-0561/)) defines
how a type checker decides whether an installed package's annotations may be used. The mechanism is a
marker file, `py.typed`, inside the package directory. Its presence says "my annotations are intended
for consumers"; its absence means a conforming checker ignores everything in the package, however
thoroughly annotated. This is verifiable in mypy's source: `mypy/modulefinder.py:887` describes
computing "the search paths as specified in PEP 561", `:354` performs the literal
`isfile(dir_path/"py.typed")` check, and `:99-103` defines the message emitted when it is missing.

Shipping the marker takes two steps, and skipping the second is the classic error: the file must exist
in the package directory *and* the build backend must include it in the wheel — otherwise it is
present in your source tree, absent from the distribution, and invisible in CI because your own checks
run against the source tree.

**Inline annotations versus stubs.** Inline annotations live with the code, cannot drift, and are the
default for anything you control. Stub files (`.pyi`) answer three cases: typing a package you do not
own (the `types-*` distributions), typing C extensions with no Python source, and expressing a
signature the runtime cannot represent. A stub for your own pure-Python package is a second copy of
every signature and will drift.

#### The Finding: Written but Not Shipped

All three client packages ship the marker and declare it:

| Package                     | Marker file                          | Declaration            | `Typing :: Typed` |
|-----------------------------|--------------------------------------|------------------------|-------------------|
| `juniper-data-client`       | `juniper_data_client/py.typed`       | `pyproject.toml:73-74` | `:25`             |
| `juniper-cascor-client`     | `juniper_cascor_client/py.typed`     | `pyproject.toml:76-77` | `:25`             |
| `juniper-recurrence-client` | `juniper_recurrence_client/py.typed` | `pyproject.toml:61-62` | `:25`             |

Each declaration is the same two lines, and they are what makes the marker survive the build:

```toml
[tool.setuptools.package-data]
juniper_data_client = ["py.typed"]
```

Neither shared package has one. There is no `py.typed` anywhere under
`juniper-service-core/juniper_service_core/` or `juniper-observability/juniper_observability/`, in the
source trees or in the copies installed into the `JuniperCascor1` environment, and neither
`pyproject.toml` mentions it. Running mypy 2.1.0 on CPython 3.13.13 against a file importing all three:

```text
probe.py:4: error: Skipping analyzing "juniper_observability": module is installed,
    but missing library stubs or py.typed marker  [import-untyped]
probe.py:5: error: Skipping analyzing "juniper_service_core": module is installed,
    but missing library stubs or py.typed marker  [import-untyped]
Found 2 errors in 1 file (checked 1 source file)
```

The `juniper_data_client` import on the preceding line produces nothing, because it ships the marker.

What makes this the sharpest example here is that both shared packages are thoroughly and modernly
annotated — `from __future__ import annotations`, `str | None` unions, `Protocol` definitions, a
`TypeVar`-parameterised helper — and `juniper-service-core` went further, adding a 73-line
`TYPE_CHECKING` block (`juniper_service_core/__init__.py:38-110`) whose stated purpose (`:39-43`) is
"to make every lazily-exported name resolvable for type checkers". That is maintenance performed *for*
downstream checkers by a package those checkers refuse to read. Two empty files close the gap.

One inconsistency in the other direction: `juniper-recurrence-client` ships `py.typed` and the
`Typing :: Typed` classifier but has no mypy configuration at all — no `[tool.mypy]`, no `mypy.ini`,
no `setup.cfg` — while both siblings run `strict = true`
(`juniper-data-client/pyproject.toml:88-93`, `juniper-cascor-client/pyproject.toml:89-94`). The
package making the strongest typing promise — six `Literal` annotation sites, more than the other four
packages hold between them — is the one with nothing checking it. And `juniper-cascor-client/pyproject.toml:90` sets `python_version = "3.11"` while `:12`
declares `requires-python = ">=3.12"` — harmless today, and it will silently mask a 3.12-only
construct tomorrow.

#### Protocol, Generics, and the Precise Tools

**`Protocol`** ([PEP 544](https://peps.python.org/pep-0544/), cited by name in CPython 3.13's
`typing.py:2200`) gives structural typing: a parameter typed as a Protocol accepts anything with the
right members, with no inheritance and no import from you — which makes it the right tool for an
extension point (III.7). `juniper-service-core` defines two, `CommandExecutor`
(`juniper_service_core/websocket/commands.py:37-57`) and `WorkerTaskProtocol`
(`workers/coordinator.py:92-120`), both `@runtime_checkable`. The precision that matters:
`@runtime_checkable` makes `isinstance` work, and `isinstance` against a Protocol checks only that the
*attributes exist* — not signatures. An object with a `parse_result` attribute of any shape passes.
Runtime checkability buys a guard, not a guarantee.

**Generics and variance.** A `TypeVar` at a boundary lets a return type depend on an argument type.
`juniper-observability` has exactly one, the simple correct use
(`T = TypeVar("T")` at `juniper_observability/prometheus_helpers.py:48`, applied at `:88-93`) —
`def register_or_reuse(factory: Callable[..., T], name: str, *args: Any, **kwargs: Any) -> T`. Pass
`Counter`, get a `Counter`. No variance question arises, because variance only becomes a question for
a generic *class* — a `Container[T]` deciding whether `Container[Dog]` is usable where
`Container[Animal]` is expected. None of the five packages defines one, so these libraries never
confront variance. The rule for when you do: a container you only read from can be covariant, one you
only write to contravariant, one you do both invariant — which is why `list` is invariant.

**`Literal`, `TypedDict`, `overload`.** `Literal` earns its place for closed sets of string or int
values (III.3). `TypedDict` earns its place for a dictionary with a known fixed key set — exactly what
every one of these clients returns. `@overload` earns its place when a return type genuinely depends
on an argument's value. Across all five packages: `Literal` appears ten times in two packages — seven
in `juniper-recurrence-client` (one import, six annotation sites) and three in `juniper-observability`
(one import, two closed status enums in `health/models.py`); `TypedDict` zero times; `@overload` zero
times.

#### `Any` as a Contract Hole

`Any` disables checking in both directions. A `Dict[str, Any]` return means a caller can write
`result["totl_count"]` and `result.status_code` and neither is an error.

Sometimes it is right, and one instance here is well argued.
`juniper_cascor_client/observability.py:35` declares `_unrecognized_counter: Optional[Any] = None`,
reasoning at `:32-34`: typed as `Any` "so callers can `.labels(...).inc()` without MyPy tripping over
the runtime `Optional[object]` placeholder we'd otherwise need to keep the prometheus-client import
optional" — a deliberate, bounded hole in one module private, with the alternative considered.
Contrast `register_info_or_update(...) -> Any`
(`juniper_observability/prometheus_helpers.py:214-218`), sitting beside three siblings that return
`T`. The return is a `prometheus_client.Info`, and typing it would require importing the class the
module is careful not to import eagerly — so the `Any` is a consequence of the lazy-import design
rather than a typing choice. Real tension, resolvable with a `TYPE_CHECKING` import and a string
annotation, and worth knowing you are paying it.

**Type checkers as a compatibility gate.** The under-used capability: a checker in CI catches
signature-level breaking changes before release. Run it against a small file exercising your public
surface the way a consumer would, and a removed parameter or narrowed return type becomes a CI failure
rather than a downstream bug report. Two of the three clients have the checker configured; none uses
it this way.

#### Judgement Calls

- **Ship `py.typed`?** As soon as annotations are more right than wrong. It is opt-in by design, and
  withholding it discards work already done.
- **Strict from the start?** Enabling `strict = true` later means a large one-time cleanup; at package
  creation it costs nothing.
- **Model the response or return `dict`?** Genuinely contested, and the biggest open typing decision in
  these packages — the Controversy block at the end of this section argues it out.

#### Tradeoffs

| Choice                   | Buys                                              | Costs                                                      |
|--------------------------|---------------------------------------------------|------------------------------------------------------------|
| Ship `py.typed`          | Downstream checking, completion, refactor safety  | Annotations become a contract you must not break           |
| Inline annotations       | Cannot drift; single source                       | Runtime import cost unless typing-only imports are guarded |
| Stub files               | Types for code you cannot annotate                | A second copy of every signature                           |
| `Protocol` at boundaries | Callers need no import or inheritance             | `isinstance` checks members, never signatures              |
| `Any` returns            | No modelling work; survives server-side additions | No checking at all for consumers of that value             |

#### Best Practices

- Create `py.typed` and declare it in `package-data` in the same commit as your first annotations; add
  the `Typing :: Typed` classifier so it is discoverable.
- Verify shipping, not authoring: `python -m zipfile -l dist/*.whl | grep py.typed`.
- Run the checker in CI — `py.typed` without a checker is a promise nobody verified — and keep its
  `python_version` equal to your `requires-python` floor.
- `Protocol` for extension points; concrete classes only when you intend subclassing.
- Guard typing-only imports with `TYPE_CHECKING` plus `from __future__ import annotations`.

#### Common Failure Modes

- **Annotated but not marked.** Full annotations, no `py.typed`, every downstream checker reports
  `[import-untyped]` — the state both shared packages are in.
- **Marked but not shipped.** The file is in the repository, `package-data` is missing, the wheel has
  no marker, and local checks pass because they run against source.
- **Marked but not checked.** The marker ships, no checker runs, annotations rot.
- **`Any` creep.** One `Any` at a boundary propagates through every downstream inference.
- **Stale checker target.** A `python_version` below your supported floor hides constructs that fail
  for real users.

#### Error Handling

Type errors are compile-time-adjacent, not runtime. Do not add `isinstance` checks at every public
entry point to "enforce" annotations — that duplicates the checker's job at runtime cost. Do validate
what the type system cannot express: a URL with no host, an integer outside a range, a
mutually-exclusive combination of optional arguments. That is exactly the line
`juniper_recurrence_client/client.py:183-184` draws — `base_url: str` is the type, "must include a
host" is the validation.

#### Controversy: Typed Response Models versus Raw Dictionaries

**That there is a dispute.** For an HTTP client, what should a call return: a declared type whose
fields the checker knows, or the decoded JSON body as a plain dictionary? Forty-five of the sixty-one
public methods across these three clients return `Dict[str, Any]` / `dict[str, Any]`, and no package
here defines a single `TypedDict` or `@overload` — so the ecosystem has taken a side, and the question
is whether it is the right one. It is not settled by "types are good".

**The camps.** *Modellers* hold that an untyped dictionary is a hole in an otherwise checked contract:
`result["totl_count"]` and `result.status_code` are both accepted by every tool you own, so a client
shipping `py.typed` makes a promise it does not keep past its own return statement. *Dictionarians*
hold that a client's job is to deliver the server's response, that any model in the client is a
hand-copy of a schema owned elsewhere, and that the copy drifts the first time the server adds a field.

**The background.** The split follows the dependency direction: client and server are usually separate
distributions on separate release cadences, so the schema must be duplicated or imported — and
importing makes the client depend on the server package, inverting the arrow the client exists to
preserve.

That is a false dilemma as stated, and the missing third option is the one Part II of this primer is
about. **Generate the client types in CI from the server's published OpenAPI document.** Nobody
hand-copies anything, nothing is imported across the dependency arrow, and drift stops being silent:
regenerate on every build, diff the result, and a server-side rename is a *failing build* in the client
repository rather than a `KeyError` in someone's production. `datamodel-code-generator` emits models
(Pydantic or `TypedDict`) from a schema document; `openapi-python-client` emits a whole typed client.
The cost moves from maintaining a copy to maintaining a pipeline — the generated code has to be
reviewable, the generator's output style is not yours, and you have acquired a build-time dependency on
a document the other team owns — but the Modelling camp's headline weakness, "every model is a second
copy that drifts", is answered rather than mitigated.

The reason this ecosystem cannot take that option yet is worth stating precisely, because it is a
property of the *document*, not of the tooling. Generation is only as good as the schema, and
`juniper-cascor` publishes exactly one `response_model=` across forty-seven route decorators
(`src/api/routes/health.py:130`, `ReadinessResponse`). Generate against that document and forty-six of
its operations come back returning an unmodelled body — `dict[str, Any]` with a build step. The
generated-client argument is therefore an argument for *first* declaring response models server-side;
III.6's finding and Part II's are the same finding seen from two ends. This ecosystem shows both halves
of the older dilemma too. Recurrence's *server* declares real response models —
`@router.post("/v1/train", response_model=TrainResponse)` (`juniper_recurrence/routers/training.py:37`)
against `TrainResponse` (`juniper_recurrence/schemas.py:145-151`, four fields), seven
`response_model=` declarations in all; `juniper-data` has fifteen, `juniper-cascor` one. Its client's
`train` (`juniper_recurrence_client/client.py:291-310`) returns `dict[str, Any]` anyway. The two live
in the *same repository*, so drift would be CI-checkable — but the client depends only on `requests`
and `urllib3` (`juniper-recurrence-client/pyproject.toml:27-30`), so importing `TrainResponse` would
drag the whole app and Pydantic into every client install.

**Modelling — strengths.** The caller gets what the `py.typed` marker promised: completion, typos
caught at author time, and a rename surfacing as a checker error at every call site rather than a
`KeyError` in production. It also creates one place where a schema change is visible — today the fact
that `/v1/train` returns `final_metrics`, `n_epochs`, `stopped_reason`, `dataset` exists in the client
only as prose.

**Modelling — weaknesses.** Every *hand-written* model is a second copy of a schema you do not own —
the qualifier matters, because generation removes this weakness and nothing else does. Building the
model from a *runtime* model rather than a typing construct also buys that model's semantics. A Pydantic v2
model drops unknown fields by default — on pydantic 2.13.3, validating
`{"n_epochs": 3, "new_server_field": "kept?"}` against a one-field model yields `{"n_epochs": 3}` and
no attribute for the extra. That is data loss, not a missing annotation: a caller who upgraded the
server and not the client cannot see the new field at all.

**Modelling — risks.** The client becomes the bottleneck for every server addition, and the pressure
that creates is to widen the model until it is `dict[str, Any]` with extra steps. The other risk is
structural: importing the server's models to avoid duplication inverts the dependency arrow and drags a
heavy install into every consumer of a thin client.

**Modelling — guardrails.** Generate rather than transcribe wherever the server publishes a document
worth generating from: `datamodel-code-generator` into `TypedDict`s keeps the runtime free of the
server's models, and a CI job that regenerates and fails on a diff converts every schema change into a
reviewable pull request. Where the document is too thin for that — cascor's one `response_model` in
forty-seven routes — fix the server first; generating from a schema that says nothing produces types
that say nothing. Failing both, model with a *typing* construct rather than a runtime one, since
`TypedDict` has no validation step and so cannot drop or reject anything the server sends, and use
`total=False` for anything not guaranteed. Where client and server share a repository, as recurrence's
do, add a CI test comparing the key set against the server model's fields, turning silent drift into a
failing check.

**Raw dictionaries — strengths.** They never break on an additive server change, duplicate no schema,
and are honestly typed for what a thin wrapper actually knows: the client did not validate the body, so
claiming a shape would overstate what it verified. Where callers hand the payload straight to a logger,
a template, or `json.dumps`, a model buys nothing and costs a conversion.

**Raw dictionaries — weaknesses.** `Any` disables checking in both directions and propagates through
every downstream inference, so one dictionary return un-checks a great deal of consumer code. The shape
then lives only in a docstring — and III.3's `create_network` shows where that ends: it cannot even
drift detectably, because there is nothing to drift from.

**Raw dictionaries — risks.** The response shape becomes public by use rather than by declaration.
Consumers index the keys they need, those keys become a contract nobody wrote down, and a server-side
rename breaks them with nothing in either repository able to see the connection.

**Raw dictionaries — guardrails.** Keep the promise honest: document the key set next to the method,
return the decoded body untouched so callers can adopt fields you have not modelled, and do not let
`Dict[str, Any]` spread from return values into parameters, where it removes checking on the way in
too.

**Recommendation** (as a recommendation): `TypedDict` with `total=False` — the compromise both camps
can accept, and the one these packages left on the table. It is a plain `dict` at runtime (no
validation, no dropped fields, no new dependency) and a checked shape at type-check time. For a client
already shipping `py.typed`, converting `-> dict[str, Any]` to `-> TrainResponseDict` costs nothing at
runtime and closes the gap between the marker and what it actually guarantees. Reserve full runtime
models for responses you genuinely intend to validate.

One qualification the compromise is usually sold without, and the Dictionarians are entitled to it.
Forward-compatibility survives at *runtime* — the unmodelled key really is in the dict — but not at
*type-check* time. Against mypy 2.1.0, given `class TrainResponseDict(TypedDict, total=False)` with a
single `n_epochs: int`, the expression `r["new_server_field"]` is
`error: TypedDict "TrainResponseDict" has no key "new_server_field"  [typeddict-item]`, while
`r.get("new_server_field")` is not flagged. `total=False` governs the *optionality of declared keys*,
never openness to undeclared ones. So the caller who upgraded the server and not the client can still
reach the new field, but only through `.get()` — a narrower escape hatch than the checked path, and
exactly the property the Raw-dictionaries side defends. The honest form of the recommendation is that
you trade a small, `.get()`-shaped amount of forward-compatibility for checking on everything else.

---

### III.7 Extension Points and Plugin APIs

#### Overview

An extension point is a place where a consumer supplies behaviour. The question is not whether to have
one but how much of your internals it forces you to freeze — every extension mechanism converts some
part of your implementation into a contract.

#### Background

| Mechanism            | Consumer supplies                | You freeze                                                       |
|----------------------|----------------------------------|------------------------------------------------------------------|
| Callback / hook      | A function                       | One signature                                                    |
| `Protocol` injection | An object with the right members | One method set                                                   |
| Registry             | A registration call              | The registration API and dispatch contract                       |
| Entry points         | Package metadata                 | The group name and the loaded object's contract                  |
| Subclassing          | A subclass                       | Your call order, attribute names, and internal method boundaries |

Subclassing is last for a reason: a consumer overriding your method depends not on that method's
signature but on *when you call it, how many times, and what state exists then*. Offering it freezes
your implementation's shape, not merely its interface. Whether that makes subclassing an illegitimate
extension point for a library or just a demanding one is this section's live dispute — the Controversy
block at the end argues both positions and the mechanism behind them.

#### Callbacks and Hooks

The cheapest extension point, and what all three clients use for instrumentation. The type is
published as a named alias so consumers can annotate their own closures
(`juniper_data_client/client.py:106`, identically at `juniper_recurrence_client/client.py:90`):

```python
RequestHook = Callable[[str, str, Optional[int], float, Optional[BaseException]], None]
```

`juniper-data-client` exports it from the root (`juniper_data_client/__init__.py:24`) with the reason
in-comment (`:22-23`): "instrumentation hook type alias exported so consumers can type their hook
closures". Injection is a constructor keyword (`client.py:145`), the default is a *named* no-op rather
than `None` (`:109-122`), and calls happen in a `finally` with swallowed hook exceptions (`:321-330`)
— all covered in III.4. The alias also carries its parameter semantics in a comment block above it
(`client.py:95-105`), including something a bare `Callable` cannot express: "`error is None` is the
canonical success signal — `status` may be set even on the error path... so it's not a reliable
success indicator". That belongs next to a callback type, because a consumer writing a hook will
otherwise guess wrong.

#### Registries and Typed Registrars

`juniper-cascor-client`'s training stream exposes six typed registration methods over one private
mechanism (`juniper_cascor_client/ws_client.py:378-407`):

```python
def on_metrics(self, callback: Callable[[Dict[str, Any]], None]) -> None:
    """Register a callback for metrics messages."""
    self._register(WS_MSG_TYPE_METRICS, callback)
```

— likewise `on_state`, `on_topology`, `on_cascade_add`, `on_event`, `on_candidate_progress`, plus
`on_disconnect` (`:409-432`) with a different payload type. The mechanism underneath is four lines
(`:448-451`) and accepts an arbitrary `message_type: str`.

The design point: the *registrars* are the API and `_register` is not. A closed set of typed methods
gives completion, catches a misspelled message type at author time, and lets each carry its own
docstring — `on_candidate_progress`'s (`:399-406`) explains which server frames it sees and why the
method was added. The cost is that a seventh message type needs a release; an open
`on(message_type, callback)` would not, at the price of every one of those benefits. The
fault-isolation asymmetry from III.4 restates as an extension-point rule: if you invoke consumer code
in a loop, one consumer's exception must not stop the others. `_dispatch_disconnect` (`:459-471`) gets
this right; `_dispatch` (`:453-457`) does not.

#### Protocol-Based Injection

`Protocol` costs a consumer nothing — no import from you, no inheritance, no registration.
`WorkerTaskProtocol` (`juniper_service_core/workers/coordinator.py:92-120`) declares three methods and
states the boundary in its docstring (`:96-99`): "These methods are the *only* place model-specific
schema lives; everything else in the coordinator and the `/ws/workers` stream is generic." Injection
is by constructor argument (`coordinator.py:136-144`):

```python
def __init__(
    self,
    registry: WorkerRegistry,
    protocol: WorkerTaskProtocol,
    *,
    task_reassignment_timeout: float = 120.0,
    health_check_interval: float = 10.0,
    anomaly_detector: Any | None = None,
) -> None:
    ...
```

Note the `*` placement: the two collaborators are positional, everything tunable is keyword-only —
III.3's rule applied deliberately. `CommandExecutor`
(`juniper_service_core/websocket/commands.py:37-57`) is the same pattern for control commands. Its
docstring states the convention (`:41`) — "A service injects any object satisfying this protocol on
`app.state.command_executor`" — and the machinery that performs it is the bridge
(`websocket/bridge.py:90-91`, guarded so a `None` never lands on `app.state`), read back at
`websocket/control_stream.py:230`. A `commands` property declares the closed verb
set; `LifecycleCommandExecutor` (`commands.py:60-`) is the default implementation — the shape worth
copying, since publishing the Protocol *and* a working default means consumers extend only when they
must. The two Protocols use different member conventions (`WorkerTaskProtocol`'s methods have `pass`
bodies, `CommandExecutor`'s are `@abstractmethod` raising `NotImplementedError`); both work, only one
can be usefully inherited from, so pick one per package.

#### Duck-Typed Configuration Lookup

The most interesting trade here deliberately gives up validation
(`juniper_service_core/websocket/control_stream.py:66-69`):

```python
def _setting(websocket: WebSocket, name: str, default):
    """Read a tunable off ``app.state.settings`` with a default (no service settings import)."""
    settings = getattr(websocket.app.state, "settings", None)
    return getattr(settings, name, default) if settings is not None else default
```

`SettingsBase` (`juniper_service_core/settings.py:33-36`) declares exactly four fields —
`service_name`, `host`, `port`, `log_level`. Every WebSocket tunable is read through `_setting`
instead: eleven distinct names across thirteen call sites in two modules.

The benefit is genuine decoupling: the shared package never imports a consuming service's settings
class, and each service declares only the tunables it uses. The cost is that both `getattr` calls have
a default, so a typo'd or absent name silently yields the hard-coded default rather than erroring. Set
`ws_control_rate_limit_per_second` where the library reads `ws_control_rate_limit_per_sec`, and
everything works — at the default rate limit, forever, silently. There are also two byte-identical
copies of `_setting` (`control_stream.py:66-69` and `training_stream.py:40-43`): a duplicated helper
is a small drift surface on a mechanism that is already unvalidated.

#### Entry-Point Plugin Discovery

For plugins from packages you do not know about, the mechanism is `[project.entry-points]` in the
plugin's `pyproject.toml` and `importlib.metadata.entry_points(group=...)` in yours — how pytest finds
plugins, and the right answer when third parties must extend you without your knowing they exist. None
of the five packages uses it, which is correct: every extension here comes from a known first-party
consumer, and constructor injection is simpler, testable without installing anything, and free of the
import-time cost of scanning distribution metadata.

#### Judgement Calls

- **Callback or Protocol?** One function: callback. Several related operations sharing state: Protocol.
- **Entry points?** Only if extenders are strangers. Otherwise inject at construction.
- **Publish a default implementation?** Yes whenever a sensible one exists — it turns your extension
  point from mandatory work into optional work.

#### Tradeoffs

| Mechanism          | Stability cost                                 | Consumer cost                            |
|--------------------|------------------------------------------------|------------------------------------------|
| Callback           | One signature frozen                           | Write one function                       |
| Protocol injection | One method set frozen                          | Write a small adapter class              |
| Typed registrars   | Registrar set frozen; new types need a release | Nothing; completion works                |
| Entry points       | Group name and loaded contract frozen          | Publish a distribution                   |
| Subclassing        | Internal call order frozen                     | Inherit — and re-verify on every upgrade |

#### Best Practices

- Publish the callback type as a named alias and export it; default hooks to a named no-op, never
  `None`.
- Isolate faults when invoking consumer code in a loop.
- Prefer `Protocol` over an ABC: no inheritance, no import, and it works on objects that already exist.
  Ship a default implementation alongside every Protocol.
- If you must support subclassing, document which methods are override points, treat their call order
  as public, and never call one from `__init__`.

#### Common Failure Modes

- **The unisolated dispatch loop.** One bad listener kills the stream for every other listener.
- **Silent configuration typos.** A duck-typed lookup with a default turns a misspelling into a
  permanent, invisible default.
- **The accidental subclass contract.** Consumers subclass a class never intended as an extension
  point, and your next internal refactor breaks them.
- **The `None` default hook.** Every call site grows an `if hook is not None:` guard, and one of them
  eventually gets forgotten.

#### Error Handling

Consumer code is untrusted code: wrap each invocation, log with `exc_info=True`, continue — the
`_dispatch_disconnect` shape. The exception is a hook whose purpose is to veto (an authorisation or
validation callback); those must be allowed to raise, and that should be documented at the type alias.

#### Controversy: Is Subclassing a Legitimate Extension Point?

**That there is a dispute.** "Prefer composition over inheritance" is repeated often enough to sound
settled, and it is not. The contested question is narrow: may a *library* publish a class it expects
consumers to subclass, or should every extension point be a callback, a Protocol, or an injected
object? The disagreement is between people who agree completely about the fragile base class problem
and differ on what follows from it. `juniper-service-core` takes both sides in one distribution — it
publishes Protocols as its seams and, in `settings.py`, an explicitly subclassable base.

**The camps.** *Composition-only* holds that publishing a subclassable class converts your call order,
attribute names, and method boundaries into a contract you did not intend and cannot see yourself
breaking. *Documented inheritance* holds that this argues for documenting the override points, not for
banning them — that some problems genuinely want a base supplying defaults and shared state, and that a
Protocol with no default implementation merely moves the work onto every consumer.

**The background.** The fragile base class problem is the mechanism: refactoring a class's internal
call sequence is invisible from outside and breaks every subclass, while your own tests stay green
because you have no subclasses. Python sharpens it twice. Every method is an override point by default;
and `typing.final` — often reported as absent — exists but does not do what its name suggests. Its own
documentation is explicit: "There is no runtime checking of these properties" (CPython 3.13
`typing.py:2769`, quoted from `:2791`). `@final` is advice to a type checker, constraining the consumer
who runs one and nobody else.

The distinction the dispute usually collapses is between overriding *behaviour* and supplying *data*.
`SettingsBase` (`juniper_service_core/settings.py:17-36`) is a published subclassing point — the module
docstring says so plainly (`:4-5`), "Concrete services subclass it and set their own `env_prefix`", with
a two-line worked example in the class docstring at `:23-24` — and it carries none of the fragility
above, because a subclass overrides
`model_config` and adds fields rather than interleaving behaviour with the base's. `pydantic-settings`
owns the control flow; the subclass is a declaration.

**Documented inheritance — strengths.** Least consumer code for a small variation: inherit, override
one thing, keep every default. Where the base genuinely owns the control flow it is the only mechanism
that fits — a Protocol cannot express "and also collect these fields from the environment under this
prefix". It also answers the composition camp's real weakness: `WorkerTaskProtocol`
(`juniper_service_core/workers/coordinator.py:92-120`) ships no default implementation anywhere in the
package, so every consumer writes all three methods from scratch.

**Documented inheritance — weaknesses.** The frozen surface is far larger than the documented one: call
order, attribute names, and method boundaries all become contract, and none appear in a signature.
`super()` chains fail in ways that are hard to attribute. And because `@final` is checker-only, "not an
override point" is a request rather than a constraint.

**Documented inheritance — risks.** A refactor breaks consumers at a distance with nothing in your
repository able to detect it — which is why it surfaces a release late. The sharpest form is calling an
overridable method from `__init__`: the consumer's override then runs against a half-constructed
object, before their own `__init__` has set anything up.

**Documented inheritance — guardrails.** Name the override points and treat their call order as public
API under the same SemVer rules as a signature. Never call one from `__init__`. Mark everything else
`@final` — checker-only, but it states intent. Prefer subclasses that supply data over subclasses that
supply behaviour, the property that makes `SettingsBase` safe. And keep one real subclass in your own
test suite: it is the only thing that will notice a call-order change.

**Composition-only — strengths.** A Protocol freezes a method set and nothing else. The consumer needs
no import, no inheritance, and no registration; the implementation can be an object that already
exists; a test double is a small class rather than a subclass of your machinery. `WorkerTaskProtocol`'s
docstring draws the boundary explicitly (`coordinator.py:96-99`): these methods "are the *only* place
model-specific schema lives".

**Composition-only — weaknesses.** It supplies no defaults and no shared state, so unless you also ship
an implementation the extension point is pure obligation. The runtime guarantee is also weaker than an
ABC's: `@runtime_checkable` makes `isinstance` work, but the check confirms only that the attributes
exist, never that their signatures match (III.6).

**Composition-only — risks.** Publishing a concrete default beside the Protocol — the right move —
invites the inheritance you were avoiding: consumers subclass `LifecycleCommandExecutor`
(`juniper_service_core/websocket/commands.py:60`) instead of implementing `CommandExecutor` (`:37-57`),
and you get the fragile-base-class problem without having designed for it. Its docstring does not say
whether that is supported, so the answer is whatever the first consumer assumes.

**Composition-only — guardrails.** Ship a working default alongside every Protocol, so extension is
optional rather than mandatory. Pick one member convention per package: `juniper-service-core` has both
— `WorkerTaskProtocol`'s methods with `pass` bodies, `CommandExecutor`'s as `@abstractmethod` raising
`NotImplementedError` — and only the second can be usefully inherited from. Say in the default
implementation's docstring whether subclassing it is supported, and mark it `@final` if it is not.

**Recommendation** (as a recommendation): composition by default, with subclassing legitimate in one
specific shape — when the base owns the control flow and the subclass supplies data or declarations
rather than behaviour interleaved with yours. `SettingsBase` is that shape and is the right call, not a
compromise. It is not legitimate when it exists only to spare the consumer an adapter class: that
saving is small and one-time, while the frozen call order is permanent. Either way, say which at the
class — an undeclared answer is decided by your first consumer, and you find out when you refactor.

---

### III.8 Packaging and the Distribution Boundary

#### Overview

The distribution boundary is not the import surface, and confusing the two causes real bugs. The
import surface is what `import` reaches; the distribution boundary is what `pip` installs. Different
names, versions, granularity, and failure modes — a wheel can install perfectly and be broken at
import, and a package can import perfectly from a source tree and be broken in every wheel you ship.

#### Background

The `[project]` metadata consumers actually feel: **`requires-python`**, a floor `pip` enforces (all
five packages declare `>=3.12`); **`dependencies`**, mandatory at install time and *not* the same as
"imported at import time"; **`[project.optional-dependencies]`**, the extras, each installable as
`pkg[name]`; and **`classifiers`**, mostly discovery metadata with the notable exception of
`Typing :: Typed`, which is how a consumer learns you ship annotations without downloading the wheel.

#### Self-Referential Extras and Package Data

An extra may depend on its own distribution with other extras, which composes an "everything" group
without repeating members — `juniper-observability/pyproject.toml:29-32`:

```toml
[project.optional-dependencies]
prometheus = ["prometheus-client>=0.20.0"]
sentry = ["sentry-sdk[fastapi]>=2.0.0"]
all = ["juniper-observability[prometheus,sentry]"]
```

`all` names no packages of its own, so adding a third extra to the aggregate is a one-token edit. The
same idiom appears for development groups — `juniper-data-client/pyproject.toml:55` and
`juniper-cascor-client/pyproject.toml:58` both open `dev` with `"juniper-<name>-client[test]"`, so
`dev` is `test` plus tooling and cannot drift from it. The meta-package uses it at the top of the tree
(`juniper-ml/pyproject.toml:71-73`): `all = ["juniper-ml[clients,worker,servers,tools,recurrence]"]`.

Anything that is not a `.py` file needs an explicit inclusion rule, and `py.typed` is the case that
bites. The three clients each declare it (`juniper-data-client/pyproject.toml:73-74`,
`juniper-cascor-client/pyproject.toml:76-77`, `juniper-recurrence-client/pyproject.toml:61-62`); the
two shared packages have neither the file nor the declaration. The failure mode is nasty because it is
invisible locally — your own checks run against the source tree, where the marker exists, so
everything passes, and only a consumer installing your wheel sees the difference. The check is one
command:

```bash
python -m build --wheel && python -m zipfile -l dist/*.whl | grep py.typed
```

#### Install-Time Dependencies Are Not Import-Time Dependencies

`juniper-service-core` makes this distinction unusually visible, and it is easy to over-claim.
`juniper-service-core/pyproject.toml:24-38` declares five *mandatory* dependencies — `fastapi`,
`pydantic`, `pydantic-settings`, `juniper-model-core`, `numpy`. None is optional; a plain
`pip install` brings all five. Yet the PEP 562 scheme means none is imported by
`import juniper_service_core` — measured in III.2 at two new top-level modules, no third-party among
them.

So the guarantee at `juniper_service_core/__init__.py:10-16` is an *import-time* property, not an
install-time one. What it buys is what the docstring says: a publish-verification step can install the
wheel with `--no-deps` and confirm the package imports, catching a real error class — a broken
`__init__.py`, a module missing from the wheel, a syntax error under a newer Python — without
provisioning a full dependency tree. It does not make the package usable without dependencies. The two
`pyproject.toml` comments documenting this tension are worth reading together: `:28-31` explains that
`juniper-model-core` must be on PyPI before this package publishes, and `:33-36` that `numpy` "loads
only when `.routes` is accessed, so the dependency-free top-level `import juniper_service_core` still
holds". Both are precise about which property they mean.

This is the correction to make against III.2's Controversy, where "optional heavy dependencies" is the
strength most often claimed for the lazy position. A lazy import defers *cost*; what makes a dependency
optional is moving it into `[project.optional-dependencies]`, a metadata decision taken here for none
of the five. Laziness makes that move *available* — you cannot mark a dependency optional if your
`__init__.py` imports it — but they are not the same edit, and a package that has done only the first
still installs everything.

#### Names, Meta-Packages, and Namespaces

`pip install juniper-data-client` gives `import juniper_data_client`. The hyphen-to-underscore
transform is conventional, not required, and packages exist where the two names are unrelated — a real
usability trap, since a user who knows the import name cannot always guess the install command and a
`ModuleNotFoundError` does not say what to install. The Juniper packages are consistent, with one
genuine divergence: `juniper-recurrence-client` is published from a *subdirectory* of the
`juniper-recurrence` repository, so repository, distribution, and import names are three different
strings — a documentation problem, and why `[project.urls]`
(`juniper-recurrence-client/pyproject.toml:49-52`) pointing at the right repository matters.

A **meta-package** installs other distributions and contains no code. `juniper-ml` is the canonical
form, and says so in two lines — `dependencies = []` (`pyproject.toml:26`) and, at `:75-76`:

```toml
[tool.setuptools]
packages = []
```

Zero mandatory dependencies, zero packages. Everything is an extra — `clients`, `worker`, `servers`,
`tools`, `doc-tools`, `recurrence`, `all` — so `pip install juniper-ml` installs metadata and nothing
else. Meta-packages earn their place when a set of distributions is versioned and released together
and consumers think of them as one thing; they stop earning it when release cadences diverge, at which
point the meta-package's own version means nothing and its pins go stale. The `doc-tools` extra shows
its version of backward compatibility: the comment at `pyproject.toml:40-42` explains the group is
"kept as a distinct extra for back-compat with `pip install juniper-ml[doc-tools]` even though it is
also included in the broader `tools` aggregate below". An extra name is a public API — someone's CI
has it in a `pip install` line — and removing it is a breaking change with no deprecation mechanism
available, because nothing warns when an extra is requested.

**Namespace packages** let several distributions contribute modules under one shared parent
(`acme.foo` from one wheel, `acme.bar` from another). Since 3.3 the implicit form needs no
`__init__.py` in the shared parent — which is also the trap, since an accidentally-missing
`__init__.py` silently creates one, and it then behaves subtly differently for tooling and packaging.
None of the five packages uses one, and unless you are building a plugin ecosystem under a shared
prefix, you do not need one.

#### Judgement Calls

- **Extra or separate distribution?** An extra when the optional code lives in your package and only
  its dependency is optional; a separate distribution when the code itself is separable.
- **Is a meta-package worth it?** Only with coordinated releases. Otherwise it is a pin set that goes
  stale.
- **How many extras?** Enough that a consumer can avoid a dependency they genuinely do not want; few
  enough that the matrix is testable.

#### Tradeoffs

| Choice                        | Buys                                          | Costs                                                 |
|-------------------------------|-----------------------------------------------|-------------------------------------------------------|
| Extras for optional deps      | One distribution, one version, one repository | Every extra combination is an untested install path   |
| Self-referential `all`        | No duplication; additive by one token         | Slightly obscure to readers who have not seen it      |
| Meta-package                  | One install command; coordinated version      | Its version means nothing once cadences diverge       |
| Mandatory deps + lazy imports | Fast, verifiable import                       | Reviewers must know the guarantee is import-time only |

#### Best Practices

- Declare `requires-python` at your tested floor and keep every tool's target in step with it.
- Declare `py.typed` in `package-data` and verify it in the built wheel, not the source tree.
- Compose aggregate extras self-referentially, and treat extra names as public API — never remove one
  without a major bump.
- Keep the import name a mechanical transform of the distribution name.
- Install the built wheel in a clean environment and import it in CI — the only check that catches
  "works in the source tree, broken in the wheel".

#### Common Failure Modes

- **Missing package data.** `py.typed`, stubs, or templates in the repository and absent from the
  wheel. Local checks pass; consumers see nothing.
- **The untested extra.** `pkg[a]` and `pkg[b]` are each tested; `pkg[a,b]` conflicts and nobody
  installed it before a user did.
- **Stale meta-package pins.** A member ships a breaking minor and the meta-package's floor admits it.
- **Import/distribution name confusion.** A `ModuleNotFoundError` naming a module the user cannot map
  to an install command.
- **Accidental namespace package.** A missing `__init__.py` changes packaging behaviour in ways that
  surface only at install time.

#### Error Handling

Packaging failures should be loud at install or import, never later. Two mechanisms here do that: the
`--no-deps` import check that `juniper-service-core`'s lazy surface exists to enable, and
`enforce_dependency_floors` (`juniper_service_core/dependency_floors.py:213-217`), which turns a
below-floor installed wheel into a refusal to start rather than a subtle runtime failure — the
docstring names the incident it prevents (`:10-13`), a wheel below its declared floor that "passed
unit tests but broke the live app". Together they cover both halves of the distribution boundary: the
wheel is importable, and what got installed alongside it is what the code expects.

### III.9 Part III Worked Example — A Client Library That Does Not Lose Information

This example is the corrected version of the design defects Part III identified in the three real Juniper client libraries. Each correction is a direct response to something observable in the shipped code.

| Defect in the real clients                                                                                                   | Correction here                                                                                                                 |
|------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------|
| Exceptions carry only a formatted string — no `.status_code`, no `.response` — so callers cannot branch without parsing text | Every HTTP-derived error preserves `status_code`, the parsed problem-details `payload`, and the `request_id` as real attributes |
| One client retries `POST`, `PATCH`, and `DELETE` on transient 5xx with no idempotency key                                    | Non-idempotent methods are retried **only** when an idempotency key is supplied                                                 |
| A single scalar timeout covers connect, read, write, and pool                                                                | Timeouts are separated, with per-call override                                                                                  |
| `create_network(**kwargs: Any)` types nothing and forwards blind                                                             | Public methods are keyword-only with `Literal` types for closed enums                                                           |
| Retry exhaustion collapses a typed 503 into the base exception, losing the status                                            | The final response is mapped before raising, so the typed error survives exhaustion                                             |
| No jitter on backoff                                                                                                         | Full jitter, with `Retry-After` honoured when the server supplies it                                                            |

The instrumentation hook is worth studying as a small ergonomics lesson: it defaults to a **named no-op function** rather than `None`, so the call site has no branch; it fires in a `finally` so failures are observed as well as successes; and its own exceptions are swallowed with an explicit comment, because instrumentation that can break the caller is worse than no instrumentation.

The exception hierarchy is deliberately flat — one base plus typed leaves — matching the shape the real clients already use. The improvement is not the shape; it is that the objects carry their information.

<!-- example-file: wellformed_client.py -->
```python
"""A well-formed client library: the corrected design.

Motivation (three sibling packages, three different mistakes)
------------------------------------------------------------
``juniper-data-client``, ``juniper-cascor-client`` and
``juniper-recurrence-client`` were written by one author, on one base library,
in one month, and disagree with each other on nearly everything:

* **Exceptions carry only a formatted message string.** No ``.status_code``, no
  ``.response``, so telling 404 from 409 means parsing English out of
  ``str(exc)``. Worse, urllib3's ``RetryError`` (raised on retry exhaustion) is
  caught as a generic ``RequestException`` and mapped to the *base* exception
  type, destroying the status distinction exactly when it matters most.
* **One retries non-idempotent methods.** cascor-client's allow-list is
  ``{GET, POST, DELETE, PUT, PATCH}``, so a 502 silently re-sends
  ``POST /v1/training/start``.
* **One abandons its signature entirely.** ``create_network(**kwargs: Any)``
  names none of its eleven real parameters; they live in the docstring and are
  forwarded blind, so a typo reaches the server as a silently missing field.
* **One flat scalar timeout** (30 s) covers connect, read and write, so "the host
  is unreachable" and "the server is thinking" get the same budget.

This module is what those three should have agreed on: exceptions preserving
``status_code`` / ``payload`` / ``request_id`` and chained with
``raise ... from ...``; retries restricted to idempotent methods **plus**
non-idempotent ones carrying an idempotency key; keyword-only methods with
``Literal`` enums; split connect/read/write/pool timeouts; and an instrumentation
hook with a named no-op default whose failures can never break the caller.

Run the tests with::

    pytest test_wellformed_client.py
"""

from __future__ import annotations

import asyncio
import logging
import random
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
from types import TracebackType
from typing import Any, Final, Literal

import httpx

__all__ = [
    "ApiError",
    "AttemptRecord",
    "ConflictError",
    "DatasetStatus",
    "InstrumentationHook",
    "JobKind",
    "JuniperClient",
    "NotFoundError",
    "RateLimitedError",
    "RetryPolicy",
    "ServerError",
    "Timeouts",
    "TransportError",
    "ValidationError",
    "__version__",
    "null_instrument",
    "parse_retry_after",
]

#: Stands in for the ``_version.py`` + ``dynamic = ["version"]`` pattern: a real
#: package puts this string in ``juniper_client/_version.py`` and has setuptools
#: read it (``[tool.setuptools.dynamic] version = {attr = "..."}``) so
#: ``pyproject.toml`` and the runtime dunder can never disagree. Duplicating the
#: literal in both places is how two of the three real clients ended up shipping
#: a version that contradicts their own metadata.
__version__: Final = "1.0.0"

_logger = logging.getLogger(__name__)

#: RFC 9110 section 9.2.2. A retried idempotent request has the same effect as a
#: single one; POST and PATCH have no such guarantee, which is why they are absent.
IDEMPOTENT_METHODS: Final = frozenset({"GET", "HEAD", "OPTIONS", "TRACE", "PUT", "DELETE"})

DatasetStatus = Literal["ready", "pending", "failed"]
JobKind = Literal["train", "evaluate"]


# --------------------------------------------------------------------------- #
# Exceptions
# --------------------------------------------------------------------------- #
class ApiError(Exception):
    """Base of the public exception hierarchy.

    The hierarchy is deliberately flat -- one base, typed leaves -- so
    ``except ApiError`` catches everything and ``except NotFoundError`` catches
    exactly one thing, with nothing in between to learn. ``status_code is None``
    is the single discriminator between "the server answered" and "we never got
    an answer" (``TransportError``), which is the only structural distinction a
    caller actually needs.

    Attributes:
        status_code: HTTP status, or ``None`` for transport failures.
        payload: Parsed response body (RFC 9457 problem details when available).
            Always a dict, never ``None``, so ``exc.payload.get(...)`` is safe.
        request_id: Server-assigned correlation id, for pasting into a ticket.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        payload: Mapping[str, Any] | None = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.payload: dict[str, Any] = dict(payload or {})
        self.request_id = request_id

    def __repr__(self) -> str:
        return f"{type(self).__name__}({str(self)!r}, status_code={self.status_code}, request_id={self.request_id!r})"


class TransportError(ApiError):
    """No response was received: DNS, connect, TLS, timeout, or a reset socket."""


class NotFoundError(ApiError):
    """404."""


class ConflictError(ApiError):
    """409 -- the resource's state forbids the operation."""


class ValidationError(ApiError):
    """400 or 422 -- the request itself was rejected."""


class RateLimitedError(ApiError):
    """429. ``retry_after`` is the parsed ``Retry-After`` value in seconds, if any."""

    def __init__(self, message: str, *, retry_after: float | None = None, **kwargs: Any) -> None:
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class ServerError(ApiError):
    """5xx."""


_STATUS_MAP: Final[dict[int, type[ApiError]]] = {
    400: ValidationError,
    404: NotFoundError,
    409: ConflictError,
    422: ValidationError,
    429: RateLimitedError,
}


# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class Timeouts:
    """Four budgets, because they answer four different questions.

    A single scalar forces one number to mean both "how long until I accept the
    host is unreachable" (should be short -- failing fast is the point) and "how
    long may the server think about this" (may legitimately be minutes). Collapsing
    them means either fast failure detection or long operations, never both.
    """

    connect: float = 5.0
    read: float = 30.0
    write: float = 10.0
    pool: float = 5.0

    def to_httpx(self) -> httpx.Timeout:
        return httpx.Timeout(connect=self.connect, read=self.read, write=self.write, pool=self.pool)


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    max_attempts: int = 3
    base_delay: float = 0.1
    max_delay: float = 10.0
    retry_statuses: frozenset[int] = frozenset({429, 500, 502, 503, 504})
    #: A server can ask for an unbounded wait; honouring it literally would let one
    #: bad deployment park every worker in the fleet for a day.
    max_retry_after: float = 60.0

    def may_retry(self, *, method: str, has_idempotency_key: bool) -> bool:
        """Idempotent methods always; others only behind an idempotency key.

        This is the whole rule. An idempotency key is a *promise from the server*
        that a duplicate is recognised and replayed, which is exactly the
        guarantee ``POST`` lacks by default. Without a key, a retried POST is a
        coin flip on whether the first attempt already committed.
        """
        if method.upper() in IDEMPOTENT_METHODS:
            return True
        return has_idempotency_key


DEFAULT_TIMEOUTS: Final = Timeouts()
DEFAULT_RETRY_POLICY: Final = RetryPolicy()


# --------------------------------------------------------------------------- #
# Instrumentation
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class AttemptRecord:
    """One HTTP attempt -- including the ones that failed and were retried."""

    method: str
    url: str
    attempt: int
    status_code: int | None
    error: BaseException | None
    duration_s: float
    request_id: str | None


InstrumentationHook = Callable[[AttemptRecord], None]


def null_instrument(record: AttemptRecord) -> None:
    """The default hook: a named function that does nothing.

    A named no-op beats ``None`` for three reasons. The call site stays
    unconditional (no ``if hook is not None`` to forget on a new code path), the
    default is introspectable and mockable, and the type stays
    ``Callable[...]`` instead of ``Callable[...] | None``, so callers never have
    to narrow it.
    """


# --------------------------------------------------------------------------- #
# Client
# --------------------------------------------------------------------------- #
def parse_retry_after(value: str | None, *, now: datetime | None = None) -> float | None:
    """Parse ``Retry-After`` (RFC 9110 section 10.2.3): delta-seconds or an HTTP-date.

    Both forms are legal and real servers emit both. Handling only the integer
    form means silently ignoring the header from anything fronted by a proxy that
    prefers dates.
    """
    if value is None:
        return None
    text = value.strip()
    try:
        return max(0.0, float(int(text)))
    except ValueError:
        pass
    try:
        when = parsedate_to_datetime(text)
    except (TypeError, ValueError):
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    reference = now or datetime.now(timezone.utc)
    return max(0.0, (when - reference).total_seconds())


class JuniperClient:
    """A typed, retry-safe async client owning exactly one connection pool.

    Use it as an async context manager so the pool's lifetime is explicit::

        async with JuniperClient(base_url="https://api.example.com") as client:
            dataset = await client.get_dataset(dataset_id="spiral-v1-abc")
    """

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str | None = None,
        timeouts: Timeouts = DEFAULT_TIMEOUTS,
        retry: RetryPolicy = DEFAULT_RETRY_POLICY,
        instrument: InstrumentationHook = null_instrument,
        transport: httpx.AsyncBaseTransport | None = None,
        rng: random.Random | None = None,
        sleeper: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        if not base_url.strip():
            # Fail at construction, not at the first call: a misconfigured client
            # should not survive long enough to look like a network problem.
            raise ValueError("base_url must be a non-empty URL")

        self._retry = retry
        self._instrument = instrument
        self._rng = rng if rng is not None else random.Random()
        self._sleeper = sleeper
        headers = {"User-Agent": f"juniper-client/{__version__}", "Accept": "application/json"}
        if api_key:
            headers["X-API-Key"] = api_key
        # One pool for the client's whole lifetime: connection reuse is most of
        # the latency win, and a per-call client silently disables it.
        self._http = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            headers=headers,
            timeout=timeouts.to_httpx(),
            transport=transport,
        )

    async def __aenter__(self) -> JuniperClient:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._http.aclose()

    # ---- public API: keyword-only, closed enums typed as Literal ---------- #
    async def get_dataset(self, *, dataset_id: str) -> dict[str, Any]:
        response = await self._request("GET", f"/v1/datasets/{dataset_id}")
        return response.json()

    async def list_datasets(self, *, status: DatasetStatus | None = None, limit: int = 50) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"limit": limit}
        if status is not None:
            params["status"] = status
        response = await self._request("GET", "/v1/datasets", params=params)
        return list(response.json()["items"])

    async def create_job(
        self,
        *,
        kind: JobKind,
        dataset_id: str,
        epochs: int = 10,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Start a job.

        Supplying ``idempotency_key`` is what makes this POST retryable; without
        one the client will surface the first failure rather than risk a
        duplicate run.
        """
        response = await self._request(
            "POST",
            "/v1/jobs",
            json={"kind": kind, "dataset_id": dataset_id, "epochs": epochs},
            idempotency_key=idempotency_key,
        )
        return response.json()

    async def delete_dataset(self, *, dataset_id: str) -> None:
        await self._request("DELETE", f"/v1/datasets/{dataset_id}")

    # ---- transport ------------------------------------------------------- #
    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: Any | None = None,
        params: Mapping[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> httpx.Response:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        retryable = self._retry.may_retry(method=method, has_idempotency_key=idempotency_key is not None)
        attempts = self._retry.max_attempts if retryable else 1

        for attempt in range(1, attempts + 1):
            response: httpx.Response | None = None
            failure: BaseException | None = None
            started = asyncio.get_running_loop().time()
            try:
                response = await self._http.request(method, path, json=json, params=params, headers=headers)
            except httpx.TransportError as exc:
                failure = exc
            finally:
                # In a finally so an attempt is recorded even when it raised --
                # the failures are the interesting half of the telemetry.
                self._fire(
                    AttemptRecord(
                        method=method.upper(),
                        url=path,
                        attempt=attempt,
                        status_code=response.status_code if response is not None else None,
                        error=failure,
                        duration_s=asyncio.get_running_loop().time() - started,
                        request_id=response.headers.get("X-Request-ID") if response is not None else None,
                    )
                )

            last_attempt = attempt == attempts
            if failure is not None:
                if last_attempt:
                    raise TransportError(f"{method} {path} failed: {failure}") from failure
                await self._sleeper(self._backoff(attempt))
                continue

            assert response is not None
            if response.status_code in self._retry.retry_statuses and not last_attempt:
                await self._sleeper(self._backoff(attempt, response=response))
                continue

            if response.status_code >= 400:
                self._raise_for_response(response)
            return response

        raise AssertionError("unreachable: the loop always returns or raises")  # pragma: no cover

    def _backoff(self, attempt: int, *, response: httpx.Response | None = None) -> float:
        """Full-jitter exponential backoff, overridden by a (capped) ``Retry-After``.

        Full jitter -- uniform over ``[0, ceiling]`` rather than exactly
        ``ceiling`` -- is what actually de-synchronises a fleet. Plain exponential
        backoff keeps every client that failed at the same instant colliding at
        every subsequent step.
        """
        if response is not None:
            server_hint = parse_retry_after(response.headers.get("Retry-After"))
            if server_hint is not None:
                return min(server_hint, self._retry.max_retry_after)
        ceiling = min(self._retry.max_delay, self._retry.base_delay * (2 ** (attempt - 1)))
        return self._rng.uniform(0.0, ceiling)

    def _raise_for_response(self, response: httpx.Response) -> None:
        """Map a failing response onto a typed exception, preserving the chain."""
        payload: dict[str, Any]
        try:
            parsed: Any = response.json()
        except ValueError:
            # A non-JSON error body (the HTML 502 a proxy emits when the origin is
            # down) must not surface as a JSONDecodeError escaping a typed client.
            parsed = None
        # A JSON body that is not an *object* (a bare string, or an array) is just
        # as unusable as no JSON at all, so both degrade the same way: salvage a
        # bounded prefix of the raw text rather than discarding the only evidence.
        payload = parsed if isinstance(parsed, dict) else {"detail": response.text[:200]}

        request_id = response.headers.get("X-Request-ID")
        detail = payload.get("detail") or payload.get("title") or response.reason_phrase
        message = f"{response.request.method} {response.request.url.path} -> {response.status_code}: {detail}"

        exc_type = _STATUS_MAP.get(response.status_code)
        if exc_type is None:
            exc_type = ServerError if response.status_code >= 500 else ApiError

        kwargs: dict[str, Any] = {"status_code": response.status_code, "payload": payload, "request_id": request_id}
        if exc_type is RateLimitedError:
            kwargs["retry_after"] = parse_retry_after(response.headers.get("Retry-After"))

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            # "from exc" keeps httpx's own context reachable via __cause__ for
            # anyone debugging, without leaking httpx into the public surface.
            raise exc_type(message, **kwargs) from exc

    def _fire(self, record: AttemptRecord) -> None:
        try:
            self._instrument(record)
        except Exception:
            # Instrumentation is an observer, never a participant. A metrics
            # backend that is down must not convert a successful API call into a
            # failure -- that turns a monitoring outage into a service outage.
            _logger.debug("instrumentation hook raised; ignoring", exc_info=True)
```

<!-- example-file: test_wellformed_client.py -->
```python
"""Tests for wellformed_client.py.

Each test names the real-world defect it pins down. The stub server is a
FastAPI app driven in-process through httpx's ASGITransport, so the suite makes
no network calls and needs no fixtures beyond the app itself.
"""

from __future__ import annotations

import random
from typing import Any

import httpx
import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

from wellformed_client import (
    ApiError,
    AttemptRecord,
    ConflictError,
    JuniperClient,
    NotFoundError,
    RateLimitedError,
    RetryPolicy,
    ServerError,
    Timeouts,
    TransportError,
    ValidationError,
    __version__,
    null_instrument,
    parse_retry_after,
)


# --------------------------------------------------------------------------- #
# Stub server
# --------------------------------------------------------------------------- #
def make_stub(*, get_failures: int = 0, post_failures: int = 0) -> FastAPI:
    """A stub that counts calls and can be told to flap a fixed number of times."""
    app = FastAPI()
    app.state.counts = {"GET": 0, "POST": 0, "DELETE": 0}
    app.state.get_failures = get_failures
    app.state.post_failures = post_failures
    app.state.idempotency_keys = []

    def problem(status: int, title: str, detail: str, request: Request, **extra: Any) -> JSONResponse:
        return JSONResponse(
            {
                "type": f"https://errors.example.com/{title.lower().replace(' ', '-')}",
                "title": title,
                "status": status,
                "detail": detail,
                "instance": request.url.path,
                **extra,
            },
            status_code=status,
            media_type="application/problem+json",
            headers={"X-Request-ID": "req-abc123"},
        )

    @app.get("/v1/datasets")
    async def list_datasets(limit: int = 50, status: str | None = None) -> JSONResponse:
        items = [{"id": "spiral-v1-aaa", "status": "ready"}, {"id": "moons-v1-bbb", "status": "pending"}]
        if status is not None:
            items = [i for i in items if i["status"] == status]
        return JSONResponse({"items": items[:limit]}, headers={"X-Request-ID": "req-list"})

    @app.get("/v1/datasets/{dataset_id}")
    async def get_dataset(dataset_id: str, request: Request) -> JSONResponse:
        app.state.counts["GET"] += 1

        if dataset_id == "flaky":
            if app.state.counts["GET"] <= app.state.get_failures:
                return problem(503, "Service Unavailable", "Upstream is restarting.", request)
            return JSONResponse({"id": dataset_id, "status": "ready"}, headers={"X-Request-ID": "req-ok"})

        if dataset_id == "rate-limited":
            return problem(
                429,
                "Too Many Requests",
                "Quota exhausted for this API key.",
                request,
                limit=100,
            )
        if dataset_id == "locked":
            return problem(409, "Conflict", "Dataset is being rebuilt.", request)
        if dataset_id == "boom":
            return problem(500, "Internal Server Error", "Unhandled exception.", request)
        if dataset_id == "teapot":
            return problem(418, "I am a teapot", "Short and stout.", request)
        if dataset_id == "html-error":
            # A raw HTML body, as a proxy emits when the origin is down: not
            # problem+json, not JSON at all.
            return Response(
                content="<html><body>502 Bad Gateway</body></html>",
                status_code=502,
                media_type="text/html",
            )
        if dataset_id == "known":
            return JSONResponse({"id": "known", "status": "ready"}, headers={"X-Request-ID": "req-known"})
        return problem(404, "Dataset not found", f"No dataset with id '{dataset_id}'.", request)

    @app.post("/v1/jobs")
    async def create_job(request: Request) -> JSONResponse:
        app.state.counts["POST"] += 1
        app.state.idempotency_keys.append(request.headers.get("Idempotency-Key"))
        if app.state.counts["POST"] <= app.state.post_failures:
            return problem(503, "Service Unavailable", "Scheduler is restarting.", request)
        return JSONResponse({"id": "job-1", "status": "queued"}, status_code=201, headers={"X-Request-ID": "req-job"})

    @app.delete("/v1/datasets/{dataset_id}", status_code=204)
    async def delete_dataset(dataset_id: str) -> JSONResponse:
        app.state.counts["DELETE"] += 1
        return JSONResponse(None, status_code=204)

    return app


def client_for(
    app: FastAPI,
    *,
    retry: RetryPolicy | None = None,
    **kwargs: Any,
) -> JuniperClient:
    async def instant_sleep(_: float) -> None:
        """Never actually wait: the backoff maths is tested separately."""

    return JuniperClient(
        base_url="http://test",
        transport=httpx.ASGITransport(app=app),
        retry=retry or RetryPolicy(),
        rng=random.Random(20260813),
        sleeper=kwargs.pop("sleeper", instant_sleep),
        **kwargs,
    )


class Recorder:
    def __init__(self) -> None:
        self.records: list[AttemptRecord] = []

    def __call__(self, record: AttemptRecord) -> None:
        self.records.append(record)


# --------------------------------------------------------------------------- #
# 1. Typed exceptions that preserve status_code and payload
# --------------------------------------------------------------------------- #
@pytest.mark.asyncio
async def test_404_raises_notfound_with_status_and_parsed_payload() -> None:
    """THE defect being corrected: the real clients keep only a message string."""
    async with client_for(make_stub()) as client:
        with pytest.raises(NotFoundError) as caught:
            await client.get_dataset(dataset_id="missing")

    exc = caught.value
    # A caller can branch on the status without parsing English out of str(exc).
    assert exc.status_code == 404
    assert exc.payload["title"] == "Dataset not found"
    assert exc.payload["detail"] == "No dataset with id 'missing'."
    assert exc.payload["instance"] == "/v1/datasets/missing"
    assert exc.request_id == "req-abc123"
    assert isinstance(exc, ApiError)  # one base catches everything
    assert "404" in str(exc)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("dataset_id", "expected_type", "expected_status"),
    [
        ("missing", NotFoundError, 404),
        ("locked", ConflictError, 409),
        ("rate-limited", RateLimitedError, 429),
        ("boom", ServerError, 500),
        ("teapot", ApiError, 418),  # unmapped 4xx falls back to the base type
    ],
)
async def test_status_codes_map_to_typed_leaves(
    dataset_id: str, expected_type: type[ApiError], expected_status: int
) -> None:
    async with client_for(make_stub(), retry=RetryPolicy(max_attempts=1)) as client:
        with pytest.raises(expected_type) as caught:
            await client.get_dataset(dataset_id=dataset_id)
    assert caught.value.status_code == expected_status
    assert type(caught.value) is expected_type


@pytest.mark.asyncio
async def test_validation_error_is_raised_for_a_422() -> None:
    app = FastAPI()

    @app.get("/v1/datasets/{dataset_id}")
    async def bad(dataset_id: str) -> JSONResponse:
        return JSONResponse({"title": "Unprocessable", "detail": "bad id"}, status_code=422)

    async with client_for(app) as client:
        with pytest.raises(ValidationError) as caught:
            await client.get_dataset(dataset_id="x")
    assert caught.value.status_code == 422


@pytest.mark.asyncio
async def test_a_non_json_error_body_does_not_leak_a_decode_error() -> None:
    async with client_for(make_stub(), retry=RetryPolicy(max_attempts=1)) as client:
        with pytest.raises(ServerError) as caught:
            await client.get_dataset(dataset_id="html-error")

    assert caught.value.status_code == 502
    assert "502 Bad Gateway" in caught.value.payload["detail"]  # salvaged, not exploded


@pytest.mark.asyncio
async def test_a_json_body_that_is_not_an_object_is_still_salvaged() -> None:
    """Valid JSON that is not an object is as unusable as none; degrade the same way."""
    app = FastAPI()

    @app.get("/v1/datasets/{dataset_id}")
    async def array_body(dataset_id: str) -> JSONResponse:
        return JSONResponse(["field required", "bad id"], status_code=400)

    async with client_for(app, retry=RetryPolicy(max_attempts=1)) as client:
        with pytest.raises(ValidationError) as caught:
            await client.get_dataset(dataset_id="x")

    assert caught.value.status_code == 400
    assert isinstance(caught.value.payload, dict)  # the contract holds regardless
    assert "field required" in caught.value.payload["detail"]


# --------------------------------------------------------------------------- #
# 2. Retry-After
# --------------------------------------------------------------------------- #
@pytest.mark.asyncio
async def test_429_raises_ratelimited_with_parsed_retry_after() -> None:
    app = FastAPI()

    @app.get("/v1/datasets/{dataset_id}")
    async def limited(dataset_id: str) -> JSONResponse:
        return JSONResponse(
            {"title": "Too Many Requests", "detail": "slow down", "status": 429},
            status_code=429,
            headers={"Retry-After": "42", "X-Request-ID": "req-429"},
        )

    async with client_for(app, retry=RetryPolicy(max_attempts=1)) as client:
        with pytest.raises(RateLimitedError) as caught:
            await client.get_dataset(dataset_id="anything")

    exc = caught.value
    assert exc.status_code == 429
    assert exc.retry_after == 42.0
    assert exc.request_id == "req-429"
    assert exc.payload["detail"] == "slow down"


def test_parse_retry_after_handles_both_legal_forms() -> None:
    from datetime import datetime, timezone

    now = datetime(2026, 8, 13, 12, 0, 0, tzinfo=timezone.utc)
    assert parse_retry_after("120") == 120.0
    assert parse_retry_after("Thu, 13 Aug 2026 12:02:00 GMT", now=now) == 120.0
    assert parse_retry_after("Thu, 13 Aug 2026 11:00:00 GMT", now=now) == 0.0  # never negative
    assert parse_retry_after(None) is None
    assert parse_retry_after("not-a-date") is None


@pytest.mark.asyncio
async def test_retry_after_overrides_backoff_but_is_capped() -> None:
    """A server asking for a 24-hour wait must not park the worker for a day."""
    app = FastAPI()
    calls = {"n": 0}

    @app.get("/v1/datasets/{dataset_id}")
    async def limited(dataset_id: str) -> JSONResponse:
        calls["n"] += 1
        if calls["n"] == 1:
            return JSONResponse({"detail": "wait"}, status_code=429, headers={"Retry-After": "86400"})
        return JSONResponse({"id": dataset_id, "status": "ready"})

    slept: list[float] = []

    async def spy(delay: float) -> None:
        slept.append(delay)

    async with client_for(app, sleeper=spy, retry=RetryPolicy(max_attempts=3, max_retry_after=60.0)) as client:
        result = await client.get_dataset(dataset_id="x")

    assert result["status"] == "ready"
    assert slept == [60.0]


# --------------------------------------------------------------------------- #
# 3. Retry only what is safe to retry
# --------------------------------------------------------------------------- #
@pytest.mark.asyncio
async def test_get_is_retried_on_503_and_eventually_succeeds() -> None:
    app = make_stub(get_failures=2)
    async with client_for(app, retry=RetryPolicy(max_attempts=3)) as client:
        result = await client.get_dataset(dataset_id="flaky")

    assert result == {"id": "flaky", "status": "ready"}
    assert app.state.counts["GET"] == 3  # two failures, then the success


@pytest.mark.asyncio
async def test_post_without_an_idempotency_key_is_never_retried() -> None:
    """The cascor-client defect: a retried POST duplicates the side effect.

    Note the trade being made explicit -- without a key the client surfaces the
    first 503 rather than risk starting a second training run.
    """
    app = make_stub(post_failures=5)
    async with client_for(app, retry=RetryPolicy(max_attempts=3)) as client:
        with pytest.raises(ServerError) as caught:
            await client.create_job(kind="train", dataset_id="spiral-v1-aaa")

    assert caught.value.status_code == 503
    assert app.state.counts["POST"] == 1  # exactly one attempt reached the server
    assert app.state.idempotency_keys == [None]


@pytest.mark.asyncio
async def test_post_with_an_idempotency_key_is_retried() -> None:
    """The key is the server's promise to de-duplicate, so retrying becomes safe."""
    app = make_stub(post_failures=2)
    async with client_for(app, retry=RetryPolicy(max_attempts=3)) as client:
        result = await client.create_job(
            kind="train", dataset_id="spiral-v1-aaa", idempotency_key="sub-0001"
        )

    assert result == {"id": "job-1", "status": "queued"}
    assert app.state.counts["POST"] == 3
    # The same key on every attempt -- a fresh key per attempt would be no key at all.
    assert app.state.idempotency_keys == ["sub-0001"] * 3


def test_retry_policy_states_the_rule_directly() -> None:
    policy = RetryPolicy()
    assert policy.may_retry(method="GET", has_idempotency_key=False)
    assert policy.may_retry(method="delete", has_idempotency_key=False)  # case-insensitive
    assert policy.may_retry(method="PUT", has_idempotency_key=False)
    assert not policy.may_retry(method="POST", has_idempotency_key=False)
    assert not policy.may_retry(method="PATCH", has_idempotency_key=False)
    assert policy.may_retry(method="POST", has_idempotency_key=True)


@pytest.mark.asyncio
async def test_transport_errors_are_retried_and_finally_wrapped() -> None:
    attempts = {"n": 0}

    class DeadTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
            attempts["n"] += 1
            raise httpx.ConnectError("no route to host", request=request)

    client = JuniperClient(
        base_url="http://test",
        transport=DeadTransport(),
        retry=RetryPolicy(max_attempts=3),
        sleeper=_instant,
    )
    async with client:
        with pytest.raises(TransportError) as caught:
            await client.get_dataset(dataset_id="whatever")

    assert attempts["n"] == 3
    assert caught.value.status_code is None  # the discriminator: no response at all
    assert caught.value.payload == {}


async def _instant(_: float) -> None:
    """Module-level instant sleeper (needed by tests that build a client directly)."""


# --------------------------------------------------------------------------- #
# 4. Instrumentation
# --------------------------------------------------------------------------- #
@pytest.mark.asyncio
async def test_hook_observes_every_attempt_including_failures() -> None:
    app = make_stub(get_failures=2)
    recorder = Recorder()
    async with client_for(app, retry=RetryPolicy(max_attempts=3), instrument=recorder) as client:
        await client.get_dataset(dataset_id="flaky")

    assert [r.attempt for r in recorder.records] == [1, 2, 3]
    assert [r.status_code for r in recorder.records] == [503, 503, 200]
    assert all(r.method == "GET" for r in recorder.records)
    assert all(r.url == "/v1/datasets/flaky" for r in recorder.records)
    assert all(r.duration_s >= 0.0 for r in recorder.records)
    assert recorder.records[-1].request_id == "req-ok"


@pytest.mark.asyncio
async def test_hook_sees_transport_failures_too() -> None:
    class DeadTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("boom", request=request)

    recorder = Recorder()
    client = JuniperClient(
        base_url="http://test",
        transport=DeadTransport(),
        retry=RetryPolicy(max_attempts=2),
        instrument=recorder,
        sleeper=_instant,
    )
    async with client:
        with pytest.raises(TransportError):
            await client.get_dataset(dataset_id="x")

    assert len(recorder.records) == 2
    assert all(r.status_code is None for r in recorder.records)
    assert all(isinstance(r.error, httpx.ConnectError) for r in recorder.records)


@pytest.mark.asyncio
async def test_a_raising_hook_cannot_break_the_call() -> None:
    """A metrics backend being down must not turn into an API outage."""
    calls = {"n": 0}

    def hostile(record: AttemptRecord) -> None:
        calls["n"] += 1
        raise RuntimeError("metrics backend is down")

    async with client_for(make_stub(), instrument=hostile) as client:
        result = await client.get_dataset(dataset_id="known")

    assert result == {"id": "known", "status": "ready"}
    assert calls["n"] == 1  # the hook really did run and really did raise


@pytest.mark.asyncio
async def test_a_raising_hook_does_not_mask_a_real_error() -> None:
    def hostile(record: AttemptRecord) -> None:
        raise RuntimeError("still down")

    async with client_for(make_stub(), instrument=hostile, retry=RetryPolicy(max_attempts=1)) as client:
        with pytest.raises(NotFoundError):
            await client.get_dataset(dataset_id="missing")


def test_default_hook_is_a_named_function_not_none() -> None:
    """A named no-op keeps the call site unconditional and the type non-optional."""
    assert callable(null_instrument)
    assert null_instrument.__name__ == "null_instrument"
    assert null_instrument(AttemptRecord("GET", "/x", 1, 200, None, 0.0, None)) is None


# --------------------------------------------------------------------------- #
# 5. Exception chaining
# --------------------------------------------------------------------------- #
@pytest.mark.asyncio
async def test_raise_from_preserves_the_cause() -> None:
    async with client_for(make_stub(), retry=RetryPolicy(max_attempts=1)) as client:
        with pytest.raises(NotFoundError) as caught:
            await client.get_dataset(dataset_id="missing")

    cause = caught.value.__cause__
    assert isinstance(cause, httpx.HTTPStatusError)  # httpx context stays reachable
    assert cause.response.status_code == 404
    assert caught.value.__suppress_context__ is True  # "from", not an accidental nested raise


@pytest.mark.asyncio
async def test_transport_error_chains_to_the_httpx_exception() -> None:
    class DeadTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectTimeout("timed out", request=request)

    client = JuniperClient(base_url="http://test", transport=DeadTransport(), retry=RetryPolicy(max_attempts=1))
    async with client:
        with pytest.raises(TransportError) as caught:
            await client.get_dataset(dataset_id="x")

    assert isinstance(caught.value.__cause__, httpx.ConnectTimeout)


# --------------------------------------------------------------------------- #
# Surface: signatures, timeouts, lifecycle
# --------------------------------------------------------------------------- #
@pytest.mark.asyncio
async def test_public_methods_are_keyword_only() -> None:
    """Contrast: create_network(**kwargs: Any) names none of its eleven parameters."""
    import inspect

    for name in ("get_dataset", "list_datasets", "create_job", "delete_dataset"):
        signature = inspect.signature(getattr(JuniperClient, name))
        positional = [
            p
            for p in signature.parameters.values()
            if p.name != "self" and p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
        ]
        assert positional == [], f"{name} accepts positional arguments: {positional}"
        assert not any(p.kind is p.VAR_KEYWORD for p in signature.parameters.values()), f"{name} takes **kwargs"


def test_timeouts_are_separated_not_one_scalar() -> None:
    timeouts = Timeouts(connect=1.0, read=60.0, write=2.0, pool=3.0)
    as_httpx = timeouts.to_httpx()
    assert (as_httpx.connect, as_httpx.read, as_httpx.write, as_httpx.pool) == (1.0, 60.0, 2.0, 3.0)


def test_construction_fails_fast_on_a_bad_base_url() -> None:
    with pytest.raises(ValueError):
        JuniperClient(base_url="   ")


@pytest.mark.asyncio
async def test_context_manager_owns_one_pool() -> None:
    app = make_stub()
    client = client_for(app)
    async with client as entered:
        assert entered is client
        await client.get_dataset(dataset_id="known")
        await client.list_datasets(status="ready")
        assert not client._http.is_closed
    assert client._http.is_closed  # the pool is released on exit


@pytest.mark.asyncio
async def test_literal_typed_filters_reach_the_server() -> None:
    async with client_for(make_stub()) as client:
        ready = await client.list_datasets(status="ready")
        everything = await client.list_datasets()

    assert [d["id"] for d in ready] == ["spiral-v1-aaa"]
    assert len(everything) == 2


@pytest.mark.asyncio
async def test_delete_is_retried_because_it_is_idempotent() -> None:
    app = make_stub()
    async with client_for(app) as client:
        assert await client.delete_dataset(dataset_id="spiral-v1-aaa") is None
    assert app.state.counts["DELETE"] == 1


def test_version_is_a_single_source_string() -> None:
    assert isinstance(__version__, str)
    assert __version__.count(".") == 2


def test_all_declares_the_real_public_surface() -> None:
    """__all__ is a promise; an unresolvable or stale name breaks `from x import *`."""
    import wellformed_client as module

    for name in module.__all__:
        assert hasattr(module, name), f"__all__ names {name!r}, which does not exist"
    assert module.__all__ == sorted(module.__all__)
    assert len(set(module.__all__)) == len(module.__all__)

    # Every exception the client can raise must be exported, or a caller cannot
    # write `except` against it.
    raisable = (
        ApiError,
        TransportError,
        NotFoundError,
        ConflictError,
        ValidationError,
        RateLimitedError,
        ServerError,
    )
    for exc_type in raisable:
        assert exc_type.__name__ in module.__all__
```

Run this example, and the other two, with the harness described in [Appendix D](#appendix-d--running-the-examples).

## Appendix A — Common Interview Questions

### A.1 How to use this appendix

The questions below are the ones that recur across backend, platform, and API-focused interviews. Each entry gives the question, **what the interviewer is actually probing** (which is rarely the surface question), and a compressed strong answer with a pointer back into the body of this primer.

Three notes on using them well.

**Interviewers are testing calibration, not recall.** "It depends" is the correct opening for most of these — but only when followed by *what* it depends on. An answer that names the two or three variables that decide the question is stronger than one that picks a side immediately.

**The follow-up is the real question.** Most of these have an obvious first answer and a much more interesting second layer. The entries below mark the usual follow-up, because that is where candidates are separated.

**Say what you don't know.** For anything version-dependent or contested — 400 vs 422, whether to cap dependency versions, whether HATEOAS is worth it — the strongest answer states that reasonable engineers disagree, and then gives your position with its cost. Bluffing a specification detail is the most damaging thing you can do in an API interview, because the interviewer usually knows the answer exactly.

---

### A.2 Fundamentals and HTTP

**Q1. What is the difference between an API and a library?**
*Probing:* whether you understand contracts and blast radius, not vocabulary.
*Strong answer:* both are interfaces, but they differ in failure mode, versioning unit, and cost of change. A library call fails deterministically and its version is a dependency you can resolve; a network call can fail ambiguously — succeeding while reporting failure — and its "version" is a coordination problem across parties you may not control. See the comparison table in [Overview: What an API Actually Is](#overview-what-an-api-actually-is).

**Q2. Walk me through what happens when a client calls `GET /v1/users/42`.**
*Probing:* breadth. They want to see how many layers you know exist.
*Strong answer:* DNS → TCP (or QUIC) → TLS handshake → HTTP request framing → load balancer / reverse proxy → middleware chain (request ID, metrics, auth, rate limit, body limit) → routing and path-parameter binding → handler → data access → serialisation → response framing → any caching layer. Mentioning the middleware chain and its *ordering* is what distinguishes a strong answer; see [I.2](#i2-the-http-substrate).

**Q3. What did HTTP/2 actually fix, and what did it not?**
*Probing:* whether you repeat marketing or understand mechanism.
*Strong answer:* it fixed application-layer head-of-line blocking via binary framing and stream multiplexing over one connection, and cut header overhead with HPACK. It did **not** fix *transport*-layer head-of-line blocking, because a lost TCP segment still stalls every multiplexed stream — that is what HTTP/3 over QUIC addresses.
Note also that HTTP semantics are version-independent and now live in a separate document (RFC 9110), which is itself a good API-design lesson about separating semantics from wire format.

**Q4. Is HTTP/2 always faster?**
*Probing:* resistance to cargo cult.
*Strong answer:* no. On a low-loss, low-latency link with few requests the difference is small, and under packet loss a single HTTP/2 connection can be *worse* than several HTTP/1.1 connections because loss stalls all streams. The honest answer is that it depends on loss rate, concurrency, and header sizes.

**Q5. Why is `Host` required in HTTP/1.1?**
*Probing:* basic protocol literacy.
*Strong answer:* virtual hosting — one IP serving many origins needs the client to say which one it means.

**Q6. What is the difference between an origin, a host, and a URI authority?**
*Probing:* precision, and it sets up CORS and WebSocket-Origin questions.

---

### A.3 REST semantics — the deep cuts

**Q7. What does REST actually mean, and does it matter that most "REST" APIs are not RESTful?**
*Probing:* whether you can hold a pedantic distinction without being pedantic about it.
*Strong answer:* REST is an architectural style with specific constraints; most industry "REST" APIs satisfy some and ignore the hypermedia constraint entirely. It matters where it buys something concrete — cacheability and statelessness pay for themselves — and does not matter as a purity test. See [II.1](#ii1-what-part-ii-covers-and-what-rest-actually-means) and the controversy block there.

**Q8. Which HTTP methods are safe? Which are idempotent? Is `POST` ever idempotent?**
*Probing:* exact knowledge, because this is where bluffing shows.
*Strong answer:* safe methods are read-only in intent (`GET`, `HEAD`, `OPTIONS`, `TRACE`); idempotent methods are those where multiple identical requests have the same effect on the server as one (`GET`, `HEAD`, `PUT`, `DELETE`, `OPTIONS`, `TRACE`). `POST` is neither by default — but *can* be made effectively idempotent by the server via an idempotency key. Note that all safe methods are idempotent, but not the reverse, and that idempotent does **not** mean the responses are
identical (two `DELETE`s give 204 then 404). See [II.3](#ii3-methods-safety-idempotency-and-the-complete-table).

**Q9. `PUT` vs `PATCH` vs `POST` — when do you use each?**
*Follow-up they will ask:* is `PATCH` idempotent?
*Strong answer:* `PUT` replaces a resource wholesale and is idempotent; `PATCH` applies a partial modification and is **not** idempotent in general (a patch document like "increment by 1" is the counterexample); `POST` is the general-purpose non-idempotent submission. Do not say `If-Match` makes `PATCH` *safe* — safety is a property of a method's defined semantics being "essentially read-only" (RFC 9110 §9.2.1), and a partial modification is not read-only; RFC 5789 §2 states
flatly that "PATCH is neither safe nor idempotent." What `If-Match` buys is **collision safety**. RFC 5789 §2 recommends the conditional request precisely because some patch formats "need to operate from a known base-point or else they will corrupt the resource", so a stale ETag fails with 412 rather than applying a patch to a resource that moved underneath. That is lost-update protection, not safety, and getting the word right in the one question about safety and idempotency
is exactly what is being tested.

**Q10. `401` vs `403`.**
*Strong answer:* 401 means the request lacked valid authentication — who are you? — and must carry `WWW-Authenticate`. 403 means you are authenticated and still not allowed. A common real-world deviation: returning 404 instead of 403 to avoid confirming a resource exists, which is a deliberate security tradeoff worth naming.

**Q11. `400` vs `422`.**
*Probing:* whether you know this is contested.
*Strong answer:* say up front that this one is genuinely disputed. One camp reserves 400 for malformed syntax and uses 422 for well-formed but semantically invalid content. Do not argue the other side from 422's WebDAV lineage — RFC 9110 Appendix B.3 records that 422, "previously defined in Section 11.2 of [WEBDAV]", "has been added because of its general applicability", which retires that objection outright. The live 400-camp argument is different and stronger: 400's own
definition — "something that is perceived to be a client error" — is already broad enough, 400 is universally recognised so no intermediary can surprise you with it, and RFC 9205 §4.6 advises "making generous use of the general status codes (200, 400, and 500) when in doubt" while warning against mapping application errors one-to-one onto status codes clients then have to learn. Either is defensible; consistency within one API matters far more than the choice, and an API that
returns *both* is worse than either. This primer's recommendation, labelled as such: let your framework's default stand wherever it fires — on FastAPI that means 422 for *every* automatic validation failure, query and path and header parameters as well as body fields — and hand-raise 400 only for failures the framework never sees, such as a malformed pagination cursor or a rejected combination of individually-valid parameters. Fighting the framework produces exactly the mixed
surface both camps want to avoid. See the controversy block in [II.4](#ii4-status-codes).

**Q12. `409` vs `412`.**
*Strong answer:* 409 is a conflict with the current state of the resource that the client might resolve and retry; 412 specifically means a *precondition the client supplied* (typically `If-Match`) evaluated false. Use 412 for optimistic concurrency, not 409.

**Q13. `301` vs `302` vs `307` vs `308`.**
*Probing:* the method-rewriting trap.
*Strong answer:* the axis that matters is permanence × whether the method may change. 301 and 302 have a long history of clients rewriting `POST` to `GET`; 307 and 308 explicitly forbid changing the method. Use 308 for a permanent move that must preserve `POST`, and 307 for a temporary one. See [II.4](#ii4-status-codes).

**Q14. When is `202 Accepted` the right answer, and what must the response contain?**
*Strong answer:* when the work is genuinely asynchronous and the result is not available yet. It must give the client a way to find out what happened — typically a job resource URL in `Location` and a status endpoint. A 202 with no handle back to the work is an anti-pattern. The Juniper dataset service is a useful counter-example to name: juniper-data has **no async job pattern at all** — no 202, no job resource — and instead offloads blocking generation per-request via
`asyncio.to_thread`, which works right up until a generator outlives the client's socket timeout. That is the failure mode 202 exists to avoid; see [II.4](#ii4-status-codes).

**Q15. Design the URL structure for a nested resource. When does nesting stop being a good idea?**
*Strong answer:* nest to express containment where the child has no independent identity; stop nesting when the child is addressable on its own, because deep nesting multiplies URL variants for one resource and complicates caching and permissions. Prefer a shallow canonical URI plus filters.

**Q16. How do you model an action that isn't CRUD — "cancel order", "send email", "retrain model"?**
*Probing:* whether you can reason past the noun rule instead of reciting it.
*Strong answer:* the options are a sub-resource representing the action's *result* (`POST /orders/1/cancellations`), a state field updated via `PATCH`, or a frankly RPC-shaped endpoint (`POST /orders/1/cancel`). All three ship in serious APIs; the honest answer names the tradeoff rather than insisting on purity. Say which you'd pick and why.

---

### A.4 Reliability — idempotency, retries, and failure

**Q17. A client sends `POST /payments` and the connection drops before it reads the response. What happened, and what should it do?**
*Probing:* the single most important idea in network API design.
*Strong answer:* it cannot know. The request may never have arrived, or may have been fully processed with the response lost. A blind retry risks a double charge; not retrying risks a lost payment. The resolution is an idempotency key chosen by the client and reused across retries, so the server can recognise the replay and return the original result. See [I.7](#i7-idempotency-retries-and-the-exactly-once-illusion).

**Q18. Design an idempotency-key mechanism.**
*Follow-up:* what if the same key arrives with a different body? What about two concurrent requests with the same key?
*Strong answer:* store key → (request fingerprint, status, response body) with a TTL, scoped per account and per endpoint. Same key + same fingerprint → replay the stored response. Same key + different fingerprint → reject (the client has a bug). Concurrent same key → either block on a per-key lock or return 409 while in flight. Worked implementation in [I.12](#i12-part-i-worked-example--making-a-non-idempotent-post-safe-to-retry).

**Q19. Can you guarantee exactly-once delivery?**
*Strong answer:* no. Exactly-once *delivery* is impossible across an unreliable network; what is achievable is at-least-once delivery combined with idempotent processing, which yields exactly-once *effect*. Candidates who claim exactly-once delivery are usually describing exactly this and calling it the wrong name.

**Q20. Why do retries need jitter?**
*Probing:* whether you have seen a retry storm.
*Strong answer:* without jitter, every client that failed at the same moment retries at the same moment, so the load arrives in synchronised waves that keep re-breaking a recovering service. Full jitter randomises each delay across the whole backoff window and de-synchronises the fleet. Retries also *amplify* load exactly when the system is least able to take it, which is why retry budgets and circuit breakers exist.

**Q21. Which status codes are safe to retry?**
*Strong answer:* the transient ones — 429, 502, 503, 504 — and transport errors, and only for idempotent methods unless an idempotency key is in play. 500 is ambiguous: it may be deterministic, in which case retrying just multiplies the failure. Note that the three Juniper client libraries disagree about exactly this, and one of them — cascor-client — retries `POST`, `DELETE`, **and `PATCH`** (its allowed-methods list is `GET, POST, DELETE, PUT, PATCH`); see
[I.7](#i7-idempotency-retries-and-the-exactly-once-illusion).

**Q22. What is a circuit breaker and when does it hurt?**
*Strong answer:* it stops calls to a failing dependency to let it recover and to fail fast locally. It hurts when the trip threshold is tuned for the wrong traffic shape — a low-volume endpoint can trip on a handful of unlucky errors — and when a half-open probe stampedes.

**Q23. Your API is behind three replicas and rate limiting is implemented with an in-memory counter. What is wrong?**
*Strong answer:* each replica enforces its own limit, so the effective limit is roughly N times the configured one, and it varies with load-balancer behaviour. Fixing it needs shared state (Redis or similar) or a token allocation scheme. The Juniper implementation is explicitly single-process for this reason; see [I.6](#i6-rate-limiting-quotas-and-backpressure).

**Q24. Compare fixed-window, sliding-window, and token-bucket rate limiting.**
*Follow-up:* what is wrong with fixed windows specifically?
*Strong answer:* a fixed window permits a burst of up to twice the limit across a window boundary — all of window N's budget at its end and all of N+1's at its start. Sliding windows fix that at higher cost; token buckets model a sustained rate with a burst allowance and are usually the best default.

---

### A.5 Security and authentication

**Q25. API keys vs OAuth 2.0 — when is a key enough?**
*Strong answer:* keys are fine for server-to-server calls within a trust boundary where the key can be stored securely and rotated. They are weak when you need delegated authority, per-user scoping, short lifetimes, or third-party access — that is what OAuth exists for. A key is a bearer credential with no expiry and no audience, which is exactly its convenience and its risk.

**Q26. Why must API key comparison be constant-time?**
*Probing:* whether you think about side channels.
*Strong answer:* a short-circuiting comparison leaks how many leading bytes matched via timing, which is enough to recover a secret byte-by-byte given enough samples. Use `hmac.compare_digest`. Note a subtlety the Juniper code gets right: iterating a list of keys and short-circuiting on the first match reintroduces the leak across the *set*, so the loop must not break early.

**Q27. What is wrong with `alg: none` in a JWT, and what else do you validate?**
*Strong answer:* `alg: none` lets an attacker strip the signature; a validator that trusts the header's algorithm can be tricked into verifying nothing, or into treating an RSA public key as an HMAC secret. You must pin the expected algorithm(s) server-side and validate issuer, audience, expiry, and not-before, with bounded clock skew.

**Q28. JWT vs server-side sessions.**
*Probing:* whether you know revocation is the crux.
*Strong answer:* stateless tokens scale reads and remove a lookup, but you cannot revoke one before expiry without reintroducing state — which is the thing you gave up state to avoid. Short lifetimes plus refresh rotation is the usual compromise. See the controversy block in [I.5](#i5-authentication-and-authorization).

**Q29. Where do you store a token in a browser?**
*Strong answer:* `localStorage` is readable by any XSS; an `HttpOnly`, `Secure`, `SameSite` cookie is not, but reintroduces CSRF, which you then handle with tokens or `SameSite`. There is no option without a tradeoff; name the one you are accepting.

**Q30. Why does the order of authentication and rate limiting matter?**
*Probing:* systems thinking about middleware.
*Strong answer:* because the rate-limit *key* depends on identity. Put the limiter first and `api_key` is `None` on every request, so every caller collapses into a shared `ip:` bucket — which is also precisely why unauthenticated garbage then consumes a legitimate caller's budget. Those are not two reasons: they are **one mechanism seen from two sides**, the defender's and the attacker's, and saying so is worth more than reciting both as a list. Juniper runs auth first, and
the part worth volunteering unprompted is the ordering's **cost**: the auth check *raises*, so a single limiter placed after it is never reached and the entire 401 path goes unthrottled — credential guessing and garbage-key floods consume zero tokens. The fix is not to reverse the order but to run two limiters, a coarse IP-keyed bucket before authentication and the identity-keyed one after. Volunteering the cost is what separates a memorised rule from an understood one. See [I.6](#i6-rate-limiting-quotas-and-backpressure).

**Q31. What is the risk in reflecting a client-supplied request ID into your logs?**
*Strong answer:* log injection — CR/LF in the value can forge log lines, and unescaped control characters can corrupt a log pipeline. Sanitise or bound it. This is a live, unmitigated surface in the Juniper request-ID middleware.

**Q32. How do you prevent a large request body from exhausting memory?**
*Follow-up:* is checking `Content-Length` enough?
*Strong answer:* no — `Content-Length` is a client-supplied hint. A chunked request may omit it entirely, and an under-declared value can be followed by a larger body. You must cap the *stream* cumulatively as you read. This is the exact difference between the shared Juniper middleware, which stream-caps, and a diverged copy in `juniper-data`, which only checks the header and is therefore bypassable; see [I.4](#i4-real-time-and-streaming).

---

### A.6 Caching and performance

**Q33. `no-cache` vs `no-store`.**
*Probing:* the most commonly confused pair in HTTP.
*Strong answer:* `no-store` forbids storing the response at all. `no-cache` permits storing it but requires revalidation before reuse. If you meant "never write this to disk", `no-cache` does not do that.

**Q34. Explain `ETag` and `If-None-Match`.**
*Follow-up:* what is a weak validator?
*Strong answer:* the server labels a representation with an opaque validator; the client sends it back and the server replies 304 with no body if it still matches, saving bandwidth but not the origin round trip. A weak validator (`W/` prefix) asserts semantic rather than byte-for-byte equivalence, so it may not be used where byte equality matters, such as range requests.

**Q35. How do you prevent lost updates?**
*Strong answer:* optimistic concurrency with `If-Match` and the resource's current ETag; a stale ETag gets 412 and the client re-reads and retries. Consider 428 to *require* the precondition so a careless client cannot silently clobber. Worked implementation in [II.11](#ii11-part-ii-worked-example--conditional-requests-and-optimistic-concurrency).

**Q36. What does `Vary` do and why is it dangerous?**
*Strong answer:* it tells caches which request headers form part of the cache key. Getting it wrong is the standard cause of cache poisoning and cross-user leakage — omit `Vary: Authorization` on a user-specific response behind a shared cache and you will serve one user's data to another.

**Q37. When can you cache aggressively with no invalidation strategy?**
*Strong answer:* when the URL is content-addressed, so the content cannot change under a given URL. Then `immutable` with a long `max-age` is safe and invalidation is just a new URL. Say the qualifier that keeps it safe, though, because it is the half interviewers listen for: the directive must name who may store the response. Juniper's dataset artifacts are content-addressed and would qualify — they currently emit no cache headers at all — but the artifact route sits behind
`X-API-Key`, so the right header is `private, max-age=31536000, immutable`, never `public`. `public` on an authenticated endpoint instructs every shared cache to hand one caller's body to the next, and `immutable` then suppresses the revalidation that might have caught it. "Cache aggressively" means aggressively *and* privately whenever a credential gates the route.

**Q38. Your p50 latency is fine and p99 is terrible. What do you look at?**
*Strong answer:* tail-specific causes — GC pauses, connection-pool saturation and queueing, lock contention, a slow dependency on a fraction of requests, cold caches, retries stacking. Averages hide all of this, which is why histograms and percentiles are the minimum viable latency metric.

---

### A.7 Evolution and versioning

**Q39. How do you version an API?**
*Follow-up:* which do you actually recommend?
*Strong answer:* URI path (`/v1/`), a custom header, or media-type negotiation — plus the option of not versioning and evolving additively. URI versioning wins on debuggability and cache-key clarity and loses on purity and on forcing whole-API version bumps. Media-type versioning is the most correct and the least used, which is itself a signal. Say which you'd choose and name the cost you're accepting. See [I.8](#i8-versioning-and-evolution).

**Q40. What counts as a breaking change?**
*Probing:* whether you think past "removing a field".
*Strong answer:* removing or renaming a field; adding a *required* request field; tightening validation; narrowing or widening an enum the client switches on; changing an error code or status; changing default values; changing ordering a client relies on; changing a field's type or nullability. Widening an enum breaks strict clients even though it "only adds" — which is why tolerant readers matter.

**Q41. How do you deprecate an endpoint responsibly?**
*Strong answer:* announce, instrument, then remove. Concretely: emit the `Deprecation` header (RFC 9745) and `Sunset` (RFC 8594) with a link to migration docs, measure who is still calling it and tell them specifically, keep it alive past the announced date if usage is non-trivial, and only then remove. A deprecation you cannot measure is a deprecation you cannot finish.

**Q42. Two teams consume your API and one needs a breaking change. What do you do?**
*Probing:* judgement and communication, not technique.

---

### A.8 Library and SDK design

**Q43. What makes something part of your library's public API in Python?**
*Probing:* whether you know the language cannot enforce this.
*Strong answer:* convention plus documentation, not enforcement. Leading underscores signal private; `__all__` controls `from x import *` and guides tooling but does not prevent importing anything. In practice, anything users can reach and do reach becomes public whether you meant it or not, which is why the surface must be curated deliberately. See [III.2](#iii2-designing-the-public-surface).

**Q44. Why would you make parameters keyword-only?**
*Strong answer:* it is a compatibility tool, not a style preference. Keyword-only parameters can be reordered, deprecated, and extended without breaking callers; positional ones freeze order into every call site forever. For a function with more than about three parameters it is close to mandatory.

**Q45. Design an exception hierarchy for an HTTP client library.**
*Follow-up:* what should the exception carry?
*Strong answer:* one package-level base so callers can catch broadly, typed leaves so they can catch narrowly, and — the part most implementations get wrong — **structured attributes**, not just a formatted message. The status code, parsed error payload, and request ID belong on the object. All three Juniper clients format everything into a string, so a caller cannot branch on status without parsing text; see [III.4](#iii4-errors-and-exception-hierarchy-design).

**Q46. What does `py.typed` do?**
*Strong answer:* it marks a package as PEP 561-compliant so downstream type checkers will actually read its inline annotations. Without it, a fully annotated package is treated as untyped by consumers — which is the current state of two Juniper shared packages: both are annotated, neither ships the marker, and one of them (`juniper-service-core`) has gone as far as a 73-line `TYPE_CHECKING` block (`juniper_service_core/__init__.py:38-110`) that consumers still cannot see.
Effort spent on annotations that a single empty file would have made visible is the cleanest illustration of what the marker is for.

**Q47. What is SemVer's 0.x rule, and why does everyone rely on it?**
*Strong answer:* under SemVer 2.0.0, anything may change at any time while the major version is zero — there is no stability guarantee. Projects lean on it to keep shipping breaking changes without the ceremony of a major bump, which is honest as long as consumers know. It stops being honest when 0.x has been in production for years.

**Q48. Should a library cap its dependencies' upper versions?**
*Probing:* whether you know this is genuinely contested.
*Strong answer:* say that it is disputed. Caps prevent a future incompatible release from breaking your users, but they also cause unresolvable dependency conflicts and require a release just to unblock users. The prevailing library-ecosystem advice is to avoid speculative upper caps and pin only against known breakage; application authors reasonably do the opposite. See the controversy block in [III.5](#iii5-versioning-semver-and-deprecation).

**Q49. Why is `DeprecationWarning` hidden by default, and what do you do about it?**
*Strong answer:* it is hidden outside `__main__` so end users of an application are not shown warnings about code they do not maintain. The consequences are that library authors must not rely on the warning alone being seen, must set `stacklevel` correctly so it points at the caller rather than the library, and should also document and communicate the removal window.

**Q50. Is subclassing a good extension mechanism?**
*Strong answer:* it is the most expensive contract you can offer. Every method a subclass may override, and every internal call between your own methods, becomes part of your public API — the fragile base class problem. Prefer composition, callbacks, or `Protocol`-based injection, and reserve subclassing for cases where you deliberately design and document a template method.

---

### A.9 Open-ended design prompts

These are 30-45 minute whiteboard prompts. What is being assessed is how you scope, what you ask before designing, and whether you name tradeoffs unprompted.

**Q51. Design an API for a long-running ML training job.**
Expected coverage: submit/status/cancel; 202 with a job resource vs 200 plus polling; how the client observes progress (poll, SSE, WebSocket) and why; idempotent submission; what happens on server restart mid-job; how you expose partial results and failure reasons. The Juniper training API is a real instance and gets several of these choices unusually — worth referencing.

**Q52. Design a file/artifact upload and download API for multi-gigabyte files.**
Expected coverage: multipart vs resumable vs presigned URLs; chunking and resume; checksums and integrity; content-addressing; caching for immutable objects; streaming rather than buffering on both sides; timeouts sized for the transfer, not the request.

**Q53. Design a webhook delivery system.**
Expected coverage: at-least-once delivery and consumer idempotency; signing so the receiver can verify origin; replay protection with timestamps; retry with backoff and a dead-letter path; ordering guarantees (and whether you offer any); how a consumer verifies and how you rotate signing secrets.

**Q54. Design a public API with tiered rate limits and quotas.**
Expected coverage: limit keying, algorithm choice, distributed enforcement, what headers you return, burst allowance, per-endpoint cost weighting, and what happens at the boundary between tiers.

**Q55. Design pagination for a feed that changes while the user is scrolling.**
Expected coverage: why offset pagination duplicates and skips items under concurrent writes; keyset pagination on a stable sort key; opaque cursors and why they should be opaque; whether you offer a total count and what it costs.

**Q56. You are asked to add GraphQL in front of an existing REST API. What do you ask first?**
Expected coverage: what problem it is solving (usually over-fetching or client velocity); who owns the schema; caching implications; the N+1 resolver problem; auth at field granularity; and whether a tailored REST endpoint would solve it more cheaply.

---

### A.10 Code-reading and debugging prompts

Interviewers increasingly hand you code. These are the patterns worth practising.

**Q57.** Here is a middleware stack registration. What order do these actually execute in, and what breaks?
*What they want:* recognition that registration order and execution order can be inverted (Starlette's `add_middleware` is LIFO), and the ability to trace a consequence — for example that a CORS middleware registered first ends up *innermost*, so a cross-origin preflight is rejected by auth before CORS ever sees it. This is a real, live instance in the Juniper cascor service (`juniper-cascor/src/api/app.py:620-649`): `CORSMiddleware` is registered first (`:621`) and therefore
executes innermost, and the in-code comment that spells the order out (`:644-646`) is itself wrong — it omits `RequestBodyLimitMiddleware` (`:630`), which really runs between `SecurityHeadersMiddleware` and CORS. The mechanism is one line of Starlette: `add_middleware` does `self.user_middleware.insert(0, ...)`.

**Q58.** This handler catches `ValueError` and returns 400. What could go wrong?
*What they want:* recognition that a broad exception handler reclassifies unrelated failures. In the Juniper codebase, cascor registers `@app.exception_handler(ValueError)` returning `400 VALIDATION_ERROR` (`juniper-cascor/src/api/app.py:678-684`), and `PydanticSerializationError` subclasses `ValueError` — so a *serialisation bug in the server* surfaced to clients as `400 VALIDATION_ERROR`: a server defect reported as a client error, which also means it never appeared in 5xx
alerting. The mechanism is recorded in the codebase itself, in the docstring of the helper written to work around it (`juniper-cascor/src/api/models/common.py:93-95`).

**Q59.** This client retries on 503. Is that safe?
*What they want:* "which method?" as the immediate response, then the idempotency-key question.

**Q60.** This endpoint validates JSON and then calls `msg.get(...)`. What input breaks it?
*What they want:* recognition that parse success is not shape success — `json.loads("[]")` succeeds and `[].get` raises `AttributeError`. In a WebSocket receive loop that exception tears down the connection rather than rejecting one message.

**Q61.** Why might this Prometheus metric take down the monitoring system?
*What they want:* unbounded label cardinality — labelling by raw request path rather than the resolved route template means every 404 from a scanner creates a new time series.

---

### A.11 Questions worth asking your interviewer

These signal seniority because they are the questions that matter once you are actually doing the job.

- How do you find out who is still calling a deprecated endpoint, and how long does a deprecation typically take here?
- Is the API specification generated from the code, hand-written, or both — and which one is authoritative when they disagree?
- What is the process when a change turns out to be breaking after it has shipped?
- Who owns the client libraries, and are they generated or hand-written?
- How are error responses standardised across services, and what happens when a team deviates?
- What is the rate-limiting story for internal callers, and does it differ from external?

---

## Appendix B — Reference Tables

### B.1 Method properties

Properties are as defined in RFC 9110 §9. "Cacheable" means a response to the method may be stored by a cache in principle; whether it is cached in practice depends on the response's own directives and status.

| Method    | Safe | Idempotent | Cacheable    | Request body         | Response body |
|-----------|------|------------|--------------|----------------------|---------------|
| `GET`     | Yes  | Yes        | Yes          | No defined semantics | Yes           |
| `HEAD`    | Yes  | Yes        | Yes          | No defined semantics | No            |
| `POST`    | No   | No         | In principle | Yes                  | Yes           |
| `PUT`     | No   | Yes        | No           | Yes                  | Yes           |
| `DELETE`  | No   | Yes        | No           | No defined semantics | Yes           |
| `PATCH`   | No   | **No**     | No           | Yes                  | Yes           |
| `OPTIONS` | Yes  | Yes        | No           | Optional             | Yes           |
| `TRACE`   | Yes  | Yes        | No           | No                   | Yes           |
| `CONNECT` | No   | No         | No           | No                   | Yes           |

Three notes on reading this table, each taken from the specification rather than from folklore.

**Safe** (RFC 9110 §9.2.1): "Of the request methods defined by this specification, the GET, HEAD, OPTIONS, and TRACE methods are defined to be safe." The definition is about *intent*, not a guarantee the server does nothing — the same section explicitly allows a safe request to write access logs or charge an advertising account, the point being that "the client did not request that additional behavior and cannot be held accountable for it."

**Idempotent** (RFC 9110 §9.2.2): "Of the request methods defined by this specification, PUT, DELETE, and safe request methods are idempotent." Note the definition is about the *intended effect on the server*, not about the responses matching — two successive `DELETE`s may legitimately return 204 then 404.

**Cacheable** (RFC 9110 §9.2.3): the specification "defines caching semantics for GET, HEAD, and POST, although the overwhelming majority of cache implementations only support GET and HEAD." `POST` is therefore cacheable in principle and effectively not in practice.

`PATCH` is defined in RFC 5789, not RFC 9110 — §9.3 of RFC 9110 defines only GET, HEAD, POST, PUT, DELETE, CONNECT, OPTIONS, and TRACE. Every safe method is idempotent; the converse does not hold.

### B.2 Status codes that carry design decisions

| Code      | Name                       | Use it when                                                       | Do not use it when                                         |
|-----------|----------------------------|-------------------------------------------------------------------|------------------------------------------------------------|
| 200       | OK                         | A request succeeded and there is a body                           | You created something — prefer 201                         |
| 201       | Created                    | A new resource exists; include `Location`                         | The resource already existed                               |
| 202       | Accepted                   | Work was queued; include a status handle                          | You have no way for the client to follow up                |
| 204       | No Content                 | Success with deliberately no body                                 | You have a body to send                                    |
| 206       | Partial Content            | Responding to a valid `Range`                                     | —                                                          |
| 301 / 308 | Moved Permanently          | The resource has a new canonical URI                              | Use 308 when the method must not change                    |
| 302 / 307 | Found / Temporary Redirect | Temporary relocation                                              | Use 307 when the method must not change                    |
| 304       | Not Modified               | A conditional `GET` validator matched                             | You are sending a body                                     |
| 400       | Bad Request                | Malformed syntax the server cannot parse                          | A well-formed but invalid value, if your convention is 422 |
| 401       | Unauthorized               | Authentication missing or invalid; send `WWW-Authenticate`        | The caller is known and merely not permitted               |
| 403       | Forbidden                  | Authenticated but not permitted                                   | You wish to hide existence — consider 404                  |
| 404       | Not Found                  | No resource at this URI                                           | You know it existed and want to say so — 410               |
| 405       | Method Not Allowed         | URI exists, method does not; send `Allow`                         | —                                                          |
| 409       | Conflict                   | State conflict the client may resolve                             | A supplied precondition failed — 412                       |
| 410       | Gone                       | Deliberately removed, permanently                                 | You do not actually know                                   |
| 412       | Precondition Failed        | An `If-Match`/`If-Unmodified-Since` evaluated false               | —                                                          |
| 415       | Unsupported Media Type     | The request's `Content-Type` is unsupported                       | The *content* is invalid — 400/422                         |
| 422       | Unprocessable Content      | Well-formed but semantically invalid (contested)                  | Your API convention uses 400                               |
| 428       | Precondition Required      | You require conditional requests for writes                       | —                                                          |
| 429       | Too Many Requests          | Rate limit exceeded; send `Retry-After`                           | The condition is not rate-related                          |
| 500       | Internal Server Error      | An unhandled server fault                                         | You know it is a client error                              |
| 501       | Not Implemented            | The capability does not exist here and will not appear on its own | It is a transient outage — 503                             |
| 502       | Bad Gateway                | An upstream returned something invalid                            | —                                                          |
| 503       | Service Unavailable        | Temporarily down or overloaded; send `Retry-After`                | The condition will never clear — 501                       |
| 504       | Gateway Timeout            | An upstream did not respond in time                               | —                                                          |

428, 429, and 431 are defined in RFC 6585, not RFC 9110.

### B.3 Headers that carry API-design weight

| Header                          | Direction | Purpose                                        | Notes                                                 |
|---------------------------------|-----------|------------------------------------------------|-------------------------------------------------------|
| `ETag`                          | Response  | Opaque validator for a representation          | `W/` prefix marks a weak validator                    |
| `If-None-Match`                 | Request   | Conditional GET → 304                          | Bandwidth saving, not round-trip saving               |
| `If-Match`                      | Request   | Optimistic concurrency → 412                   | The lost-update fix                                   |
| `Cache-Control`                 | Both      | Freshness and storage directives               | `no-cache` ≠ `no-store`                               |
| `Vary`                          | Response  | Declares the cache key's request-header inputs | Getting it wrong leaks data across users              |
| `Retry-After`                   | Response  | Seconds or HTTP-date to wait                   | Meaningful on 429 and 503                             |
| `Location`                      | Response  | Created or redirected resource URI             | Required in spirit on 201                             |
| `Link`                          | Response  | Typed relations to other resources             | RFC 8288; the one widely-adopted hypermedia mechanism |
| `Deprecation`                   | Response  | Marks a deprecated resource                    | RFC 9745                                              |
| `Sunset`                        | Response  | When the resource stops working                | RFC 8594                                              |
| `WWW-Authenticate`              | Response  | Challenge accompanying a 401                   | Frequently omitted in practice                        |
| `Idempotency-Key`               | Request   | Client-chosen replay token                     | Internet-Draft, not an RFC                            |
| `RateLimit`, `RateLimit-Policy` | Response  | Standardised quota signalling                  | Internet-Draft; supersedes the older three-field form |
| `X-RateLimit-*`                 | Response  | De-facto quota signalling                      | Vendor convention, never standardised                 |
| `X-Request-ID`                  | Both      | Correlation across services                    | Convention; sanitise before logging                   |

### B.4 Retry decision table

This condenses the retryability table in [I.7](#i7-idempotency-retries-and-the-exactly-once-illusion); where the two could be read differently, that one governs.

| Condition | Retry? | Notes |
| ----------- | -------- | ------- |
| DNS failure, or connection refused before any request bytes were sent | Yes | Nothing reached the server, so the request demonstrably did not execute. This is the one genuinely unambiguous row — and only when your client can prove the case |
| Any other connection error (reset mid-flight, broken pipe, TLS failure after send) | **Yes, if idempotent** | May never have reached the server — or may have been fully applied. Most HTTP libraries collapse this with the row above into a single exception type, so treat an undifferentiated "connection error" as *this* row |
| Read timeout / no response | **Yes, if idempotent** (or keyed) | Unknown outcome — the two-generals case exactly |
| 408 Request Timeout | Yes | The server explicitly says it did not complete the request |
| 429 Too Many Requests | Yes, after `Retry-After` | Explicitly transient (RFC 6585 §4). Respect the header rather than your own backoff |
| 500 Internal Server Error | **Ambiguous** | Your handler was reached and broke inside it — possibly after the first of three writes. May also be deterministic, in which case retrying just multiplies a hard failure |
| 502 Bad Gateway | **Yes, if idempotent** | RFC 9110 §15.6.3: an invalid response *from* an inbound server — so the request did reach upstream and the effect may already be applied. Many proxies also emit 502 on a failed connection, and the code alone does not distinguish the two |
| 503 Service Unavailable | **Yes, if idempotent**, after `Retry-After` | RFC 9110 §15.6.4: temporary overload, "likely be alleviated after some delay" |
| 504 Gateway Timeout | **Yes, if idempotent** | RFC 9110 §15.6.5: upstream did not answer in time — but may still be working |
| 501, 405, 415 | No | Deterministic; retrying cannot help |
| Any other 4xx | No | The request was understood and rejected; retrying a 400 or 404 produces a 400 or 404 |

The "if idempotent" qualifiers on 502/503/504 are not decoration. Those codes are widely *assumed* to mean the request never landed, and that assumption is where duplicate effects come from. For a non-idempotent `POST` or `PATCH`, every qualified row above collapses to "retry only with an idempotency key."

---

## Appendix C — Cited Specifications

Every document below was fetched and read locally rather than cited from memory; reproduce the cache with [`util/ad-hoc/2026-08-13_fetch_api_specs.bash`](../util/ad-hoc/2026-08-13_fetch_api_specs.bash). Titles, dates, categories, and obsoletes relationships are as printed in the canonical text.

| Document                                                | Title                                                         | Category              | Date           | Obsoletes                                            |
|---------------------------------------------------------|---------------------------------------------------------------|-----------------------|----------------|------------------------------------------------------|
| [RFC 5789](https://www.rfc-editor.org/rfc/rfc5789.html) | PATCH Method for HTTP                                         | Standards Track       | March 2010     | —                                                    |
| [RFC 6455](https://www.rfc-editor.org/rfc/rfc6455.html) | The WebSocket Protocol                                        | Standards Track       | December 2011  | —                                                    |
| [RFC 6585](https://www.rfc-editor.org/rfc/rfc6585.html) | Additional HTTP Status Codes                                  | Standards Track       | April 2012     | —                                                    |
| [RFC 6749](https://www.rfc-editor.org/rfc/rfc6749.html) | The OAuth 2.0 Authorization Framework                         | Standards Track       | October 2012   | 5849                                                 |
| [RFC 6750](https://www.rfc-editor.org/rfc/rfc6750.html) | The OAuth 2.0 Authorization Framework: Bearer Token Usage     | Standards Track       | October 2012   | —                                                    |
| [RFC 7519](https://www.rfc-editor.org/rfc/rfc7519.html) | JSON Web Token (JWT)                                          | Standards Track       | May 2015       | —                                                    |
| [RFC 7636](https://www.rfc-editor.org/rfc/rfc7636.html) | Proof Key for Code Exchange by OAuth Public Clients           | Standards Track       | September 2015 | —                                                    |
| [RFC 7807](https://www.rfc-editor.org/rfc/rfc7807.html) | Problem Details for HTTP APIs                                 | Standards Track       | March 2016     | — (obsoleted **by** 9457)                            |
| [RFC 8259](https://www.rfc-editor.org/rfc/rfc8259.html) | The JavaScript Object Notation (JSON) Data Interchange Format | Standards Track       | December 2017  | 7159                                                 |
| [RFC 8288](https://www.rfc-editor.org/rfc/rfc8288.html) | Web Linking                                                   | Standards Track       | October 2017   | 5988                                                 |
| [RFC 8414](https://www.rfc-editor.org/rfc/rfc8414.html) | OAuth 2.0 Authorization Server Metadata                       | Standards Track       | June 2018      | —                                                    |
| [RFC 8594](https://www.rfc-editor.org/rfc/rfc8594.html) | The Sunset HTTP Header Field                                  | Informational         | May 2019       | —                                                    |
| [RFC 8615](https://www.rfc-editor.org/rfc/rfc8615.html) | Well-Known Uniform Resource Identifiers (URIs)                | Standards Track       | May 2019       | 5785                                                 |
| [RFC 9068](https://www.rfc-editor.org/rfc/rfc9068.html) | JSON Web Token (JWT) Profile for OAuth 2.0 Access Tokens      | Standards Track       | October 2021   | —                                                    |
| [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html) | HTTP Semantics (STD 97)                                       | Standards Track       | June 2022      | 2818, 7230, 7231, 7232, 7233, 7235, 7538, 7615, 7694 |
| [RFC 9111](https://www.rfc-editor.org/rfc/rfc9111.html) | HTTP Caching (STD 98)                                         | Standards Track       | June 2022      | 7234                                                 |
| [RFC 9112](https://www.rfc-editor.org/rfc/rfc9112.html) | HTTP/1.1 (STD 99)                                             | Standards Track       | June 2022      | 7230                                                 |
| [RFC 9113](https://www.rfc-editor.org/rfc/rfc9113.html) | HTTP/2                                                        | Standards Track       | June 2022      | 7540, 8740                                           |
| [RFC 9114](https://www.rfc-editor.org/rfc/rfc9114.html) | HTTP/3                                                        | Standards Track       | June 2022      | —                                                    |
| [RFC 9205](https://www.rfc-editor.org/rfc/rfc9205.html) | Building Protocols with HTTP (BCP 56)                         | Best Current Practice | June 2022      | 3205                                                 |
| [RFC 9421](https://www.rfc-editor.org/rfc/rfc9421.html) | HTTP Message Signatures                                       | Standards Track       | February 2024  | —                                                    |
| [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457.html) | Problem Details for HTTP APIs                                 | Standards Track       | July 2023      | 7807                                                 |
| [RFC 9651](https://www.rfc-editor.org/rfc/rfc9651.html) | Structured Field Values for HTTP                              | Standards Track       | September 2024 | 8941                                                 |
| [RFC 9700](https://www.rfc-editor.org/rfc/rfc9700.html) | Best Current Practice for OAuth 2.0 Security (BCP 240)        | Best Current Practice | January 2025   | — (updates 6749, 6750, 6819)                         |
| [RFC 9745](https://www.rfc-editor.org/rfc/rfc9745.html) | The Deprecation HTTP Response Header Field                    | Standards Track       | March 2025     | —                                                    |

### C.1 Non-RFC references

These are cited in the body and are **not** IETF standards. The distinction matters: an Internet-Draft may change or expire, and a vendor convention has no normative force at all.

| Reference                                                                            | What it is                                  | Status                                       |
|--------------------------------------------------------------------------------------|---------------------------------------------|----------------------------------------------|
| [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html)                     | Version-numbering convention                | Community specification, not a standard      |
| [PEP 440](https://peps.python.org/pep-0440/)                                         | Python version identifiers                  | Python packaging standard                    |
| [PEP 561](https://peps.python.org/pep-0561/)                                         | Distributing and packaging type information | Python packaging standard                    |
| [PEP 562](https://peps.python.org/pep-0562/)                                         | Module `__getattr__` and `__dir__`          | Python language standard                     |
| [OpenAPI Specification](https://spec.openapis.org/)                                  | API description format                      | Linux Foundation specification               |
| [JSON Schema](https://json-schema.org/)                                              | Schema vocabulary                           | IETF Internet-Draft series                   |
| [GraphQL Specification](https://spec.graphql.org/)                                   | Query language and type system              | GraphQL Foundation specification             |
| [Server-Sent Events](https://html.spec.whatwg.org/multipage/server-sent-events.html) | `text/event-stream` push                    | WHATWG HTML Living Standard — **not** an RFC |
| `draft-ietf-httpapi-idempotency-key-header`                                          | `Idempotency-Key` request header            | **Internet-Draft**                           |
| `draft-ietf-httpapi-ratelimit-headers`                                               | `RateLimit` / `RateLimit-Policy` fields     | **Internet-Draft**                           |
| `X-RateLimit-*`, `X-Request-ID`                                                      | Widely used response/request headers        | **De-facto convention only**                 |

## Appendix D — Running the Examples

### D.1 Why this appendix exists

Documentation code rots faster than anything else in a repository, because nothing executes it. Every code block in this primer marked as an example file was run — not merely written — and the mechanism below lets any reader reproduce that.

The examples are extracted **from this document**, not from a parallel copy kept somewhere else. A parallel copy is exactly the thing that drifts; if the code here changes, the code that runs changes with it.

### D.2 Pinned toolchain

These are the versions the examples were actually verified against.

| Component      | Version |
|----------------|---------|
| CPython        | 3.13.13 |
| FastAPI        | 0.141.1 |
| Starlette      | 1.6.0   |
| Pydantic       | 2.13.4  |
| httpx          | 0.28.1  |
| pytest         | 8.x     |
| pytest-asyncio | current |

One version-specific note that will bite anyone adapting these examples from older tutorials: **httpx 0.28 removed the `AsyncClient(app=...)` shortcut**. Driving an ASGI application in-process now requires the transport explicitly.

```python
transport = httpx.ASGITransport(app=app)
async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
    response = await client.get("/v1/health")
```

This matters beyond syntax: testing through `ASGITransport` exercises the real middleware stack, routing, and serialisation without opening a socket, which is the right default for API tests. It does **not** exercise the HTTP server itself — connection handling, header parsing limits, timeouts, and keep-alive behaviour all live in the server and need at least one test over a real socket. See [I.11](#i11-testing-apis).

### D.3 Running them

The extraction harness lives at [`util/ad-hoc/2026-08-13_run_primer_examples.py`](../util/ad-hoc/2026-08-13_run_primer_examples.py). It parses this document for fenced blocks preceded by an `example-file` marker comment, writes them to a scratch directory, builds a virtualenv, and runs `pytest`.

```bash
# List the example files this document exports.
python util/ad-hoc/2026-08-13_run_primer_examples.py --list

# Extract, build a scratch venv, and run the full suite.
python util/ad-hoc/2026-08-13_run_primer_examples.py

# Reuse an existing environment instead of building one.
python util/ad-hoc/2026-08-13_run_primer_examples.py --venv /path/to/.venv

# Keep the scratch directory to poke at the extracted files.
python util/ad-hoc/2026-08-13_run_primer_examples.py --keep
```

Exit codes are `0` (all passed), `1` (tests failed), `2` (misuse, or the document's example markers are malformed).

To run one example by hand instead:

```bash
python -m venv /tmp/primer-venv
/tmp/primer-venv/bin/pip install fastapi httpx pydantic pytest pytest-asyncio
/tmp/primer-venv/bin/pytest -q test_conditional_datasets.py
```

### D.4 The extraction convention

A block is exported when the line immediately before its opening fence is an HTML comment naming the target file:

```text
<!-- example-file: idempotent_jobs.py -->
```

The comment renders as nothing, so the document reads normally. Blocks without a marker are illustrative snippets and are deliberately not extracted — they are fragments chosen for clarity in prose and are not expected to run standalone.

If you edit an example, re-run the harness. A marker whose fence has been orphaned by an edit is a hard error rather than a silent skip, precisely so that an edit cannot quietly stop verifying anything.

### D.5 Reproducing the specification cache

Citations in this document were checked against locally downloaded specification texts rather than recalled. To rebuild that cache:

```bash
util/ad-hoc/2026-08-13_fetch_api_specs.bash
# default cache location: ${TMPDIR:-/tmp}/juniper-api-primer-specs
```

Then grep it directly — which is the whole point:

```bash
grep -n -A 8 '9.2.2.  Idempotent Methods' /tmp/juniper-api-primer-specs/rfc9110-http-semantics.txt
```

The script exits non-zero if any document fails to download, so a partial cache is loud rather than silently incomplete.
