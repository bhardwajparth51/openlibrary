"""
Book Genome Schema for Open Library.

Inspired by GroupLens Book Genome Project, creates a rich, structured representation
of book metadata extracted from subjects, descriptions, and Machine Learning.

This schema enables:
- Precise book discovery and recommendations
- Genre/mood-based searches
- Content warning filtering
- Audience targeting
"""

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class Character:
    """Character mentioned in the book."""

    name: str
    role: str | None = None  # e.g., "protagonist", "antagonist"
    description: str | None = None
    mentions: int = 1  # How many times mentioned in sample text


@dataclass
class Setting:
    """Physical or temporal setting."""

    name: str
    setting_type: str = "place"  # "place", "time_period", "fictional_world"
    description: str | None = None


@dataclass
class BookGenome:
    """Complete genome for a book.

    Note: The current POC pipeline only populates `genres`, `moods`,
    `content_warnings`, and `target_audience`. The other fields (like `themes`,
    `characters`, etc.) are structural placeholders for Phase 2 (ML/Editorial enrichment).
    """

    work_id: str
    title: str

    # Basic classification
    fiction: bool = True
    formats: list[str] = field(default_factory=list)  # novel, short story, etc.

    # Content characteristics
    genres: list[str] = field(default_factory=list)
    moods: list[str] = field(default_factory=list)
    themes: list[str] = field(default_factory=list)
    styles: list[str] = field(default_factory=list)

    # Narrative elements
    characters: list[Character] = field(default_factory=list)
    settings: list[Setting] = field(default_factory=list)
    time_periods: list[str] = field(default_factory=list)

    # Content warnings & audience
    content_warnings: list[str] = field(default_factory=list)
    target_audience: str = "All Ages"

    # Features & special elements
    has_magic: bool = False
    has_romance: bool = False
    has_mystery: bool = False
    has_adventure: bool = False
    has_humor: bool = False
    pacing: str | None = None  # "slow", "steady", "fast", "variable"
    density: str | None = None  # "light", "medium", "dense"

    # Topics (what the book is about)
    topics: list[str] = field(default_factory=list)

    # Metadata
    source_subjects: list[str] = field(default_factory=list)
    confidence_scores: dict[str, float] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    data_quality_score: float = 0.0  # 0-1, how confident we are in this genome

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary using custom serialization."""
        data = asdict(self)
        # Convert Character and Setting objects to dicts
        data["characters"] = [asdict(c) for c in self.characters]
        data["settings"] = [asdict(s) for s in self.settings]
        return data

    def to_json(self) -> str:
        """Serialize to JSON."""
        return json.dumps(self.to_dict(), indent=2, default=str)

    @property
    def enrichment_level(self) -> str:
        """
        Estimate how enriched this genome is for a rule-based Phase-1 pipeline.

        Only counts the four fields the subject-mapping pipeline actually fills:
          1. genres            (primary signal, weight 2)
          2. moods             (secondary signal, weight 1)
          3. content_warnings  (secondary signal, weight 1)
          4. non-default audience (secondary signal, weight 1)

        Levels:
          poor      - no tags at all
          basic     - genres only
          good      - genres + at least one secondary field
          excellent - genres + 2 or more secondary fields
        """
        has_genres = len(self.genres) > 0
        secondary = sum(
            [
                len(self.moods) > 0,
                len(self.content_warnings) > 0,
                self.target_audience != "All Ages",
            ]
        )

        if not has_genres:
            return "poor"
        elif secondary == 0:
            return "basic"
        elif secondary == 1:
            return "good"
        else:
            return "excellent"

    def has_flag(self, flag: str) -> bool:
        """Check if book has certain special feature."""
        flags = {
            "romance": self.has_romance,
            "magic": self.has_magic,
            "mystery": self.has_mystery,
            "adventure": self.has_adventure,
            "humor": self.has_humor,
        }
        return flags.get(flag.lower(), False)

    def add_confidence_score(self, field: str, score: float):
        """Record confidence score for a field."""
        self.confidence_scores[field] = max(0.0, min(1.0, score))

    def calculate_data_quality_score(self) -> float:
        """
        Calculate overall data quality (0-1).

        Combines:
          - average confidence score for any tagged fields (if available)
          - field-completeness ratio (genres, moods, content_warnings, audience)
        The weighted blend ensures that even works with only genre tags get a
        meaningful score rather than zero.
        """
        # Field completeness contribution (always computable)
        field_score = 0.0
        weights = [
            (bool(self.genres), 0.40),
            (bool(self.moods), 0.20),
            (bool(self.content_warnings), 0.15),
            (self.target_audience != "All Ages", 0.10),
            (bool(self.themes), 0.08),
            (bool(self.characters), 0.04),
            (bool(self.settings), 0.03),
        ]
        for filled, weight in weights:
            if filled:
                field_score += weight

        # Confidence contribution (from tagged fields only)
        if self.confidence_scores:
            conf_score = sum(self.confidence_scores.values()) / len(
                self.confidence_scores
            )
        else:
            conf_score = field_score  # mirror field score when no explicit confidences

        # Blend: 60% field completeness, 40% confidence
        self.data_quality_score = round(0.60 * field_score + 0.40 * conf_score, 3)
        return self.data_quality_score


class GenomeFactory:
    """Factory for creating and enriching Book Genomes."""

    @staticmethod
    def from_work_dict(work: dict) -> BookGenome:
        """Create initial genome from OpenLibrary work dict."""
        genome = BookGenome(
            work_id=work.get("key", "").replace("/works/", ""),
            title=work.get("title", "Unknown"),
            source_subjects=work.get("subjects", []),
        )

        # Infer fiction status
        subjects = work.get("subjects", [])
        subject_text = " ".join(subjects).lower()
        if "--fiction" in subject_text or "fiction" in subject_text:
            genome.fiction = True
        elif any(word in subject_text for word in ["history", "biography", "memoir"]):
            genome.fiction = False

        return genome

    @staticmethod
    def enrich_with_genres(
        genome: BookGenome, genres: list[str], confidences: Optional[dict[str, float]] = None
    ):
        """Add genres to genome with optional confidence scores."""
        genome.genres = genres
        if confidences:
            for genre in genres:
                if genre in confidences:
                    genome.add_confidence_score(f"genre_{genre}", confidences[genre])

    @staticmethod
    def enrich_with_moods(
        genome: BookGenome, moods: list[str], confidences: Optional[dict[str, float]] = None
    ):
        """Add moods to genome with optional confidence scores."""
        genome.moods = moods
        if confidences:
            for mood in moods:
                if mood in confidences:
                    genome.add_confidence_score(f"mood_{mood}", confidences[mood])

    @staticmethod
    def enrich_with_content_warnings(genome: BookGenome, warnings: list[str]):
        """Add content warnings to genome."""
        genome.content_warnings = warnings

    @staticmethod
    def auto_enrich_features(genome: BookGenome):
        """Automatically set feature flags based on genres and themes."""
        genres_text = " ".join(genome.genres).lower()
        themes_text = " ".join(genome.themes).lower()

        genome.has_romance = any(w in genres_text for w in ["romance", "lgbtq"])
        genome.has_magic = any(w in genres_text for w in ["fantasy", "magical"])
        genome.has_mystery = any(w in genres_text for w in ["mystery", "thriller"])
        genome.has_adventure = any(w in genres_text for w in ["adventure", "action"])
        genome.has_humor = any(w in genres_text for w in ["comedy", "humor"])
