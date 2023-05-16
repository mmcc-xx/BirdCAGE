import sqlite3
from config import DATABASE_FILE


def create_streams_table():
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS streams (  
                      id INTEGER PRIMARY KEY,  
                      name TEXT NOT NULL UNIQUE,  
                      address TEXT NOT NULL,  
                      protocol TEXT NOT NULL,  
                      transport TEXT)''')

    connection.commit()
    connection.close()
