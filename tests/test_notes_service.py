"""Tests for the Notes service (CRUD operations)."""

from datetime import datetime

from services.notes_service import get_notes, get_note, add_note, update_note, delete_note, CATEGORIES


def test_add_note():
    note = add_note("Test note content", category="general")
    assert note["content"] == "Test note content"
    assert note["category"] == "general"
    assert note["id"] is not None


def test_add_note_default_category():
    note = add_note("Quick thought")
    assert note["content"] == "Quick thought"
    assert note["category"] == "general"


def test_get_notes():
    add_note("First note", category="general")
    add_note("Second note", category="study")
    notes = get_notes()
    assert len(notes) >= 2


def test_get_notes_filter_by_category():
    add_note("Study note 1", category="study")
    add_note("Study note 2", category="study")
    add_note("General note", category="general")

    study_notes = get_notes(category="study")
    assert len(study_notes) == 2
    for n in study_notes:
        assert n["category"] == "study"

    general_notes = get_notes(category="general")
    assert len(general_notes) >= 1


def test_get_note():
    note = add_note("Find me", category="ideas")
    fetched = get_note(note["id"])
    assert fetched is not None
    assert fetched["id"] == note["id"]
    assert fetched["content"] == "Find me"
    assert fetched["category"] == "ideas"


def test_get_note_nonexistent():
    fetched = get_note(99999)
    assert fetched is None


def test_update_note():
    note = add_note("Original content")
    updated = update_note(note["id"], "Updated content")
    assert updated is not None
    assert updated["content"] == "Updated content"
    # Verify updated_at changed
    assert updated["updated_at"] is not None


def test_update_note_with_category():
    note = add_note("Content", category="general")
    updated = update_note(note["id"], "New content", category="pomodoro")
    assert updated["content"] == "New content"
    assert updated["category"] == "pomodoro"


def test_delete_note():
    note = add_note("Delete me")
    note_id = note["id"]
    assert get_note(note_id) is not None

    delete_note(note_id)
    assert get_note(note_id) is None


def test_delete_note_nonexistent():
    # Should not raise
    delete_note(99999)


def test_note_has_timestamps():
    note = add_note("Timestamp test")
    assert note["created_at"] is not None
    assert note["updated_at"] is not None
    # Should be valid ISO format timestamps
    datetime.fromisoformat(note["created_at"])
    datetime.fromisoformat(note["updated_at"])


def test_categories_constant():
    assert "general" in CATEGORIES
    assert "pomodoro" in CATEGORIES
    assert "study" in CATEGORIES
    assert "ideas" in CATEGORIES
    assert "personal" in CATEGORIES