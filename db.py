import sqlite3
import datetime
import json

DATABASE = '/home/baohoang235/infore-check-in/database.db'

class CheckinManager(object):
    def __init__(self, database):
        self.conn = None
        self.cursor = None

        if database:
            self.open(database)

    def open(self, database):
        try:
            self.conn = sqlite3.connect(database)
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            print("Error connecting to database!")

    def close(self):
        if self.conn:
            self.conn.commit()
            self.cursor.close()
            self.conn.close()
    
    def create_table(self):
        self.conn.execute('\
            CREATE TABLE IF NOT EXISTS "predictions" (\
                "pred"	TEXT NOT NULL\
            )\
        ')

    def add_predictions(self, list_predictions):
        for item in list_predictions:
            self.cursor.execute("INSERT INTO predictions(pred) VALUES(?)", (item,))
        count = len(self.get_predictions())
        if count <= 5:
            count = 0
        else:
            count = count - 5
        self.limit_predictions(count)
        self.conn.commit()

    def update_predictions(self, list_predictions):
        self.delete_predictions()
        self.add_predictions(list_predictions)
        self.conn.commit()

    def delete_predictions(self):
        self.cursor.execute("DELETE FROM predictions")
        self.conn.commit()

    def limit_predictions(self, count):
        self.cursor.execute(f"DELETE FROM predictions limit {count}")
        self.conn.commit()

    def get_predictions(self):
        predictions = []
        self.cursor.execute("SELECT * from predictions")
        rows = self.cursor.fetchall()
        for row in rows:
            predictions.append(str(row[0]))

        return predictions

    def delete_tables(self):
        self.cursor.execute('DROP TABLE predictions')

if __name__ == "__main__":
    c = CheckinManager(DATABASE)
    # c.delete_tables()
    c.create_table()
    c.add_predictions([3,4,5])
    c.update_predictions([])
    c.get_predictions()
    c.close()