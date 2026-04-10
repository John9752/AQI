import sqlite3
import datetime

import os

DB_NAME = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'aqi_assistant.db')

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Table for hourly AQI trends
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS aqi_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT NOT NULL,
            aqi INTEGER NOT NULL,
            pm25 REAL,
            pm10 REAL,
            no2 REAL,
            co REAL,
            so2 REAL,
            o3 REAL,
            temperature REAL,
            humidity REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Table for user alert subscriptions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            city TEXT NOT NULL,
            threshold INTEGER DEFAULT 100,
            last_alert_sent DATETIME
        )
    ''')
    
    conn.commit()
    conn.close()

def save_aqi_reading(city, aqi, components):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO aqi_history (city, aqi, pm25, pm10, no2, co, so2, o3, temperature, humidity)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (city, aqi, components.get('pm2_5'), components.get('pm10'), 
          components.get('no2'), components.get('co'), components.get('so2'), components.get('o3'),
          components.get('temperature', 25.0), components.get('humidity', 50.0)))
    conn.commit()
    conn.close()

def get_aqi_trends(city, days=7):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Get data grouped by date (average AQI per day)
    cursor.execute('''
        SELECT DATE(timestamp) as date, AVG(aqi) as avg_aqi
        FROM aqi_history
        WHERE city = ? AND timestamp >= datetime('now', ?)
        GROUP BY DATE(timestamp)
        ORDER BY date ASC
    ''', (city, f'-{days} days'))
    
    results = cursor.fetchall()
    conn.close()
    return [{"date": row[0], "aqi": round(row[1], 2)} for row in results]

def get_subscriptions():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT email, city, threshold, last_alert_sent FROM subscriptions')
    subs = cursor.fetchall()
    conn.close()
    return subs

def add_subscription(email, city, threshold=101):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO subscriptions (email, city, threshold)
            VALUES (?, ?, ?)
        ''', (email, city, threshold))
        conn.commit()
        return True
    except Exception as e:
        print(f"DB Error: {e}")
        return False
    finally:
        conn.close()
def delete_subscription(email):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM subscriptions WHERE email = ?', (email,))
        conn.commit()
        return True
    except Exception as e:
        print(f"DB Error: {e}")
        return False
    finally:
        conn.close()
