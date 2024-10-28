import mysql.connector

connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="database"
)

cur = connection.cursor()

with open('schema.sql') as f:
    sql_commands = f.read().split(';')  # Split the file content by semicolon to handle multiple queries
    for command in sql_commands:
        if command.strip():  # Skip empty commands
            cur.execute(command)

cur = connection.cursor()

cur.execute("INSERT INTO locations (name, description, address) VALUES (%s, %s, %s)",
            ('First Location', 'Description of the first location', 'Address of the First Location')
            )

cur.execute("INSERT INTO locations (name, description, address) VALUES (%s, %s, %s)",
            ('Second Location', 'Description of the second location', 'address of the Second location')
            )

connection.commit()
connection.close()