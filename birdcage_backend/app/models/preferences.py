import sqlite3
from config import DATABASE_FILE


def create_preferences_table():
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute('''CREATE TABLE  IF NOT EXISTS user_preferences (  
                        id INTEGER PRIMARY KEY AUTOINCREMENT,  
                        user_id INTEGER NOT NULL,  
                        preference_key TEXT NOT NULL,  
                        preference_value TEXT NOT NULL,  
                        last_updated TIMESTAMP NOT NULL  
                        )''')

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
