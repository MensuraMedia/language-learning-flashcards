CREATE TABLE IF NOT EXISTS characters (
  id            INTEGER PRIMARY KEY,
  glyph         TEXT NOT NULL UNIQUE,
  script        TEXT NOT NULL,      -- 'hiragana' | 'katakana' | 'kanji'
  romaji        TEXT,               -- kana only
  meaning       TEXT,               -- kanji only
  onyomi        TEXT,               -- kanji only, katakana convention
  kunyomi       TEXT,               -- kanji only, hiragana convention
  kana_group    TEXT,               -- 'gojuon'|'dakuon'|'handakuon'|'yoon'
  jlpt_level    TEXT,               -- 'N5'..'N1'
  category      TEXT,               -- thematic grouping
  stroke_count  INTEGER
);

CREATE TABLE IF NOT EXISTS sessions (
  id            INTEGER PRIMARY KEY,
  started_at    TEXT NOT NULL,      -- ISO 8601 UTC
  ended_at      TEXT,
  challenge     TEXT NOT NULL,      -- recognition|recall|timed|listening|mixed
  scoring       TEXT NOT NULL,      -- accuracy|speed|streak|srs
  difficulty    TEXT NOT NULL,      -- level key, e.g. 'hiragana:gojuon'
  score         INTEGER DEFAULT 0,
  total         INTEGER DEFAULT 0,
  correct       INTEGER DEFAULT 0,
  max_streak    INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS attempts (
  id            INTEGER PRIMARY KEY,
  session_id    INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  character_id  INTEGER NOT NULL REFERENCES characters(id),
  answered_at   TEXT NOT NULL,
  correct       INTEGER NOT NULL,   -- 0|1
  skipped       INTEGER NOT NULL DEFAULT 0,  -- 1 = passed without answering
  latency_ms    INTEGER,
  first_attempt INTEGER NOT NULL DEFAULT 1,
  given_answer  TEXT                -- for confusion analysis
);

CREATE TABLE IF NOT EXISTS review_state (
  character_id  INTEGER PRIMARY KEY REFERENCES characters(id),
  ease          REAL NOT NULL DEFAULT 2.5,
  interval_days REAL NOT NULL DEFAULT 0,
  due_at        TEXT,
  lapses        INTEGER NOT NULL DEFAULT 0,
  reps          INTEGER NOT NULL DEFAULT 0,
  last_seen     TEXT
);

CREATE INDEX IF NOT EXISTS idx_attempts_char    ON attempts(character_id);
CREATE INDEX IF NOT EXISTS idx_attempts_session ON attempts(session_id);
CREATE INDEX IF NOT EXISTS idx_sessions_started ON sessions(started_at);
