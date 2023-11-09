import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

cred = credentials.Certificate("baigiamasisServiceKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://baigiamasis-darbas-cea75-default-rtdb.firebaseio.com/"
})

ref = db.reference('Students')

data = {
    "852741":
        {
            "name": "Emily Blunt",
            "major": "Software engineering",
            "group": "PI20A",
            "starting_year": 2019,
            "total_attendance": 7,
            "last_attendance_time": "2022-12-11 00:54:34"
        },
    "963852":
        {
            "name": "Elon Musk",
            "major": "Software engineering",
            "group": "PI20A",
            "starting_year": 2019,
            "total_attendance": 7,
            "year": 2,
            "last_attendance_time": "2022-12-11 00:54:34"
        },
     "795627":
        {
            "name": "John Krasinski",
            "major": "Software engineering",
            "group": "PI20A",
            "starting_year": 2019,
            "total_attendance": 7,
            "year": 2,
            "last_attendance_time": "2022-12-11 00:54:34"
        },
     "569894":
        {
            "name": "Mantas Vysniauskas",
            "major": "Software engineering",
            "group": "PI20A",
            "starting_year": 2019,
            "total_attendance": 7,
            "year": 2,
            "last_attendance_time": "2022-12-11 00:54:34"
        }
        
}

for key, value in data.items():
    ref.child(key).set(value)