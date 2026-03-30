"""
Comprehensive Tag Taxonomy for Open Library Tag Clean Up POC (2026).
Defines controlled vocabularies for all tag types and sophisticated mapping rules.

References:
- Book Genome Project: https://grouplens.org/datasets/book-genome/
- StoryGraph & Netflix genres
- BISAC codes
- Library of Congress Subject Headings (LCSH)
"""

from enum import Enum


class TagType(Enum):
    """Official tag types for Open Library."""

    GENRE = "genre"
    MOOD = "mood"
    FORMAT = "format"
    CONTENT_WARNING = "content_warning"
    PLACE = "place"
    PEOPLE_CHARACTER = "people_character"
    THEME = "theme"
    FEATURE = "feature"
    AUDIENCE = "audience"
    STYLE = "style"


# ============================================================================
# CONTROLLED VOCABULARIES
# ============================================================================

GENRES = [
    "Action",
    "Adventure",
    "Apocalyptic",
    "Biography",
    "Classic",
    "Comedy",
    "Cookbooks",
    "Crime",
    "Cult",
    "Cyberpunk",
    "Design",
    "Documentary",
    "Drama",
    "Education",
    "Environment",
    "Epic",
    "Erotica",
    "Fantasy",
    "Fandom",
    "Futurism",
    "Historical Fiction",
    "History",
    "Horror",
    "Humor",
    "Literary Fiction",
    "LGBTQ+",
    "Manga",
    "Mystery",
    "Mythology",
    "Nature",
    "Philosophy",
    "Photography",
    "Romance",
    "Satire",
    "Science",
    "Science Fiction",
    "Speculative Fiction",
    "Self Help",
    "Sports",
    "Thriller",
    "Travel",
    "True Crime",
    "Western",
]

MOODS = [
    "Calm",
    "Cozy",
    "Confusing",
    "Comical",
    "Dark",
    "Disturbing",
    "Depressing",
    "Exciting",
    "Happy",
    "Harrowing",
    "Playful",
    "Nostalgic",
    "Suspenseful",
    "Thrilling",
    "Uplifting",
    "Intense",
    "Inspiring",
    "Overwhelming",
    "Humbling",
    "Melancholic",
    "Sad",
    "Scary",
    "Soapy",
    "Swoonworthy",
    "Whimsical",
]

FORMATS = [
    "Novel",
    "Novella",
    "Short Story",
    "Poetry",
    "Essay",
    "Memoir",
    "Autobiography",
    "Biography",
    "Textbook",
    "Reference",
    "Anthology",
    "Graphic Novel",
    "Manga",
    "Comic",
    "Play",
    "Script",
    "Letters",
    "Diary",
    "Journal",
    "Encyclopedia",
    "Dictionary",
    "Thesaurus",
    "Atlas",
    "Cookbook",
    "Art Book",
    "Photo Book",
]

CONTENT_WARNINGS = [
    "Violence",
    "Gore",
    "Sexual Content",
    "Nudity",
    "Drug Use",
    "Alcohol Use",
    "Self Harm",
    "Suicide",
    "Abuse",
    "Torture",
    "War",
    "Death",
    "Grief",
    "Mental Health Issues",
    "Racism",
    "Sexism",
    "Homophobia",
    "Transphobia",
    "Ableism",
    "Slavery",
]

AUDIENCES = [
    "Children",
    "Young Adults",
    "Teens",
    "Adults",
    "New Adults",
    "Mature Adults",
    "All Ages",
    "Educators",
    "Academics",
]

THEMES = [
    "Love",
    "Redemption",
    "Grief",
    "Friendship",
    "Family",
    "Betrayal",
    "Revenge",
    "Survival",
    "Identity",
    "Power",
    "Freedom",
    "Justice",
    "Morality",
    "Fate",
    "Destiny",
    "Hope",
    "Despair",
    "Ambition",
    "Sacrifice",
    "Corruption",
]

STYLES = [
    "Avant Garde",
    "Deadpan",
    "Slick",
    "Gritty",
    "Witty",
    "Poetic",
    "Minimalist",
    "Maximalist",
    "Surreal",
    "Magical Realism",
    "Noir",
    "Absurdist",
    "Stream of Consciousness",
    "Unreliable Narrator",
]

# ============================================================================
# COMPREHENSIVE MAPPING RULES
# ============================================================================

