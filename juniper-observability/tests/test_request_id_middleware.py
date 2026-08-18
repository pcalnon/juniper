"""Tests for ``RequestIdMiddleware``."""

from unittest.mock import MagicMock

import pytest

from juniper_observability import RequestIdMiddleware, request_id_var
from juniper_observability.middleware.request_id import MAX_REQUEST_ID_LENGTH, is_valid_request_id


class TestRequestIdMiddleware:
    @pytest.mark.asyncio
    async def test_generates_uuid_when_no_header(self):
        import uuid

        middleware = RequestIdMiddleware(app=MagicMock())
        captured: dict = {}

        async def call_next(request):
            captured["rid"] = request_id_var.get("")
            response = MagicMock()
            response.headers = {}
            return response

        request = MagicMock()
        request.headers = {}

        response = await middleware.dispatch(request, call_next)
        # Generated value must be a valid UUID
        uuid.UUID(captured["rid"])
        # Header echoed in response
        assert response.headers["X-Request-ID"] == captured["rid"]

    @pytest.mark.asyncio
    async def test_uses_provided_header(self):
        middleware = RequestIdMiddleware(app=MagicMock())
        captured: dict = {}

        async def call_next(request):
            captured["rid"] = request_id_var.get("")
            response = MagicMock()
            response.headers = {}
            return response

        request = MagicMock()
        request.headers = {"X-Request-ID": "explicit-id-42"}

        response = await middleware.dispatch(request, call_next)
        assert captured["rid"] == "explicit-id-42"
        assert response.headers["X-Request-ID"] == "explicit-id-42"

    @pytest.mark.asyncio
    async def test_contextvar_reset_after_dispatch(self):
        """The middleware must reset the contextvar so adjacent requests don't see each other's IDs."""
        middleware = RequestIdMiddleware(app=MagicMock())

        async def call_next(_request):
            response = MagicMock()
            response.headers = {}
            return response

        # Set a known sentinel before dispatch — must be restored after.
        token = request_id_var.set("before-test")
        try:
            request = MagicMock()
            request.headers = {"X-Request-ID": "during-test"}
            await middleware.dispatch(request, call_next)
            assert request_id_var.get("") == "before-test"
        finally:
            request_id_var.reset(token)


class TestInboundValidation:
    """APD-OBS-001: the inbound header is attacker-controlled and must be validated.

    The value lands in a process-wide ContextVar that consumers copy into log records
    and is echoed back on the response. Today that is contained by h11's defaults --
    the request head is capped at 16384 bytes and CR/LF in a header value is rejected
    outright -- but that containment is *incidental* and belongs to h11, not to this
    package. These arms pin the guarantee locally so it survives an h11 default
    change, a non-h11 server, or a non-HTTP caller.
    """

    @staticmethod
    def _dispatch(header_value):
        """Run dispatch with an inbound header and return (propagated, echoed)."""
        import asyncio

        middleware = RequestIdMiddleware(app=MagicMock())
        captured: dict = {}

        async def call_next(_request):
            captured["rid"] = request_id_var.get("")
            response = MagicMock()
            response.headers = {}
            return response

        request = MagicMock()
        request.headers = {} if header_value is None else {"X-Request-ID": header_value}
        response = asyncio.run(middleware.dispatch(request, call_next))
        return captured["rid"], response.headers["X-Request-ID"]

    def test_uuid_is_accepted_verbatim(self):
        rid = "550e8400-e29b-41d4-a716-446655440000"
        propagated, echoed = self._dispatch(rid)
        assert propagated == rid
        assert echoed == rid

    def test_service_scoped_and_trace_shaped_ids_are_accepted(self):
        """Real correlation IDs are not all UUIDs; the allowlist must not break them."""
        for rid in ("svc-cascor:42", "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01", "01ARZ3NDEKTSV4RRFFQ69G5FAV", "a.b.c"):
            propagated, _ = self._dispatch(rid)
            assert propagated == rid, f"{rid!r} should be accepted"

    def test_oversized_value_is_replaced_with_a_fresh_uuid(self):
        import uuid

        propagated, echoed = self._dispatch("x" * (MAX_REQUEST_ID_LENGTH + 1))
        uuid.UUID(propagated)
        assert echoed == propagated

    def test_exactly_max_length_is_still_accepted(self):
        """Off-by-one guard on the cap."""
        rid = "x" * MAX_REQUEST_ID_LENGTH
        propagated, _ = self._dispatch(rid)
        assert propagated == rid

    def test_newline_bearing_value_never_reaches_the_contextvar(self):
        """The log-forging shape. h11 would reject it over HTTP; do not rely on that."""
        import uuid

        propagated, echoed = self._dispatch("abc\r\nX-Injected: 1")
        uuid.UUID(propagated)
        assert "\n" not in propagated and "\r" not in propagated
        assert echoed == propagated

    def test_other_hostile_shapes_are_replaced(self):
        import uuid

        for hostile in ("a b", "\x1b[31mred", "id\x00null", "../../etc/passwd", '{"json":"ish"}', "emoji-\U0001f600"):
            propagated, _ = self._dispatch(hostile)
            assert propagated != hostile, f"{hostile!r} should have been replaced"
            uuid.UUID(propagated)  # and the replacement is a real UUID

    def test_empty_header_value_is_replaced(self):
        """An empty ID correlates nothing and would render as a blank log field."""
        import uuid

        propagated, _ = self._dispatch("")
        uuid.UUID(propagated)

    def test_replacement_is_silent(self, caplog):
        """Rejection must not log.

        Logging every rejected header would hand an attacker a log-flood lever --
        the exact class this guard exists to bound.
        """
        import logging

        with caplog.at_level(logging.DEBUG):
            self._dispatch("bad value here")
        ours = [r for r in caplog.records if r.name.startswith("juniper_observability")]
        assert ours == [], f"rejection logged: {[r.getMessage() for r in ours]}"

    def test_response_echo_always_matches_what_was_propagated(self):
        """Echo and ContextVar must never diverge, valid or not."""
        for value in (None, "good-id", "bad id", "y" * 999):
            propagated, echoed = self._dispatch(value)
            assert propagated == echoed


class TestIsValidRequestId:
    def test_accepts_the_allowlisted_alphabet(self):
        assert is_valid_request_id("Aa0._:-")

    def test_rejects_empty(self):
        assert not is_valid_request_id("")

    def test_rejects_over_length(self):
        assert not is_valid_request_id("a" * (MAX_REQUEST_ID_LENGTH + 1))

    def test_is_anchored_at_both_ends(self):
        """A regex without \\A/\\Z would accept a good prefix carrying a bad tail."""
        assert not is_valid_request_id("good-prefix then bad")
        assert not is_valid_request_id("bad tail-good-suffix")
        assert not is_valid_request_id("good\nbad")
