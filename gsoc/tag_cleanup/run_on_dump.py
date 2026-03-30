#!/usr/bin/env python3
"""
Run the Tag-Cleanup POC against the real Open Library works dump.

Usage:
    python run_on_dump.py                         # default: sample 50k, report on 10k
    python run_on_dump.py --sample 100000         # larger sample
    python run_on_dump.py --all                   # full dump (slow!)
    python run_on_dump.py --out results.jsonl     # save enriched works

The dump format (tab-separated, 5 columns):
    /type/work  /works/OLxxxW  <revision>  <timestamp>  <json>
"""

import argparse
import gzip
import json
import os
import sys
import time
from collections import Counter
from collections.abc import Iterator

# Make local modules importable when run from this directory
sys.path.insert(0, os.path.dirname(__file__))

from tag_enrichment import WorkEnricher

# ─────────────────────────── constants ───────────────────────────────────────

# The dump file location (checked in local dir then Downloads)
DUMP_NAME = "ol_dump_works_2026-02-28.txt.gz"
DUMP_FILE = os.path.join(os.path.dirname(__file__), DUMP_NAME)

# Fallback to Downloads if not found (standard for laptop-dev environments)
if not os.path.exists(DUMP_FILE):
    DUMP_FILE = os.path.join(os.path.expanduser("~"), "Downloads", DUMP_NAME)

DEFAULT_SAMPLE_SIZE = 50_000  # works to inspect
DEFAULT_ENRICH_LIMIT = 10_000  # works to fully enrich (subjects required)

PROGRESS_EVERY = 10_000  # print progress every N works


# ─────────────────────────── dump reader ─────────────────────────────────────


def iter_works(dump_path: str, limit: int | None = None) -> Iterator[dict]:
    """
    Stream work JSON objects from the gzipped OL dump.

    Each line is tab-separated:
        /type/work  /works/OLxxxW  revision  timestamp  json_blob
    """
    count = 0
    opener = gzip.open if dump_path.endswith(".gz") else open

    with opener(dump_path, "rt", encoding="utf-8") as fh:
        for raw_line in fh:
            parts = raw_line.rstrip("\n").split("\t", 4)
            if len(parts) < 5:
                continue
            _type, _key, _rev, _ts, json_blob = parts
            if _type != "/type/work":
                continue
            try:
                work = json.loads(json_blob)
            except json.JSONDecodeError:
                continue

            yield work
            count += 1

            if limit and count >= limit:
                break


# ─────────────────────────── analysis helpers ────────────────────────────────


def analyze_subject_distribution(works: list[dict]) -> dict:
    """
    Report on raw subject data quality before enrichment.
    """
    subject_counter: Counter = Counter()
    has_subjects = 0
    no_subjects = 0
    total_subject_strings = 0
    long_subjects = 0  # > 100 chars — likely noise
    short_subjects = 0  # < 3 chars  — likely noise
    lcsh_style = 0  # contains " -- " or "--"

    for work in works:
        subjects = work.get("subjects", [])
        if not subjects:
            no_subjects += 1
            continue

        has_subjects += 1
        total_subject_strings += len(subjects)

        for s in subjects:
            s = str(s).strip()
            subject_counter[s.lower()] += 1
            if len(s) > 100:
                long_subjects += 1
            if len(s) < 3:
                short_subjects += 1
            if "--" in s or " -- " in s:
                lcsh_style += 1

    return {
        "has_subjects": has_subjects,
        "no_subjects": no_subjects,
        "subjects_pct": has_subjects / len(works) * 100 if works else 0,
        "total_subject_strings": total_subject_strings,
        "avg_subjects_per_work": (
            total_subject_strings / has_subjects if has_subjects else 0
        ),
        "unique_subjects": len(subject_counter),
        "long_subjects": long_subjects,
        "short_subjects": short_subjects,
        "lcsh_style": lcsh_style,
        "top_50_subjects": subject_counter.most_common(50),
    }


