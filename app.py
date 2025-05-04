import io
import os
import traceback
import pandas as pd
from flask import Flask, send_file, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

from data_merger.data_merger import data_merger
from data_cleaner.data_cleaner import data_cleaner

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

UPLOAD_FOLDER = 'uploads'
MERGED_FOLDER = 'merged_data'
ALLOWED_EXTENSIONS = {'excel': ['xlsx', 'xls', 'xlsm', 'xlsb']}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MERGED_FOLDER'] = MERGED_FOLDER

db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Create database tables
with app.app_context():
    db.create_all()

def allowed_file(filename, file_type):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS.get(file_type, [])

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        if not username or not password:
            flash('Please provide both username and password', 'error')
            return redirect(url_for('login'))

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session.permanent = remember
            flash('Login successful!', 'success')
            return redirect(url_for('data_upload'))
        else:
            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not username or not password or not email:
            flash('Please fill in all required fields', 'error')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('register'))

        existing_user = User.query.filter_by(username=username).first()
        existing_email = User.query.filter_by(email=email).first()

        if existing_user:
            flash('Username already exists', 'error')
            return redirect(url_for('register'))

        if existing_email:
            flash('Email already in use', 'error')
            return redirect(url_for('register'))

        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/data_upload', methods=['GET'])
def data_upload():
    if 'user_id' not in session:
        flash('Please login first', 'error')
        return redirect(url_for('login'))
    return render_template('data_upload.html')

@app.route('/upload_files', methods=['POST'])
def upload_files():
    if 'user_id' not in session:
        flash('Please login first', 'error')
        return redirect(url_for('login'))

    uploaded_files = []
    error_messages = []

    if 'excel_file_1' not in request.files or not request.files['excel_file_1'].filename:
        error_messages.append("First Excel file is required")
    else:
        excel_file_1 = request.files['excel_file_1']
        if allowed_file(excel_file_1.filename, 'excel'):
            filename_1 = secure_filename(excel_file_1.filename)
            uploaded_files.append(f"Excel 1: {filename_1}")
        else:
            error_messages.append("Invalid format for first Excel file. Only .xlsx files are allowed.")

    if 'excel_file_2' not in request.files or not request.files['excel_file_2'].filename:
        error_messages.append("Second Excel file is required")
    else:
        excel_file_2 = request.files['excel_file_2']
        if allowed_file(excel_file_2.filename, 'excel'):
            filename_2 = secure_filename(excel_file_2.filename)
            uploaded_files.append(f"Excel 2: {filename_2}")
        else:
            error_messages.append("Invalid format for second Excel file. Only .xlsx files are allowed.")

    if len(uploaded_files) == 2 and not error_messages:
        try:
            print("Starting data cleaning and merging")
            d_clean = data_cleaner(excel_file_1, excel_file_2)
            d1, d2 = d_clean.data_cleaner_fun()

            um_data = data_merger(d1, d2)
            m_data = um_data.data_merger_to_one()

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                m_data.to_excel(writer, index=False)
            output.seek(0)

            upload_to_blob(output.getvalue(), "merged_data.xlsx")

            session['merged_ready'] = True
            flash("Files merged successfully! You can now go to dashboard or download the file.", "success")
            return redirect(url_for('data_upload'))

        except Exception as e:
            print(" ERROR DURING MERGE:")
            traceback.print_exc()
            error_messages.append(f"Error in data merging process: {str(e)}")

    if not uploaded_files and not error_messages:
        flash('No files selected for upload', 'info')
    elif error_messages:
        for error in error_messages:
            flash(error, 'error')

    return redirect(url_for('data_upload'))

@app.route('/download_merged_file')
def download_merged_file():
    if 'user_id' not in session:
        flash('Please login first', 'error')
        return redirect(url_for('login'))

    try:
        connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        container_name = os.getenv("AZURE_BLOB_CONTAINER")
        blob_name = "merged_data.xlsx"

        blob_service = BlobServiceClient.from_connection_string(connection_string)
        blob_client = blob_service.get_blob_client(container=container_name, blob=blob_name)
        blob_data = blob_client.download_blob().readall()

        return send_file(
            io.BytesIO(blob_data),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=blob_name
        )
    except Exception as e:
        print("ERROR DURING FILE DOWNLOAD:")
        traceback.print_exc()
        flash(f"Error downloading file: {str(e)}", 'error')
        return redirect(url_for('data_upload'))

@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        return redirect("https://your-streamlit-app.azurewebsites.net")  # Replace with real dashboard URL
    else:
        flash("Session expired. Please login again.", "error")
        return redirect(url_for('login'))

def upload_to_blob(file_bytes, blob_name):
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    container_name = os.getenv("AZURE_BLOB_CONTAINER")

    blob_service = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service.get_container_client(container_name)

    try:
        container_client.create_container()
    except Exception:
        pass  # Container already exists

    container_client.upload_blob(name=blob_name, data=file_bytes, overwrite=True)
    print(f"Uploaded {blob_name} to Azure Blob Storage.")

if __name__ == '__main__':
    app.run(debug=True)
