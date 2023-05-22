from config import DATABASE_FILE
from app.views.filters import get_birds_of_the_week, get_thresholds, get_overrides
import sqlite3
import json


def create_birdsoftheweek_table():
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS birdsoftheweek (  
                      id INTEGER PRIMARY KEY, 
                      scientific_name TEXT NOT NULL,
                      common_name TEXT NOT NULL,
                      occurrence FLOAT NOT NULL
                      )''')

    connection.commit()
    connection.close()


def update_birdsoftheweek_table():

    # Fetch data using get_birds_of_the_week()
    birds_of_the_week = get_birds_of_the_week()

    if birds_of_the_week:
        connection = sqlite3.connect(DATABASE_FILE)
        cursor = connection.cursor()

        # Delete all data from the table
        cursor.execute("DELETE FROM birdsoftheweek")

        # Insert new data into the table
        for bird in birds_of_the_week:
            scientific_name, common_name = bird[0].split('_')
            occurrence = bird[1]
            cursor.execute("INSERT INTO birdsoftheweek (scientific_name, common_name, occurrence) VALUES (?, ?, ?)",
                           (scientific_name, common_name, occurrence))

        connection.commit()
        connection.close()


def get_birdsoftheweek():
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute("SELECT scientific_name, common_name, occurrence FROM birdsoftheweek")
    rows = cursor.fetchall()

    birds_data = {}
    for row in rows:
        scientific_name, common_name, occurrence = row
        birds_data[scientific_name] = {
            "common_name": common_name,
            "occurrence": occurrence
        }

    connection.close()

    return birds_data


def get_thresholds_dict():
    thresholds_jsonify = get_thresholds(0)

    # Convert the jsonify object to a JSON string
    thresholds_json_str = thresholds_jsonify.get_data(as_text=True)

    # Parse the JSON string to a Python dictionary
    thresholds_dict = json.loads(thresholds_json_str)

    return thresholds_dict


def get_overrides_dict():
    overrides_jsonify = get_overrides(0)
    overrides_json_str = overrides_jsonify.get_data(as_text=True)
    overrides_list = json.loads(overrides_json_str)
    overrides_dict = {"ignore": [], "log": [], "record": [], "alert": []}

    for override in overrides_list:
        override_type = override["override_type"]
        species_name = override["species_name"]
        overrides_dict[override_type].append(species_name)

    return overrides_dict


def getaction(species):
    # For a given species scientific name, this function will return the action to perform
    # based on app configuration: ignore, log, record, or alert
    overrides = get_overrides_dict()
    thresholds = get_thresholds_dict()
    birdsoftheweek = get_birdsoftheweek()

    # Check for species in overrides
    if species in overrides['ignore']:
        return 'ignore'
    elif species in overrides['log']:
        return 'log'
    elif species in overrides['record']:
        return 'record'
    elif species in overrides['alert']:
        return 'alert'

        # If species not in overrides, get its occurrence
    occurrence = birdsoftheweek.get(species, {}).get('occurrence', None)

    # If there's no occurrence value, return 'alert'
    if occurrence is None:
        return 'alert'

        # Compare occurrence with thresholds
    if occurrence >= thresholds['ignore_threshold']:
        return 'ignore'
    elif occurrence >= thresholds['log_threshold']:
        return 'log'
    elif occurrence >= thresholds['recordalert_threshold']:
        return 'record'
    else:
        return 'alert'


if __name__ == '__main__':

    # some testing logic for the filter stuff
    from app import create_app
    app = create_app(init_celery=False)

    with app.app_context():
        create_birdsoftheweek_table()
        update_birdsoftheweek_table()
        print("Zenaida macroura: " + getaction('Zenaida macroura'))
        print("Dumetella carolinensis: " + getaction('Dumetella carolinensis'))
        print("Sturnus vulgaris: " + getaction('Sturnus vulgaris'))
        print("Contopus virens: " + getaction('Contopus virens'))