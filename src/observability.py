"""
Finnie AI — Observability Module

Arize Phoenix integration for tracing, evaluation, and telemetry.
Provides request tracing, agent-level spans, token usage metrics, and
a local evaluation dashboard at localhost:6006.

Falls back to local-only tracing if Phoenix is not installed.
"""

from __future__ import annotations

import os
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


# =============================================================================
# Trace Data Classes
# =============================================================================


@dataclass
class SpanRecord:
    """Record of a single operation span."""
    name: str
    start_time: float
    end_time: float = 0.0
    status: str = "ok"
    metadata: dict = field(default_factory=dict)

    @property
    def duration_ms(self) -> int:
        return int((self.end_time - self.start_time) * 1000)


@dataclass
class TraceRecord:
    """Complete trace for a request lifecycle."""
    trace_id: str
    session_id: str
    user_id: Optional[str] = None
    input_text: str = ""
    output_text: str = ""
    spans: list[SpanRecord] = field(default_factory=list)
    start_time: float = 0.0
    end_time: float = 0.0
    token_usage: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)

    @property
    def total_latency_ms(self) -> int:
        return int((self.end_time - self.start_time) * 1000)


# =============================================================================
# Phoenix Observer
# =============================================================================


class FinnieObserver:
    """
    Observability client using Arize Phoenix.

    Provides:
    - Request tracing (full lifecycle) via OpenTelemetry
    - Agent-level span tracking
    - Token usage metrics
    - Error tracking
    - Phoenix dashboard at localhost:6006 for eval workbench

    Falls back to local logging if Phoenix is not installed.
    """

    def __init__(self):
        self._phoenix_session = None
        self._tracer = None
        self._enabled = False
        self._local_traces: list[TraceRecord] = []
        self._dashboard_url: str = ""
        self._init_phoenix()

    def _init_phoenix(self):
        """Initialize Phoenix session and OpenTelemetry tracer."""
        phoenix_enabled = os.getenv("PHOENIX_ENABLED", "true").lower() == "true"
        if not phoenix_enabled:
            return

        try:
            import phoenix as px
            from opentelemetry import trace as otel_trace

            # Launch Phoenix in the background
            self._phoenix_session = px.launch_app()
            self._dashboard_url = "http://localhost:6006"

            # Set up OpenTelemetry tracer via Phoenix
            from opentelemetry.sdk.trace import TracerProvider

            try:
                from phoenix.otel import register
                tracer_provider = register(project_name="finnie-ai")
            except (ImportError, Exception):
                tracer_provider = TracerProvider()
                otel_trace.set_tracer_provider(tracer_provider)

            self._tracer = otel_trace.get_tracer("finnie-ai")
            self._enabled = True

        except ImportError:
            pass
        except Exception:
            pass

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    @property
    def dashboard_url(self) -> str:
        return self._dashboard_url

    def create_trace(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        input_text: str = "",
    ) -> TraceRecord:
        """Create a new trace for a request."""
        trace = TraceRecord(
            trace_id=str(uuid.uuid4()),
            session_id=session_id,
            user_id=user_id,
            input_text=input_text,
            start_time=time.time(),
        )

        if self._enabled and self._tracer:
            try:
                span = self._tracer.start_span(
                    name="finnie-ai-request",
                    attributes={
                        "session.id": session_id,
                        "user.id": user_id or "",
                        "input.value": input_text,
                    },
                )
                trace.metadata["_otel_span"] = span
            except Exception:
                pass

        return trace

    @contextmanager
    def span(self, trace: TraceRecord, name: str, metadata: dict | None = None):
        """
        Context manager for tracking an operation span.

        Usage:
            with observer.span(trace, "execute_quant") as span:
                result = quant_agent.process(state)
        """
        span_record = SpanRecord(
            name=name,
            start_time=time.time(),
            metadata=metadata or {},
        )

        otel_span = None
        if self._enabled and self._tracer:
            try:
                otel_span = self._tracer.start_span(
                    name=name,
                    attributes={
                        "agent.name": name,
                        "trace.id": trace.trace_id,
                        **(metadata or {}),
                    },
                )
            except Exception:
                pass

        try:
            yield span_record
            span_record.status = "ok"
            if otel_span:
                otel_span.set_attribute("status", "ok")
        except Exception as e:
            span_record.status = "error"
            span_record.metadata["error"] = str(e)
            if otel_span:
                otel_span.set_attribute("status", "error")
                otel_span.set_attribute("error.message", str(e))
            raise
        finally:
            span_record.end_time = time.time()
            trace.spans.append(span_record)
            if otel_span:
                try:
                    otel_span.end()
                except Exception:
                    pass

    def end_trace(self, trace: TraceRecord, output: str = ""):
        """Finalize a trace with the output."""
        trace.end_time = time.time()
        trace.output_text = output
        self._local_traces.append(trace)

        otel_span = trace.metadata.pop("_otel_span", None)
        if otel_span:
            try:
                otel_span.set_attribute("output.value", output[:500])
                otel_span.set_attribute("latency_ms", trace.total_latency_ms)
                otel_span.end()
            except Exception:
                pass

    def log_token_usage(
        self,
        trace: TraceRecord,
        model: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
    ):
        """Log token usage for cost tracking."""
        trace.token_usage = {
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
        }

    def get_callback_handler(self, session_id: str, user_id: str | None = None):
        """Get an OpenInference callback handler for LangChain integration."""
        if self._enabled:
            try:
                from openinference.instrumentation.langchain import LangChainInstrumentor
                LangChainInstrumentor().instrument()
            except ImportError:
                pass
        return None

    def get_recent_traces(self, limit: int = 20) -> list[dict]:
        """Get recent traces from local storage (for dashboard display)."""
        traces = self._local_traces[-limit:]
        return [
            {
                "trace_id": t.trace_id,
                "session_id": t.session_id,
                "input": t.input_text[:100],
                "output": t.output_text[:100],
                "latency_ms": t.total_latency_ms,
                "spans": len(t.spans),
                "token_usage": t.token_usage,
                "timestamp": datetime.fromtimestamp(t.start_time).isoformat(),
            }
            for t in reversed(traces)
        ]

    def get_metrics(self) -> dict:
        """Get aggregate metrics from local traces."""
        if not self._local_traces:
            return {"total_requests": 0}

        latencies = [t.total_latency_ms for t in self._local_traces]
        return {
            "total_requests": len(self._local_traces),
            "avg_latency_ms": int(sum(latencies) / len(latencies)),
            "p95_latency_ms": int(sorted(latencies)[int(len(latencies) * 0.95)]) if len(latencies) > 1 else latencies[0],
            "error_count": sum(1 for t in self._local_traces if any(s.status == "error" for s in t.spans)),
            "total_tokens": sum(t.token_usage.get("total_tokens", 0) for t in self._local_traces),
        }

    def flush(self):
        """Flush any pending spans."""
        pass  # OTEL auto-exports, no manual flush needed


# =============================================================================
# Singleton
# =============================================================================

_observer: FinnieObserver | None = None


def get_observer() -> FinnieObserver:
    """Get or create the global observer instance."""
    global _observer
    if _observer is None:
        _observer = FinnieObserver()
    return _observer
