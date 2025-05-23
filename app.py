from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd
import chardet
from college_predictor import list_of_colleges, category
from dotenv import load_dotenv
import os
from logtail import LogtailHandler
import logging
import gspread
from google.oauth2.service_account import Credentials

# Initialize Flask application
app = Flask(__name__)

# Logging setup
handler = LogtailHandler(source_token="NYbykzX5znjU3iRCvMaGX9ie")
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.handlers = []
logger.addHandler(handler)

# Load environment variables
load_dotenv()

# MySQL configuration
db_config = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
    'user': os.getenv('DB_USERNAME'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}

# Google Sheets configuration
google_sheet_key = '1x37iFC4Qg1l-voMcrxT5v71TxT9EXEoYIGIRy7RFU_k'
google_sheet_name = '2025_data'
google_credentials_path = os.path.join(os.path.dirname(__file__), 'credentials.json')

# Set default SQL config
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+mysqlconnector://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,
    'max_overflow': 20,
    'pool_timeout': 120,
    'pool_recycle': 1800
}

# Initialize SQLAlchemy
try:
    db = SQLAlchemy(app)
except Exception as e:
    db = None
    logger.error(f"Failed to initialize database: {e}")

# Define the Student model
class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255))
    mobile_number = db.Column(db.String(15))
    course = db.Column(db.String(255))
    community = db.Column(db.String(50))
    cutoff = db.Column(db.Float)

# Create the table if db is available
if db:
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            logger.error(f"Error creating tables: {e}")

def insert_data(name, mobile_number, course, community, cutoff):
    if not db:
        logger.warning("DB not initialized; skipping insert.")
        return
    try:
        existing_record = Student.query.filter_by(
            name=name,
            mobile_number=mobile_number,
            course=course,
            community=community,
            cutoff=cutoff
        ).first()
        if not existing_record:
            new_student = Student(name=name, mobile_number=mobile_number, course=course, community=community, cutoff=cutoff)
            db.session.add(new_student)
            db.session.commit()
    except SQLAlchemyError as err:
        logger.error(f"MySQL Error: {err}")
        db.session.rollback()

def write_to_google_sheets(name, mobile_number, course, community, cutoff):
    try:
        logger.info("Starting Google Sheets write process.")
        if not os.path.exists(google_credentials_path):
            logger.error(f"Google credentials file not found: {google_credentials_path}")
            return

        creds = Credentials.from_service_account_file(google_credentials_path, scopes=[
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ])
        client = gspread.authorize(creds)
        sheet = client.open_by_key(google_sheet_key)
        worksheet = sheet.worksheet(google_sheet_name)

        expected_headers = ['Name', 'Mobile Number', 'Course', 'Community', 'Cutoff']
        headers = worksheet.row_values(1)
        if headers != expected_headers:
            worksheet.update('A1:E1', [expected_headers])
        worksheet.append_row([name, mobile_number, course, community, cutoff])
        logger.info("Google Sheets write successful.")

    except Exception as e:
        logger.error(f"Google Sheets Error: {e}")

def read_csv_with_fallback(file_path):
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    encoding = result['encoding']
    try:
        data = pd.read_csv(file_path, encoding=encoding)
    except UnicodeDecodeError:
        data = pd.read_csv(file_path, encoding='utf-8', errors='ignore')

    data.fillna(0, inplace=True)
    for community in ['OC', 'BC', 'BCM', 'MBC', 'SC', 'SCA', 'ST']:
        if community in data.columns:
            data[community] = pd.to_numeric(data[community], errors='coerce')
    return data

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/results', methods=['POST'])
def results():
    name = request.form['FullName']
    mobile_number = request.form['MobileNumber']
    course = request.form['course']
    community = request.form['Community']
    cutoff_str = request.form['Cutoff']

    try:
        cutoff = float(cutoff_str)
    except ValueError:
        return render_template('error.html', message="Invalid cutoff value. Please enter a valid number.")

    insert_data(name, mobile_number, course, community, cutoff)
    write_to_google_sheets(name, mobile_number, course, community, cutoff)

    data = read_csv_with_fallback('ogdatanew.csv')
    filtered_colleges = list_of_colleges(cutoff, course, community, data)
    filtered_colleges = filtered_colleges[filtered_colleges[community] > 0]
    count = len(filtered_colleges)
    min_cutoff = filtered_colleges[community].min() if count else None
    max_cutoff = filtered_colleges[community].max() if count else None

    top_colleges_all = data[['College Code', 'College Name', 'Branch Name', 'Branch Code', community]]
    top_colleges_all = top_colleges_all[top_colleges_all[community] > 0].sort_values(by=community, ascending=False)
    top_colleges_course = top_colleges_all[top_colleges_all['Branch Name'].isin(category(course))]

    return render_template('results.html',
        filtered_colleges=filtered_colleges.to_dict(orient='records'),
        top_colleges=top_colleges_course.to_dict(orient='records'),
        caste=community,
        count=count,
        min_cutoff=min_cutoff,
        max_cutoff=max_cutoff,
        original_marks=cutoff,
        selected_community=community
    )

@app.route('/filter_colleges')
def filter_colleges():
    course = request.args.get('course')
    community = request.args.get('caste', 'OC')
    original_marks = float(request.args.get('original_marks', 0))

    data = read_csv_with_fallback('2024data.csv')
    course_final = category(course)
    filtered_colleges = data[data['Branch Name'].isin(course_final) & (data[community] <= (original_marks + 5))]
    filtered_colleges = filtered_colleges[filtered_colleges[community] > 0]

    min_cutoff = filtered_colleges[community].min() if not filtered_colleges.empty else None
    max_cutoff = filtered_colleges[community].max() if not filtered_colleges.empty else None

    top_colleges_all = data[['College Code', 'College Name', 'Branch Name', 'Branch Code', community]]
    top_colleges_all = top_colleges_all[top_colleges_all[community] > 0].sort_values(by=community, ascending=False)
    top_colleges_course = top_colleges_all[top_colleges_all['Branch Name'].isin(course_final)]

    return jsonify({
        "filtered_colleges": filtered_colleges.to_dict(orient='records'),
        "top_colleges": top_colleges_course.to_dict(orient='records'),
        "count": len(filtered_colleges),
        "caste": community,
        "original_marks": original_marks,
        "min_cutoff": min_cutoff,
        "max_cutoff": max_cutoff
    })

if __name__ == '__main__':
    logger.info("App is running on port 5000.")
    app.run(debug=True, port=5000, host="0.0.0.0")
