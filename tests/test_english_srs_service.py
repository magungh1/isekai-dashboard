from datetime import datetime, timedelta

from core.db import get_shared_connection
from services.english_srs_service import get_due_cards, review_card, save_mnemonic, get_stats


def _seed_card(word="ephemeral", definition="lasting for a very short time",
               pos="adj", example="Ephemeral containers", level=0):
    conn = get_shared_connection()
    conn.execute(
        'INSERT INTO english_srs (word, definition, example, part_of_speech, level, next_review) '
        'VALUES (?, ?, ?, ?, ?, ?)',
        (word, definition, example, pos, level, datetime.now().isoformat())
    )
    conn.commit()
    row = conn.execute('SELECT id FROM english_srs WHERE word = ?', (word,)).fetchone()
    return row['id']


def test_get_due_cards():
    _seed_card("ubiquitous", "found everywhere")
    cards = get_due_cards()
    assert len(cards) == 1
    assert cards[0].word == "ubiquitous"


def test_get_due_cards_excludes_future():
    conn = get_shared_connection()
    future = (datetime.now() + timedelta(days=30)).isoformat()
    conn.execute(
        'INSERT INTO english_srs (word, definition, part_of_speech, level, next_review) '
        'VALUES (?, ?, ?, ?, ?)',
        ("future_word", "a future word", "noun", 5, future)
    )
    conn.commit()
    cards = get_due_cards()
    assert len(cards) == 0


def test_review_card_good():
    card_id = _seed_card()
    updated = review_card(card_id, 'good')
    assert updated.level == 1


def test_review_card_miss():
    card_id = _seed_card(level=3)
    conn = get_shared_connection()
    conn.execute('UPDATE english_srs SET level = 3 WHERE id = ?', (card_id,))
    conn.commit()

    updated = review_card(card_id, 'miss')
    assert updated.level == 0


def test_save_mnemonic():
    card_id = _seed_card()
    save_mnemonic(card_id, "Ephemeral like RAM - gone when power's off!")
    conn = get_shared_connection()
    row = conn.execute('SELECT mnemonic FROM english_srs WHERE id = ?', (card_id,)).fetchone()
    assert "RAM" in row['mnemonic']


def test_get_stats():
    _seed_card("word1", "def1", level=0)
    _seed_card("word2", "def2", level=5)
    stats = get_stats()
    assert stats['total'] == 2
    assert stats['mastered'] == 1


def test_vocab_card_has_example():
    card_id = _seed_card(example="Test example sentence")
    from services.english_srs_service import get_card_by_id
    card = get_card_by_id(card_id)
    assert card.example == "Test example sentence"
    assert card.part_of_speech == "adj"
