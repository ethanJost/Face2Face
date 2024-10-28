import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.exceptions import abort

# Function to get the MySQL connection
def get_db_connection():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="database" 
    )
    return conn

def get_location(location_id):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute('SELECT * FROM locations WHERE id = %s', (location_id,))
    location = cur.fetchone()
    cur.close()
    conn.close()
    if location is None:
        abort(404)
    return location

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

@app.route('/')
def index():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute('SELECT * FROM locations')
    locations = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', locations=locations)

@app.route('/<int:location_id>')
def location(location_id):
    location = get_location(location_id)
    return render_template('post.html', location=location)

@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        address = request.form['address']
        activites_string = request.form['activities']
        activity_list = activites_string.split(', ')

        if not name:
            flash('Name is required!')
        else:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('INSERT INTO locations (name, description, address) VALUES (%s, %s, %s)', 
                        (name, description, address))
            for activity in activity_list:
                cur.execute('SELECT id FROM activities WHERE name = %s', (activity,))
                activity_exists = cur.fetchone()
                if not activity_exists:
                    cur.execute('INSERT INTO activities (name) VALUES (%s)', 
                            (activity,))
                    
            conn.commit()
            cur.close()
            conn.close()
            return redirect(url_for('index'))
    return render_template('create.html')


@app.route('/<int:id>/edit', methods=('GET', 'POST'))
def edit(id):
    location = get_location(id)

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']

        if not name:
            flash('Name is required!')
        else:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('UPDATE locations SET name = %s, description = %s WHERE id = %s',
                        (name, description, id))
            conn.commit()
            cur.close()
            conn.close()
            return redirect(url_for('index'))
    return render_template('edit.html', location=location)

# ....

@app.route('/<int:id>/delete', methods=('POST',))
def delete(id):
    location = get_location(id)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM locations WHERE id = %s', (id,))
    conn.commit()
    cur.close()
    conn.close()
    if 'name' in location:
        flash('"{}" was successfully deleted!'.format(location['name']))
    else:
        flash('The location was successfully deleted!')
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)