# Genre mapping: messy subjects -> official genres (with confidence scores)
# Keys are the *normalized* subject (lower-cased, "--" replaced with space).
GENRE_MAPPING = {
    # ── Adventure ────────────────────────────────────────────────────────────
    "buried treasure fiction": [("Adventure", 0.95)],
    "pirates fiction": [("Adventure", 0.95)],
    "adventure and adventurers fiction": [("Adventure", 0.98)],
    "treasure hunting fiction": [("Adventure", 0.95)],
    "expeditions": [("Adventure", 0.90)],
    "exploration": [("Adventure", 0.88)],
    "quests": [("Adventure", 0.92)],
    "adventure stories": [("Adventure", 0.97)],
    "sea stories": [("Adventure", 0.88)],
    "survival fiction": [("Adventure", 0.90)],
    # ── Science Fiction ───────────────────────────────────────────────────────
    "science fiction": [("Science Fiction", 0.99)],
    "sci fi": [("Science Fiction", 0.99)],
    "science fiction fiction": [("Science Fiction", 0.99)],
    "dystopian": [("Science Fiction", 0.90)],
    "cyberpunk": [("Cyberpunk", 0.95), ("Science Fiction", 0.85)],
    "futuristic": [("Futurism", 0.90), ("Science Fiction", 0.80)],
    "space fiction": [("Science Fiction", 0.95)],
    "space opera": [("Science Fiction", 0.95)],
    "aliens": [("Science Fiction", 0.88)],
    "robots": [("Science Fiction", 0.82)],
    "time travel fiction": [("Science Fiction", 0.93)],
    "alternate history": [("Science Fiction", 0.88), ("Historical Fiction", 0.75)],
    "interplanetary voyages": [("Science Fiction", 0.92)],
    "artificial intelligence fiction": [("Science Fiction", 0.92)],
    # ── Fantasy ───────────────────────────────────────────────────────────────
    "fantasy": [("Fantasy", 0.99)],
    "fantasy fiction": [("Fantasy", 0.99)],
    "magic fiction": [("Fantasy", 0.98)],
    "magical realism": [("Fantasy", 0.85)],
    "wizards fiction": [("Fantasy", 0.95)],
    "witches fiction": [("Fantasy", 0.95)],
    "dragons fiction": [("Fantasy", 0.95)],
    "elves fiction": [("Fantasy", 0.95)],
    "castles fiction": [("Fantasy", 0.88)],
    "quests fiction": [("Fantasy", 0.85), ("Adventure", 0.75)],
    "fairy tales": [("Fantasy", 0.92)],
    "fairy stories": [("Fantasy", 0.92)],
    "folklore": [("Fantasy", 0.80), ("Mythology", 0.85)],
    "mythology": [("Mythology", 0.97)],
    "legends": [("Mythology", 0.85), ("Fantasy", 0.75)],
    "epic fantasy": [("Fantasy", 0.99), ("Epic", 0.90)],
    # ── Horror ─────────────────────────────────────────────────────────────
    "horror stories": [("Horror", 0.99)],
    "horror fiction": [("Horror", 0.99)],
    "horror": [("Horror", 0.97)],
    "ghost stories": [("Horror", 0.95)],
    "vampires fiction": [("Horror", 0.90)],
    "werewolves fiction": [("Horror", 0.90)],
    "haunted houses fiction": [("Horror", 0.95)],
    "zombies fiction": [("Horror", 0.95)],
    "monsters fiction": [("Horror", 0.90)],
    "psychological thrillers": [("Thriller", 0.85), ("Horror", 0.75)],
    "occult fiction": [("Horror", 0.85)],
    "supernatural fiction": [("Horror", 0.88)],
    # ── Crime & Mystery ──────────────────────────────────────────────────────
    "detective and mystery stories": [("Mystery", 0.98), ("Crime", 0.85)],
    "mystery": [("Mystery", 0.98)],
    "mystery fiction": [("Mystery", 0.99)],
    "crime": [("Crime", 0.90)],
    "crime fiction": [("Crime", 0.95)],
    "detective fiction": [("Mystery", 0.98)],
    "private detectives fiction": [("Mystery", 0.95), ("Crime", 0.80)],
    "murder mystery": [("Mystery", 0.98), ("Crime", 0.92)],
    "murder fiction": [("Crime", 0.90), ("Thriller", 0.85)],
    "spy fiction": [("Thriller", 0.90), ("Crime", 0.80)],
    "espionage fiction": [("Thriller", 0.90), ("Crime", 0.80)],
    # ── Historical Fiction ─────────────────────────────────────────────────
    "historical fiction": [("Historical Fiction", 0.99)],
    "historical fiction fiction": [("Historical Fiction", 0.99)],
    "civil war fiction": [("Historical Fiction", 0.95)],
    "world war fiction": [("Historical Fiction", 0.95)],
    "world war, 1914-1918 fiction": [("Historical Fiction", 0.97)],
    "world war, 1939-1945 fiction": [("Historical Fiction", 0.97)],
    "middle ages fiction": [("Historical Fiction", 0.95)],
    "ancient rome fiction": [("Historical Fiction", 0.95)],
    "ancient egypt fiction": [("Historical Fiction", 0.95)],
    "viking fiction": [("Historical Fiction", 0.90), ("Adventure", 0.80)],
    # ── Western ───────────────────────────────────────────────────────────
    "western stories": [("Western", 0.99)],
    "western fiction": [("Western", 0.99)],
    "westerns": [("Western", 0.99)],
    "cowboys fiction": [("Western", 0.95)],
    "frontier and pioneer life fiction": [("Western", 0.92)],
    "fiction westerns": [("Western", 0.99)],
    # ── Biography & Memoir ─────────────────────────────────────────────────
    "biography": [("Biography", 0.99)],
    "autobiography": [("Biography", 0.98)],
    "autobiographies": [("Biography", 0.98)],
    "memoirs": [("Biography", 0.95)],
    "memoir": [("Biography", 0.95)],
    "life histories": [("Biography", 0.90)],
    "personal narratives": [("Biography", 0.88)],
    "correspondence": [("Biography", 0.80)],
    "diaries": [("Biography", 0.80)],
    # ── Cookbooks & Food ──────────────────────────────────────────────────
    "cookery": [("Cookbooks", 0.99)],
    "cooking": [("Cookbooks", 0.99)],
    "recipes": [("Cookbooks", 0.98)],
    "cookbook": [("Cookbooks", 0.99)],
    "food": [("Cookbooks", 0.80)],
    "cuisine": [("Cookbooks", 0.85)],
    "baking": [("Cookbooks", 0.92)],
    # ── Romance ───────────────────────────────────────────────────────────
    "romance": [("Romance", 0.99)],
    "romance fiction": [("Romance", 0.99)],
    "love stories": [("Romance", 0.95)],
    "love fiction": [("Romance", 0.90)],
    "erotic fiction": [("Erotica", 0.97)],
    # ── Thriller / Suspense ────────────────────────────────────────────────
    "thriller": [("Thriller", 0.99)],
    "thriller fiction": [("Thriller", 0.99)],
    "suspense": [("Thriller", 0.90)],
    "suspense fiction": [("Thriller", 0.95)],
    "political thrillers": [("Thriller", 0.95)],
    "legal thrillers": [("Thriller", 0.95)],
    "medical thrillers": [("Thriller", 0.95)],
    # ── True Crime ────────────────────────────────────────────────────────
    "true crime": [("True Crime", 0.99)],
    "criminals": [("True Crime", 0.88)],
    "crime investigation": [("True Crime", 0.90)],
    "serial killers": [("True Crime", 0.97)],
    "cold cases": [("True Crime", 0.95)],
    # ── Drama ────────────────────────────────────────────────────────────
    "drama": [("Drama", 0.90)],
    "drama fiction": [("Drama", 0.95)],
    "domestic fiction": [("Drama", 0.85)],
    "family drama": [("Drama", 0.92)],
    # ── Comedy / Humor ────────────────────────────────────────────────────
    "comedy": [("Comedy", 0.97)],
    "humor": [("Humor", 0.99)],
    "humour": [("Humor", 0.99)],
    "humorous fiction": [("Comedy", 0.95)],
    "satire": [("Satire", 0.99)],
    "parody": [("Satire", 0.90)],
    "wit and humor": [("Humor", 0.95)],
    # ── Literary Fiction ─────────────────────────────────────────────────
    "literary fiction": [("Literary Fiction", 0.99)],
    "literary": [("Literary Fiction", 0.85)],
    "fiction": [("Literary Fiction", 0.70)],
    "novels": [("Literary Fiction", 0.72)],
    "short stories": [("Literary Fiction", 0.75)],
    "classic literature": [("Classic", 0.95), ("Literary Fiction", 0.85)],
    "classics": [("Classic", 0.90)],
    "english fiction": [("Literary Fiction", 0.80)],
    "american fiction": [("Literary Fiction", 0.80)],
    # ── Children's & YA Fiction ───────────────────────────────────────────
    "children's fiction": [("Literary Fiction", 0.80)],
    "juvenile fiction": [("Literary Fiction", 0.80)],
    "juvenile literature": [("Literary Fiction", 0.72), ("Education", 0.80)],
    "picture books": [("Literary Fiction", 0.75)],
    "young adult fiction": [("Literary Fiction", 0.80)],
    # ── History ───────────────────────────────────────────────────────────
    "history": [("History", 0.95)],
    "world history": [("History", 0.97)],
    "ancient history": [("History", 0.97)],
    "military history": [("History", 0.95)],
    "social history": [("History", 0.93)],
    "economic history": [("History", 0.90)],
    "church history": [("History", 0.88)],
    "history and criticism": [("History", 0.85)],
    "historical aspects": [("History", 0.80)],
    # ── Science / Nature ──────────────────────────────────────────────────
    "science": [("Science", 0.90)],
    "natural history": [("Nature", 0.92)],
    "nature": [("Nature", 0.90)],
    "biology": [("Science", 0.92)],
    "chemistry": [("Science", 0.92)],
    "physics": [("Science", 0.92)],
    "mathematics": [("Science", 0.88)],
    "astronomy": [("Science", 0.92)],
    "ecology": [("Environment", 0.90), ("Science", 0.85)],
    "environment": [("Environment", 0.92)],
    "climate change": [("Environment", 0.90), ("Science", 0.80)],
    "environmental protection": [("Environment", 0.92)],
    "wildlife": [("Nature", 0.90)],
    "animals": [("Nature", 0.80)],
    # ── Philosophy & Religion ─────────────────────────────────────────────
    "philosophy": [("Philosophy", 0.97)],
    "ethics": [("Philosophy", 0.90)],
    "religion": [("Philosophy", 0.80)],
    "theology": [("Philosophy", 0.80)],
    "spirituality": [("Philosophy", 0.80)],
    "buddhism": [("Philosophy", 0.82)],
    "christianity": [("Philosophy", 0.80)],
    "islam": [("Philosophy", 0.80)],
    # ── Education ─────────────────────────────────────────────────────────
    "education": [("Education", 0.92)],
    "textbook": [("Education", 0.97)],
    "textbooks": [("Education", 0.97)],
    "study and teaching": [("Education", 0.90)],
    "juvenile works": [("Education", 0.78)],
    "handbooks, manuals, etc": [("Education", 0.80)],
    "handbooks manuals etc": [("Education", 0.80)],
    # ── Politics & Society ────────────────────────────────────────────────
    "politics and government": [("History", 0.80)],
    "political science": [("History", 0.80)],
    "social conditions": [("History", 0.75)],
    "social life and customs": [("History", 0.75)],
    "economic conditions": [("History", 0.75)],
    "law and legislation": [("History", 0.72)],
    "foreign relations": [("History", 0.80)],
    "international relations": [("History", 0.80)],
    # ── Travel & Geography ────────────────────────────────────────────────
    "description and travel": [("Travel", 0.92)],
    "travel": [("Travel", 0.99)],
    "travel writing": [("Travel", 0.99)],
    "guidebooks": [("Travel", 0.90)],
    "geography": [("Travel", 0.80)],
    "voyages and travels": [("Travel", 0.95)],
    # ── Self-Help ─────────────────────────────────────────────────────────
    "self help": [("Self Help", 0.99)],
    "self-help": [("Self Help", 0.99)],
    "personal development": [("Self Help", 0.95)],
    "success": [("Self Help", 0.80)],
    "motivation": [("Self Help", 0.85)],
    "leadership": [("Self Help", 0.80)],
    "business and leadership": [("Self Help", 0.80)],
    "health and fitness": [("Self Help", 0.82)],
    "psychology": [("Self Help", 0.75)],
    "mental health": [("Self Help", 0.80)],
    # ── Sports ───────────────────────────────────────────────────────────
    "sports": [("Sports", 0.99)],
    "sport": [("Sports", 0.97)],
    "athletics": [("Sports", 0.92)],
    "football": [("Sports", 0.95)],
    "soccer": [("Sports", 0.95)],
    "basketball": [("Sports", 0.95)],
    "baseball": [("Sports", 0.95)],
    "cricket": [("Sports", 0.95)],
    "tennis": [("Sports", 0.95)],
    "cycling": [("Sports", 0.92)],
    "running": [("Sports", 0.88)],
    # ── Art & Photography ─────────────────────────────────────────────────
    "art": [("Photography", 0.75)],
    "photography": [("Photography", 0.99)],
    "design": [("Design", 0.97)],
    "architecture": [("Design", 0.85)],
    "graphic design": [("Design", 0.95)],
    "illustration": [("Design", 0.88)],
    "painting": [("Photography", 0.80)],
    "drawing": [("Design", 0.80)],
    "exhibitions": [("Photography", 0.72)],
    "catalogs": [("Photography", 0.65)],
}

