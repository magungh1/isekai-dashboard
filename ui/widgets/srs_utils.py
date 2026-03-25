"""Shared SRS display utilities."""

# Level labels and colors for visual hierarchy
LEVEL_LABELS = {
    0: ("NEW", "srs-new"),
    1: ("4h", "srs-apprentice"),
    2: ("1d", "srs-apprentice"),
    3: ("3d", "srs-journeyman"),
    4: ("1w", "srs-master"),
    5: ("1mo", "srs-enlightened"),
}


def level_badge(level: int) -> str:
    """Return a colored level badge string."""
    label, _ = LEVEL_LABELS.get(level, ("?", "srs-new"))
    icons = {0: "🆕", 1: "🟢", 2: "🟡", 3: "🟠", 4: "⭐", 5: "👑"}
    icon = icons.get(level, "🔮")
    return f"{icon} {label}"


def progress_bar_text(mastered: int, total: int, width: int = 20) -> str:
    """Render a text-based progress bar."""
    if total == 0:
        return "░" * width + " 0/0"
    filled = round(mastered / total * width)
    bar = "█" * filled + "░" * (width - filled)
    pct = round(mastered / total * 100)
    return f"{bar} {mastered}/{total} ({pct}%)"
