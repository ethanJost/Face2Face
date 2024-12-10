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
    conn.rollback()
    conn.close()

    if user:
        return User(user['id'], user['username'], user['password_hash'])
    return None

def get_location(location_id):
    conn = get_db_connection()
    location = get_location_by_id(conn, location_id)
    if location is None:
        conn.rollback()
        conn.close()
        abort(404)
    location['activities'] = get_activities_by_location(conn, location_id)
    conn.rollback()
    conn.close()
    return location

@app.route('/')
def index():
    conn = get_db_connection()
    locations = get_all_locations_with_activities(conn)
    conn.rollback()
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
        activities_string = form.activities.data
        activity_list = [a.strip() for a in activities_string.split(',') if a.strip()]

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # Insert new location with no initial rating (defaults: num_ratings=0, avg_rating=0)
            cur.execute('INSERT INTO locations (name, description) VALUES (%s, %s)',
                        (name, description))
            location_id = cur.lastrowid

            for activity_name in activity_list:
                activity = get_activity_by_name(conn, activity_name)
                if activity:
                    activity_id = activity['id']
                else:
                    activity_id = insert_activity(conn, activity_name)
                link_location_activity(conn, location_id, activity_id)

            conn.commit()
        except:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

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
        rating=0,  # Placeholder, won't be used
        activities=activities
    )

    if form.validate_on_submit():
        conn = get_db_connection()
        try:
            name = form.name.data
            description = form.description.data
            activities_string = form.activities.data
            activity_list = [a.strip() for a in activities_string.split(',') if a.strip()]

            update_location(conn, id, name, description)  # Passing None for replaced address
            delete_location_activities(conn, id)
            for activity_name in activity_list:
                activity = get_activity_by_name(conn, activity_name)
                if activity:
                    activity_id = activity['id']
                else:
                    activity_id = insert_activity(conn, activity_name)
                link_location_activity(conn, id, activity_id)
            conn.commit()
        except:
            conn.rollback()
            raise
        finally:
            conn.close()

        flash('Location updated successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('edit.html', form=form, location_id=id)


@app.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    # Writing transaction
    conn = get_db_connection()
    try:
        location = get_location(id) 
        conn2 = get_db_connection()
        cur = conn2.cursor()
        # Delete activity associations
        cur.execute('DELETE FROM location_activities WHERE location_id = %s', (id,))
        # Delete the location
        cur.execute('DELETE FROM locations WHERE id = %s', (id,))
        conn2.commit()
        cur.close()
        conn2.close()
        flash(f'Location "{location["name"]}" was successfully deleted!', 'success')
    except:
        conn.rollback()
        raise
    finally:
        conn.close()
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
    # Read-only transaction
    conn.rollback()
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
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute('SELECT * FROM users WHERE username = %s', (form.username.data,))
        user = cur.fetchone()
        # No changes, just rollback
        conn.rollback()
        conn.close()
        if user and check_password_hash(user['password_hash'], form.password.data):
            user_obj = User(user['id'], user['username'], user['password_hash'])
            login_user(user_obj, remember=form.remember_me.data)
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
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute('INSERT INTO users (username, password_hash) VALUES (%s, %s)', 
                        (form.username.data, generate_password_hash(form.password.data)))
            conn.commit()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))
        except mysql.connector.IntegrityError:
            conn.rollback()
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

@app.route('/rate/<int:id>', methods=['POST'])
@login_required
def rate_location(id):
    new_rating = int(request.form.get('rating', 0))
    if new_rating < 1 or new_rating > 5:
        flash('Invalid rating. Must be between 1 and 5.', 'danger')
        return redirect(url_for('index'))

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        # Fetch current ratings info
        cur.execute('SELECT num_ratings, avg_rating FROM locations WHERE id = %s', (id,))
        loc = cur.fetchone()
        if not loc:
            conn.rollback()
            flash('Location not found.', 'danger')
            return redirect(url_for('index'))

        num = loc['num_ratings']
        avg = loc['avg_rating']

        # Compute new average
        new_num = num + 1
        new_avg = ((avg * num) + new_rating) / new_num

        cur.execute('UPDATE locations SET num_ratings = %s, avg_rating = %s WHERE id = %s', (new_num, new_avg, id))
        conn.commit()
        flash('Rating submitted successfully!', 'success')
    except:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)