# Mood mapping based on keywords
MOOD_MAPPING = {
    # Direct labels
    "cozy": [("Cozy", 0.95)],
    "dark": [("Dark", 0.90)],
    "depressing": [("Depressing", 0.95)],
    "exciting": [("Exciting", 0.90)],
    "happy": [("Happy", 0.88)],
    "sad": [("Sad", 0.88)],
    "scary": [("Scary", 0.92)],
    "thrilling": [("Thrilling", 0.88)],
    "nostalgic": [("Nostalgic", 0.90)],
    "melancholic": [("Melancholic", 0.88)],
    "tragic": [("Dark", 0.85), ("Melancholic", 0.80)],
    "uplifting": [("Uplifting", 0.90)],
    "inspiring": [("Inspiring", 0.90)],
    "inspiring stories": [("Inspiring", 0.95)],
    "overwhelming": [("Overwhelming", 0.85)],
    "calm": [("Calm", 0.88)],
    "whimsical": [("Whimsical", 0.90)],
    "humorous": [("Playful", 0.85)],
    "funny": [("Playful", 0.88)],
    "light-hearted": [("Cozy", 0.85), ("Happy", 0.80)],
    "lighthearted": [("Cozy", 0.85), ("Happy", 0.80)],
    "heartwarming": [("Uplifting", 0.90), ("Happy", 0.85)],
    "heartbreaking": [("Sad", 0.95), ("Melancholic", 0.85)],
    "disturbing": [("Disturbing", 0.92)],
    "unsettling": [("Disturbing", 0.88)],
    "suspenseful": [("Suspenseful", 0.95)],
    "tense": [("Suspenseful", 0.88), ("Intense", 0.82)],
    "intense": [("Intense", 0.90)],
    "comical": [("Comical", 0.90)],
    "soapy": [("Soapy", 0.90)],
    "swoonworthy": [("Swoonworthy", 0.92)],
    "harrowing": [("Harrowing", 0.92)],
    "hopeful": [("Uplifting", 0.82)],
    "bleak": [("Dark", 0.90), ("Depressing", 0.85)],
    "gritty": [("Dark", 0.85), ("Intense", 0.80)],
    "atmospheric": [("Nostalgic", 0.80)],
    "romantic": [("Swoonworthy", 0.85)],
    "adventurous": [("Exciting", 0.85)],
    "philosophical": [("Humbling", 0.80)],
    "thought-provoking": [("Humbling", 0.85)],
    "thought provoking": [("Humbling", 0.85)],
    "page-turner": [("Exciting", 0.90), ("Thrilling", 0.85)],
    "page turner": [("Exciting", 0.90), ("Thrilling", 0.85)],
}

