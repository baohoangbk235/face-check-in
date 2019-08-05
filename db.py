import sqlite3
from datetime import datetime
import json

DATABASE = '/home/baohoang235/face-check-in/database.db'

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
        self.conn.execute('\
            CREATE TABLE IF NOT EXISTS "results" (\
                "name"	TEXT NOT NULL,\
                "datetime" DATETIME NOT NULL,\
                "image" TEXT NOT NULL\
            )\
        ')

    def add_predictions(self,camID, list_predictions):
        for item in list_predictions:
            self.cursor.execute("INSERT INTO predictions(pred) VALUES(?)", (item,))
        count = len(self.get_predictions(camID))
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
    
    def add_result(self, name, time, image):
        self.cursor.execute("INSERT INTO results(name, datetime, image) VALUES(?,?,?)", (name,time,image))
        self.conn.commit()
    
    def get_result(self):
        self.cursor.execute("SELECT * from results")
        rows = self.cursor.fetchall()
        for row in rows:
            print(row)        

    def check(self,name, now):
        self.cursor.execute("SELECT * from results")
        rows = self.cursor.fetchall()
        for row in reversed(rows):
            print(row)
            date_time_obj = datetime.strptime(str(row[1]), '%m/%d/%Y-%H:%M:%S')
            delay_check_in = int((now - date_time_obj).total_seconds())
            if delay_check_in > 300:
                return False
            else:
                if str(row[0]) == name:
                    print(f"\n[INFO]{name} have been checked-in recently!\n")
                    return True        
        return False 

    def delete_predictions(self):
        self.cursor.execute("DELETE FROM predictions")
        self.conn.commit()

    def limit_predictions(self, count):
        self.cursor.execute(f"DELETE FROM predictions limit {count}")
        self.conn.commit()

    def get_predictions(self, camID):
        predictions = []
        self.cursor.execute("SELECT * from predictions")
        rows = self.cursor.fetchall()
        for row in rows:
            predictions.append(str(row[camID]))

        return predictions

    def delete_tables(self):
        self.cursor.execute('DROP TABLE predictions')
        self.cursor.execute('DROP TABLE results')


if __name__ == "__main__":
    c = CheckinManager(DATABASE)
    c.delete_tables()
    c.create_table()
    c.close()