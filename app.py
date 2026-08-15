import os
from datetime import datetime
from flask import Flask, request, render_template, session, url_for, redirect, flash
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import sqlite3

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')

mail = Mail(app)

def get_db_connection():
    connection = sqlite3.connect('hotel.db')
    connection.row_factory = sqlite3.Row
    return connection

@app.route('/')
def home():
    if session.get('role') == 'admin':
        return render_template('admin_home.html')
    return render_template('home.html')

@app.route('/rooms')
def room_list():
    if not is_logged_in():
        return redirect(url_for('login'))
    if session.get('role') == 'admin':
        return redirect(url_for('admin_dashboard'))

    selected_type = request.args.get('typeName')

    connection = get_db_connection()
    if selected_type:
        rooms = connection.execute('SELECT * FROM rooms WHERE typeName = ?', (selected_type,)).fetchall()
    else:
        rooms = connection.execute('SELECT * FROM rooms').fetchall()
    connection.close()

    return render_template('rooms.html', rooms=rooms, selected_type=selected_type)

@app.route('/rooms/<room_number>')
def room_detail(room_number):
    if not is_logged_in():
        return redirect(url_for('login'))
    if session.get('role') == 'admin':
        return redirect(url_for('admin_dashboard'))

    connection = get_db_connection()
    room = connection.execute('SELECT * FROM rooms WHERE roomNumber = ?', (room_number,)).fetchone()
    connection.close()

    if room is None:
        return "Room not found", 404

    return render_template('room_detail.html', room=room, message=None)

@app.route('/book/<room_number>', methods=['POST'])
def book_room(room_number):
    if not is_logged_in():
        return redirect(url_for('login'))
    if session.get('role') == 'admin':
        return redirect(url_for('admin_dashboard'))

    guest_name = session['username']
    connection = get_db_connection()
    room = connection.execute('SELECT * FROM rooms WHERE roomNumber = ?', (room_number,)).fetchone()

    if room is None:
        connection.close()
        return "Room not found", 404

    result = connection.execute(
        'UPDATE rooms SET isAvailable = 0 WHERE roomNumber = ? AND isAvailable = 1',
        (room_number,)
    )

    if result.rowcount == 0:
        connection.close()
        return render_template('room_detail.html', room=room, message="Booking failed: room not available")

    connection.execute(
    'INSERT INTO bookings (roomNumber, guestName, email, bookingDate, status) VALUES (?, ?, ?, ?, ?)',
    (room_number, guest_name, session['email'], datetime.now().strftime('%Y-%m-%d'), "active")
    )
    connection.commit()
    connection.close()

    try:
        msg = Message(
            subject="Booking Confirmation",
            sender=app.config['MAIL_USERNAME'],
            recipients=[session['email']],
            body=f"Hi {guest_name}, your booking for Room {room_number} is confirmed!"
        )
        mail.send(msg)
    except Exception as e:
        print("Email failed to send:", e)
        
    flash("Booking confirmed!")
    return redirect(url_for('room_list'))

