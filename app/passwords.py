from passlib.hash import sha512_crypt


def hash_password(password: str) -> str:
    return sha512_crypt.hash(password)


def check_password(stored_hash: str, password: str) -> bool:
    return sha512_crypt.verify(password, stored_hash)
