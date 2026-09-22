# YouTube Research Tool — Specification

Version: 0.1
Status: MVP
Type: CLI / Local Python Application
Purpose: Automated YouTube search-result collection for niche research

---

# 1. Objective

Build a small local Python application that receives a dataset of YouTube search queries and automatically collects structured information from the first N results of each YouTube search.

The initial use case is researching approximately 280 YouTube search terms for a monetizable AI-assisted YouTube channel.

The application must reduce manual research by converting:

    Search terms
        ↓
    YouTube search results
        ↓
    Structured dataset
        ↓
    Quantitative analysis

The MVP must prioritize reliability, resumability, traceability, and clean structured output over UI complexity.

---

# 2. Scope

## 2.1 In Scope

The MVP must:

- Accept a CSV input file containing YouTube search queries.
- Support a configurable number of results per query.
- Open YouTube search-result pages using a real browser.
- Extract data from search results.
- Store one record per discovered video.
- Preserve search-query context.
- Preserve result position.
- Save results incrementally.
- Resume interrupted executions.
- Record errors without stopping the entire process.
- Produce CSV output.
- Produce an execution log.
- Provide basic CLI configuration.
- Provide a dry-run / test mode for a small number of queries.

## 2.2 Out of Scope

The MVP must NOT include:

- Web dashboard.
- Database server.
- Cloud deployment.
- Authentication system.
- YouTube API dependency.
- Automatic niche scoring.
- AI analysis of titles.
- LLM integration.
- Thumbnail analysis.
- Video transcription.
- Video downloading.
- Comment extraction.
- Channel scraping beyond information visible in search results.
- Automated interaction with videos.
- Automatic publishing.
- Proxy rotation.
- CAPTCHA bypass.
- Anti-bot evasion mechanisms.

These may become future versions.

---

# 3. Primary Use Case

The user has a dataset similar to:

| category | query | url |
|---|---|---|
| Propósito | no sé qué hacer con mi vida | https://www.youtube.com/results?search_query=no+se+que+hacer+con+mi+vida |
| Propósito | qué hacer con mi vida | https://www.youtube.com/results?search_query=que+hacer+con+mi+vida |
| Nietzsche | Nietzsche felicidad | https://www.youtube.com/results?search_query=Nietzsche+felicidad |

The application processes each query and extracts the first N organic video results.

Default:

    N = 10

Configurable:

    N = 5
    N = 10
    N = 15
    etc.

---

# 4. Functional Requirements

## FR-001 — Input Dataset

The application MUST accept a CSV file.

Minimum required field:

    query

Optional fields:

    category
    url

Example:

```csv
category,query,url
Propósito,no sé qué hacer con mi vida,https://www.youtube.com/results?search_query=no+se+que+hacer+con+mi+vida
Propósito,qué hacer con mi vida,https://www.youtube.com/results?search_query=que+hacer+con+mi+vida
Nietzsche,Nietzsche felicidad,https://www.youtube.com/results?search_query=Nietzsche+felicidad
```

The application MUST support UTF-8.

The application SHOULD use the supplied URL when available.

If URL is absent, the application MUST generate the YouTube search URL from the query.

---

# 5. FR-002 — Query Processing

For every query:

1. Open the corresponding YouTube search URL.
2. Wait for the page to load.
3. Wait for search-result elements to become available.
4. Extract video results.
5. Stop when N valid video results have been collected.
6. Save the results immediately.
7. Move to the next query.

A failure in one query MUST NOT terminate the complete execution.

---

# 6. FR-003 — Browser Automation

Use:

    Python
    Playwright
    Chromium

The browser MUST operate in normal visible-browser-compatible mode during MVP development.

The implementation MUST NOT attempt to bypass CAPTCHA, authentication systems, rate limits, or anti-bot protections.

The browser layer MUST be isolated from the extraction and persistence layers.

Suggested architecture:

```text
src/
├── main.py
├── config.py
├── input_loader.py
├── browser.py
├── extractor.py
├── models.py
├── storage.py
├── logger.py
└── utils.py
```

---

# 7. FR-004 — Result Extraction

For each video result extract, when available:

- query
- category
- position
- video_id
- title
- channel
- views
- published_text
- duration
- video_url
- thumbnail_url
- scraped_at

