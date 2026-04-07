from dataclasses import dataclass
from datetime import datetime


@dataclass
class Quest:
    id: int
    title: str
    status: str  # 'pending' or 'done'
    created_at: str
    category: str = 'daily'  # 'daily', 'weekly', 'goals'
    deadline: str | None = None
    sort_order: int = 0

    @property
    def is_done(self) -> bool:
        return self.status == 'done'


@dataclass
class KanaCard:
    id: int
    word: str
    meaning: str
    mnemonic: str | None
    level: int
    next_review: str
    type: str = 'katakana'


@dataclass
class KanjiCard:
    id: int
    kanji: str
    kun_reading: str | None
    on_reading: str | None
    meaning: str
    mnemonic: str | None
    level: int
    next_review: str


@dataclass
class VocabCard:
    id: int
    word: str
    definition: str
    example: str | None
    mnemonic: str | None
    part_of_speech: str
    level: int
    next_review: str
