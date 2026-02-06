# sam-observe: Observability & Monitoring

## Overview

**sam-observe** provides comprehensive observability for the SAM workflow including structured logging, metrics collection, distributed tracing, and error tracking. It enables debugging, performance optimization, and data-driven insights while maintaining full backward compatibility.

## Quick Start

```bash
# Initialize observability for a project
/sam-observe init

# View live dashboard
/sam-observe dashboard

# Query logs
/sam-observe logs --component sam-specs --level ERROR

# Export diagnostic bundle
/sam-observe export --output diag.zip

# Interactive console
/sam-observe console
```

## Integration

### Basic Usage

```python
from skills.shared.observability import get_logger, get_metrics
from skills.shared.observability.decorators import observe, timed

@observe()
@timed("spec_parse_duration")
def parse_spec(feature_dir):
    logger = get_logger("sam-specs", feature_id=feature_dir.name)

    logger.info("Starting specification parse", file=feature_dir)

    # Your existing code - print() still works!
    print(f"Parsing: {feature_dir}")

    logger.info("Specification parsed successfully", tasks_found=42)
```

### Available Decorators

- `@observe()` - Full instrumentation with logging and error tracking
- `@timed(metric_name)` - Record execution time
- `@catch_and_track(message)` - Catch and track exceptions

### Context Management

```python
logger = get_logger("sam-specs", feature_id="user_auth")
logger.with_context(task_id="3.2").info("Task started")

# Or use a context manager
with logger.timed("operation_name"):
    # Automatically logged with timing
    do_work()
```

## Data Storage

All observability data is stored in `.sam/`:

```
.sam/
├── logs/           # Structured JSON logs
├── metrics/        # Performance metrics
├── traces/         # Distributed traces
└── errors/         # Error reports
```

## Configuration

Edit `config/observability.yaml` to customize:

```yaml
logging:
  level: INFO
  components:
    sam-specs: DEBUG
    sam-develop: INFO

metrics:
  enabled: true
  retention_days: 30

tracing:
  enabled: true
  sample_rate: 1.0
```

## CLI Reference

| Command | Description |
|---------|-------------|
| `init` | Initialize observability for project |
| `logs` | Query and filter logs |
| `metrics` | View metrics summary |
| `dashboard` | Show live status dashboard |
| `console` | Interactive diagnostic console |
| `export` | Export diagnostic bundle |

## API Reference

### SamLogger

```python
logger = get_logger("component", feature_id="xxx", task_id="3.2")

logger.info("Message", **context)
logger.warning("Message", **context)
logger.error("Message", exception=e, **context)
logger.debug("Message", **context)

# Context binding
child_logger = logger.with_context(task_id="3.3")

# Timing
with logger.timed("operation"):
    do_work()
```

### MetricsCollector

```python
metrics = get_metrics("sam-specs")

# Timing
with metrics.start_timer("operation"):
    do_work()

# Counters
metrics.increment("tasks_completed", tags={"status": "success"})

# Gauges
metrics.gauge("active_tasks", value=5)

# Histograms
metrics.histogram("task_duration_ms", value=234)
```

### TracingContext

```python
from skills.shared.observability import get_tracer

tracer = get_tracer("sam-specs")

# Create span
span = tracer.start_span("parse_spec")
span.set_attribute("file", "TECHNICAL_SPEC.md")
span.add_event("parse_complete", {"tasks": 42})
span.end()
```

### ErrorTracker

```python
from skills.shared.observability import get_error_tracker

tracker = get_error_tracker()

try:
    risky_operation()
except Exception as e:
    error_id = tracker.track_exception(e, context={"file": "spec.md"})
    print(f"Error tracked: {error_id}")

# Get error groups
for group in tracker.get_error_groups():
    print(f"{group.error_type}: {group.count} occurrences")
```

## See Also

- [Observability Configuration Guide](../templates/observability/OBSERVABILITY_CONFIG.yaml)
- [Integration Guide](../shared/observability/__init__.py)
- [sam-status](../sam-status/SKILL.md) - Enhanced status reporting with metrics
