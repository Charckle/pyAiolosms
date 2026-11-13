from enum import Enum


class UserRole(Enum):
    ADMIN = 1
    READWRITE = 2
    READ = 3


ROLE_LABELS = {
    UserRole.ADMIN: 'Admin',
    UserRole.READWRITE: 'Read / Write',
    UserRole.READ: 'Read Only',
}

ROLE_CHOICES = [
    ('1', 'Admin'),
    ('2', 'Read / Write'),
    ('3', 'Read Only'),
]


def role_label(role_int) -> str:
    try:
        return ROLE_LABELS[UserRole(int(role_int))]
    except (ValueError, KeyError):
        return str(role_int)


def can_send(role_int) -> bool:
    try:
        return UserRole(int(role_int)).value <= UserRole.READWRITE.value
    except (ValueError, KeyError):
        return False
