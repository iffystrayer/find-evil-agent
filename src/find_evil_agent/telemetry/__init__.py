"""Observability layer with structured logging, metrics, and LLM tracing.

This module provides comprehensive observability for Find Evil Agent:

1. **Structured Logging** (structlog)
   - JSON-formatted logs for easy parsing
   - Contextual fields (incident_id, agent_name, tool_name)
   - ISO timestamps

2. **Prometheus Metrics**
   - Tool execution duration and status
   - LLM call duration and status
   - Agent error counters
   - Active incident gauge

3. **LLM Tracing** (Langfuse)
   - Agent execution traces
   - LLM call traces with input/output
   - Token usage tracking
   - Cost estimation

Example Usage:
    >>> # In agent code:
    >>> from find_evil_agent.telemetry import log_tool_execution, trace_agent_execution
    >>>
    >>> async with trace_agent_execution("tool_selector", input_data) as trace:
    ...     result = await process()
    ...     if trace:
    ...         trace.update(output=result.data)
    >>>
    >>> log_tool_execution(
    ...     tool_name="volatility",
    ...     duration=12.5,
    ...     status="success",
    ...     confidence=0.85
    ... )

Configuration:
    Set via environment variables:
    - LANGFUSE_SECRET_KEY
    - LANGFUSE_PUBLIC_KEY
    - LANGFUSE_BASE_URL
    - LANGFUSE_ENABLED (default: true)
"""

import structlog
from prometheus_client import Counter, Histogram, Gauge
from typing import Optional, Any
from contextlib import asynccontextmanager

# Lazy import Langfuse (optional dependency)
try:
    from langfuse import Langfuse
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    Langfuse = None

# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# =============================================================================
# Prometheus Metrics
# =============================================================================

tool_executions_total = Counter(
    'tool_executions_total',
    'Total number of SIFT tool executions',
    ['tool_name', 'status']
)

tool_execution_duration_seconds = Histogram(
    'tool_execution_duration_seconds',
    'SIFT tool execution duration in seconds',
    ['tool_name'],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600, 1800, 3600]
)

llm_calls_total = Counter(
    'llm_calls_total',
    'Total LLM API calls',
    ['provider', 'model', 'status']
)

llm_call_duration_seconds = Histogram(
    'llm_call_duration_seconds',
    'LLM call duration in seconds',
    ['provider', 'model'],
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30, 60]
)

tool_selection_confidence = Gauge(
    'tool_selection_confidence',
    'Confidence score for tool selection',
    ['tool_name']
)

agent_errors_total = Counter(
    'agent_errors_total',
    'Total agent errors',
    ['agent_name', 'error_type']
)

active_incidents = Gauge(
    'active_incidents',
    'Number of active incident analysis sessions'
)

# =============================================================================
# Langfuse Integration
# =============================================================================

# Global Langfuse client (initialized lazily)
_langfuse_client: Optional[Any] = None


def get_langfuse_client() -> Optional[Any]:
    """Get Langfuse client (lazy initialization).

    Returns None if Langfuse is not configured or disabled.

    Returns:
        Langfuse client instance or None

    Example:
        >>> langfuse = get_langfuse_client()
        >>> if langfuse:
        ...     trace = langfuse.trace(name="my_workflow", input=data)
    """
    global _langfuse_client

    if not LANGFUSE_AVAILABLE:
        return None

    if _langfuse_client is None:
        try:
            from find_evil_agent.config.settings import get_settings
            settings = get_settings()

            if not settings.langfuse_enabled:
                return None

            if settings.langfuse_secret_key and settings.langfuse_public_key:
                _langfuse_client = Langfuse(
                    secret_key=settings.langfuse_secret_key,
                    public_key=settings.langfuse_public_key,
                    host=settings.langfuse_base_url
                )
                logger.info(
                    "langfuse_initialized",
                    host=settings.langfuse_base_url
                )
        except Exception as e:
            logger.warning(
                "langfuse_init_failed",
                error=str(e)
            )
            return None

    return _langfuse_client


