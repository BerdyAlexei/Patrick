from json     import load, dump
from pathlib  import Path

def loadFileAsText(path, name):
    return Path(path.format(name)).read_text()

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