# Content warning mapping
CONTENT_WARNING_MAPPING = {
    "violence": [("Violence", 0.95)],
    "gore": [("Gore", 0.95)],
    "sexual content": [("Sexual Content", 0.95)],
    "nudity": [("Nudity", 0.95)],
    "drug": [("Drug Use", 0.90)],
    "alcohol": [("Alcohol Use", 0.90)],
    "self harm": [("Self Harm", 0.95)],
    "suicide": [("Suicide", 0.95)],
    "abuse": [("Abuse", 0.90)],
    "torture": [("Torture", 0.95)],
    "war": [("War", 0.95)],
    "death": [("Death", 0.90)],
    "racism": [("Racism", 0.95)],
    "slavery": [("Slavery", 0.95)],
}

# ============================================================================
# MAPPING FUNCTIONS
# ============================================================================


def normalize_subject(subject: str) -> str:
    """
    Normalize a subject string for matching.
    Keeps the raw form so exact-match rules (which include '--fiction') still fire,
    but also produces a stripped form used for substring matching.
    """
    s = subject.lower().strip()
    # Collapse common separators so "civic--life" and "civic life" both match
    s = s.replace(" -- ", " ").replace("--", " ")
    return s


def get_tags_for_subjects(
    subjects: list[str], tag_type: TagType = TagType.GENRE, min_confidence: float = 0.70
) -> list[tuple[str, float]]:
    """
    Map a list of subjects to official tags with confidence scores.
    Returns list of (tag, confidence) tuples sorted by confidence.
    """
    detected_tags = {}
    mapping_rule = GENRE_MAPPING

    if tag_type == TagType.MOOD:
        mapping_rule = MOOD_MAPPING
    elif tag_type == TagType.CONTENT_WARNING:
        mapping_rule = CONTENT_WARNING_MAPPING

    for subject in subjects:
        norm_subject = normalize_subject(subject)

        # Direct exact match
        if norm_subject in mapping_rule:
            for tag, confidence in mapping_rule[norm_subject]:
                if confidence >= min_confidence:
                    detected_tags[tag] = max(detected_tags.get(tag, 0), confidence)

        # Keyword substring match (less strict)
        for pattern, tag_list in mapping_rule.items():
            if pattern in norm_subject and len(pattern) > 3:
                for tag, confidence in tag_list:
                    adjusted_confidence = (
                        confidence * 0.85
                    )  # Discount substring matches
                    if adjusted_confidence >= min_confidence:
                        detected_tags[tag] = max(
                            detected_tags.get(tag, 0), adjusted_confidence
                        )

    # Sort by confidence descending
    return sorted(detected_tags.items(), key=lambda x: x[1], reverse=True)


