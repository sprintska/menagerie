#!/usr/bin/python3

import json
import logging
import logging.handlers
import os
import pickle
import requests
import sqlite3
import shutil

from contextlib import closing

_handler = logging.handlers.WatchedFileHandler("/var/log/menagerie.log")
logging.basicConfig(handlers=[_handler], level=logging.INFO)

API_TARGET_URL = "http://www.dropzonecommander.com:3001/ships/"
LOCAL_MIRROR_PATH = os.path.join(os.getcwd(), "data", "ships.sqlite3")


def create_db(db_path=g_db_path):

    """Create the db at the path if it doesn't exist"""

    if not os.path.exists(db_path):
        with open(db_path, "w") as foo:
            logging.info(f"Created ships db at {db_path}.")

        with closing(sqlite3.connect(db_path)) as conn:
            success = conn.execute('''CREATE TABLE dropfleet_ships (
                _id             text,
                _rev            text,
                Name            text,
                Faction         text,
                Designation     text,
                Scan            text,
                Signal          text,
                Thrust          text,
                Hull            int,
                Armour          text,
                PointDefence    int,
                GroupMin        int,
                GroupMax        int,
                Tonnage         text,
                TonnageClass    int,
                Points          int,
                HardPoints      int,
                Special         text,
                Weapons         text,
                LaunchAssets    text,
                SpecRules       text,
                MinHardPoints   int,
                MaxBroadSides   int,
                icons           text
            )''')
            conn.commit()
    return success


def request_update(api_url):

    """Requests the updated set of ships from DZC.com and returns them as a giant ass nested dict."""

    with requests.get(api_url, stream=True) as r:
        ships = json.loads(r.raw)
    
    for ship in ships:
        ship['Weapons'] = pickle.dumps(ship['Weapons'])

    return ships


def update_db(ships_obj,db_path):

    """Updates the db with the new ships."""

    with closing(sqlite3.conntect(db_path)) as conn:
        for ship in ships_obj:
            out = conn.execute('''INSERT INTO dropfleet_ships VALUES (
                :_id,
                :_rev,
                :Name,
                :Faction,
                :Designation,
                :Scan,
                :Signal,
                :Thrust,
                :Hull,
                :Armour,
                :PointDefence,
                :GroupMin,
                :GroupMax,
                :Tonnage,
                :TonnageClass,
                :Points,
                :HardPoints,
                :Special,
                :Weapons,
                :LaunchAssets,
                :SpecRules,
                :MinHardPoints,
                :MaxBroadSides,
                :icons
            )''', ship)
            conn.commit()


def main(api_url,ship_db):

    create_db(ship_db)

    ships = request_update(api_url)

    update_db(ships,ship_db)