Example:

```json
{
  "query": "Nietzsche felicidad",
  "category": "Nietzsche",
  "position": 1,
  "video_id": "abc123",
  "title": "Nietzsche y la felicidad",
  "channel": "Example Channel",
  "views": 125000,
  "published_text": "hace 2 años",
  "duration": "12:34",
  "video_url": "https://www.youtube.com/watch?v=abc123",
  "thumbnail_url": "...",
  "scraped_at": "2026-09-22T..."
}
```

Fields unavailable in the UI MUST be stored as null/empty rather than inferred.

---

# 8. FR-005 — Result Position

Position MUST represent the order in which valid video results appear in the search result list.

Positions must start at:

    1

and increment sequentially.

Non-video elements must NOT consume positions.

For example:

```text
Position 1 → Video
Position 2 → Video
Advertisement → ignored
Position 3 → Video
```

---

# 9. FR-006 — Data Normalization

Views MUST be normalized into an integer whenever possible.

Examples:

    "1.2M views" → 1200000
    "500K views" → 500000
    "12 mil vistas" → 12000

If normalization cannot be performed reliably:

    views = null

The original visible text SHOULD also be preserved:

    views_text

Dates must NOT be converted into an invented absolute date if only relative text is available.

Preserve:

    published_text

Example:

    "hace 3 años"

Do not infer the exact publication date unless the source explicitly provides it.

---

# 10. FR-007 — Duplicate Handling

The application MUST detect duplicate videos.

Primary duplicate key:

    video_id

The same video may appear for multiple queries.

It MUST remain associated with each query where it appears.

Therefore deduplication should happen at the record/query level, not globally.

Example:

```text
query A + video X
query B + video X
```

Both records are valid.

Within the same query, the same video MUST NOT be stored twice.

---

# 11. FR-008 — Incremental Persistence

Results MUST be persisted incrementally.

Do NOT wait until all 280 queries are completed.

If the application stops after query 137, results from queries 1–136 MUST remain available.

Preferred MVP implementation:

    CSV append / checkpoint file

Alternative:

    SQLite

SQLite is preferred if it simplifies reliable resume behavior without significantly increasing complexity.

---

# 12. FR-009 — Resume

The application MUST support resuming an interrupted run.

Example:

```bash
python -m src.main --input input/searches.csv --limit 10
```

If execution stops after query 50:

```bash
python -m src.main --input input/searches.csv --limit 10 --resume
```

The application MUST skip queries that have already completed successfully.

A query is considered complete only if the required processing finished successfully.

---

# 13. FR-010 — Error Handling

Errors must be isolated per query.

Possible errors:

- page timeout
- navigation error
- selector not found
- YouTube unavailable
- browser failure
- malformed input
- extraction failure
- unexpected page structure

Errors MUST be written to:

    output/errors.csv

Minimum fields:

```text
query
category
error_type
error_message
timestamp
retry_count
```

The main process MUST continue after recoverable query-level errors.

---

# 14. FR-011 — Retry

Each failed query SHOULD be retried a configurable number of times.

Default:

    2 retries

Example:

```text
Attempt 1 → failed
Attempt 2 → failed
Attempt 3 → failed
→ mark query as failed
→ continue
```

Retries MUST NOT become an infinite loop.

---

# 15. FR-012 — Rate Control

The application MUST introduce configurable delays between queries.

Default:

    random delay between 2 and 5 seconds

Configuration:

    MIN_DELAY
    MAX_DELAY

The application MUST NOT implement aggressive request patterns.

---

# 16. FR-013 — Test Mode

The application MUST support a limited test mode.

Example:

```bash
python -m src.main \
  --input input/searches.csv \
  --limit 10 \
  --queries 5
```

Meaning:

- process only first 5 queries
- extract up to 10 results per query

This is mandatory for MVP validation before running the full dataset.

---

# 17. FR-014 — Configurable Result Limit

CLI:

```bash
--limit 10
```

Default:

    10

Examples:

```bash
--limit 5
--limit 10
--limit 15
```

---

# 18. FR-015 — Output

The application MUST generate:

```text
output/
├── results.csv
├── errors.csv
└── run_summary.json
```

## results.csv

Required columns:

