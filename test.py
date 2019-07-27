import csv 
from datetime import datetime

with open('check_in_results.csv','r') as csv_file:
    csv_reader = csv.reader(csv_file)
    for i,row in enumerate(csv_reader[-10:]):
        time
        