@app.route('/bookings')
def bookings_list():
    if not is_logged_in():
        return redirect(url_for('login'))

    connection = get_db_connection()
    my_bookings = connection.execute(
        'SELECT * FROM bookings WHERE guestName = ? AND status = ?',
        (session['username'], "active")
    ).fetchall()
    connection.close()

    return render_template('bookings.html', bookings=my_bookings)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            return render_template('register.html', error="Passwords do not match")
        if not username or username.strip() == "":
            return render_template('register.html', error="Username cannot be empty")
        if not password or len(password) < 8:
            return render_template('register.html', error="Password must be at least 8 characters")
        if not any(c.isupper() for c in password):
            return render_template('register.html', error="Password must contain an uppercase letter")
        if not any(c.islower() for c in password):
            return render_template('register.html', error="Password must contain a lowercase letter")
        if not any(c.isdigit() for c in password):
            return render_template('register.html', error="Password must contain a number")

        password_hash = generate_password_hash(password)
        connection = get_db_connection()

        existing_username = connection.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
        if existing_username:
            connection.close()
            return render_template('register.html', error="Username already taken")

        existing_email = connection.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
        if existing_email:
            connection.close()
            return render_template('register.html', error="Email already registered")

        try:
            connection.execute(
                'INSERT INTO users (username, email, passwordHash, role) VALUES (?, ?, ?, ?)',
                (username, email, password_hash, "guest")
            )
            connection.commit()
        except sqlite3.IntegrityError:
            connection.close()
            return render_template('register.html', error="Registration failed")
        connection.close()

        return redirect(url_for('login'))

    return render_template('register.html', error=None)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        connection = get_db_connection()
        user = connection.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        connection.close()

        if user is None:
            return render_template('login.html', error="Incorrect email or password")

        if not check_password_hash(user['passwordHash'], password):
            return render_template('login.html', error="Incorrect email or password")

        username = user['username']
        session['username'] = username
        session['email'] = user['email']
        session['role'] = user['role']

        if user['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('room_list'))

    return render_template('login.html', error=None)    

def is_logged_in():
    return 'username' in session

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    connection = get_db_connection()
    all_bookings = connection.execute('SELECT * FROM bookings').fetchall()
    total_bookings = connection.execute('SELECT COUNT(*) as total FROM bookings').fetchone()
    most_booked = connection.execute('''
        SELECT roomNumber, COUNT(*) as bookingCount 
        FROM bookings 
        GROUP BY roomNumber 
        ORDER BY bookingCount DESC 
        LIMIT 1
    ''').fetchone()
    all_rooms = connection.execute('SELECT * FROM rooms').fetchall()
    connection.close()

    return render_template('admin.html', bookings=all_bookings, total=total_bookings['total'], most_booked=most_booked, rooms=all_rooms)

@app.route('/admin/free/<room_number>', methods=['POST'])
def free_room(room_number):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    connection = get_db_connection()
    connection.execute('UPDATE rooms SET isAvailable = 1 WHERE roomNumber = ?', (room_number,))
    connection.commit()
    connection.close()

    flash("Room freed up")
    return redirect(url_for('admin_dashboard'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template('500.html'), 500

@app.route('/cancel/<int:booking_id>', methods=['POST'])
def cancel_booking(booking_id):
    if not is_logged_in():
        return redirect(url_for('login'))

    connection = get_db_connection()
    booking = connection.execute('SELECT * FROM bookings WHERE id = ?', (booking_id,)).fetchone()

    if booking is None:
        connection.close()
        return "Booking not found", 404

    if booking['email'] != session['email']:
        connection.close()
        return "You can't cancel this booking", 403

    connection.execute('UPDATE rooms SET isAvailable = 1 WHERE roomNumber = ?', (booking['roomNumber'],))
    connection.execute('UPDATE bookings SET status = ? WHERE id = ?', ("cancelled", booking_id))
    connection.commit()
    connection.close()

    flash("Booking cancelled")
    return redirect(url_for('bookings_list'))

@app.route('/admin/book/<room_number>', methods=['POST'])
def admin_book_room(room_number):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    guest_email = request.form.get('guest_email')
    guest_username = request.form.get('guest_username')
    connection = get_db_connection()

    guest = connection.execute('SELECT * FROM users WHERE email = ?', (guest_email,)).fetchone()

    if guest is None:
        if not guest_username or guest_username.strip() == "":
            connection.close()
            flash("New guest needs a username")
            return redirect(url_for('admin_dashboard'))

        temp_password_hash = generate_password_hash("ChangeMe123")
        connection.execute(
            'INSERT INTO users (username, email, passwordHash, role) VALUES (?, ?, ?, ?)',
            (guest_username, guest_email, temp_password_hash, "guest")
        )
        connection.commit()
        guest = connection.execute('SELECT * FROM users WHERE email = ?', (guest_email,)).fetchone()

    result = connection.execute(
        'UPDATE rooms SET isAvailable = 0 WHERE roomNumber = ? AND isAvailable = 1',
        (room_number,)
    )

    if result.rowcount == 0:
        connection.close()
        flash("Room not available")
        return redirect(url_for('admin_dashboard'))

    connection.execute(
        'INSERT INTO bookings (roomNumber, guestName, email, bookingDate, status) VALUES (?, ?, ?, ?, ?)',
        (room_number, guest['username'], guest['email'], datetime.now().strftime('%Y-%m-%d'), "active")
    )
    connection.commit()
    connection.close()

    flash(f"Booked room {room_number} for {guest['username']}")
    return redirect(url_for('admin_dashboard'))




if __name__ == '__main__':
    app.run(debug=True)

