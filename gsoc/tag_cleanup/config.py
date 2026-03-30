"""
Configuration for Tag Cleanup POC.

Allows centralized control of enrichment parameters, thresholds, and behaviors.
"""

# ============================================================================
# ENRICHMENT PARAMETERS
# ============================================================================

# Minimum confidence threshold for accepting a tag mapping
MIN_GENRE_CONFIDENCE = 0.70
MIN_MOOD_CONFIDENCE = 0.70
MIN_CONTENT_WARNING_CONFIDENCE = 0.80

# Maximum number of tags to assign to a work
MAX_GENRES_PER_WORK = 5
MAX_MOODS_PER_WORK = 3
MAX_CONTENT_WARNINGS_PER_WORK = 5

# ============================================================================
# PROCESSING PARAMETERS
# ============================================================================

# Batch size for bulk processing
BULK_PROCESSING_BATCH_SIZE = 1000

# Enable/disable different enrichment stages
ENABLE_GENRE_ENRICHMENT = True
ENABLE_MOOD_ENRICHMENT = True
ENABLE_CONTENT_WARNING_ENRICHMENT = True
ENABLE_FEATURE_AUTO_DETECTION = True

# ============================================================================
# DATA QUALITY PARAMETERS
# ============================================================================

# Minimum data quality score to consider enrichment "good"
MIN_DATA_QUALITY_SCORE = 0.70

# Quality score weights (how much each field contributes)
QUALITY_WEIGHTS = {
    "genre_coverage": 0.25,
    "mood_coverage": 0.20,
    "content_warning_coverage": 0.15,
    "character_data": 0.15,
    "setting_data": 0.10,
    "theme_data": 0.10,
    "style_data": 0.05,
}

# ============================================================================
# LOGGING & REPORTING
# ============================================================================

# Verbosity level: 0=silent, 1=summary, 2=detailed, 3=debug
LOG_LEVEL = 2

# Generate detailed reports
GENERATE_REPORT = True
REPORT_FORMAT = "json"  # json or csv

# Save enriched works to file
SAVE_ENRICHED_WORKS = True
ENRICHED_WORKS_OUTPUT = "enriched_works.jsonl"


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def get_config_summary() -> dict[str, any]:
    """Get human-readable configuration summary."""
    return {
        "Minimum Genre Confidence": f"{MIN_GENRE_CONFIDENCE:.0%}",
        "Max Genres per Work": MAX_GENRES_PER_WORK,
        "Bulk Batch Size": BULK_PROCESSING_BATCH_SIZE,
        "Min Data Quality": f"{MIN_DATA_QUALITY_SCORE:.0%}",
        "Log Level": LOG_LEVEL,
    }


def print_config():
    """Print current configuration."""
    print("\n" + "=" * 70)
    print("ENRICHMENT CONFIGURATION")
    print("=" * 70)

    summary = get_config_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")

    print("=" * 70 + "\n")