def enrich_sample(works: list[dict], limit: int) -> dict:
    """
    Run the WorkEnricher on works that have subjects.

    Returns aggregated stats + per-work enrichment results.
    """
    enriched_results = []
    genre_counter: Counter = Counter()
    mood_counter: Counter = Counter()
    warning_counter: Counter = Counter()
    audience_counter: Counter = Counter()
    quality_levels: Counter = Counter()
    quality_scores: list[float] = []

    skipped_no_subjects = 0
    processed = 0
    enrich_errors = 0

    for work in works:
        if not work.get("subjects"):
            skipped_no_subjects += 1
            continue
        if processed >= limit:
            break

        try:
            enricher = WorkEnricher(work, dry_run=True)
            result = enricher.enrich()

            if result["status"] == "success":
                processed += 1
                enriched_results.append(result)

                for g in result["genres"]:
                    genre_counter[g] += 1
                for m in result["moods"]:
                    mood_counter[m] += 1
                for w in result["content_warnings"]:
                    warning_counter[w] += 1
                audience_counter[result["target_audience"]] += 1
                quality_levels[result["enrichment_level"]] += 1
                quality_scores.append(result["data_quality_score"])

        except Exception as exc:
            enrich_errors += 1
            if enrich_errors <= 3:
                print(f"  [WARN] Enrichment error on {work.get('key')}: {exc}")

    works_with_genre = sum(1 for r in enriched_results if r["genres"])
    works_with_mood = sum(1 for r in enriched_results if r["moods"])
    works_with_warning = sum(1 for r in enriched_results if r["content_warnings"])

    return {
        "processed": processed,
        "skipped_no_subjects": skipped_no_subjects,
        "enrich_errors": enrich_errors,
        "genre_coverage_pct": works_with_genre / processed * 100 if processed else 0,
        "mood_coverage_pct": works_with_mood / processed * 100 if processed else 0,
        "warning_coverage_pct": (
            works_with_warning / processed * 100 if processed else 0
        ),
        "avg_quality_score": (
            sum(quality_scores) / len(quality_scores) if quality_scores else 0
        ),
        "avg_genres_per_work": (
            sum(len(r["genres"]) for r in enriched_results) / processed
            if processed
            else 0
        ),
        "quality_distribution": dict(quality_levels),
        "top_genres": genre_counter.most_common(20),
        "top_moods": mood_counter.most_common(10),
        "top_warnings": warning_counter.most_common(10),
        "audience_distribution": dict(audience_counter),
        "enriched_results": enriched_results,
    }


# ─────────────────────────── reporting ───────────────────────────────────────


def print_report(sample_stats: dict, enrich_stats: dict, elapsed: float):
    sep = "=" * 80

    print(f"\n{sep}")
    print("  TAG CLEANUP POC — REAL DUMP ANALYSIS")
    print("  Dump: ol_dump_works_2026-02-28.txt.gz")
    print(sep)

    # ── Subject Distribution ──────────────────────────────────────────────────
    print("\n📊  RAW SUBJECT DISTRIBUTION")
    print("-" * 80)
    s = sample_stats
    print(
        f"  Works with subjects    : {s['has_subjects']:>10,}  ({s['subjects_pct']:.1f}%)"
    )
    print(f"  Works without subjects : {s['no_subjects']:>10,}")
    print(f"  Total subject strings  : {s['total_subject_strings']:>10,}")
    print(f"  Unique subjects        : {s['unique_subjects']:>10,}")
    print(f"  Avg subjects / work    : {s['avg_subjects_per_work']:>10.1f}")
    print(f"  LCSH-style (with '--') : {s['lcsh_style']:>10,}")
    print(f"  Too-long  (> 100 chars): {s['long_subjects']:>10,}")
    print(f"  Too-short (<  3 chars) : {s['short_subjects']:>10,}")

    print("\n  Top 20 raw subjects:")
    for rank, (subj, cnt) in enumerate(s["top_50_subjects"][:20], 1):
        print(f"    {rank:>3}. {cnt:>6,}×  {subj[:70]}")

    # ── Enrichment Results ───────────────────────────────────────────────────
    print(
        f"\n🔖  ENRICHMENT RESULTS  (n={enrich_stats['processed']:,} works with subjects)"
    )
    print("-" * 80)
    e = enrich_stats
    print(f"  Genre coverage         : {e['genre_coverage_pct']:>6.1f}%")
    print(f"  Mood coverage          : {e['mood_coverage_pct']:>6.1f}%")
    print(f"  Content warning cov.   : {e['warning_coverage_pct']:>6.1f}%")
    print(f"  Avg genres / work      : {e['avg_genres_per_work']:>6.1f}")
    print(f"  Avg quality score      : {e['avg_quality_score']:>6.2f} / 1.00")

    print("\n  Quality distribution:")
    for level in ("excellent", "good", "basic", "poor"):
        cnt = e["quality_distribution"].get(level, 0)
        pct = cnt / e["processed"] * 100 if e["processed"] else 0
        bar = "█" * int(pct / 2)
        print(f"    {level:<10} : {cnt:>6,} ({pct:5.1f}%) {bar}")

    print("\n  Top genres detected:")
    for genre, cnt in e["top_genres"]:
        pct = cnt / e["processed"] * 100
        print(f"    {genre:<25} {cnt:>6,} ({pct:5.1f}%)")

    print("\n  Top moods detected:")
    for mood, cnt in e["top_moods"]:
        pct = cnt / e["processed"] * 100
        print(f"    {mood:<25} {cnt:>6,} ({pct:5.1f}%)")

    print("\n  Content warnings detected:")
    for warning, cnt in e["top_warnings"]:
        pct = cnt / e["processed"] * 100
        print(f"    {warning:<25} {cnt:>6,} ({pct:5.1f}%)")

    print("\n  Audience distribution:")
    for audience, cnt in sorted(
        e["audience_distribution"].items(), key=lambda x: -x[1]
    ):
        pct = cnt / e["processed"] * 100
        print(f"    {audience:<25} {cnt:>6,} ({pct:5.1f}%)")

    # ── Scale Projection ─────────────────────────────────────────────────────
    TOTAL_WORKS_APPROX = 30_000_000  # rough OL total
    genre_cov_frac = e["genre_coverage_pct"] / 100
    print(
        f"\n📈  SCALE PROJECTION  (extrapolated to {TOTAL_WORKS_APPROX:,} total works)"
    )
    print("-" * 80)
    has_subj_frac = s["subjects_pct"] / 100
    est_works_with_subjects = int(TOTAL_WORKS_APPROX * has_subj_frac)
    est_genre_tagged = int(est_works_with_subjects * genre_cov_frac)
    print(f"  Est. works with subjects   : {est_works_with_subjects:>12,}")
    print(f"  Est. genre-tag-able works  : {est_genre_tagged:>12,}")
    print(
        f"  Est. unique subjects total : {int(s['unique_subjects'] * TOTAL_WORKS_APPROX / max(s['has_subjects'] + s['no_subjects'], 1)):>12,}"
    )

    # ── Performance ──────────────────────────────────────────────────────────
    rate = e["processed"] / elapsed if elapsed > 0 else 0
    print("\n⏱   PERFORMANCE")
    print("-" * 80)
    print(f"  Works enriched         : {e['processed']:>10,}")
    print(f"  Wall-clock time        : {elapsed:>10.1f} s")
    print(f"  Throughput             : {rate:>10.0f} works/s")
    if rate > 0:
        eta_full = TOTAL_WORKS_APPROX / rate / 3600
        print(f"  ETA (full dump, 1 cpu) : {eta_full:>10.1f} h")

    print(f"\n{sep}\n")


