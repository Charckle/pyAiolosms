"""Shared send path for the web form and POST /api/v1/sms."""
from flask import current_app

from app.lertify import LertifyError, configured, send_sms
from app.models import MessageM
from app.phones import PhoneError, normalize_phone
from app.roles import can_send


class SendRejected(Exception):
    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.status_code = status_code


def deliver(user: dict, raw_to: str, raw_message: str) -> dict:
    if user.get('status') != 1:
        raise SendRejected('This account is disabled.', 403)
    if not can_send(user.get('role')):
        raise SendRejected('This account cannot send SMS.', 403)

    try:
        destination = normalize_phone(raw_to, current_app.config.get('DEFAULT_COUNTRY_CODE', '386'))
    except PhoneError as exc:
        raise SendRejected(str(exc), 400) from exc

    message = (raw_message or '').strip()
    if not message:
        raise SendRejected('Message is empty.', 400)
    if len(message) > 640:
        raise SendRejected('Message is longer than 640 characters.', 400)

    if not configured():
        raise SendRejected('Lertify is not configured. Set LERTIFY_API_KEY and LERTIFY_SENDER.', 503)

    sender = (current_app.config.get('LERTIFY_SENDER') or '').strip()
    try:
        result = send_sms(destination, message)
    except LertifyError as exc:
        MessageM.create(
            user=user,
            destination=destination,
            body=message,
            sender=sender,
            status='error',
            error=str(exc)[:500],
        )
        raise SendRejected(str(exc), 502) from exc

    message_row = MessageM.create(
        user=user,
        destination=destination,
        body=message,
        sender=result['sender'],
        status=result['status'],
        provider_message_id=result['message_id'],
        segment_count=result['segment_count'],
    )
    return {
        'id': message_row,
        'destination': destination,
        'messageId': result['message_id'],
        'status': result['status'],
        'segmentCount': result['segment_count'],
    }
