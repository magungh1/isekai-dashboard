-- v5: Add habits and habit_log tables

CREATE TABLE IF NOT EXISTS habits (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL,
    icon TEXT NOT NULL DEFAULT '📌',
    category TEXT NOT NULL DEFAULT 'daily',
    xp_reward INTEGER NOT NULL DEFAULT 5,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_date TEXT NOT NULL DEFAULT CURRENT_DATE,
    is_countable INTEGER NOT NULL DEFAULT 0,
    target_count INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS habit_log (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    habit_id BIGINT NOT NULL REFERENCES habits(id) ON DELETE CASCADE,
    date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'done',
    count INTEGER NOT NULL DEFAULT 1,
    note TEXT,
    UNIQUE(habit_id, date)
);

CREATE INDEX IF NOT EXISTS idx_habit_log_date ON habit_log (date);
CREATE INDEX IF NOT EXISTS idx_habit_log_habit ON habit_log (habit_id, date);
CREATE INDEX IF NOT EXISTS idx_habits_category ON habits (category, sort_order);