# ─────────────────────────── main ────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Run Tag Cleanup POC on OL dump")
    parser.add_argument("--dump", default=DUMP_FILE, help="Path to dump .gz file")
    parser.add_argument(
        "--sample",
        type=int,
        default=DEFAULT_SAMPLE_SIZE,
        help=f"Number of works to read from dump (default: {DEFAULT_SAMPLE_SIZE:,})",
    )
    parser.add_argument(
        "--enrich-limit",
        type=int,
        default=DEFAULT_ENRICH_LIMIT,
        help=f"Max works to fully enrich (default: {DEFAULT_ENRICH_LIMIT:,})",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process the entire dump (overrides --sample)",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Write enriched results to this JSONL file",
    )
    args = parser.parse_args()

    sample_limit = None if args.all else args.sample
    enrich_limit = args.enrich_limit

    print(f"\n🚀 Tag Cleanup POC — reading dump: {args.dump}")
    if sample_limit:
        print(f"   Sampling first {sample_limit:,} works  (use --all for full dump)")

    # ── 1. Stream works ──────────────────────────────────────────────────────
    print("\n  Loading works...", flush=True)
    t0 = time.perf_counter()

    works: list[dict] = []
    for i, work in enumerate(iter_works(args.dump, limit=sample_limit)):
        works.append(work)
        if (i + 1) % PROGRESS_EVERY == 0:
            elapsed = time.perf_counter() - t0
            print(f"    {i+1:>8,} works read  ({elapsed:.1f}s)", flush=True)

    load_elapsed = time.perf_counter() - t0
    print(f"  ✓ Loaded {len(works):,} works in {load_elapsed:.1f}s")

    # ── 2. Analyse raw subjects ──────────────────────────────────────────────
    print("\n  Analysing subjects...", flush=True)
    sample_stats = analyze_subject_distribution(works)

    # ── 3. Enrich ────────────────────────────────────────────────────────────
    print(f"\n  Enriching up to {enrich_limit:,} works with subjects...", flush=True)
    t_enrich = time.perf_counter()
    enrich_stats = enrich_sample(works, limit=enrich_limit)
    enrich_elapsed = time.perf_counter() - t_enrich

    # ── 4. Report ────────────────────────────────────────────────────────────
    print_report(sample_stats, enrich_stats, enrich_elapsed)

    # ── 5. Optionally save results ───────────────────────────────────────────
    if args.out:
        out_path = args.out
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.writelines(
                json.dumps(result) + "\n" for result in enrich_stats["enriched_results"]
            )
        print(
            f"  💾 Saved {len(enrich_stats['enriched_results']):,} enriched results → {out_path}\n"
        )


if __name__ == "__main__":
    main()
