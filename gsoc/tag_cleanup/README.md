# Tag Cleanup: Structured Genre Tags — POC

Proof-of-concept for the GSoC 2026 project: routing genre signal already present in Open Library's unstructured `subjects` field into the dormant `genres` property defined in `/type/work`.

---

## What This POC Does

Open Library works store subject metadata as flat strings (e.g. `"buried treasure--Fiction"`, `"history"`). The `/type/work` Infogami schema already defines a `genres` property of `/type/string`, but it is never populated. The goal of this project is to map existing subject strings to a controlled genre vocabulary using deterministic rules (confidence-scored dictionary lookups), then write the results back to the `genres` field via `site.save_many()`.

This POC validates that approach against the February 2026 OL dump.

---

## Files

| File | Purpose |
|---|---|
| `run_on_dump.py` | Main analysis script — streams the OL dump and reports genre coverage |
| `taxonomy.py` | Rule engine — maps raw subject strings to genres with confidence scores |
| `tag_enrichment.py` | `WorkEnricher` class — applies taxonomy rules to a single work |
| `config.py` | Thresholds and limits (confidence floor, batch size, etc.) |
| `create_tags.py` | Tag lifecycle management (creation, deduplication, audit log) |
| `book_genome.py` | Structured metadata schema for a single work |

---

## Quick Start

```bash
# From the repo root
python3 gsoc/tag_cleanup/run_on_dump.py --sample 500000
```

Requires the February 2026 dump (`ol_dump_works_2026-02-28.txt.gz`) in either:
- `gsoc/tag_cleanup/` (same directory), or
- `~/Downloads/` (standard laptop dev location)

---

## Sample Output

```
Tag Cleanup POC — reading dump: ol_dump_works_2026-02-28.txt.gz
   Sampling first 500,000 works  (use --all for full dump)

  Loading works...
     ...
  Loaded 500,000 works in 11.1s

================================================================================
  TAG CLEANUP POC — REAL DUMP ANALYSIS
  Dump: ol_dump_works_2026-02-28.txt.gz
================================================================================

-- RAW SUBJECT DISTRIBUTION
--------------------------------------------------------------------------------
  Works with subjects    :    247,901  (49.6%)
  Works without subjects :    252,099
  Total subject strings  :    858,039
  Unique subjects        :    127,513
  Avg subjects / work    :        3.5
  LCSH-style (with '--') :      3,517

  Top 20 raw subjects:
      1. 30,036x  history
      2. 10,971x  biography
      3.  8,055x  fiction
      4.  7,534x  congresses
      5.  7,228x  politics and government
      ...

-- ENRICHMENT RESULTS  (n=10,000 works with subjects)
--------------------------------------------------------------------------------
  Genre coverage         :   44.3%
  Avg quality score      :   0.26 / 1.00

  Quality distribution:
    excellent  :      9 (  0.1%)
    good       :    319 (  3.2%) -
    basic      :  4,106 ( 41.1%) --------------------
    poor       :  5,566 ( 55.7%) ---------------------------

  Top genres detected:
    History                    2,267 ( 22.7%)
    Biography                    510 (  5.1%)
    Education                    488 (  4.9%)
    ...

-- SCALE PROJECTION  (extrapolated to 30,000,000 total works)
--------------------------------------------------------------------------------
  Est. works with subjects   :   14,874,060
  Est. genre-tag-able works  :    6,595,158

-- PERFORMANCE
--------------------------------------------------------------------------------
  Throughput             :      12,387 works/s
  ETA (full dump, 1 cpu) :        0.7 h
```

---

## Key Findings

- **44.3%** of works with subject data already contain mappable genre signal.
- **55.7% "poor"** quality is *honest*: these are subjects like `"congresses"` (7,534 hits) and `"catalogs"` (3,074) — bibliographic metadata, not genre.
- The pipeline processes **12,387 works/second** on a single CPU. The full 30M corpus takes **~0.7 hours**.
- At scale, approximately **6.6M works** can receive at least one genre tag from existing subject data alone.

---

## Architecture

```
subjects array          rules engine         genres field
"buried treasure--      conf >= 0.90    -->  "Adventure"
  fiction"
                              |
                              v
                    site.save_many()
                    RunAs('ImportBot')
                              |
                              v
                    Infogami DB
                    work.type (line 228)
                              |
                              v
                    WorkSolrBuilder
                    .seed + .build_subjects
                              |
                              v
                    Solr Index
                    genre_facet / genre_key
                              |
                              v
                    /subjects/genre:adventure
                    (patron-visible)
```

---

## False Positive Strategy

- Rules are **deterministic string lookups**, not model inference. A false positive means a missing rule, not a hallucination.
- `subjects` is **never modified**. Rolling back means clearing the `genres` field only.
- Every write is logged with source subject string + confidence score for librarian auditability.

---

## CLI Reference

```bash
# Sample 500k works (default: 50k)
python3 run_on_dump.py --sample 500000

# Full dump (slow — use for final validation)
python3 run_on_dump.py --all

# Save enriched results to JSONL
python3 run_on_dump.py --sample 100000 --out results.jsonl

# Adjust enrichment limit
python3 run_on_dump.py --sample 500000 --enrich-limit 50000
```

---

## Related

- GSoC 2026 Project: [Tag Cleanup: Structured Genre Tags](https://github.com/internetarchive/openlibrary)
- Tracking Issue: [#11610](https://github.com/internetarchive/openlibrary/issues/11610)
- `work.type` schema: `openlibrary/plugins/openlibrary/types/work.type` (line 228)
