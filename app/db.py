"""SQLite connection and schema. One connection per request."""
from __future__ import annotations

import os
import sqlite3

from flask import current_app, g


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role INTEGER NOT NULL,
    status INTEGER NOT NULL DEFAULT 1,
    api_token_hash TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT NOT NULL,
    destination TEXT NOT NULL,
    body TEXT NOT NULL,
    sender TEXT NOT NULL,
    provider_message_id TEXT,
    status TEXT NOT NULL,
    segment_count INTEGER,
    error TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_messages_created ON messages (id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_token ON users (api_token_hash);
"""


def get_db() -> sqlite3.Connection:
    if 'db' not in g:
        conn = sqlite3.connect(current_app.config['DATABASE'], timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys = ON')
        conn.execute('PRAGMA journal_mode = WAL')
        g.db = conn
    return g.db


def close_db(_exc=None):
    conn = g.pop('db', None)
    if conn is not None:
        conn.close()


def init_app(app):
    os.makedirs(app.config['DATA_DIR'], exist_ok=True)
    app.config['DATABASE'] = os.path.join(app.config['DATA_DIR'], 'sms.db')

    with app.app_context():
        db = get_db()
        db.executescript(SCHEMA)
        db.commit()

    app.teardown_appcontext(close_db)
