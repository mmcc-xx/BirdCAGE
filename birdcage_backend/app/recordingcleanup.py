from config import DETECTION_DIR_NAME
from config import DATABASE_FILE
import sqlite3
import os
import datetime


def recordingcleanup(numdays):

    # 0 means keep forever
    if numdays <= 0:
        return

    # Calculate the timestamp limit
    timestamp_limit = datetime.datetime.now() - datetime.timedelta(days=numdays)

    # Set the value of DETECTION_DIR
    basedir = os.path.dirname(os.path.abspath(__file__))
    DETECTION_DIR = os.path.join(basedir, '..', DETECTION_DIR_NAME)

    # Connect to the database
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    # Retrieve records older than numdays
    cursor.execute("SELECT id, filename FROM detections WHERE timestamp < ? AND LENGTH(filename) > 0 AND (id, filename) NOT IN (SELECT id, filename FROM (SELECT id, filename, max(confidence) FROM detections WHERE LENGTH(filename)> 0 GROUP BY scientific_name))", (timestamp_limit,))
    records = cursor.fetchall()

    # Iterate through records
    for record in records:
        record_id, filename = record

        # Delete the file
        try:
            file_path = os.path.join(DETECTION_DIR, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Deleted file: {file_path}")
            else:
                print(f"File not found: {file_path}")

                # Update the record in the database
            cursor.execute("UPDATE detections SET filename = '' WHERE id = ?", (record_id,))
            print(f"Updated record id: {record_id}")

        except Exception as e:
            print(f"Error processing record id {record_id}: {e}")

            # Commit the changes and close the connection
    conn.commit()
    conn.close()

if __name__ == '__main__':
    recordingcleanup(3)