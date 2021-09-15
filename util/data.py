import sqlite3
import os

class Data:

    def __init__(self) -> None:
        os.makedirs('data', exist_ok=True)
        self.conn = sqlite3.connect('data/data.db')