```text
query
category
position
video_id
title
channel
views
views_text
published_text
duration
video_url
thumbnail_url
scraped_at
```

## errors.csv

```text
query
category
error_type
error_message
timestamp
retry_count
```

## run_summary.json

Example:

```json
{
  "started_at": "...",
  "finished_at": "...",
  "total_queries": 280,
  "completed_queries": 270,
  "failed_queries": 10,
  "videos_collected": 2650,
  "requested_results_per_query": 10
}
```

---

# 19. CLI Specification

Minimum interface:

```bash
python -m src.main --input INPUT
```

Options:

```text
--input PATH
--output PATH
--limit INTEGER
--queries INTEGER
--resume
--headless
--delay-min FLOAT
--delay-max FLOAT
--retries INTEGER
```

Example:

```bash
python -m src.main \
  --input input/searches.csv \
  --output output \
  --limit 10 \
  --queries 5 \
  --delay-min 2 \
  --delay-max 5
```

---

# 20. Architecture

Use a simple layered architecture.

```text
                ┌─────────────────┐
                │      CLI        │
                └────────┬────────┘
                         ↓
                ┌─────────────────┐
                │ Query Processor │
                └────────┬────────┘
                         ↓
                ┌─────────────────┐
                │ Browser Adapter │
                │   Playwright    │
                └────────┬────────┘
                         ↓
                ┌─────────────────┐
                │    Extractor    │
                └────────┬────────┘
                         ↓
                ┌─────────────────┐
                │    Validator    │
                └────────┬────────┘
                         ↓
                ┌─────────────────┐
                │    Storage      │
                └─────────────────┘
```

Responsibilities:

### CLI

Configuration and execution.

### Query Processor

Controls iteration, retries, resume and orchestration.

### Browser Adapter

Only browser/page interaction.

### Extractor

Only converts page content into structured records.

### Validator

Validates extracted records.

### Storage

Persistence and checkpoints.

---

# 21. Domain Model

## SearchQuery

```text
id
category
query
url
status
attempts
last_error
created_at
completed_at
```

Status:

```text
pending
processing
completed
failed
```

## VideoResult

```text
query
category
position
video_id
title
channel
views
views_text
published_text
duration
video_url
thumbnail_url
scraped_at
```

---

# 22. Non-Functional Requirements

## NFR-001 — Reliability

A failure in one search MUST NOT destroy previously collected data.

## NFR-002 — Resumability

The process MUST be restartable.

## NFR-003 — Traceability

Every result MUST be traceable to:

    query
    category
    position
    source URL
    scrape timestamp

## NFR-004 — Maintainability

Selectors and browser-specific logic MUST be isolated.

If YouTube changes its DOM, extraction logic should be replaceable without rewriting the entire application.

## NFR-005 — Observability

The application MUST provide readable console progress.

Example:

```text
[001/280] Nietzsche felicidad
    ✓ 10 videos

[002/280] Nietzsche propósito
    ✓ 10 videos

[003/280] Nietzsche éxito
    ⚠ timeout → retry 1/2
```

---

# 23. MVP Acceptance Criteria

The MVP is considered complete when all conditions below are satisfied.

## AC-001

Given a CSV with 5 YouTube queries, the application processes all 5 without manual interaction.

## AC-002

For each successful query, up to 10 video results are extracted.

## AC-003

Each result contains at minimum:

```text
query
position
title
channel
video_url
```

## AC-004

Views are normalized when reliably available.

## AC-005

The original visible views text is preserved.

## AC-006

Results are persisted incrementally.

## AC-007

The application can resume after interruption.

## AC-008

A failed query does not terminate the complete run.

## AC-009

Failures are recorded in errors.csv.

## AC-010

A run summary is generated.

## AC-011

The application can process the supplied research dataset.

## AC-012

No CAPTCHA/anti-bot bypass mechanism is implemented.

---

# 24. Test Plan

## Test 1 — Input

Input:

    5 queries

Expected:

    5 queries loaded

## Test 2 — Extraction

Expected:

    5 × up to 10 videos

## Test 3 — Resume

Interrupt execution after 2 queries.

Restart with:

```bash
--resume
```

Expected:

    Queries 1–2 skipped
    Queries 3–5 processed

## Test 4 — Failure

Force an invalid YouTube URL.

