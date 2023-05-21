import sqlite3
from config import DATABASE_FILE


def create_filters_tables():
    create_filter_thresholds_table()
    create_species_overrides()


def create_filter_thresholds_table():
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute('''  
    CREATE TABLE IF NOT EXISTS filter_thresholds (  
        user_id INTEGER PRIMARY KEY,  
        ignore_threshold REAL NOT NULL,  
        log_threshold REAL NOT NULL,  
        recordalert_threshold REAL NOT NULL  
    );  
    ''')

    # Check if the default values have been set
    cursor.execute("SELECT COUNT(*) FROM filter_thresholds WHERE user_id = 0;")
    count = cursor.fetchone()[0]

    # If the default values haven't been set, insert them
    if count == 0:
        cursor.execute(
            "INSERT INTO filter_thresholds (user_id, ignore_threshold, log_threshold, recordalert_threshold) VALUES (0, 1, 1, 0);")

    connection.commit()
    connection.close()


def create_species_overrides():
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    # Create the species_overrides table
    cursor.execute("""  
    CREATE TABLE IF NOT EXISTS species_overrides (  
        id INTEGER PRIMARY KEY,  
        user_id INTEGER NOT NULL,  
        species_name TEXT NOT NULL,  
        override_type TEXT NOT NULL,  
        FOREIGN KEY (user_id) REFERENCES filter_thresholds(user_id),  
        UNIQUE(user_id, species_name)  
    );  
    """)

    connection.commit()
    connection.close()