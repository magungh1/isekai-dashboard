-- v6: Add srs_reviews table (was only in init_schema, not migrations)

CREATE TABLE IF NOT EXISTS srs_reviews (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    deck TEXT NOT NULL,
    card_id BIGINT NOT NULL,
    rating TEXT NOT NULL,
    prev_level INTEGER NOT NULL DEFAULT 0,
    new_level INTEGER NOT NULL DEFAULT 0,
    reviewed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_srs_reviews_card ON srs_reviews (deck, card_id);
CREATE INDEX IF NOT EXISTS idx_srs_reviews_date ON srs_reviews (reviewed_at);
