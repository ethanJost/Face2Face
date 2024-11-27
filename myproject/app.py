import mysql.connector
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask import Flask, render_template, request, redirect, url_for, flash, Blueprint
from werkzeug.exceptions import abort
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import CSRFProtect
from models import Session, Location, Activity, User
from forms import LoginForm, RegistrationForm, LocationForm, ReportForm
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
    insert_location,
    get_all_activities_linked
)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
csrf = CSRFProtect(app)

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute('SELECT * FROM users WHERE id = %s', (user_id,))
    user = cur.fetchone()
    conn.close()

    if user:
        return User(user['id'], user['username'], user['password_hash'])
    return None

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
    form = LocationForm()
    if form.validate_on_submit():
        name = form.name.data
        description = form.description.data
        address = form.address.data
        activities_string = form.activities.data
        activity_list = [a.strip() for a in activities_string.split(',') if a.strip()]

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
        flash('Location created successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('create.html', form=form)

@app.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    location = get_location(id)
    activities = ', '.join(location['activities'])
    form = LocationForm(
        name=location['name'],
        description=location['description'],
        address=location['address'],
        activities=activities
    )

    if form.validate_on_submit():
        name = form.name.data
        description = form.description.data
        address = form.address.data
        activities_string = form.activities.data
        activity_list = [a.strip() for a in activities_string.split(',') if a.strip()]

        conn = get_db_connection()
        update_location(conn, id, name, description, address)
        delete_location_activities(conn, id)
        for activity_name in activity_list:
            activity = get_activity_by_name(conn, activity_name)
            if activity:
                activity_id = activity['id']
            else:
                activity_id = insert_activity(conn, activity_name)
            link_location_activity(conn, id, activity_id)
        conn.commit()
        conn.close()
        flash('Location updated successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('edit.html', form=form)



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
    activities = get_all_activities_linked(conn)
    form = ReportForm()
    # Populate the activity choices
    form.activity.choices = [(str(activity['id']), activity['name']) for activity in activities]
    locations = []
    if form.validate_on_submit():
        selected_activity_id = int(form.activity.data)
        locations = get_locations_by_activity(conn, selected_activity_id)
        if not locations:
            flash('No locations found matching the selected activity.', 'warning')
    conn.close()
    return render_template('report.html', form=form, locations=locations)





@app.route('/profile')
def profile():
    return render_template('profile.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        remember = form.remember_me.data

        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            user_obj = User(user['id'], user['username'], user['password_hash'])
            login_user(user_obj, remember=remember)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        password_hash = generate_password_hash(password)

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute('INSERT INTO users (username, password_hash) VALUES (%s, %s)', (username, password_hash))
            conn.commit()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))
        except mysql.connector.IntegrityError:
            flash('Username already exists', 'danger')
        finally:
            cur.close()
            conn.close()

    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)