Expected:

    query marked failed
    error recorded
    execution continues

## Test 5 — Duplicate

If the same video appears twice for one query:

Expected:

    only one result record

If the same video appears for different queries:

Expected:

    one record per query

---

# 25. Initial Project Structure

Create:

```text
youtube-research-tool/
│
├── README.md
├── SPEC.md
├── pyproject.toml
├── .gitignore
│
├── input/
│   └── searches.csv
│
├── output/
│
├── logs/
│
├── tests/
│   ├── test_input_loader.py
│   ├── test_extractor.py
│   ├── test_storage.py
│   └── test_utils.py
│
└── src/
    ├── __init__.py
    ├── main.py
    ├── config.py
    ├── models.py
    ├── input_loader.py
    ├── browser.py
    ├── extractor.py
    ├── validator.py
    ├── storage.py
    ├── logger.py
    └── utils.py
```

---

# 26. Implementation Constraints

Codex MUST:

1. Read this specification before implementation.
2. Implement the MVP only.
3. Avoid unnecessary frameworks.
4. Prefer standard Python libraries where practical.
5. Use Playwright for browser automation.
6. Keep browser-specific selectors isolated.
7. Write tests for core parsing and storage behavior.
8. Never hardcode the user's 280 searches into application logic.
9. Treat the input dataset as external data.
10. Keep configuration separate from implementation.
11. Document installation and execution.
12. Do not add future features unless required for MVP correctness.

---

# 27. Definition of Done

The implementation is complete when:

```text
[ ] Project structure created
[ ] Python environment documented
[ ] Playwright configured
[ ] Chromium installation documented
[ ] CSV input implemented
[ ] Query loading implemented
[ ] Browser adapter implemented
[ ] YouTube result extraction implemented
[ ] Data normalization implemented
[ ] Validation implemented
[ ] Incremental persistence implemented
[ ] Resume implemented
[ ] Retry implemented
[ ] Error logging implemented
[ ] CLI implemented
[ ] Test mode implemented
[ ] Unit tests implemented
[ ] README implemented
[ ] MVP tested with 5 real queries
[ ] Output verified manually
```

---

# 28. Development Sequence

Implement in this order:

### Phase 1 — Foundation

- project structure
- pyproject.toml
- configuration
- models
- logging

### Phase 2 — Input

- CSV loader
- validation
- query model

### Phase 3 — Browser

- Playwright setup
- Chromium launch
- navigation
- page loading

### Phase 4 — Extraction

- video result detection
- title extraction
- channel extraction
- views extraction
- date extraction
- duration extraction
- URL extraction
- thumbnail extraction

### Phase 5 — Persistence

- results storage
- error storage
- checkpoints
- resume

### Phase 6 — Reliability

- retries
- timeouts
- delays
- validation
- duplicate handling

### Phase 7 — CLI

- arguments
- test mode
- progress output

### Phase 8 — MVP Validation

Run:

```bash
python -m src.main \
  --input input/searches.csv \
  --limit 10 \
  --queries 5
```

Validate the generated dataset manually.

Only after successful validation should the tool be used against the complete research dataset.

---

# 29. Future Extensions

Do NOT implement these in MVP.

Potential future versions:

## V0.2

- SQLite storage
- richer statistics
- automatic keyword summaries
- Excel export

## V0.3

- title pattern analysis
- channel concentration analysis
- view distribution analysis
- publication-age analysis

## V0.4

- automated opportunity scoring
- category comparison
- demand/competition dashboard

## V0.5

- LLM-assisted qualitative analysis
- hook classification
- format classification
- content-gap detection

---

# 30. Research Context

This tool exists to support the research phase of a YouTube monetization project.

The research dataset contains approximately 280 search terms covering human problems and applications of philosophical / historical thinkers.

The tool MUST remain domain-agnostic.

It should work equally well for:

    Nietzsche felicidad

or:

    cómo encontrar mi propósito

or:

    cómo dejar de procrastinar

The tool's responsibility is data collection.

Interpretation and niche selection are separate processes.

---

# 31. Principle

The application should follow this principle:

    Automate collection.
    Preserve raw evidence.
    Normalize only when justified.
    Never invent missing data.
    Keep research reproducible.

The application is a research instrument, not the decision-maker.
