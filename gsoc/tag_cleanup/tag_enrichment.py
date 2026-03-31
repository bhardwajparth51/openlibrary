"""
Tag Enrichment Pipeline for Open Library Works.

Processes millions of subjects and enriches works with typed, high-quality tags
including genres, moods, content warnings, and complete Book Genomes.
"""

import os
import sys
from dataclasses import asdict

# Add paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../scripts"))
)

from book_genome import BookGenome, GenomeFactory
from taxonomy import (
    TagType,
    calculate_tag_coverage,
    estimate_audience,
    get_content_warnings_for_subjects,
    get_tags_for_subjects,
)


class WorkEnricher:
    """Enriches a single work with tags and genome data."""

    def __init__(self, work: dict, dry_run: bool = True):
        self.work = work
        self.dry_run = dry_run
        self.work_id = work.get("key", "").replace("/works/", "")
        self.title = work.get("title", "Unknown")
        self.subjects = work.get("subjects", [])
        self.genome: BookGenome | None = None
        self.enrichment_results: dict = {}

    def enrich(self) -> dict:
        """Run complete enrichment pipeline."""
        if not self.subjects:
            return {"status": "skipped", "reason": "No subjects"}

        # Create genome from work
        self.genome = GenomeFactory.from_work_dict(self.work)

        # Detect genres
        genre_tags = get_tags_for_subjects(
            self.subjects, TagType.GENRE, min_confidence=0.70
        )
        genres = [tag for tag, _ in genre_tags]
        genre_confidences = {tag: conf for tag, conf in genre_tags}
        GenomeFactory.enrich_with_genres(self.genome, genres, genre_confidences)

        # Detect moods
        mood_tags = get_tags_for_subjects(
            self.subjects, TagType.MOOD, min_confidence=0.70
        )
        moods = [tag for tag, _ in mood_tags]
        mood_confidences = {tag: conf for tag, conf in mood_tags}
        GenomeFactory.enrich_with_moods(self.genome, moods, mood_confidences)

        # Detect content warnings
        warnings = get_content_warnings_for_subjects(self.subjects)
        GenomeFactory.enrich_with_content_warnings(self.genome, warnings)

        # Estimate audience
        audience = estimate_audience(self.subjects, self.title)
        self.genome.target_audience = audience

        # Auto-detect features
        GenomeFactory.auto_enrich_features(self.genome)

        # Calculate data quality
        self.genome.calculate_data_quality_score()

        self.enrichment_results = {
            "status": "success",
            "work_id": self.work_id,
            "title": self.title,
            "genres": genres,
            "moods": moods,
            "content_warnings": warnings,
            "target_audience": audience,
            "enrichment_level": self.genome.enrichment_level,
            "data_quality_score": self.genome.data_quality_score,
            "subject_count": len(self.subjects),
        }

        return self.enrichment_results

    def get_genome(self) -> BookGenome | None:
        """Return the enriched genome."""
        return self.genome

    def to_dict(self) -> dict:
        """Convert enriched work to dictionary format."""
        if not self.genome:
            return {"work_id": self.work_id, "status": "not_enriched"}

        work_enriched = {
            "key": self.work.get("key"),
            "title": self.title,
            "subjects": self.subjects,
            "genres": self.genome.genres,
            "moods": self.genome.moods,
            "content_warnings": self.genome.content_warnings,
            "target_audience": self.genome.target_audience,
            "enrichment_level": self.genome.enrichment_level,
            "data_quality_score": self.genome.data_quality_score,
            "book_genome": asdict(self.genome),
        }
        return work_enriched


class BulkWorkEnricher:
    """Processes multiple works with enrichment."""

    def __init__(self, works: list[dict], dry_run: bool = True):
        self.works = works
        self.dry_run = dry_run
        self.enriched_works: list[dict] = []
        self.stats = {
            "total_processed": 0,
            "successfully_enriched": 0,
            "skipped": 0,
            "excellent_quality": 0,
            "good_quality": 0,
            "basic_quality": 0,
            "poor_quality": 0,
            "avg_data_quality": 0.0,
            "genre_coverage_pct": 0.0,
            "mood_coverage_pct": 0.0,
        }

    def process(self) -> list[dict]:
        """Process all works."""
        print(f"Processing {len(self.works)} works...")

        quality_scores = []

        for work in self.works:
            enricher = WorkEnricher(work, dry_run=self.dry_run)
            result = enricher.enrich()

            self.stats["total_processed"] += 1

            if result["status"] == "success":
                self.stats["successfully_enriched"] += 1
                enriched_work = enricher.to_dict()
                self.enriched_works.append(enriched_work)

                # Track quality
                quality = result["enrichment_level"]
                self.stats[f"{quality}_quality"] += 1
                quality_scores.append(result["data_quality_score"])

            elif result["status"] == "skipped":
                self.stats["skipped"] += 1

        # Calculate averages
        if quality_scores:
            self.stats["avg_data_quality"] = sum(quality_scores) / len(quality_scores)

        # Coverage statistics
        coverage = calculate_tag_coverage(self.works)
        self.stats["genre_coverage_pct"] = coverage["genre_coverage_pct"]
        self.stats["mood_coverage_pct"] = coverage["mood_coverage_pct"]

        return self.enriched_works

    def get_stats(self) -> dict:
        """Get processing statistics."""
        return self.stats

    def print_report(self):
        """Print enrichment report."""
        print("\n" + "=" * 70)
        print("TAG ENRICHMENT REPORT")
        print("=" * 70)
        print(f"\nTotal Works Processed: {self.stats['total_processed']}")
        print(f"Successfully Enriched: {self.stats['successfully_enriched']}")
        print(f"Skipped (no subjects): {self.stats['skipped']}")
        print("\nData Quality Distribution:")
        print(f"  Excellent: {self.stats['excellent_quality']}")
        print(f"  Good:      {self.stats['good_quality']}")
        print(f"  Basic:     {self.stats['basic_quality']}")
        print(f"  Poor:      {self.stats['poor_quality']}")
        print(f"\nAverage Data Quality Score: {self.stats['avg_data_quality']:.2f}/1.0")
        print(f"Genre Coverage: {self.stats['genre_coverage_pct']:.1f}% of works")
        print(f"Mood Coverage: {self.stats['mood_coverage_pct']:.1f}% of works")
        print("=" * 70 + "\n")