def get_genres_for_subjects(subjects: list[str]) -> list[str]:
    """
    Convenience function: return sorted genre names for subjects.
    """
    tags = get_tags_for_subjects(subjects, TagType.GENRE)
    return [tag for tag, _ in tags]


def get_moods_for_subjects(subjects: list[str]) -> list[str]:
    """
    Convenience function: return sorted mood names for subjects.
    """
    tags = get_tags_for_subjects(subjects, TagType.MOOD)
    return [tag for tag, _ in tags]


def get_content_warnings_for_subjects(subjects: list[str]) -> list[str]:
    """
    Convenience function: return content warnings for subjects.
    """
    tags = get_tags_for_subjects(subjects, TagType.CONTENT_WARNING)
    return [tag for tag, _ in tags]


def estimate_audience(subjects: list[str], title: str = "") -> str:
    """
    Estimate primary audience from subjects and title.
    Uses a priority order: Children > YA/Teens > Adults > All Ages.
    """
    combined = " ".join(subjects + [title]).lower()

    # Children's markers (check first — highest priority among youth)
    children_keywords = [
        "juvenile",
        "children",
        "picture book",
        "young reader",
        "children's fiction",
        "children's literature",
        "picture books",
        "board books",
        "easy reader",
        "beginning reader",
    ]
    if any(word in combined for word in children_keywords):
        return "Children"

    # Young Adult / Teen markers
    ya_keywords = [
        "young adult",
        "teen",
        "adolescent",
        " ya ",
        "ya fiction",
        "high school",
        "teenage",
        "teenagers",
    ]
    if any(word in combined for word in ya_keywords):
        return "Teens"

    # Adult markers
    adult_keywords = ["adult", "mature", "erotic", "sexuality"]
    if any(word in combined for word in adult_keywords):
        return "Adults"

    return "All Ages"


