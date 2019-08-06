import sqlite3
from datetime import datetime
import json

DATABASE = '/home/baohoang235/face-check-in/database.db'

class CheckinManager(object):
    def __init__(self, database, cameraNum):
        self.conn = None
        self.cursor = None
        self.cameraNum = cameraNum

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
                "camID" INT NOT NULL,\
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


    def add_prediction(self,prediction, camID):
        predictions_list = self.get_predictions(camID)
        predictions_list.append(prediction)
        self.update_predictions(predictions_list, camID)

    def update_predictions(self, list_predictions, camID):
        task = {"prediction": list_predictions}
        self.cursor.execute("UPDATE predictions SET pred=? WHERE camID=?", (str(task),camID))        
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

    def get_predictions(self,camID):
        predictions = []
        self.cursor.execute("SELECT * from predictions WHERE camID=?",(camID,))
        row = self.cursor.fetchone()
        if row is not None:
            predictions = json.loads(row[1].replace('\'','\"'))["prediction"]
            return predictions
        return None

    def delete_tables(self):
        self.cursor.execute('DROP TABLE predictions')   
        self.cursor.execute('DROP TABLE results')


if __name__ == "__main__":
    c = CheckinManager(DATABASE,2)
    c.delete_tables()
    c.create_table()
    # task = {"prediction": []}
    # c.cursor.execute("INSERT INTO predictions(pred,camID) VALUES(?,?)", (str(task),0))
    # c.conn.commit()
    # task = {"prediction": []}
    # c.cursor.execute("INSERT INTO predictions(pred,camID) VALUES(?,?)", (str(task),2))
    # c.conn.commit()

    # c.update_predictions(["hoang_gia_bao", "nguyen_phuong_nam"],0)
    # c.update_predictions(["hoang_gia_bao", "nguyen_hong_son"],2)    

    # print(c.get_predictions(0))
    # print(c.get_predictions(2))
    c.close()