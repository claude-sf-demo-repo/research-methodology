from research_methodology.storage.encryption import Encryptor, IdentityEncryptor


def test_identity_round_trips():
    enc = IdentityEncryptor()
    assert enc.decrypt(enc.encrypt(b"hello")) == b"hello"


def test_identity_is_passthrough():
    enc = IdentityEncryptor()
    assert enc.encrypt(b"payload") == b"payload"


def test_identity_satisfies_the_protocol():
    assert isinstance(IdentityEncryptor(), Encryptor)
