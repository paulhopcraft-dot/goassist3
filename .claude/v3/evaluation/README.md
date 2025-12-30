# APE Evaluation System

**Version**: 1.0.0
**Purpose**: Track command performance metrics and store optimization artifacts

---

## Directory Structure

```
.claude/v3/evaluation/
├── README.md                    # This file
├── metrics-tracker.jsonl        # Time-series metrics for all command executions
├── command-performance.json     # Current performance summary per command
└── variants/                    # Generated prompt variations
    ├── build-feature/           # Variations for /build-feature
    │   ├── v1-baseline.md
    │   ├── v2-variation-1.md
    │   ├── v2-variation-2.md
    │   ├── v2-variation-3.md
    │   ├── v2-variation-4.md
    │   ├── v2-variation-5.md
    │   └── evaluation-results.json
    ├── prd-check/
    └── verify/
```

---

## Files

### metrics-tracker.jsonl

**Format**: JSONL (one JSON object per line)
**Purpose**: Record every command execution with metrics

**Schema**:
```jsonl
{"command":"/build-feature","timestamp":"2025-12-26T19:00:00Z","success":true,"test_coverage":87,"quality_score":85,"duration_sec":120,"prompt_version":"1.0"}
{"command":"/build-feature","timestamp":"2025-12-26T20:15:00Z","success":true,"test_coverage":92,"quality_score":88,"duration_sec":95,"prompt_version":"1.0"}
{"command":"/prd-check","timestamp":"2025-12-26T20:30:00Z","success":true,"violations":0,"compliance_score":100,"prompt_version":"1.0"}
```

**Fields**:
- `command`: Command name (e.g., "/build-feature")
- `timestamp`: ISO 8601 timestamp
- `success`: Boolean (did command complete without errors?)
- `test_coverage`: Percentage (0-100) if applicable
- `quality_score`: Numeric score (0-100) if applicable
- `duration_sec`: Execution time in seconds
- `prompt_version`: Version of prompt used (e.g., "1.0", "2.0-ape")
- Additional metrics specific to command type

---

### command-performance.json

**Format**: JSON
**Purpose**: Summary of current performance per command

**Schema**:
```json
{
  "/build-feature": {
    "prompt_version": "2.0-ape",
    "optimized_at": "2025-12-26T21:00:00Z",
    "baseline_score": 60.0,
    "current_score": 76.6,
    "improvement_pct": 27.7,
    "executions_total": 75,
    "executions_since_optimization": 25,
    "next_optimization_at": 125,
    "metrics": {
      "success_rate": 0.88,
      "avg_test_coverage": 92,
      "avg_quality_score": 88,
      "avg_duration_sec": 105
    },
    "optimization_history": [
      {
        "version": "1.0",
        "baseline_score": 60.0,
        "optimized_at": "2025-12-20",
        "executions": 50
      },
      {
        "version": "2.0-ape",
        "score": 76.6,
        "improvement": "+27.7%",
        "optimized_at": "2025-12-26",
        "executions": 25
      }
    ]
  },
  "/prd-check": {
    "prompt_version": "1.0",
    "baseline_score": 85.0,
    "current_score": 85.0,
    "improvement_pct": 0,
    "executions_total": 30,
    "next_optimization_at": 50
  }
}
```

---

### variants/[command-name]/

**Purpose**: Store generated prompt variations and evaluation results

**Files**:
- `v1-baseline.md`: Original prompt before optimization
- `v2-variation-1.md`: First generated variation
- `v2-variation-2.md`: Second generated variation
- (... up to variation-5.md)
- `evaluation-results.json`: Performance comparison

**Example `evaluation-results.json`**:
```json
{
  "command": "/build-feature",
  "optimization_date": "2025-12-26",
  "baseline": {
    "version": "1.0",
    "success_rate": 0.75,
    "test_coverage": 82,
    "quality_score": 80,
    "composite_score": 60.0
  },
  "variations": [
    {
      "id": "variation-1",
      "strategy": "Explicit Step-by-Step",
      "success_rate": 0.88,
      "test_coverage": 90,
      "quality_score": 85,
      "composite_score": 74.4,
      "improvement_pct": 24.0
    },
    {
      "id": "variation-4",
      "strategy": "Best Practices",
      "success_rate": 0.87,
      "test_coverage": 92,
      "quality_score": 88,
      "composite_score": 76.6,
      "improvement_pct": 27.7,
      "winner": true
    }
  ],
  "selected": "variation-4",
  "deployment_date": "2025-12-26T21:00:00Z"
}
```

---

## Workflow

### 1. Record Metrics (After Each Command)

After command completes, append to `metrics-tracker.jsonl`:
```bash
echo '{"command":"/build-feature","timestamp":"'$(date -Iseconds)'","success":true,"test_coverage":90,"quality_score":88}' >> metrics-tracker.jsonl
```

