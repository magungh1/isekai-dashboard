from datetime import datetime, timedelta

from core.db import get_shared_connection
from services.srs_service import get_due_cards, review_card, save_mnemonic, get_stats


def _seed_card(word="テスト", meaning="Test", level=0):
    conn = get_shared_connection()
    conn.execute(
        'INSERT INTO kana_srs (word, meaning, level, next_review) VALUES (?, ?, ?, ?)',
        (word, meaning, level, datetime.now().isoformat())
    )
    conn.commit()
    row = conn.execute('SELECT id FROM kana_srs WHERE word = ?', (word,)).fetchone()
    return row['id']


def test_get_due_cards():
    _seed_card("カード", "Card")
    cards = get_due_cards()
    assert len(cards) == 1
    assert cards[0].word == "カード"


def test_get_due_cards_excludes_future():
    conn = get_shared_connection()
    future = (datetime.now() + timedelta(days=30)).isoformat()
    conn.execute(
        'INSERT INTO kana_srs (word, meaning, level, next_review) VALUES (?, ?, ?, ?)',
        ("フューチャー", "Future", 5, future)
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
    # Manually set level to 3
    conn = get_shared_connection()
    conn.execute('UPDATE kana_srs SET level = 3 WHERE id = ?', (card_id,))
    conn.commit()

    updated = review_card(card_id, 'miss')
    assert updated.level == 0


def test_save_mnemonic():
    card_id = _seed_card()
    save_mnemonic(card_id, "Test sounds like テスト!")
    conn = get_shared_connection()
    row = conn.execute('SELECT mnemonic FROM kana_srs WHERE id = ?', (card_id,)).fetchone()
    assert row['mnemonic'] == "Test sounds like テスト!"


def test_get_stats():
    _seed_card("ワード1", "Word1", level=0)
    _seed_card("ワード2", "Word2", level=5)
    stats = get_stats()
    assert stats['total'] == 2
    assert stats['mastered'] == 1
