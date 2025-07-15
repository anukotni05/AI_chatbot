
import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
import google.generativeai as genai
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from docx import Document
from fpdf import FPDF
import json
import io

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configure Gemini API
genai.configure(api_key="AIzaSyDKLN6IxEzHkuuFIkMYsLwSifbEgtUzoNo")
model = genai.GenerativeModel('gemini-2.5-pro')

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'docx', 'csv', 'xlsx', 'json', 'xml', 'html', 'md'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_file_content(filepath):
    ext = filepath.rsplit('.', 1)[1].lower()
    try:
        if ext in ['txt', 'md', 'html', 'xml']:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        elif ext == 'csv':
            import pandas as pd
            return pd.read_csv(filepath).to_string()
        elif ext == 'xlsx':
            import pandas as pd
            return pd.read_excel(filepath).to_string()
        elif ext == 'pdf':
            from PyPDF2 import PdfReader
            reader = PdfReader(filepath)
            return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        elif ext == 'docx':
            from docx import Document
            doc = Document(filepath)
            return "\n".join([p.text for p in doc.paragraphs])
        elif ext == 'json':
            import json
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.dumps(json.load(f), indent=2)
        else:
            return "Unsupported file format."
    except Exception as e:
        return f"Error reading file: {str(e)}"
    past_chats = get_last_n_chats(session['user'], 5)
    context = "\n".join([f"Q: {q}\nA: {a}" for q, a in past_chats])
    full_prompt = f"{context}\nCurrent Prompt: {prompt}"

def init_db():
    os.makedirs('db', exist_ok=True)
    conn = sqlite3.connect('db/users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY AUTOINCREMENT, user_email TEXT, prompt TEXT, response TEXT, timestamp TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS feedback (id INTEGER PRIMARY KEY AUTOINCREMENT, user_email TEXT, prompt TEXT, rating TEXT, timestamp TEXT)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return redirect(url_for('login'))
@app.route('/download_response')
def download_response():
    content = request.args.get('text', '')
    format = request.args.get('format', 'txt')
    buffer, filename = save_text_to_format(content, format)
    if buffer:
        return send_file(buffer, as_attachment=True, download_name=filename)
    return "Invalid format", 400

@app.route('/convert_file', methods=['POST'])
def convert_file():
    file = request.files.get('file')
    to_format = request.form.get('to_format')
    if not file or not to_format:
        return jsonify({"error": "Missing file or format"})
    content = file.read().decode('utf-8')
    buffer, filename = save_text_to_format(content, to_format)
    if buffer:
        return send_file(buffer, as_attachment=True, download_name=filename)
    return jsonify({"error": "Conversion failed"})

@app.route('/rate_response', methods=['POST'])
def rate_response():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    rating = data.get('rating')
    prompt = data.get('prompt')
    if rating and prompt:
        conn = sqlite3.connect('db/users.db')
        c = conn.cursor()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute('''INSERT INTO feedback (user_email, prompt, rating, timestamp) VALUES (?, ?, ?, ?)''', (session['user'], prompt, rating, timestamp))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Thanks for your feedback!'}), 200
    return jsonify({'error': 'Invalid data'}), 400

@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=30)
@app.route('/upload-photo', methods=['POST'])
def upload_photo():
    if 'photo' in request.files:
        file = request.files['photo']
        file.save(f'static/profile_{session["user"]}.jpg')
    return redirect(url_for('profile'))


@app.route('/delete-account', methods=['POST'])
def delete_account():
    email = session['user']
    conn = sqlite3.connect('db/users.db')
    c = conn.cursor()
    c.execute('DELETE FROM users WHERE email = ?', (email,))
    conn.commit()
    conn.close()
    session.clear()
    return redirect(url_for('register'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = sqlite3.connect('db/users.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password))
        user = c.fetchone()
        conn.close()
        if user:
            session['user'] = email
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = sqlite3.connect('db/users.db')
        c = conn.cursor()
        try:
            c.execute('INSERT INTO users (email, password) VALUES (?, ?)', (email, password))
            conn.commit()
        except sqlite3.IntegrityError:
            return render_template('register.html', error="Email already exists")
        conn.close()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', email=session['user'])

@app.route('/ask', methods=['POST'])
def ask():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    prompt = data.get('prompt')
    mode = data.get('mode')

    if not prompt:
        return jsonify({'error': 'Empty prompt'}), 400

    full_prompt = f"Mode: {mode}\nPrompt: {prompt}"

    try:
        response = model.generate_content(full_prompt)

        conn = sqlite3.connect('db/users.db')
        c = conn.cursor()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute('''
            INSERT INTO history (user_email, prompt, response, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (session['user'], prompt, response.text, timestamp))
        conn.commit()
        conn.close()

        return jsonify({'response': response.text})

    except Exception as e:
        print("Gemini API error:", e)
        return jsonify({'error': 'Something went wrong with Gemini API'}), 500

@app.route('/upload', methods=['POST'])
def upload():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    file = request.files.get('file')
    if not file or file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if allowed_file(file.filename):
        filename = secure_filename(file.filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        try:
            file_text = extract_file_content(file_path)
        except Exception as e:
            return jsonify({'error': f"Could not extract file content: {e}"}), 500

        return jsonify({'message': 'File uploaded successfully', 'content': file_text})
    else:
        return jsonify({'error': 'Invalid file type'}), 400

@app.route('/profile')
def profile():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('profile.html', email=session['user'])

@app.route('/change-password', methods=['POST'])
def change_password():
    if 'user' not in session:
        return redirect(url_for('login'))

    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if new_password != confirm_password:
        return "Passwords do not match", 400

    conn = sqlite3.connect('db/users.db')
    c = conn.cursor()
    c.execute('UPDATE users SET password = ? WHERE email = ?', (new_password, session['user']))
    conn.commit()
    conn.close()

    return redirect(url_for('profile'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/history')
def get_history():
    if 'user' not in session:
        return jsonify({'history': []})

    conn = sqlite3.connect('db/users.db')
    c = conn.cursor()
    c.execute('SELECT prompt, response, timestamp FROM history WHERE user_email = ? ORDER BY id DESC', (session['user'],))
    rows = c.fetchall()
    conn.close()
    history = [{'prompt': r[0], 'response': r[1], 'timestamp': r[2]} for r in rows]
    return jsonify({'history': history})

@app.route('/clear_history', methods=['POST'])
def clear_history():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    conn = sqlite3.connect('db/users.db')
    c = conn.cursor()
    c.execute('DELETE FROM history WHERE user_email = ?', (session['user'],))
    conn.commit()
    conn.close()

    return jsonify({'message': 'History cleared successfully'})

if __name__ == '__main__':
    app.run(debug=True)