@asynccontextmanager
async def trace_agent_execution(agent_name: str, input_data: dict):
    """Context manager for tracing agent execution.

    Creates a Langfuse trace for the entire agent execution,
    capturing input, output, duration, and any errors.

    Args:
        agent_name: Name of the agent being executed
        input_data: Input data for the agent

    Yields:
        Langfuse trace object (or None if Langfuse unavailable)

    Example:
        >>> async with trace_agent_execution("tool_selector", input_data) as trace:
        ...     result = await process()
        ...     if trace:
        ...         trace.update(output=result.data)
    """
    langfuse = get_langfuse_client()
    trace = None

    if langfuse:
        try:
            trace = langfuse.trace(
                name=f"agent_{agent_name}",
                input=input_data,
                metadata={"agent": agent_name}
            )
        except Exception as e:
            logger.warning(
                "langfuse_trace_creation_failed",
                agent=agent_name,
                error=str(e)
            )

    try:
        yield trace
    finally:
        if langfuse:
            try:
                langfuse.flush()
            except Exception as e:
                logger.warning(
                    "langfuse_flush_failed",
                    error=str(e)
                )


# =============================================================================
# Logging Functions
# =============================================================================

def log_tool_execution(
    tool_name: str,
    duration: float,
    status: str,
    confidence: float | None = None,
    **kwargs
):
    """Log tool execution with metrics and structured logging.

    Updates Prometheus metrics and writes structured log entry.

    Args:
        tool_name: Name of the SIFT tool executed
        duration: Execution duration in seconds
        status: Execution status (success, failed, timeout)
        confidence: Optional confidence score (0.0-1.0)
        **kwargs: Additional context fields

    Example:
        >>> log_tool_execution(
        ...     tool_name="volatility",
        ...     duration=12.5,
        ...     status="success",
        ...     confidence=0.85,
        ...     plugin="pslist",
        ...     incident_id="inc-123"
        ... )
    """
    tool_executions_total.labels(tool_name=tool_name, status=status).inc()
    tool_execution_duration_seconds.labels(tool_name=tool_name).observe(duration)

    if confidence is not None:
        tool_selection_confidence.labels(tool_name=tool_name).set(confidence)

    logger.info(
        "tool_executed",
        tool=tool_name,
        duration=duration,
        status=status,
        confidence=confidence,
        **kwargs
    )


def log_llm_call(
    provider: str,
    model: str,
    duration: float,
    status: str,
    **kwargs
):
    """Log LLM API call with metrics.

    Updates Prometheus metrics and writes structured log entry.

    Args:
        provider: LLM provider (ollama, openai, anthropic)
        model: Model name
        duration: Call duration in seconds
        status: Call status (success, failed)
        **kwargs: Additional context (input_tokens, output_tokens, etc.)

    Example:
        >>> log_llm_call(
        ...     provider="ollama",
        ...     model="gemma4:31b-cloud",
        ...     duration=2.5,
        ...     status="success",
        ...     input_tokens=150,
        ...     output_tokens=75
        ... )
    """
    llm_calls_total.labels(provider=provider, model=model, status=status).inc()
    llm_call_duration_seconds.labels(provider=provider, model=model).observe(duration)

    logger.info(
        "llm_call",
        provider=provider,
        model=model,
        duration=duration,
        status=status,
        **kwargs
    )


def log_agent_error(agent_name: str, error_type: str, error_message: str, **kwargs):
    """Log agent error with metrics.

    Updates Prometheus error counter and writes structured log entry.

    Args:
        agent_name: Name of the agent that errored
        error_type: Type of error (validation, timeout, execution, etc.)
        error_message: Error message
        **kwargs: Additional context

    Example:
        >>> log_agent_error(
        ...     agent_name="tool_selector",
        ...     error_type="validation",
        ...     error_message="Confidence threshold not met",
        ...     confidence=0.65,
        ...     threshold=0.7
        ... )
    """
    agent_errors_total.labels(agent_name=agent_name, error_type=error_type).inc()

    logger.error(
        "agent_error",
        agent=agent_name,
        error_type=error_type,
        error=error_message,
        **kwargs
    )


__all__ = [
    "logger",
    "get_langfuse_client",
    "trace_agent_execution",
    "log_tool_execution",
    "log_llm_call",
    "log_agent_error",
    "tool_executions_total",
    "tool_execution_duration_seconds",
    "llm_calls_total",
    "llm_call_duration_seconds",
    "tool_selection_confidence",
    "agent_errors_total",
    "active_incidents",
]
