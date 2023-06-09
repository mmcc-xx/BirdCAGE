import sqlite3
from config import DATABASE_FILE


def create_commands_table():
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    # Create the commands table if it doesn't exist
    cursor.execute('''  
        CREATE TABLE IF NOT EXISTS commands (  
            id INTEGER PRIMARY KEY,  
            name TEXT UNIQUE NOT NULL,  
            value BOOLEAN NOT NULL  
        )  
    ''')

    # Check if the restart command already exists
    cursor.execute('SELECT * FROM commands WHERE name = ?', ('restart',))
    if cursor.fetchone() is None:
        # Insert the restart command with a value of False if it doesn't exist
        cursor.execute('INSERT INTO commands (name, value) VALUES (?, ?)', ('restart', False))

    connection.commit()
    connection.close()

    # reset restart command at startup
    reset_command('restart', False)


def check_command_value(command_name):
    connection = sqlite3.connect(DATABASE_FILE, timeout=20)
    cursor = connection.cursor()

    cursor.execute('SELECT value FROM commands WHERE name = ?', (command_name,))
    result = cursor.fetchone()

    connection.close()

    if result:
        return result[0]
    else:
        return None


def reset_command(command_name, value=False):
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute('UPDATE commands SET value = ? WHERE name = ?', (value, command_name))

    connection.commit()
    connection.close()


