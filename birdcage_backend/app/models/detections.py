import sqlite3
from config import DATABASE_FILE


def create_detections_table():
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS detections (  
                      id INTEGER PRIMARY KEY,  
                      timestamp TIMESTAMP NOT NULL,  
                      stream_id INTEGER NOT NULL,  
                      streamname TEXT NOT NULL,  
                      scientific_name TEXT NOT NULL,  
                      common_name TEXT NOT NULL,  
                      confidence FLOAT NOT NULL,  
                      filename TEXT NOT NULL  
                      )''')

    cursor.execute('''CREATE VIEW IF NOT EXISTS daily_detections AS  
                      SELECT  
                          date(timestamp) AS date,  
                          common_name,  
                          COUNT(*) AS count  
                      FROM  
                          detections  
                      GROUP BY  
                          date(timestamp), common_name;''')

    connection.commit()
    connection.close()


def add_detection(timestamp, stream_id, streamname, scientific_name, common_name, confidence, filename):
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute('''  
        INSERT INTO detections (timestamp, stream_id, streamname, scientific_name, common_name, confidence, filename)  
        VALUES (?, ?, ?, ?, ?, ?, ?)  
    ''', (timestamp, stream_id, streamname, scientific_name, common_name, confidence, filename))

    connection.commit()
    connection.close()

