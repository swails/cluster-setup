""" Tests the encryption module """
from ..encryption import encrypt, decrypt
import pytest

@pytest.mark.parametrize(
    "test_payload",
    [
        "15 char no work",
        "this is a long string",
        "this is a very long string",
        "this is a very, very long string",
        "this is a very, very, very long string",
        "short",
    ],
)
@pytest.mark.parametrize("password", ["thisisastrongpassword"])
def test_round_tripping(test_payload, password):
    encrypted = encrypt(test_payload, password)
    assert decrypt(encrypted, password) == test_payload
