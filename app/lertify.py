"""Lertify SMS API. The account key and sender live only in this app."""
from __future__ import annotations

import requests
from flask import current_app

from app.phones import needs_unicode


class LertifyError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


def configured() -> bool:
    cfg = current_app.config
    return bool((cfg.get('LERTIFY_API_KEY') or '').strip() and (cfg.get('LERTIFY_SENDER') or '').strip())


def send_sms(destination: str, message: str) -> dict:
    cfg = current_app.config
    api_key = (cfg.get('LERTIFY_API_KEY') or '').strip()
    sender = (cfg.get('LERTIFY_SENDER') or '').strip()
    if not api_key or not sender:
        raise LertifyError('Lertify is not configured. Set LERTIFY_API_KEY and LERTIFY_SENDER.')

    try:
        response = requests.post(
            cfg.get('LERTIFY_API_URL') or 'https://api.lertify.app/v1/sms/messages',
            headers={'apikey': api_key, 'Content-Type': 'application/json'},
            json={
                'sender': sender,
                'destinations': [destination],
                'message': {
                    'content': message,
                    'isUnicode': needs_unicode(message),
                },
            },
            timeout=20,
        )
    except requests.RequestException as exc:
        raise LertifyError('Could not reach Lertify.') from exc

    try:
        payload = response.json()
    except ValueError:
        payload = {}
    if not isinstance(payload, dict):
        payload = {}

    if not 200 <= response.status_code < 300:
        detail = payload.get('error') or f'Lertify returned HTTP {response.status_code}.'
        raise LertifyError(str(detail), response.status_code)

    messages = payload.get('messages') or []
    message_id = None
    if messages and isinstance(messages[0], dict):
        message_id = messages[0].get('messageId')

    return {
        'message_id': message_id,
        'status': payload.get('status') or 'accepted',
        'segment_count': payload.get('segmentCount'),
        'sender': sender,
    }
