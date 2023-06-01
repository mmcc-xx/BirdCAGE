import sqlite3
import bcrypt
from config import DATABASE_FILE


def create_preferences_table():
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute('''CREATE TABLE  IF NOT EXISTS user_preferences (    
                        id INTEGER PRIMARY KEY AUTOINCREMENT,    
                        user_id INTEGER NOT NULL,    
                        preference_key TEXT NOT NULL,    
                        preference_value TEXT NOT NULL,    
                        last_updated TIMESTAMP NOT NULL,
                        UNIQUE (user_id, preference_key) 
                        )''')

    password = 'birdcage'
    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    default_preferences = [
        ('recordinglength', '15'),
        ('confidence', '0.7'),
        ('extractionlength', '6'),
        ('latitude', '39.0473'),
        ('longitude', '-95.6752'),
        ('overlap', '0'),
        ('sensitivity', '1'),
        ('sf_thresh', '0.03'),
        ('password', hashed_password),
        ('locale', 'en'),
        ('recordingretention', '0'),
        ('mqttbroker', ''),
        ('mqttport', '1883'),
        ('mqttuser', ''),
        ('mqttpassword', ''),
        ('mqttrecordings', 'false')
    ]

    for key, value in default_preferences:
        cursor.execute('''INSERT OR IGNORE INTO user_preferences (user_id, preference_key, preference_value, last_updated)   
                          VALUES (?, ?, ?, datetime('now'))''', (0, key, value))

    connection.commit()
    connection.close()


def get_user_preference(user_id, preference_key):
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute('SELECT preference_value FROM user_preferences WHERE user_id = ? AND preference_key = ?',
                   (user_id, preference_key))
    result = cursor.fetchone()

    connection.close()

    # Return the preference value if found, otherwise return None
    return result[0] if result else None


def get_all_user_preferences(user_id):
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute('SELECT preference_key, preference_value FROM user_preferences WHERE user_id = ?',
                   str(user_id))
    result = cursor.fetchall()

    connection.close()

    # Convert the result to a dictionary
    preferences = {row[0]: row[1] for row in result} if result else None

    return preferences


def check_password(password_input):
    # Retrieve the hashed password from the database
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()
    cursor.execute("SELECT preference_value FROM user_preferences WHERE user_id = ? AND preference_key = ?",
                   (0, 'password'))
    stored_hashed_password = cursor.fetchone()[0]
    connection.close()

    # Verify the input password against the stored hashed password
    return bcrypt.checkpw(password_input.encode(), stored_hashed_password.encode())