# app.py
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd, csv, os, chardet, logging, gspread
from google.oauth2.service_account import Credentials
from logtail import LogtailHandler
from dotenv import load_dotenv
from college_predictor import list_of_colleges, category   # keep your other helpers

# ─── basic setup ───────────────────────────────────────────────────────────────
app     = Flask(__name__)
handler = LogtailHandler(source_token="NYbykzX5znjU3iRCvMaGX9ie")
logger  = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.handlers.clear()
logger.addHandler(handler)

load_dotenv()                                               # read .env

# ─── config helpers ────────────────────────────────────────────────────────────
BACKUP_CSV              = "leads_backup.csv"               # local sheet fallback
GOOGLE_SHEET_KEY        = "1x37iFC4Qg1l-voMcrxT5v71TxT9EXEoYIGIRy7RFU_k"
GOOGLE_SHEET_NAME       = "2025_data"
GOOGLE_CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), "credentials.json")


def choose_database_uri() -> str:
    """Return a valid MySQL URI if connection succeeds, otherwise raise."""
    mysql_uri = (
        f"mysql+mysqlconnector://{os.getenv('DB_USERNAME')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
    eng = create_engine(mysql_uri, connect_args={"connect_timeout": 5})
    with eng.connect() as conn:
        conn.execute(text("SELECT 1"))        # simple health-check
    logger.info("Connected to MySQL successfully.")
    return mysql_uri


# ─── SQLAlchemy optional setup ────────────────────────────────────────────────
DB_ENABLED = False
db         = None                              # placeholder, so name exists even if disabled

try:
    app.config["SQLALCHEMY_DATABASE_URI"] = choose_database_uri()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_recycle": 1800,
    }
    db = SQLAlchemy(app)
    DB_ENABLED = True
except Exception as e:
    logger.warning(f"SQL features disabled – database connection failed: {e}")

# ─── models (only if DB is available) ─────────────────────────────────────────
if DB_ENABLED:
    class Student(db.Model):
        __tablename__  = "students"
        id             = db.Column(db.Integer, primary_key=True, autoincrement=True)
        name           = db.Column(db.String(255))
        mobile_number  = db.Column(db.String(15))
        course         = db.Column(db.String(255))
        community      = db.Column(db.String(50))
        cutoff         = db.Column(db.Float)

    with app.app_context():
        db.create_all()
        logger.info("Database tables ensured / migrated.")
else:
    # dummy shim so type-checkers don't complain if needed elsewhere
    class Student:  # type: ignore
        pass

# ─── fall-back utilities ──────────────────────────────────────────────────────
def _append_to_local_csv(row):
    """Write a single row to the local backup CSV (create header if missing)."""
    file_exists = os.path.isfile(BACKUP_CSV)
    with open(BACKUP_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(("Name", "Mobile Number", "Course",
                             "Community", "Cutoff"))
        writer.writerow(row)
    logger.info("Saved lead to local CSV fallback.")

# ─── data-capture helpers ─────────────────────────────────────────────────────
def insert_data(name, mobile_number, course, community, cutoff):
    """
    Try DB first (if enabled).  On any failure or if DB is disabled,
    drop straight to CSV fallback.
    """
    if DB_ENABLED:
        try:
            duplicate = Student.query.filter_by(
                name=name,
                mobile_number=mobile_number,
                course=course,
                community=community,
                cutoff=cutoff
            ).first()
            if not duplicate:
                db.session.add(Student(
                    name=name,
                    mobile_number=mobile_number,
                    course=course,
                    community=community,
                    cutoff=cutoff
                ))
                db.session.commit()
                logger.info("Lead stored in DB.")
                return
            else:
                logger.info("Duplicate lead – skipped DB insert.")
                return
        except SQLAlchemyError as err:
            logger.error(f"DB error – switching to CSV backup: {err}")
            db.session.rollback()

    # Either DB disabled or errored out – use CSV
    _append_to_local_csv([name, mobile_number, course, community, cutoff])


def write_to_google_sheets(name, mobile_number, course, community, cutoff):
    """Attempt to push lead to Google Sheets; fallback to CSV if anything fails."""
    try:
        if not os.path.exists(GOOGLE_CREDENTIALS_PATH):
            raise FileNotFoundError("credentials.json not found")

        creds  = Credentials.from_service_account_file(
            GOOGLE_CREDENTIALS_PATH,
            scopes=["https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive"]
        )
        client = gspread.authorize(creds)
        sheet  = client.open_by_key(GOOGLE_SHEET_KEY)
        try:
            ws = sheet.worksheet(GOOGLE_SHEET_NAME)
        except gspread.exceptions.WorksheetNotFound:
            ws = sheet.add_worksheet(title=GOOGLE_SHEET_NAME, rows="1000", cols="10")

        if not ws.row_values(1):
            ws.update("A1:E1", [["Name", "Mobile Number", "Course",
                                 "Community", "Cutoff"]])
        ws.append_row([name, mobile_number, course, community, cutoff])
        logger.info("Lead stored in Google Sheet.")
    except Exception as e:
        logger.error(f"Google Sheets error – using file backup: {e}")
        _append_to_local_csv([name, mobile_number, course, community, cutoff])

# ─── misc helpers ─────────────────────────────────────────────────────────────
def read_csv_with_fallback(file_path):
    """Read CSV regardless of weird encodings; coerce cutoff columns to numeric."""
    with open(file_path, "rb") as f:
        encoding = chardet.detect(f.read())["encoding"]
    try:
        df = pd.read_csv(file_path, encoding=encoding)
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, encoding="utf-8", errors="ignore")

    df.fillna(0, inplace=True)
    for comm in ["OC", "BC", "BCM", "MBC", "SC", "SCA", "ST"]:
        if comm in df.columns:
            df[comm] = pd.to_numeric(df[comm], errors="coerce")
    return df

