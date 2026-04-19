import sqlite3
import os

DB_NAME = 'aqi_assistant.db'
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

print("Recent 5 rows in aqi_history:")
cursor.execute('SELECT city, aqi, timestamp FROM aqi_history ORDER BY timestamp DESC LIMIT 5')
for row in cursor.fetchall():
    print(row)

print("\nRecent 5 subscriptions:")
cursor.execute('SELECT email, city FROM subscriptions LIMIT 5')
for row in cursor.fetchall():
    print(row)

conn.close()
