from builtins import bytes
import base64
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto import Random

__all__ = ["encrypt", "decrypt"]

def encrypt(string: str, password: str) -> str:
    """
    It returns an encrypted string which can be decrypted just by the 
    password.
    """
    key = password_to_key(password.encode("utf-8"))
    IV = make_initialization_vector()
    encryptor = AES.new(key, AES.MODE_CBC, IV)

    # store the IV at the beginning and encrypt
    return encode(IV + encryptor.encrypt(pad_string(string.encode("utf-8"))))

def decrypt(string: str, password: str) -> str:
    key = password_to_key(password.encode("utf-8"))

    string = decode(string)

    # extract the IV from the beginning
    IV = string[:AES.block_size]  
    decryptor = AES.new(key, AES.MODE_CBC, IV)

    string = decryptor.decrypt(string[AES.block_size:])
    return unpad_string(string).decode("utf-8")

def password_to_key(password):
    """
    Use SHA-256 over our password to get a proper-sized AES key.
    This hashes our password into a 256 bit string. 
    """
    return SHA256.new(password).digest()

def make_initialization_vector():
    """
    An initialization vector (IV) is a fixed-size input to a cryptographic
    primitive that is typically required to be random or pseudorandom.
    Randomization is crucial for encryption schemes to achieve semantic 
    security, a property whereby repeated usage of the scheme under the 
    same key does not allow an attacker to infer relationships 
    between segments of the encrypted message.
    """
    return Random.new().read(AES.block_size)

def pad_string(string, chunk_size=AES.block_size):
    """
    Pad string the peculirarity that uses the first byte
    is used to store how much padding is applied
    """
    assert chunk_size  <= 256, 'We are using one byte to represent padding'
    to_pad = (chunk_size - (len(string) + 1)) % chunk_size
    return bytes([to_pad]) + string + bytes([0] * to_pad)

def unpad_string(string):
    to_pad = string[0]
    if to_pad == 0:
        return string[1:]
    return string[1:-to_pad]

def encode(string):
    """
    Base64 encoding schemes are commonly used when there is a need to encode 
    binary data that needs be stored and transferred over media that are 
    designed to deal with textual data.
    This is to ensure that the data remains intact without 
    modification during transport.
    """
    return base64.b64encode(string).decode("utf-8")

def decode(string):
    return base64.b64decode(string.encode("utf-8"))


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument("-p", "--password", dest="password", required=True,
                        help="Password to convert to an encryption key")
    parser.add_argument("-t", "--text", dest="text", required=True,
                        help="The text to encrypt (or decrypt) with the password")
    parser.add_argument("-f", "--file", dest="is_file", default=False, action="store_true",
                        help="If true, text is a file name")
    parser.add_argument("-d", "--decrypt", action="store_true", dest="decrypt",
                        default=False, help="Use this flag to decrypt instead of encrypt")

    args = parser.parse_args()

    if args.is_file:
        with open(args.text, "r") as f:
            text = f.read()
    else:
        text = args.text

    if args.decrypt:
        print(decrypt(text, args.password))
    else:
        print(encrypt(text, args.password))
