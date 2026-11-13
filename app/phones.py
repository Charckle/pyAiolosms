"""Phone numbers and the GSM alphabet Lertify uses to pick Unicode."""
import re

# GSM 03.38 basic set plus the extension table. Characters outside this need Unicode.
_GSM = set(
    "@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞ ÆæßÉ !\"#¤%&'()*+,-./0123456789:;<=>?"
    "¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§¿abcdefghijklmnopqrstuvwxyzäöñüà"
    "\f^{}\\[~]|€"
)


class PhoneError(ValueError):
    pass


def normalize_phone(raw: str, default_cc: str = '386') -> str:
    """Return an E.164 number. Local numbers use default_cc (386 drops the leading 0)."""
    cc = re.sub(r'\D', '', default_cc or '') or '386'
    text = re.sub(r'[\s\-()./]', '', (raw or '').strip())
    if not text:
        raise PhoneError('Enter a phone number like +38640123456 or 040123456.')

    if text.startswith('+'):
        digits = text[1:]
    elif text.startswith('00'):
        digits = text[2:]
    elif text.startswith('0'):
        digits = cc + text[1:]
    elif text.startswith(cc) and len(text) >= len(cc) + 6:
        digits = text
    else:
        digits = cc + text

    if not digits.isdigit() or not (8 <= len(digits) <= 15):
        raise PhoneError('Enter a phone number like +38640123456 or 040123456.')
    return '+' + digits


def needs_unicode(message: str) -> bool:
    return any(ch not in _GSM for ch in message)
