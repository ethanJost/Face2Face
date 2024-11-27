# stored_procedures.py

import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="database"
    )

def insert_location(conn, name, description, address):
    cur = conn.cursor()
    cur.execute('INSERT INTO locations (name, description, address) VALUES (%s, %s, %s)',
                (name, description, address))
    location_id = cur.lastrowid
    cur.close()
    return location_id

def get_activity_by_name(conn, activity_name):
    cur = conn.cursor(dictionary=True)
    cur.execute('SELECT id FROM activities WHERE name = %s', (activity_name,))
    activity = cur.fetchone()
    cur.close()
    return activity

def insert_activity(conn, activity_name):
    cur = conn.cursor()
    cur.execute('INSERT INTO activities (name) VALUES (%s)', (activity_name,))
    activity_id = cur.lastrowid
    cur.close()
    return activity_id

def link_location_activity(conn, location_id, activity_id):
    cur = conn.cursor()
    cur.execute('INSERT INTO location_activities (location_id, activity_id) VALUES (%s, %s)',
                (location_id, activity_id))
    cur.close()

def get_all_activities(conn):
    cur = conn.cursor(dictionary=True)
    cur.execute('SELECT id, name FROM activities')
    activities = cur.fetchall()
    cur.close()
    return activities

def get_all_activities_linked(conn):
    cur = conn.cursor(dictionary=True)
    cur.execute('SELECT DISTINCT a.id, a.name FROM activities a INNER JOIN location_activities la ON a.id = la.activity_id')
    activities = cur.fetchall()
    cur.close()
    return activities


def get_location_by_id(conn, location_id):
    cur = conn.cursor(dictionary=True)
    cur.execute('SELECT * FROM locations WHERE id = %s', (location_id,))
    location = cur.fetchone()
    cur.close()
    return location

def get_activities_by_location(conn, location_id):
    cur = conn.cursor(dictionary=True)
    cur.execute('''
        SELECT a.name FROM activities a
        JOIN location_activities la ON a.id = la.activity_id
        WHERE la.location_id = %s
    ''', (location_id,))
    activities = [row['name'] for row in cur.fetchall()]
    cur.close()
    return activities

def get_all_locations_with_activities(conn):
    cur = conn.cursor(dictionary=True)
    cur.execute('''
        SELECT l.*, GROUP_CONCAT(a.name SEPARATOR ', ') AS activities
        FROM locations l
        LEFT JOIN location_activities la ON l.id = la.location_id
        LEFT JOIN activities a ON la.activity_id = a.id
        GROUP BY l.id
    ''')
    locations = cur.fetchall()
    cur.close()
    return locations

def update_location(conn, location_id, name, description, address):
    cur = conn.cursor()
    cur.execute('UPDATE locations SET name = %s, description = %s, address = %s WHERE id = %s',
                (name, description, address, location_id))
    cur.close()

def delete_location_activities(conn, location_id):
    cur = conn.cursor()
    cur.execute('DELETE FROM location_activities WHERE location_id = %s', (location_id,))
    cur.close()

def delete_location(conn, location_id):
    cur = conn.cursor()
    cur.execute('DELETE FROM locations WHERE id = %s', (location_id,))
    cur.close()

def get_locations_by_activity(conn, activity_id):
    cur = conn.cursor(dictionary=True)
    query = '''
    SELECT l.id, l.name, l.description, l.address,
           GROUP_CONCAT(DISTINCT a.name ORDER BY a.name SEPARATOR ', ') AS activities
    FROM locations l
    JOIN location_activities la ON l.id = la.location_id
    JOIN activities a ON la.activity_id = a.id
    WHERE l.id IN (
        SELECT location_id FROM location_activities WHERE activity_id = %s
    )
    GROUP BY l.id, l.name, l.description, l.address
    '''
    cur.execute(query, (activity_id,))
    locations = cur.fetchall()
    cur.close()
    return locations