# Statistics & Quality Metrics
def calculate_tag_coverage(works_data: list[dict]) -> dict:
    """
    Calculate coverage statistics for tag mapping.
    """
    total_works = len(works_data)
    works_with_genres = 0
    works_with_moods = 0
    works_with_warnings = 0
    total_genres = 0
    total_moods = 0

    for work in works_data:
        subjects = work.get("subjects", [])
        if not subjects:
            continue

        genres = get_genres_for_subjects(subjects)
        moods = get_moods_for_subjects(subjects)
        warnings = get_content_warnings_for_subjects(subjects)

        if genres:
            works_with_genres += 1
            total_genres += len(genres)
        if moods:
            works_with_moods += 1
            total_moods += len(moods)
        if warnings:
            works_with_warnings += 1

    return {
        "total_works": total_works,
        "works_with_genres": works_with_genres,
        "genre_coverage_pct": (
            (works_with_genres / total_works * 100) if total_works else 0
        ),
        "avg_genres_per_work": (
            (total_genres / works_with_genres) if works_with_genres else 0
        ),
        "works_with_moods": works_with_moods,
        "mood_coverage_pct": (
            (works_with_moods / total_works * 100) if total_works else 0
        ),
        "works_with_warnings": works_with_warnings,
        "warning_coverage_pct": (
            (works_with_warnings / total_works * 100) if total_works else 0
        ),
    }
