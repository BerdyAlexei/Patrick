from module.functions import *
from module.statics   import *

from Crypto.Cipher       import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Hash         import SHA256

from base64 import b64encode, b64decode

configuration = readJSON(CONFIGURATION, 'configuration')
password_storage = loadFileAsText(FILE, 'password_storage')

use_key = configuration['use_key']

def encryptData(data: str, key):
    cipher = AES.new(key, AES.MODE_CBC)
    cipher_text_bytes = cipher.encrypt(pad(data.encode('utf-8'), AES.block_size))
    initialization_vector = b64encode(cipher.iv).decode('utf-8')
    cipher_text = b64encode(cipher_text_bytes).decode('utf-8')
    
    return initialization_vector + cipher_text

def decryptData(data, key):
    initialization_vector = b64decode(data[:24])
    cipher_text = b64decode(data[24:])

    cipher = AES.new(key, AES.MODE_CBC, initialization_vector)

    plain_text = unpad(cipher.decrypt(cipher_text), AES.block_size)

    return plain_text.decode('utf-8')

def loadPasswordStorage():
    global password_storage

    def getKey():
        if use_key:
            print('Patrick uses a key and the passwords it saves are encrypted, do you want to decrypt them?')
            key = input('Enter your key to decrypt: ')
        else:
            print('Patrick does not currently encrypt its passwords, do you want to encrypt them?')
            key = input('Enter a key to encrypt: ')

        return SHA256.new(key.encode('utf-8')).digest()

    if use_key:
        try:
            password_storage = decryptData(password_storage, getKey())
        except Exception as e:
            print('Incorrect key! Try again.')
    else:
        password_storage = encryptData(password_storage, getKey())

    configuration['use_key'] = not use_key

    saveJSON(CONFIGURATION, 'configuration', configuration)
    saveFile(FILE, 'password_storage', password_storage)

loadPasswordStorage()

print('Operation completed!')
input('[Press Enter to close]')