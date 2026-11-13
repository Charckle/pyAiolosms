"""Users and the SMS send log."""
from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timezone

from app.db import get_db
from app.passwords import check_password, hash_password
from app.roles import UserRole


def _now() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')


def _row(row):
    if row is None:
        return None
    return dict(row)


def present_user(user: dict | None) -> dict | None:
    """User fields safe to put in a template. Password and token hash stay out."""
    if not user:
        return None
    return {
        'id': user['id'],
        'username': user['username'],
        'role': user['role'],
        'status': user['status'],
        'has_token': bool(user.get('api_token_hash')),
        'created_at': user.get('created_at'),
    }


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


class UserM:
    @staticmethod
    def get_all() -> list[dict]:
        rows = get_db().execute('SELECT * FROM users ORDER BY username COLLATE NOCASE').fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def needs_setup() -> bool:
        row = get_db().execute('SELECT COUNT(*) AS n FROM users').fetchone()
        return row['n'] == 0

    @staticmethod
    def get_one(id_) -> dict | None:
        try:
            user_id = int(id_)
        except (TypeError, ValueError):
            return None
        return _row(get_db().execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone())

    @staticmethod
    def count_active() -> int:
        row = get_db().execute('SELECT COUNT(*) AS n FROM users WHERE status = 1').fetchone()
        return row['n']

    @staticmethod
    def count_active_admins() -> int:
        row = get_db().execute(
            'SELECT COUNT(*) AS n FROM users WHERE status = 1 AND role = ?',
            (UserRole.ADMIN.value,),
        ).fetchone()
        return row['n']

    @staticmethod
    def check_username(username: str, exclude_id=None) -> dict | None:
        try:
            exclude_int = int(exclude_id) if exclude_id not in (None, '', 'new') else None
        except (ValueError, TypeError):
            exclude_int = None
        row = get_db().execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if row is None:
            return None
        if exclude_int is not None and row['id'] == exclude_int:
            return None
        return dict(row)

    @staticmethod
    def login_check(username: str, password: str) -> dict | None:
        row = get_db().execute(
            'SELECT * FROM users WHERE username = ? AND status = 1',
            (username,),
        ).fetchone()
        if row and check_password(row['password'], password):
            return dict(row)
        return None

    @staticmethod
    def by_token(token: str) -> dict | None:
        if not token:
            return None
        digest = token_hash(token)
        row = get_db().execute(
            'SELECT * FROM users WHERE api_token_hash = ? AND status = 1',
            (digest,),
        ).fetchone()
        if row and hmac.compare_digest(row['api_token_hash'], digest):
            return dict(row)
        return None

    @staticmethod
    def create(username: str, password: str, role: int, status: int) -> int:
        cur = get_db().execute(
            '''INSERT INTO users (username, password, role, status, created_at)
               VALUES (?, ?, ?, ?, ?)''',
            (username, hash_password(password), int(role), int(status), _now()),
        )
        get_db().commit()
        return cur.lastrowid

    @staticmethod
    def update(id_, username: str, role: int, status: int, password: str = None):
        if password:
            get_db().execute(
                '''UPDATE users SET username = ?, role = ?, status = ?, password = ?
                   WHERE id = ?''',
                (username, int(role), int(status), hash_password(password), id_),
            )
        else:
            get_db().execute(
                'UPDATE users SET username = ?, role = ?, status = ? WHERE id = ?',
                (username, int(role), int(status), id_),
            )
        get_db().commit()

    @staticmethod
    def delete(id_) -> bool:
        cur = get_db().execute('DELETE FROM users WHERE id = ?', (id_,))
        get_db().commit()
        return cur.rowcount > 0

    @staticmethod
    def issue_token(id_) -> str:
        raw = secrets.token_urlsafe(32)
        get_db().execute(
            'UPDATE users SET api_token_hash = ? WHERE id = ?',
            (token_hash(raw), id_),
        )
        get_db().commit()
        return raw

    @staticmethod
    def revoke_token(id_):
        get_db().execute('UPDATE users SET api_token_hash = NULL WHERE id = ?', (id_,))
        get_db().commit()


class MessageM:
    @staticmethod
    def create(user: dict, destination: str, body: str, sender: str,
               status: str, provider_message_id: str = None,
               segment_count: int = None, error: str = None) -> int:
        cur = get_db().execute(
            '''INSERT INTO messages
               (user_id, username, destination, body, sender, provider_message_id,
                status, segment_count, error, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (
                user['id'], user['username'], destination, body, sender,
                provider_message_id, status, segment_count, error, _now(),
            ),
        )
        get_db().commit()
        return cur.lastrowid

    @staticmethod
    def recent(limit: int = 200, user_id: int | None = None) -> list[dict]:
        if user_id is None:
            rows = get_db().execute(
                'SELECT * FROM messages ORDER BY id DESC LIMIT ?',
                (limit,),
            ).fetchall()
        else:
            rows = get_db().execute(
                'SELECT * FROM messages WHERE user_id = ? ORDER BY id DESC LIMIT ?',
                (user_id, limit),
            ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def count(user_id: int | None = None) -> int:
        if user_id is None:
            row = get_db().execute('SELECT COUNT(*) AS n FROM messages').fetchone()
        else:
            row = get_db().execute(
                'SELECT COUNT(*) AS n FROM messages WHERE user_id = ?',
                (user_id,),
            ).fetchone()
        return row['n']
