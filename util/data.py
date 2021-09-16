import sqlite3
import os

class Data:

    def __init__(self) -> None:
        os.makedirs('data', exist_ok=True)
        self.conn = sqlite3.connect('data/data.db')

        cursor = self.conn.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS money (id INTEGER UNIQUE PRIMARY KEY, balance REAL);')
        cursor.execute('CREATE TABLE IF NOT EXISTS stonks (id INTEGER, company TEXT, amount REAL);')

        self.conn.commit()

    def exec_command(self, cmd, params=()):
        cursor = self.conn.cursor()
        cursor.execute(cmd, params)
        self.conn.commit()

    def get_rows(self, table, key_name, key_val):
        cursor = self.conn.cursor()
        cursor.execute(f'SELECT * FROM {table} WHERE {key_name} = {key_val};')
        rows = cursor.fetchall()
        return rows
    def get_row(self, table, key_name, key_val):
        rows = self.get_rows(table, key_name, key_val)
        if len(rows) == 0:
            return None
        return rows[0]

    def get_money(self, person):
        row = self.get_row('money', 'id', person)
        if row is None:
            return None
        return row[1]

    def get_stonks(self, person):
        rows = self.get_rows('stonks', 'id', person)
        res = {}
        for r in rows:
            res[r[1]] = r[2]
        return res

    def change_money(self, person, amount):
        money = self.get_money(person)
        self.exec_command(f'REPLACE INTO money (id, balance) VALUES (?, ?);', (person, amount + money))

    def change_stonks(self, person, stonk, amount):
        try:
            orig = self.get_stonks(person)[stonk]
        except KeyError:
            orig = 0.0
        self.exec_command(f'DELETE FROM stonks WHERE stonk = ? and id = ?;', (stonk, person))
        self.exec_command(f'INSERT INTO stonks (id, stonk, amount) VALUES (?, ?, ?);', (person, stonk, orig + amount))

data = Data()