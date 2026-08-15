import sqlite3
from werkzeug.security import generate_password_hash

connection = sqlite3.connect('hotel.db')
cursor = connection.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS rooms (
        roomNumber TEXT PRIMARY KEY,
        typeName TEXT,
        pricePerNight INTEGER,
        capacity INTEGER,
        isAvailable INTEGER
    )
''')

rooms_data = [
    ("101", "Single", 50, 1, 1),
    ("102", "Double", 80, 2, 1),
    ("201", "Suite", 150, 4, 1),
]

cursor.executemany('''
    INSERT OR IGNORE INTO rooms (roomNumber, typeName, pricePerNight, capacity, isAvailable)
    VALUES (?, ?, ?, ?, ?)
''', rooms_data)

cursor.execute('''
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        roomNumber TEXT,
        guestName TEXT,
        email TEXT,
        bookingDate TEXT,
        status TEXT
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        email TEXT UNIQUE,
        passwordHash TEXT,
        role TEXT
    )
''')

admin_password_hash = generate_password_hash("AdminPass123")
cursor.execute('''
    INSERT OR IGNORE INTO users (username, email, passwordHash, role)
    VALUES (?, ?, ?, ?)
''', ("admin", "admin@hotel.com", admin_password_hash, "admin"))

    

connection.commit()
connection.close()
print("Database set up successfully")