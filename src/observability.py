"""
Finnie AI — Observability Module

LangFuse integration for tracing, metrics, and cost tracking.
Provides decorators and utilities for instrumenting the multi-agent system.
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
# LangFuse Client
# =============================================================================


class FinnieObserver:
    """
    Observability client wrapping LangFuse.

    Provides:
    - Request tracing (full lifecycle)
    - Agent-level span tracking
    - Token usage metrics
    - Error tracking
    - Cost estimation

    Falls back to local logging if LangFuse is not configured.
    """

    def __init__(self):
        self._langfuse = None
        self._enabled = False
        self._local_traces: list[TraceRecord] = []
        self._init_langfuse()

    def _init_langfuse(self):
        """Initialize LangFuse client if credentials are available."""
        public_key = os.getenv("LANGFUSE_PUBLIC_KEY", "")
        secret_key = os.getenv("LANGFUSE_SECRET_KEY", "")

        if public_key and secret_key:
            try:
                from langfuse import Langfuse

                self._langfuse = Langfuse(
                    public_key=public_key,
                    secret_key=secret_key,
                    host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
                )
                self._enabled = True
            except ImportError:
                pass
            except Exception:
                pass

    @property
    def is_enabled(self) -> bool:
        return self._enabled

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

        if self._enabled and self._langfuse:
            try:
                self._langfuse.trace(
                    id=trace.trace_id,
                    session_id=session_id,
                    user_id=user_id,
                    input=input_text,
                    name="finnie-ai-request",
                )
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

        try:
            yield span_record
            span_record.status = "ok"
        except Exception as e:
            span_record.status = "error"
            span_record.metadata["error"] = str(e)
            raise
        finally:
            span_record.end_time = time.time()
            trace.spans.append(span_record)

            if self._enabled and self._langfuse:
                try:
                    self._langfuse.span(
                        trace_id=trace.trace_id,
                        name=name,
                        start_time=datetime.fromtimestamp(span_record.start_time),
                        end_time=datetime.fromtimestamp(span_record.end_time),
                        status_message=span_record.status,
                        metadata=span_record.metadata,
                    )
                except Exception:
                    pass

    def end_trace(self, trace: TraceRecord, output: str = ""):
        """Finalize a trace with the output."""
        trace.end_time = time.time()
        trace.output_text = output
        self._local_traces.append(trace)

        if self._enabled and self._langfuse:
            try:
                self._langfuse.trace(
                    id=trace.trace_id,
                    output=output,
                    metadata={
                        "latency_ms": trace.total_latency_ms,
                        "spans": len(trace.spans),
                        "token_usage": trace.token_usage,
                    },
                )
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
        """Get a LangFuse callback handler for LangChain integration."""
        if self._enabled and self._langfuse:
            try:
                from langfuse.callback import CallbackHandler

                return CallbackHandler(
                    session_id=session_id,
                    user_id=user_id,
                )
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
        """Flush any pending events to LangFuse."""
        if self._enabled and self._langfuse:
            try:
                self._langfuse.flush()
            except Exception:
                pass


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
