"""Request-ID propagation middleware.

Injects an ``X-Request-ID`` header into every response and stores the
value in a ContextVar so async handlers and log records can correlate
to the originating HTTP request without threading the ID through every
call.

Inbound values are validated before propagation (APD-OBS-001). The header is
attacker-controlled, and the value flows into a process-wide ContextVar that any
consumer may write to a line-oriented sink and that is echoed back on the response.

Today that is contained -- but only *incidentally*, by machinery this package does
not own or assert. h11 caps the entire request head at
``max_incomplete_event_size`` (16384 by default, and uvicorn leaves it alone), so a
multi-megabyte header never reaches ASGI; and h11 rejects CR/LF in header values
outright, so the response echo is not a header-injection vector. Both of those are
h11 defaults. Validating on ingress means the guarantee belongs here instead of
being borrowed.
"""

import re
import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from juniper_observability.constants import HEADER_X_REQUEST_ID

# Public ContextVar; ``JuniperJsonFormatter`` reads from it to embed the
# request ID in every log record emitted during the request scope.
request_id_var: ContextVar[str] = ContextVar("request_id", default="")

#: Maximum accepted inbound request-ID length. Generous next to the 36 characters of
#: a UUID4 and the 55 of a W3C ``traceparent``, but small enough that the value
#: cannot meaningfully bloat a log line it is copied into.
MAX_REQUEST_ID_LENGTH = 128

#: Characters accepted in an inbound request ID. Covers UUIDs, ULIDs, W3C trace
#: identifiers and the ``service:id`` shapes services use, while excluding
#: whitespace, control characters and anything with meaning to a log or terminal
#: consumer. An allowlist rather than a denylist on purpose: the set of characters
#: that are safe in *every* downstream sink is far easier to enumerate correctly
#: than the set that is dangerous in any of them.
_REQUEST_ID_RE = re.compile(r"\A[A-Za-z0-9._:-]+\Z")


def is_valid_request_id(value: str) -> bool:
    """Whether an inbound ``X-Request-ID`` may be propagated as-is.

    Args:
        value: The raw header value.

    Returns:
        True when the value is within :data:`MAX_REQUEST_ID_LENGTH` and contains only
        allowlisted characters.
    """
    return bool(value) and len(value) <= MAX_REQUEST_ID_LENGTH and bool(_REQUEST_ID_RE.match(value))


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Injects ``X-Request-ID`` into ContextVar and response header.

    If the request carries an inbound ``X-Request-ID`` header, that
    value is propagated; otherwise a fresh UUID4 is generated. The
    header is always echoed back on the response.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        inbound = request.headers.get(HEADER_X_REQUEST_ID)
        # Replace rather than sanitize. Stripping offending characters would
        # propagate a value the client never sent, so the ID in the logs would
        # correlate to nothing on either side; a fresh UUID is at least honestly
        # this server's own. Rejection is deliberately silent -- logging it would
        # hand an attacker a log-flood lever, which is the very class this guard
        # exists to bound.
        rid = inbound if inbound is not None and is_valid_request_id(inbound) else str(uuid.uuid4())
        token = request_id_var.set(rid)
        try:
            response = await call_next(request)
            response.headers[HEADER_X_REQUEST_ID] = rid
            return response
        finally:
            request_id_var.reset(token)
