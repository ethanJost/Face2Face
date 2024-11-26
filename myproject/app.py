import mysql.connector
from flask_login import LoginManager
from flask import Flask, render_template, request, redirect, url_for, flash, Blueprint
from werkzeug.exceptions import abort
from models import Session, Location, Activity
from stored_procedures import (
    get_db_connection,
    get_location_by_id,
    get_activities_by_location,
    get_all_locations_with_activities,
    get_all_activities,
    get_locations_by_activity,
    update_location,
    delete_location_activities,
    get_activity_by_name,
    insert_activity,
    link_location_activity,
    insert_location
)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

def get_location(location_id):
    conn = get_db_connection()
    location = get_location_by_id(conn, location_id)
    if location is None:
        conn.close()
        abort(404)
    # Fetch the associated activities
    location['activities'] = get_activities_by_location(conn, location_id)
    conn.close()
    return location

@app.route('/')
def index():
    conn = get_db_connection()
    locations = get_all_locations_with_activities(conn)
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
        activities_string = request.form['activities']
        activity_list = [a.strip() for a in activities_string.split(',') if a.strip()]

        if not name:
            flash('Name is required!')
        else:
            session = Session()
            location = Location(name=name, description=description, address=address)
            for activity_name in activity_list:
                activity = session.query(Activity).filter_by(name=activity_name).first()
                if not activity:
                    activity = Activity(name=activity_name)
                location.activities.append(activity)
            session.add(location)
            session.commit()
            session.close()
            return redirect(url_for('index'))
    return render_template('create.html')


@app.route('/<int:id>/edit', methods=('GET', 'POST'))
def edit(id):
    location = get_location(id)

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        address = request.form['address']
        activities_string = request.form['activities']
        activity_list = [a.strip() for a in activities_string.split(',') if a.strip()]

        if not name:
            flash('Name is required!')
        else:
            conn = get_db_connection()
            update_location(conn, id, name, description, address)
            # Delete existing activity associations
            delete_location_activities(conn, id)
            # Update the activities
            for activity_name in activity_list:
                # Check if the activity exists
                activity = get_activity_by_name(conn, activity_name)
                if activity:
                    activity_id = activity['id']
                else:
                    # Insert new activity
                    activity_id = insert_activity(conn, activity_name)
                # Link the activity with the location
                link_location_activity(conn, id, activity_id)
            conn.commit()
            conn.close()
            return redirect(url_for('index'))
    else:
        # Fetch all activities for the form
        conn = get_db_connection()
        all_activities = get_all_activities(conn)
        conn.close()
        return render_template('edit.html', location=location, all_activities=all_activities)
    return render_template('edit.html', location=location)


@app.route('/<int:id>/delete', methods=('POST',))
def delete(id):
    location = get_location(id)
    conn = get_db_connection()
    cur = conn.cursor()
    # Delete activity associations
    cur.execute('DELETE FROM location_activities WHERE location_id = %s', (id,))
    # Delete the location
    cur.execute('DELETE FROM locations WHERE id = %s', (id,))
    conn.commit()
    cur.close()
    conn.close()
    if 'name' in location:
        flash(f'"{location["name"]}" was successfully deleted!')
    else:
        flash('The location was successfully deleted!')
    return redirect(url_for('index'))

@app.route('/report', methods=('GET', 'POST'))
def report():
    conn = get_db_connection()
    activities = get_all_activities(conn)
    locations = []
    if request.method == 'POST':
        selected_activity_id = request.form.get('activity')
        print('Selected Activity ID:', selected_activity_id)  # Debugging statement
        if selected_activity_id:
            try:
                selected_activity_id = int(selected_activity_id)
                locations = get_locations_by_activity(conn, selected_activity_id)
                if not locations:
                    flash('No locations found matching the selected activity.')
            except ValueError:
                flash('Invalid activity selected.')
        else:
            flash('Please select an activity.')
    conn.close()
    return render_template('report.html', locations=locations, activities=activities)


@app.route('/profile')
def profile():
    return render_template('profile.html')

@login_manager.user_loader
def load_user(user_id):
    session = Session()
    user = session.query(User).get(int(user_id))
    session.close()
    return user

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        session = Session()

        if session.query(User).filter_by(username=username).first():
            flash('Username already exists.')
            session.close()
            return redirect(url_for('register'))

        new_user = User(username=username)
        new_user.set_password(password)
        session.add(new_user)
        session.commit()
        session.close()
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        session = Session()
        user = session.query(User).filter_by(username=username).first()
        session.close()

        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Invalid username or password.')
            return redirect(url_for('login'))

    return render_template('login.html')


if __name__ == "__main__":
    app.run(debug=True)
