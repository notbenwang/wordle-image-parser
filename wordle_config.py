import pytesseract
import requests
import json
import os

WORDLE_WORD_BANK = "valid-wordle-words.txt"
# PYTESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
PYTESSERACT_PATH = os.getenv("TESSDATA_PREFIX")
DATABASE_URL = "https://engaging-data.com/pages/scripts/wordlebot/wordlepuzzles.js"
PRE_DATABASE_PATH = "pre640.json"
PRE_DATABASE_KEY_PATH = "pre640_key.json"

def create_word_bank_from_path(path):
    word_bank = []
    with open(path, 'r') as f:
        lines = f.readlines()
        for line in lines:
            word_bank.append(line[:-1])
    return word_bank

class Config():
    word_bank = []
    def __init__(self, pytesseract_path = PYTESSERACT_PATH, word_bank_path = WORDLE_WORD_BANK) -> None:
        # Unknown case when paths don't exist
        self.word_bank = create_word_bank_from_path(word_bank_path)
        if pytesseract_path:
            pytesseract.pytesseract.tesseract_cmd = pytesseract_path
        self.word_bank_path = word_bank_path
        self.pytesseract_path = pytesseract_path
        self.db = WordleDatabase()
        print("Start Config")

    def update_word_bank(self, path):
        self.word_bank = create_word_bank_from_path(path)
    
    def update_pytesseract_path(self, path):
        pytesseract.pytesseract.tesseract_cmd = path

class WordleDatabase():
    def __init__(self, url=DATABASE_URL, json_pre_path=PRE_DATABASE_PATH, json_pre_key_path = PRE_DATABASE_KEY_PATH):
        r = requests.get(url)
        json_text = r.text[len("wordlepuzzles="):]
        self.puzzles = json.loads(json_text)
        with open(json_pre_path, 'r') as f:
            self.list_pre = json.load(f)
        with open(json_pre_key_path, 'r') as f:
            self.list_pre_key = json.load(f)
    
    def getNumber(self, word):
        if len(word) != 5:
            return -1
        word = word.upper()
        for key, value in self.puzzles.items():
            if value["answer"] == word:
                return key
        if word not in self.list_pre:
            return -1
        else:
            return self.list_pre[word]["number"]
        
    def getInfo(self, num):
        if int(num) < 0:
            return None
        if int(num) > 626:
            return self.puzzles[str(num)]
        else:
            return self.list_pre_key[str(num)]

if __name__=="__main__":
    test = WordleDatabase()
    num = test.getNumber("RIVAL")
    info = test.getInfo(num)
    print(num)
    print(info)