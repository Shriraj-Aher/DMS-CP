import os
from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'meow1234',
    'database': 'photos'
}

UPLOAD_FOLDER = 'static/images/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (username, password) VALUES (%s, %s)', (username, password))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username=%s AND password=%s', (username, password))
        account = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if account:
            session['loggedin'] = True
            session['id'] = account[0]
            return redirect(url_for('upload'))
    
    return render_template('login.html')
    
@app.route('/logout')
def logout():
    # Clear the session
    session.clear()  # This removes all data from the session
    return redirect(url_for('index'))  # Redirect to the homepage or login page

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'loggedin' in session:
        if request.method == 'POST':
            file = request.files['file']
            filename = secure_filename(file.filename)
            mimetype = file.mimetype
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute('INSERT INTO images (user_id, filename, mimetype) VALUES (%s, %s, %s)', 
                           (session['id'], filename, mimetype))
            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for('view_images'))
        
        return render_template('upload.html')
    
    return redirect(url_for('login'))

@app.route('/view_images')
def view_images():
    if 'loggedin' in session:
        try:
            # Establish a connection to the database
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()

            # Execute SQL query to fetch images for the logged-in user
            cursor.execute('SELECT * FROM images WHERE user_id=%s', (session['id'],))
            images = cursor.fetchall()  # Fetch all results

        except mysql.connector.Error as err:
            print(f"Error: {err}")
            images = []  # Set images to an empty list on error

        finally:
            # Ensure resources are cleaned up
            cursor.close()
            conn.close()

        return render_template('view_images.html', images=images)

    return redirect(url_for('login'))  # Redirect to login if not logged in

@app.route('/delete_image/<int:image_id>')
def delete_image(image_id):
    if 'loggedin' in session:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM images WHERE id=%s', (image_id,))
        conn.commit()
        cursor.close()
        conn.close()
        
        return redirect(url_for('view_images'))
    
    return redirect(url_for('login'))


if __name__ == "__main__":
    app.run(debug=True)