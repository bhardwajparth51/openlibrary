"""
Tag Creation & Lifecycle Management for Open Library.

Handles creation, validation, merging, and deletion of Tag objects
in the Infogami system with full audit trail.
"""

import hashlib
import os
import sys
from datetime import datetime
from typing import Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../scripts"))
)

from taxonomy import CONTENT_WARNINGS, FORMATS, GENRES, MOODS, TagType


class TagError(Exception):
    """Exception for tag validation errors."""

    pass


class Tag:
    """Represents an OpenLibrary Tag object (Infogami type)."""

    TAG_ID_PREFIX = "OL"
    TAG_ID_SUFFIX = "T"

    def __init__(
        self,
        label: str,
        tag_type: TagType,
        name_i18n: Optional[dict[str, str]] = None,
        description_i18n: Optional[dict[str, str]] = None,
        key: str | None = None,
    ):
        self.label = label.lower().replace(" ", "_")
        self.tag_type = tag_type
        self.name_i18n = name_i18n or {"en": label}
        self.description_i18n = description_i18n or {"en": ""}
        self.key = key or self._generate_key()
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
        self.parent_tags: list[str] = []  # For taxonomy hierarchy
        self.related_tags: list[str] = []
        self.aliases: list[str] = []  # Alternative names
        self.metadata: dict = {}  # Custom metadata

    def _generate_key(self) -> str:
        """Generate unique tag key (e.g., /tags/OL123T).

        Note: In this POC we use a descriptive MD5 hash key for determinism.
        In production, this must use Infogami's built-in auto-increment mechanism
        for tag keys to match standard OpenLibrary practices.
        """
        hash_input = f"{self.label}{self.tag_type.value}".encode()
        hash_suffix = hashlib.md5(hash_input).hexdigest()[:5].upper()
        return f"/tags/{self.TAG_ID_PREFIX}{hash_suffix}{self.TAG_ID_SUFFIX}"

    def validate(self) -> tuple[bool, list[str]]:
        """Validate tag data. Returns (is_valid, list_of_errors)."""
        errors = []

        if not self.label:
            errors.append("Label cannot be empty")
        if len(self.label) > 100:
            errors.append("Label must be <= 100 characters")
        if not self.name_i18n.get("en"):
            errors.append("Must have English name")
        if not self.tag_type:
            errors.append("Tag type must be specified")

        return len(errors) == 0, errors

    def to_infogami_dict(self) -> dict:
        """Convert to Infogami JSON format."""
        is_valid, errors = self.validate()
        if not is_valid:
            raise TagError(f"Cannot serialize invalid tag: {errors}")

        return {
            "type": {"key": "/type/tag"},
            "key": self.key,
            "label": self.label,
            "tag_type": self.tag_type.value,
            "name": self.name_i18n,
            "description": self.description_i18n,
            "created": self.created_at,
            "last_modified": self.updated_at,
            "parent_tags": self.parent_tags,
            "related_tags": self.related_tags,
            "aliases": self.aliases,
        }

    def __repr__(self):
        return f"<Tag {self.key} ({self.tag_type.value}): {self.label}>"


class TagManager:
    """Manages tag creation, validation, and lifecycle."""

    def __init__(self):
        self.tags: dict[str, Tag] = {}
        self.tag_by_label: dict[tuple[str, str], Tag] = {}  # (label, type) -> Tag
        self.audit_log: list[dict] = []

    def create_tag(
        self,
        label: str,
        tag_type: TagType,
        name_i18n: Optional[dict[str, str]] = None,
        description_i18n: Optional[dict[str, str]] = None,
    ) -> Tag:
        """Create and register a new tag."""
        # Validate uniqueness
        key = (label.lower().replace(" ", "_"), tag_type.value)
        if key in self.tag_by_label:
            raise TagError(f"Tag already exists: {key}")

        tag = Tag(label, tag_type, name_i18n, description_i18n)
        is_valid, errors = tag.validate()

        if not is_valid:
            raise TagError(f"Invalid tag: {errors}")

        self.tags[tag.key] = tag
        self.tag_by_label[key] = tag

        self._log_action("create", tag.key, f"Created tag: {tag.label}")
        return tag

    def get_tag(self, key: str) -> Tag | None:
        """Retrieve tag by key."""
        return self.tags.get(key)

    def find_tag_by_label_type(self, label: str, tag_type: TagType) -> Tag | None:
        """Find tag by label and type."""
        key = (label.lower().replace(" ", "_"), tag_type.value)
        return self.tag_by_label.get(key)

    def merge_tags(self, primary_key: str, duplicate_key: str) -> bool:
        """Merge duplicate tag into primary tag."""
        primary = self.tags.get(primary_key)
        duplicate = self.tags.get(duplicate_key)

        if not primary or not duplicate:
            raise TagError("Primary or duplicate tag not found")

        if primary.tag_type != duplicate.tag_type:
            raise TagError("Can only merge tags of same type")

        # Add duplicate's aliases to primary
        primary.aliases.extend([duplicate.label] + duplicate.aliases)
        primary.related_tags.extend(duplicate.related_tags)

        # Remove duplicate
        del self.tags[duplicate_key]
        del self.tag_by_label[(duplicate.label, duplicate.tag_type.value)]

        self._log_action(
            "merge",
            primary_key,
            f"Merged {duplicate_key} into {primary_key}",
        )
        return True

    def get_audit_log(self) -> list[dict]:
        """Get all logged actions."""
        return self.audit_log

    def _log_action(self, action: str, target: str, details: str):
        """Log an action for audit trail."""
        self.audit_log.append(
            {
                "timestamp": datetime.now().isoformat(),
                "action": action,
                "target": target,
                "details": details,
            }
        )

    def get_stats(self) -> dict:
        """Get tag statistics."""
        tags_by_type = {}
        for tag in self.tags.values():
            tag_type = tag.tag_type.value
            tags_by_type[tag_type] = tags_by_type.get(tag_type, 0) + 1

        return {
            "total_tags": len(self.tags),
            "tags_by_type": tags_by_type,
            "audit_log_entries": len(self.audit_log),
        }

    def print_stats(self):
        """Print tag statistics."""
        stats = self.get_stats()
        print("\n" + "=" * 70)
        print("TAG REGISTRY STATISTICS")
        print("=" * 70)
        print(f"Total Tags Created: {stats['total_tags']}")
        print("\nTags by Type:")
        for tag_type, count in sorted(stats["tags_by_type"].items()):
            print(f"  {tag_type}: {count}")
        print(f"\nAudit Log Entries: {stats['audit_log_entries']}")
        print("=" * 70 + "\n")


