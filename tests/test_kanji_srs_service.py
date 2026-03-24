from datetime import datetime, timedelta

from core.db import get_shared_connection
from services.kanji_srs_service import get_due_cards, review_card, save_mnemonic, get_stats


def _seed_kanji(kanji="食", kun="たべる", on="ショク", meaning="eat, food", level=0):
    conn = get_shared_connection()
    conn.execute(
        'INSERT INTO kanji_srs (kanji, kun_reading, on_reading, meaning, level, next_review) '
        'VALUES (?, ?, ?, ?, ?, ?)',
        (kanji, kun, on, meaning, level, datetime.now().isoformat())
    )
    conn.commit()
    row = conn.execute('SELECT id FROM kanji_srs WHERE kanji = ?', (kanji,)).fetchone()
    return row['id']


def test_get_due_cards():
    _seed_kanji("日", "ひ", "ニチ", "day, sun")
    cards = get_due_cards()
    assert len(cards) == 1
    assert cards[0].kanji == "日"


def test_get_due_cards_excludes_future():
    conn = get_shared_connection()
    future = (datetime.now() + timedelta(days=30)).isoformat()
    conn.execute(
        'INSERT INTO kanji_srs (kanji, meaning, level, next_review) VALUES (?, ?, ?, ?)',
        ("未", "future kanji", 5, future)
    )
    conn.commit()
    cards = get_due_cards()
    assert len(cards) == 0


def test_review_card_good():
    card_id = _seed_kanji()
    updated = review_card(card_id, 'good')
    assert updated.level == 1


def test_review_card_miss():
    card_id = _seed_kanji(level=3)
    conn = get_shared_connection()
    conn.execute('UPDATE kanji_srs SET level = 3 WHERE id = ?', (card_id,))
    conn.commit()
    updated = review_card(card_id, 'miss')
    assert updated.level == 0


def test_save_mnemonic():
    card_id = _seed_kanji()
    save_mnemonic(card_id, "Food radical + person eating")
    conn = get_shared_connection()
    row = conn.execute('SELECT mnemonic FROM kanji_srs WHERE id = ?', (card_id,)).fetchone()
    assert "eating" in row['mnemonic']


def test_get_stats():
    _seed_kanji("大", meaning="big", level=0)
    _seed_kanji("小", meaning="small", level=5)
    stats = get_stats()
    assert stats['total'] == 2
    assert stats['mastered'] == 1


def test_kanji_card_has_readings():
    card_id = _seed_kanji()
    from services.kanji_srs_service import get_card_by_id
    card = get_card_by_id(card_id)
    assert card.kun_reading == "たべる"
    assert card.on_reading == "ショク"
    assert card.meaning == "eat, food"