### 2. Trigger Optimization (Every 50 Executions)

```bash
# Count executions for command
executions=$(grep -c '"/build-feature"' metrics-tracker.jsonl)

# If >= 50, trigger APE optimization
if [ $executions -ge 50 ]; then
    # 1. Load last 50 metrics
    # 2. Calculate baseline performance
    # 3. Generate 5 variations using ape-optimizer.md
    # 4. Evaluate each variation
    # 5. Select winner
    # 6. Update command prompt
    # 7. Update command-performance.json
fi
```

### 3. Update Performance Summary

After deployment, update `command-performance.json`:
```json
{
  "/build-feature": {
    "prompt_version": "2.0-ape",
    "optimized_at": "2025-12-26T21:00:00Z",
    "current_score": 76.6,
    "improvement_pct": 27.7,
    "executions_since_optimization": 0,
    "next_optimization_at": 50
  }
}
```

---

## Metrics Definitions

### Universal Metrics (All Commands)

**success**: Boolean
- `true`: Command completed without errors
- `false`: Command failed or was interrupted

**duration_sec**: Number
- Time from command start to completion (seconds)
- Used for performance optimization

**prompt_version**: String
- Version of prompt used (e.g., "1.0", "2.0-ape", "3.1-ape-tuned")
- Tracks which optimization iteration generated this result

### Command-Specific Metrics

**Feature-Building Commands** (`/build-feature`, `/build-prd`, `/edit-prd`):
- `test_coverage`: Percentage (0-100) of code covered by tests
- `quality_score`: Code quality rating (0-100)
- `compliance_violations`: Count of PRD/domain violations found
- `features_completed`: Count of features marked complete

**Review Commands** (`/review`, `/verify`, `/prd-check`):
- `issues_found`: Count of issues identified
- `false_positives`: Count of flagged issues that weren't real
- `coverage_pct`: Percentage of code surface area reviewed
- `compliance_score`: Compliance rating (0-100)

**Decision Commands** (`/decide`, `/constraints`, `/perspectives`):
- `options_explored`: Count of alternatives considered
- `confidence_score`: User confidence rating (0-10)
- `reversal`: Boolean (was decision later reversed?)

---

## Composite Score Calculation

**Formula** (for feature-building commands):
```
composite_score = (success_rate × 40%) + (test_coverage × 30%) + (quality_score × 30%)
```

**Example**:
```
success_rate = 87% = 0.87
test_coverage = 92% = 92
quality_score = 88

composite = (0.87 × 40) + (92 × 0.30) + (88 × 0.30)
          = 34.8 + 27.6 + 26.4
          = 88.8
```

**Custom Formulas** per command type defined in `command-performance.json`.

---

## Analysis Queries

### Find Top Performers

```bash
# Extract all /build-feature metrics
grep '"/build-feature"' metrics-tracker.jsonl | \
    jq -s 'sort_by(.composite_score) | reverse | .[0:5]'
```

### Calculate Average Performance

```bash
# Average success rate for last 20 executions
grep '"/build-feature"' metrics-tracker.jsonl | tail -20 | \
    jq -s 'map(select(.success == true)) | length / 20'
```

### Compare Versions

```bash
# Compare v1.0 vs v2.0-ape
grep '"/build-feature"' metrics-tracker.jsonl | \
    jq -s 'group_by(.prompt_version) | map({version: .[0].prompt_version, avg_score: (map(.composite_score) | add / length)})'
```

---

## Future Enhancements

### v3.3: Real-Time Dashboards

```bash
# Live metrics dashboard
watch -n 5 'tail -100 metrics-tracker.jsonl | jq -s "group_by(.command) | map({command: .[0].command, executions: length, avg_success: (map(select(.success)) | length / length)})"'
```

### v3.4: A/B Testing

Run two prompt versions simultaneously:
```json
{
  "ab_test": {
    "command": "/build-feature",
    "variant_a": "2.0-ape",
    "variant_b": "2.1-ape-tuned",
    "traffic_split": "50/50",
    "started_at": "2025-12-27",
    "sample_size_target": 50
  }
}
```

### v3.5: Anomaly Detection

Alert if performance degrades:
```
if current_score < (baseline_score × 0.9):
    alert("Performance degradation detected for /build-feature")
```

---

## References

- **APE Pattern**: `.claude/v3/shared/patterns/ape.md`
- **APE Optimizer**: `.claude/v3/generators/ape-optimizer.md`
- **DAIR.AI Analysis**: `docs/DAIR-AI-ANALYSIS.md`

---

**Created**: 2025-12-26
**Toolkit Version**: v3.2
**Status**: Infrastructure ready for first optimization
