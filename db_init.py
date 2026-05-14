"""Seed Supabase with initial quest + vocab data.

Usage:
    export SUPABASE_URL="https://your-ref.supabase.co"
    export SUPABASE_SERVICE_KEY="your-secret-key"
    uv run python db_init.py
"""

import os, sys

from datetime import date

from core.db import get_shared_connection, release_connection
from config import get

VOCAB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "japanese-study", "vocab_katakana.json")


HIRAGANA_VOCAB = {
    # Colors
    "あか": "red", "あお": "blue", "きいろ": "yellow", "みどり": "green",
    "しろ": "white", "くろ": "black", "むらさき": "purple", "ちゃいろ": "brown",
    "はいいろ": "gray", "おれんじ": "orange", "ももいろ": "pink",
    # Animals
    "いぬ": "dog", "ねこ": "cat", "とり": "bird", "さかな": "fish",
    "うま": "horse", "うし": "cow", "ひつじ": "sheep", "ぶた": "pig",
    "さる": "monkey", "うさぎ": "rabbit", "かめ": "turtle", "くま": "bear",
    "きつね": "fox", "たぬき": "raccoon dog", "ねずみ": "mouse",
    "へび": "snake", "かえる": "frog", "むし": "insect", "ちょう": "butterfly",
    # Nature
    "やま": "mountain", "かわ": "river", "うみ": "sea", "そら": "sky",
    "はな": "flower", "き": "tree", "みず": "water", "ひ": "fire",
    "つき": "moon", "ほし": "star", "かぜ": "wind", "あめ": "rain",
    "ゆき": "snow", "くも": "cloud", "たいよう": "sun", "にじ": "rainbow",
    "もり": "forest", "いし": "stone", "すな": "sand", "しま": "island",
    # Body
    "あたま": "head", "かお": "face", "め": "eye", "みみ": "ear",
    "はな": "nose", "くち": "mouth", "て": "hand", "あし": "foot/leg",
    "ゆび": "finger", "かみ": "hair", "むね": "chest", "おなか": "stomach",
    "せなか": "back", "かた": "shoulder", "ひざ": "knee",
    # People & Family
    "ひと": "person", "おとこ": "man", "おんな": "woman", "こども": "child",
    "おとうさん": "father", "おかあさん": "mother", "おにいさん": "older brother",
    "おねえさん": "older sister", "おとうと": "younger brother",
    "いもうと": "younger sister", "おじいさん": "grandfather",
    "おばあさん": "grandmother", "ともだち": "friend", "せんせい": "teacher",
    # Food & Drink
    "ごはん": "rice/meal", "にく": "meat", "やさい": "vegetable",
    "くだもの": "fruit", "たまご": "egg", "さとう": "sugar", "しお": "salt",
    "しょうゆ": "soy sauce", "みそ": "miso", "とうふ": "tofu",
    "おちゃ": "tea (green)", "おかし": "snack/candy", "おこめ": "rice (uncooked)",
    "うどん": "udon noodles", "そば": "soba noodles", "おにぎり": "rice ball",
    "みそしる": "miso soup",
    # Places
    "いえ": "house", "みせ": "shop", "えき": "station", "まち": "town",
    "むら": "village", "はし": "bridge", "みち": "road", "にわ": "garden",
    "へや": "room", "まど": "window", "いりぐち": "entrance", "でぐち": "exit",
    # Things & Objects
    "かさ": "umbrella", "かぎ": "key", "かばん": "bag", "くつ": "shoes",
    "ふく": "clothes", "いす": "chair", "つくえ": "desk", "ほん": "book",
    "かみ": "paper", "はさみ": "scissors", "はこ": "box", "さら": "plate",
    "はし": "chopsticks", "ちず": "map", "くすり": "medicine",
    "まくら": "pillow", "ふとん": "futon",
    # Time
    "きょう": "today", "あした": "tomorrow", "きのう": "yesterday",
    "いま": "now", "あさ": "morning", "ひる": "noon", "よる": "night",
    "ことし": "this year", "きせつ": "season", "はる": "spring",
    "なつ": "summer", "あき": "autumn", "ふゆ": "winter",
    # Adjectives
    "おおきい": "big", "ちいさい": "small", "あたらしい": "new",
    "ふるい": "old", "たかい": "expensive/tall", "やすい": "cheap/easy",
    "ながい": "long", "みじかい": "short", "あつい": "hot", "さむい": "cold",
    "あまい": "sweet", "からい": "spicy", "にがい": "bitter", "すっぱい": "sour",
    "うつくしい": "beautiful", "かわいい": "cute", "こわい": "scary",
    "たのしい": "fun", "かなしい": "sad", "うれしい": "happy",
    "いそがしい": "busy", "つよい": "strong", "よわい": "weak",
    "はやい": "fast/early", "おそい": "slow/late",
    # Verbs
    "たべる": "to eat", "のむ": "to drink", "みる": "to see", "きく": "to listen",
    "はなす": "to speak", "よむ": "to read", "かく": "to write", "いく": "to go",
    "くる": "to come", "する": "to do", "ある": "to exist (things)",
    "いる": "to exist (living)", "わかる": "to understand", "おもう": "to think",
    "つくる": "to make", "あそぶ": "to play", "はたらく": "to work",
    "やすむ": "to rest", "ねる": "to sleep", "おきる": "to wake up",
    "あるく": "to walk", "はしる": "to run", "およぐ": "to swim",
    "とぶ": "to fly/jump", "うたう": "to sing", "おどる": "to dance",
    "わらう": "to laugh", "なく": "to cry", "あう": "to meet", "まつ": "to wait",
    "おくる": "to send", "もらう": "to receive", "おしえる": "to teach",
    "ならう": "to learn", "あらう": "to wash", "きる": "to wear",
    "ぬぐ": "to take off",
    # Greetings
    "おはよう": "good morning", "こんにちは": "hello",
    "こんばんは": "good evening", "さようなら": "goodbye",
    "ありがとう": "thank you", "すみません": "excuse me",
    "おねがいします": "please", "いただきます": "bon appetit",
    "ごちそうさま": "thanks for the meal", "おやすみなさい": "good night",
    "おめでとう": "congratulations",
    # Numbers
    "ひとつ": "one (thing)", "ふたつ": "two (things)",
    "みっつ": "three (things)", "よっつ": "four (things)",
    "いつつ": "five (things)",
}

