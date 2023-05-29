import sqlite3
from config import DATABASE_FILE


def create_notification_services_table():
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute('''CREATE TABLE  IF NOT EXISTS notification_services (    
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        service_name TEXT NOT NULL UNIQUE,    
                        service_url TEXT NOT NULL 
                        )''')

    # Insert default services with empty URLs
    default_services = [('Service 1', ''), ('Service 2', ''), ('Service 3', '')]

    for service in default_services:
        cursor.execute('''INSERT OR IGNORE INTO notification_services (service_name, service_url)  
                          VALUES (?, ?)''', service)

    connection.commit()
    connection.close()


def create_notification_assignments_table():
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute('''CREATE TABLE  IF NOT EXISTS notification_assignments (    
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        detectionaction TEXT NOT NULL,    
                        notification_service TEXT NOT NULL 
                        )''')

    connection.commit()
    connection.close()
