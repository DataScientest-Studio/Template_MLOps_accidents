import json
import os
from pathlib import Path


def create_users_db():

    users_db = {
        "fdo": {
            "username": "fdo",
            "password": "c0ps",
            "rights": 0
        },
        "admin": {
            "username": "admin",
            "password": "4dmin",
            "rights": 1
        },
        "policierA": {
            "username": "policierA",
            "password": "sherif",
            "rights": 0
        },
        "policierB": {
            "username": "policierB",
            "password": "colombo",
            "rights": 0
        }
    }

    root_path = Path(os.path.realpath(__file__)).parents[2]
    path_users_db = os.path.join(root_path, "src",
                                 "users_db",
                                 "users_db.json")

    users_db_json = json.dumps(users_db, indent=4)
    with open(path_users_db, "w") as outfile:
        outfile.write(users_db_json)


if __name__ == '__main__':
    create_users_db()
