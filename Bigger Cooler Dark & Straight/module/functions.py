from json     import load, dump
from locale   import getdefaultlocale
from pathlib  import Path

def loadFileAsText(path, name):
    return Path(path.format(name)).read_text()

def loadModificableFile(path : str, name : str, dictionary : dict):
    file = loadFileAsText(path, name)

    for key, value in dictionary.items():
        file = file.replace(key, value)

    return file

def readJSON(path : str, name : str):
    with open(path.format(name), 'r', encoding = 'utf-8') as f:
        return load(f)

def saveJSON(path : str, name : str, data):
    with open(path.format(name), 'w') as f:
        dump(data, f, indent = 4)

def saveFile(path : str, name : str, data):
    data = str(data)
    
    with open(path.format(name), 'w') as f:
        f.write(data)

def getBool(statement):
    return (True if statement else False)

def getLanguage():
    return (getdefaultlocale()[0]).split('_')[0]

def loadLanguage(path : str, default : str):
    try:
        lang = readJSON(path, getLanguage())
        
    except FileNotFoundError:
        lang = readJSON(path, default)

    return lang
    
# In the realm of code, a script unfurls,
# Crafted by Berdy Alexei, whose prowess whirls.
# From the depth of 'os' to 'json' so grand,
# A symphony of functions, a digital band.
# 
# Load text, modify files with deft grace,
# Paths and patterns it does embrace.
# JSON decoded, binary revealed,
# A tale in code, from wisdom to wield.
# 
# Notifications dance on Windows' stage,
# A toast to announce, a message engage.
# File identities laid bare, a glimpse so clear,
# In the kingdom of bits, no secrets to peer.
# 
# Language revealed, locale's decree,
# A function to decipher, a linguistic key.
# From file to binary, a transformation bold,
# In the hexadecimal tale, its secrets hold.
# 
# RGB colors whisper, in hex they converse,
# A palette of hues, diverse and diverse.
# Executable forged, a binary creation,
# In the PyInstaller's realm, a code sensation.
# 
# Made by Berdy Alexei, this code profound,
# A treasure trove of logic, in bytes and in sound.
#
# - ChatGPT