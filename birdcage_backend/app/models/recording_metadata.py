import sqlite3
from config import DATABASE_FILE


def create_recording_metadata_table():
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS recording_metadata (  
                      id INTEGER PRIMARY KEY,  
                      filename TEXT NOT NULL UNIQUE,  
                      stream_id INTEGER NOT NULL,  
                      streamname TEXT NOT NULL,  
                      timestamp TIMESTAMP NOT NULL)''')

    connection.commit()
    connection.close()


def get_metadata_by_filename(filename):
    connection = sqlite3.connect(DATABASE_FILE, timeout=20)
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM recording_metadata WHERE filename = ?", (filename,))
    result = cursor.fetchone()

    connection.close()

    if result:
        metadata = {
            "id": result[0],
            "filename": result[1],
            "stream_id": result[2],
            "streamname": result[3],
            "timestamp": result[4],
        }
        return metadata
    else:
        return None


def delete_metadata_by_filename(filename):
    with sqlite3.connect(DATABASE_FILE, timeout=20) as connection:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM recording_metadata WHERE filename = ?", (filename,))
    connection.close()


def set_metadata(filename, stream_id, streamname, timestamp):
    with sqlite3.connect(DATABASE_FILE, timeout=20) as connection:
        cursor = connection.cursor()
        cursor.execute('''INSERT INTO recording_metadata (filename, stream_id, streamname, timestamp)    
                          VALUES (?, ?, ?, ?)''', (filename, stream_id, streamname, timestamp))
    connection.close()