ENGLISH_VOCAB = [
    ("ephemeral", "adj", "lasting for a very short time", "Ephemeral containers are destroyed after use"),
    ("ubiquitous", "adj", "found everywhere; omnipresent", "Smartphones have become ubiquitous in modern life"),
    ("pragmatic", "adj", "dealing with things sensibly and realistically", "We need a pragmatic approach to debugging"),
    ("eloquent", "adj", "fluent or persuasive in speaking or writing", "She gave an eloquent presentation on ML ethics"),
    ("succinct", "adj", "briefly and clearly expressed", "Keep your commit messages succinct"),
    ("ambiguous", "adj", "open to more than one interpretation", "The requirements were too ambiguous to implement"),
    ("meticulous", "adj", "showing great attention to detail", "Code reviews require meticulous attention"),
    ("verbose", "adj", "using more words than needed", "Verbose logging helps with debugging"),
    ("obsolete", "adj", "no longer produced or used; out of date", "The legacy API is now obsolete"),
    ("tenacious", "adj", "holding firmly; persistent", "A tenacious engineer who never gives up on bugs"),
    ("candid", "adj", "truthful and straightforward; frank", "Give candid feedback during retrospectives"),
    ("diligent", "adj", "having or showing careful and persistent effort", "A diligent review of the pull request"),
    ("resilient", "adj", "able to recover quickly from difficulties", "Build resilient systems that handle failures"),
    ("nuance", "noun", "a subtle difference in meaning or expression", "There is a nuance between accuracy and precision"),
    ("paradigm", "noun", "a typical example or pattern of something", "Functional programming is a different paradigm"),
    ("consensus", "noun", "general agreement among a group", "The team reached consensus on the architecture"),
    ("anomaly", "noun", "something that deviates from the norm", "The monitoring system detected an anomaly"),
    ("catalyst", "noun", "something that causes an important change", "The outage was a catalyst for improving CI/CD"),
    ("ameliorate", "verb", "to make something bad better", "We need to ameliorate the user experience"),
    ("exacerbate", "verb", "to make a problem worse", "Caching without invalidation exacerbates staleness"),
    ("articulate", "verb", "to express clearly and effectively", "Articulate your design decisions in the RFC"),
    ("mitigate", "verb", "to make less severe or serious", "Rate limiting helps mitigate DDoS attacks"),
    ("scrutinize", "verb", "to examine closely and critically", "Scrutinize the data pipeline for bottlenecks"),
    ("consolidate", "verb", "to combine into a single more effective whole", "Consolidate the duplicate utility functions"),
    ("circumvent", "verb", "to find a way around an obstacle", "They circumvented the rate limit with caching"),
    ("pernicious", "adj", "having a harmful effect, especially gradually", "Technical debt has a pernicious effect on velocity"),
    ("sycophant", "noun", "a person who flatters to gain advantage", "A sycophant agrees with every idea without thinking"),
    ("gregarious", "adj", "fond of company; sociable", "A gregarious engineer who thrives in pair programming"),
    ("laconic", "adj", "using very few words", "His laconic PR descriptions frustrated reviewers"),
    ("pedantic", "adj", "excessively concerned with minor details", "Being pedantic about naming conventions pays off"),
    ("cogent", "adj", "clear, logical, and convincing", "She made a cogent argument for rewriting the service"),
    ("acumen", "noun", "the ability to make good judgments", "Business acumen is valuable for senior engineers"),
    ("harbinger", "noun", "a person or thing that signals the approach of another", "Increased error rates are a harbinger of system failure"),
    ("juxtapose", "verb", "to place close together for contrast", "Juxtapose the old and new implementations"),
    ("elucidate", "verb", "to make something clear; explain", "The docs should elucidate the API contract"),
    ("convoluted", "adj", "extremely complex and difficult to follow", "The convoluted logic needs refactoring"),
    ("superfluous", "adj", "unnecessary, especially through being more than enough", "Remove superfluous dependencies"),
    ("leverage", "verb", "to use something to maximum advantage", "Leverage existing libraries instead of reinventing"),
    ("iterate", "verb", "to perform or utter repeatedly", "We iterate on the design based on user feedback"),
    ("synthesize", "verb", "to combine elements into a coherent whole", "Synthesize findings from multiple data sources"),
    ("delegate", "verb", "to entrust a task to another person", "Delegate routine tasks to focus on architecture"),
    ("galvanize", "verb", "to shock or excite someone into action", "The outage galvanized the team to fix monitoring"),
    ("inadvertent", "adj", "not resulting from deliberate planning", "The inadvertent data leak exposed user emails"),
    ("quintessential", "adj", "representing the perfect example", "Python is the quintessential ML language"),
    ("dichotomy", "noun", "a division into two contrasting things", "The dichotomy between speed and quality"),
    ("entropy", "noun", "gradual decline into disorder", "Without maintenance, codebase entropy increases"),
    ("inertia", "noun", "tendency to remain unchanged", "Organizational inertia prevents adopting new tools"),
    ("serendipity", "noun", "occurrence of events by chance in a happy way", "Many discoveries in ML happen through serendipity"),
    ("propensity", "noun", "a natural tendency to behave in a certain way", "JavaScript has a propensity for type coercion bugs"),
]