# ─── routes ───────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/results", methods=["POST"])
def results():
    try:
        name   = request.form["FullName"].strip()
        mobile = request.form["MobileNumber"].strip()
        course = request.form["course"].upper().strip()
        comm   = request.form["Community"].strip()
        cutoff = float(request.form["Cutoff"])

        if not all([name, mobile, course, comm]):
            return render_template("error.html",
                                   message="All fields are required.")
        if not (0 <= cutoff <= 200):
            return render_template("error.html",
                                   message="Cutoff must be between 0 and 200.")

        # store the lead
        insert_data(name, mobile, course, comm, cutoff)
        write_to_google_sheets(name, mobile, course, comm, cutoff)

        # predict colleges
        data  = read_csv_with_fallback("data_2024.csv")
        data["Normalized_Branch"] = data["Branch Name"].str.strip().str.upper()
        course_cat = [c.strip().upper() for c in category(course)]

        filt = data[
            data["Normalized_Branch"].isin(course_cat) &
            (data[comm] > 0) &
            (data[comm] <= cutoff + 5)
        ].sort_values(by=comm, ascending=False).drop(columns=["Normalized_Branch"])

        top  = data[
            data["Normalized_Branch"].isin(course_cat) &
            (data[comm] > 0)
        ].sort_values(by=comm, ascending=False).drop(columns=["Normalized_Branch"])

        return render_template(
            "results.html",
            filtered_colleges=filt[["College Code", "College Name", "Branch Code",
                                    "Branch Name", comm]].to_dict("records"),
            top_colleges=top[["College Code", "College Name", "Branch Code",
                              "Branch Name", comm]].head(20).to_dict("records"),
            caste=comm,
            count=len(filt),
            min_cutoff=filt[comm].min() if len(filt) else None,
            max_cutoff=filt[comm].max() if len(filt) else None,
            original_marks=cutoff,
            selected_community=comm,
            course=course
        )
    except Exception as e:
        logger.error(f"/results route error: {e}")
        return render_template("error.html",
                               message="Sorry, something went wrong.")


@app.route("/filter_colleges")
def filter_colleges():
    try:
        course = request.args.get("course", "").strip()
        if not course:
            return jsonify({"error": "Course parameter is required"}), 400

        comm   = request.args.get("caste", "OC").strip()
        try:
            marks = float(request.args.get("original_marks", 0))
        except ValueError:
            return jsonify({"error": "Invalid cutoff marks"}), 400

        data  = read_csv_with_fallback("data_2024.csv")
        data["Normalized_Branch"] = data["Branch Name"].str.strip().str.upper()
        course_set = [c.strip().upper() for c in category(course.upper())]

        filt = data[
            data["Normalized_Branch"].isin(course_set) &
            (data[comm] > 0) &
            (data[comm] <= marks + 5)
        ].sort_values(by=comm, ascending=False).drop(columns=["Normalized_Branch"])

        top  = data[
            data["Normalized_Branch"].isin(course_set) &
            (data[comm] > 0)
        ].sort_values(by=comm, ascending=False).drop(columns=["Normalized_Branch"])

        return jsonify({
            "filtered_colleges": filt[["College Code", "College Name",
                                       "Branch Code", "Branch Name", comm]
                                      ].to_dict("records"),
            "top_colleges": top[["College Code", "College Name",
                                 "Branch Code", "Branch Name", comm]
                                ].head(20).to_dict("records"),
            "count": len(filt),
            "caste": comm,
            "original_marks": marks
        })
    except Exception as e:
        logger.error(f"/filter_colleges error: {e}")
        return jsonify({"error": "Internal server error"}), 500

# ─── main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
