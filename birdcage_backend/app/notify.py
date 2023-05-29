from config import DATABASE_FILE
import sqlite3
import apprise


def geturls(detectionaction):
    # Connect to the database
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    # Execute the SQL query to get the URLs
    cursor.execute('''  
            SELECT ns.service_url  
            FROM notification_assignments na  
            JOIN notification_services ns ON na.notification_service = ns.service_name  
            WHERE na.detectionaction = ?  
        ''', (detectionaction,))

    # Fetch all matching rows
    results = cursor.fetchall()

    # Close the connection
    conn.close()

    # Extract the URLs from the results
    urls = [row[0] for row in results]

    return urls


def notify(detectionaction, timestamp, stream_id, streamname, scientific_name, common_name,
                           confidence_score, mp3path):

    urls = geturls(detectionaction)

    # Create an Apprise instance
    apobj = apprise.Apprise()

    # Add each URL to the Apprise object
    for url in urls:
        apobj.add(url)

    title = detectionaction + " level bird: " + common_name
    body = "Common Name: " + common_name + "\n" + \
           "Scientific Name: " + scientific_name + "\n" + \
           "Confidence Score: " + str(confidence_score) + "\n" + \
           "Stream Name: " + streamname + "\n" + \
           "Time: " + timestamp

    #print(title, flush=True)
    #print(body, flush=True)
    print("Notifying", flush=True)

    if mp3path == '':
        apobj.notify(title=title, body=body)
    else:
        apobj.notify(title=title, body=body, attach=mp3path)