KANJI_VOCAB = [
    ("日", "ひ", "ニチ/ジツ", "day, sun"), ("月", "つき", "ゲツ/ガツ", "month, moon"),
    ("火", "ひ", "カ", "fire"), ("水", "みず", "スイ", "water"),
    ("木", "き", "モク/ボク", "tree, wood"), ("金", "かね", "キン/コン", "gold, money"),
    ("土", "つち", "ド/ト", "earth, soil"), ("人", "ひと", "ジン/ニン", "person"),
    ("大", "おおきい", "ダイ/タイ", "big, large"), ("小", "ちいさい", "ショウ", "small, little"),
    ("山", "やま", "サン", "mountain"), ("川", "かわ", "セン", "river"),
    ("田", "た", "デン", "rice field"), ("中", "なか", "チュウ", "middle, inside"),
    ("上", "うえ", "ジョウ", "above, up"), ("下", "した", "カ/ゲ", "below, down"),
    ("左", "ひだり", "サ", "left"), ("右", "みぎ", "ウ/ユウ", "right"),
    ("一", "ひとつ", "イチ", "one"), ("二", "ふたつ", "ニ", "two"),
    ("三", "みっつ", "サン", "three"), ("四", "よっつ", "シ", "four"),
    ("五", "いつつ", "ゴ", "five"), ("六", "むっつ", "ロク", "six"),
    ("七", "ななつ", "シチ", "seven"), ("八", "やっつ", "ハチ", "eight"),
    ("九", "ここのつ", "キュウ/ク", "nine"), ("十", "とお", "ジュウ", "ten"),
    ("百", None, "ヒャク", "hundred"), ("千", "ち", "セン", "thousand"),
    ("万", None, "マン/バン", "ten thousand"), ("食", "たべる", "ショク", "eat, food"),
    ("飲", "のむ", "イン", "drink"), ("見", "みる", "ケン", "see, look"),
    ("聞", "きく", "ブン/モン", "hear, listen"), ("読", "よむ", "ドク", "read"),
    ("書", "かく", "ショ", "write"), ("話", "はなす", "ワ", "talk"),
    ("言", "いう", "ゲン/ゴン", "say"), ("行", "いく", "コウ/ギョウ", "go"),
    ("来", "くる", "ライ", "come"), ("立", "たつ", "リツ", "stand"),
    ("休", "やすむ", "キュウ", "rest"), ("学", "まなぶ", "ガク", "study"),
    ("生", "いきる", "セイ/ショウ", "life"), ("先", "さき", "セン", "previous"),
    ("名", "な", "メイ/ミョウ", "name"), ("年", "とし", "ネン", "year"),
]