class TagFactory:
    """Factory for creating standard tag sets."""

    def __init__(self, manager: TagManager):
        self.manager = manager

    def create_standard_genre_tags(self) -> list[Tag]:
        """Create all standard genre tags."""
        tags = []
        for genre in GENRES:
            try:
                tag = self.manager.create_tag(
                    label=genre,
                    tag_type=TagType.GENRE,
                    name_i18n={"en": genre},
                    description_i18n={
                        "en": f"Books classified as {genre}",
                    },
                )
                tags.append(tag)
            except TagError:
                pass  # Skip if already exists
        return tags

    def create_standard_mood_tags(self) -> list[Tag]:
        """Create all standard mood tags."""
        tags = []
        for mood in MOODS:
            try:
                tag = self.manager.create_tag(
                    label=mood,
                    tag_type=TagType.MOOD,
                    name_i18n={"en": mood},
                    description_i18n={
                        "en": f"Books with a {mood.lower()} mood or atmosphere",
                    },
                )
                tags.append(tag)
            except TagError:
                pass
        return tags

    def create_standard_content_warning_tags(self) -> list[Tag]:
        """Create all standard content warning tags."""
        tags = []
        for warning in CONTENT_WARNINGS:
            try:
                tag = self.manager.create_tag(
                    label=warning,
                    tag_type=TagType.CONTENT_WARNING,
                    name_i18n={"en": warning},
                    description_i18n={
                        "en": f"Books containing {warning.lower()}",
                    },
                )
                tags.append(tag)
            except TagError:
                pass
        return tags

    def create_standard_format_tags(self) -> list[Tag]:
        """Create all standard format tags."""
        tags = []
        for format_type in FORMATS:
            try:
                tag = self.manager.create_tag(
                    label=format_type,
                    tag_type=TagType.FORMAT,
                    name_i18n={"en": format_type},
                    description_i18n={
                        "en": f"Books in {format_type} format",
                    },
                )
                tags.append(tag)
            except TagError:
                pass
        return tags

    def create_all_standard_tags(self) -> dict[str, list[Tag]]:
        """Create all standard tags at once."""
        return {
            "genres": self.create_standard_genre_tags(),
            "moods": self.create_standard_mood_tags(),
            "content_warnings": self.create_standard_content_warning_tags(),
            "formats": self.create_standard_format_tags(),
        }


# ============================================================================
# DEMONSTRATION
# ============================================================================


def demo_tag_creation():
    """Demonstrate tag creation and management."""
    print("\n" + "=" * 70)
    print("TAG CREATION & MANAGEMENT DEMONSTRATION")
    print("=" * 70)

    manager = TagManager()
    factory = TagFactory(manager)

    print("\nCreating standard tag sets...")

    # Create all standard tags
    tag_sets = factory.create_all_standard_tags()

    for tag_type, tags in tag_sets.items():
        print(f"  ✓ Created {len(tags)} {tag_type} tags")

    # Show some example tags
    print("\nSample Created Tags:")
    print("-" * 70)

    sample_count = 0
    for tag_type, tags in tag_sets.items():
        for tag in tags[:2]:
            print(f"{tag.key} ({tag.tag_type.value}): {tag.label}")
            sample_count += 1

    print(f"... and {sum(len(tags) for tags in tag_sets.values()) - sample_count} more")

    # Print statistics
    manager.print_stats()

    # Example: Merge duplicate tags
    print("\nDemonstrating tag merge operation:")
    print("-" * 70)

    # Create two related tags for demo (not standard)
    tag1 = manager.create_tag(
        "Space Opera",
        TagType.GENRE,
        {"en": "Space Opera"},
        {"en": "Space opera stories"},
    )
    tag2 = manager.create_tag(
        "Space Opera Fiction",
        TagType.GENRE,
        {"en": "Space Opera Fiction"},
        {"en": "Space opera (alternate name)"},
    )

    print(f"Created: {tag1.key}")
    print(f"Created: {tag2.key}")
    print(f"\nMerging {tag2.key} into {tag1.key}...")

    manager.merge_tags(tag1.key, tag2.key)
    print("✓ Merge complete")
    print(f"Primary tag now has aliases: {tag1.aliases}")

    manager.print_stats()

    # Show audit log
    print("\nAudit Log (last 5 entries):")
    print("-" * 70)
    for entry in manager.get_audit_log()[-5:]:
        print(f"{entry['timestamp']}: {entry['action']} - {entry['details']}")


if __name__ == "__main__":
    demo_tag_creation()