def init_db(conn=None, *, close=True):
    """Create all tables and seed data. If conn is given, use it;
    otherwise open a new Supabase connection."""
    own_conn = False
    if conn is None:
        conn = get_shared_connection()
        own_conn = True

    conn.execute("""
        CREATE TABLE IF NOT EXISTS quests (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            title TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            category TEXT NOT NULL DEFAULT 'daily',
            deadline TIMESTAMPTZ,
            sort_order INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS kana_srs (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            word TEXT NOT NULL UNIQUE,
            meaning TEXT NOT NULL,
            mnemonic TEXT,
            level INTEGER NOT NULL DEFAULT 0,
            next_review TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            type TEXT NOT NULL DEFAULT 'katakana',
            review_count INTEGER NOT NULL DEFAULT 0,
            last_reviewed TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS english_srs (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            word TEXT NOT NULL UNIQUE,
            definition TEXT NOT NULL,
            example TEXT,
            mnemonic TEXT,
            part_of_speech TEXT NOT NULL DEFAULT 'noun',
            level INTEGER NOT NULL DEFAULT 0,
            next_review TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            review_count INTEGER NOT NULL DEFAULT 0,
            last_reviewed TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS kanji_srs (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            kanji TEXT NOT NULL UNIQUE,
            kun_reading TEXT,
            on_reading TEXT,
            meaning TEXT NOT NULL,
            mnemonic TEXT,
            level INTEGER NOT NULL DEFAULT 0,
            next_review TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            review_count INTEGER NOT NULL DEFAULT 0,
            last_reviewed TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS srs_reviews (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            deck TEXT NOT NULL,
            card_id BIGINT NOT NULL,
            rating TEXT NOT NULL,
            prev_level INTEGER NOT NULL DEFAULT 0,
            new_level INTEGER NOT NULL DEFAULT 0,
            reviewed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS xp_log (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            xp INTEGER NOT NULL,
            source TEXT NOT NULL,
            created_date TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            content TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    # Seeds
    with open(VOCAB_PATH, "r", encoding="utf-8") as f:
        vocab = __import__("json").load(f)
        for word, meaning in vocab.items():
            try:
                conn.execute(
                    "INSERT INTO kana_srs (word, meaning, type) VALUES (%s, %s, 'katakana')",
                    (word, meaning),
                )
            except Exception:
                pass

    for word, meaning in HIRAGANA_VOCAB.items():
        try:
            conn.execute(
                "INSERT INTO kana_srs (word, meaning, type) VALUES (%s, %s, 'hiragana')",
                (word, meaning),
            )
        except Exception:
            pass

    for word, pos, definition, example in ENGLISH_VOCAB:
        try:
            conn.execute(
                "INSERT INTO english_srs (word, definition, example, part_of_speech) VALUES (%s, %s, %s, %s)",
                (word, definition, example, pos),
            )
        except Exception:
            pass

    for kanji, kun, on, meaning in KANJI_VOCAB:
        try:
            conn.execute(
                "INSERT INTO kanji_srs (kanji, kun_reading, on_reading, meaning) VALUES (%s, %s, %s, %s)",
                (kanji, kun, on, meaning),
            )
        except Exception:
            pass

    # Default quests
    try:
        conn.execute("SELECT COUNT(*) FROM quests")
        if conn.fetchone()[0] == 0:
            for title, category in [
                ("Review Katakana Flashcards", "daily"),
                ("Review Hiragana Flashcards", "daily"),
                ("Read an ML paper", "daily"),
                ("Check GitHub PRs", "weekly"),
                ("Review English Vocabulary", "weekly"),
                ("Catch up on ML training/inference", "goals"),
            ]:
                conn.execute(
                    "INSERT INTO quests (title, status, category) VALUES (%s, 'pending', %s)",
                    (title, category),
                )
    except Exception:
        pass

    if own_conn:
        conn.commit()
        # Create indexes
        conn.execute("CREATE INDEX IF NOT EXISTS idx_kana_due ON kana_srs (level ASC, next_review ASC)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_english_due ON english_srs (level ASC, next_review ASC)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_kanji_due ON kanji_srs (level ASC, next_review ASC)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_quests_cat ON quests (category, status, sort_order)")
        conn.commit()
        release_connection(conn)
        print("Database initialized and seeded successfully.")


if __name__ == "__main__":
    init_db()