import sqlite3
import os

try:  # db_config is imported before app.py loads .env, so load it here too
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
from pathlib import Path

# SQLite database path. Serverless hosts (Vercel) only allow writes under /tmp, so use it there.
_APP_DIR = Path(__file__).parent
if os.environ.get('SQLITE_DIR'):
    DB_DIR = Path(os.environ['SQLITE_DIR'])
elif os.environ.get('VERCEL') or not os.access(_APP_DIR, os.W_OK):
    DB_DIR = Path('/tmp')
else:
    DB_DIR = _APP_DIR
DB_NAME = os.environ.get('SQLITE_DATABASE', 'unicounsel_db.sqlite')
DB_PATH = DB_DIR / DB_NAME


# ── TiDB / MySQL backend ─────────────────────────────────────────────────────────────────────────────────────────
# Used when DATABASE_URL (mysql://user:pass@host:4000/unicounsel) or TIDB_HOST/TIDB_USER/TIDB_PASSWORD are set.
# The rest of the app keeps writing SQLite-style SQL; this layer translates it and returns sqlite3.Row-like rows.
import re
import threading
from urllib.parse import urlparse, unquote


def _mysql_settings():
    url = os.environ.get('DATABASE_URL', '')
    if url.startswith(('mysql://', 'mysql+pymysql://')):
        u = urlparse(url.replace('mysql+pymysql://', 'mysql://'))
        return {'host': u.hostname, 'port': u.port or 3306, 'user': unquote(u.username or ''),
                'password': unquote(u.password or ''), 'database': (u.path or '/').lstrip('/') or 'unicounsel'}
    if os.environ.get('TIDB_HOST'):
        return {'host': os.environ['TIDB_HOST'], 'port': int(os.environ.get('TIDB_PORT', '4000')),
                'user': os.environ['TIDB_USER'], 'password': os.environ['TIDB_PASSWORD'],
                'database': os.environ.get('TIDB_DATABASE', 'unicounsel')}
    return None


MYSQL = _mysql_settings()
USING_MYSQL = MYSQL is not None


class Row(dict):
    """Like sqlite3.Row: row['name'], row[0], iteration over values, dict(row), row.keys()."""

    def __init__(self, cols, values):
        super().__init__(zip(cols, values))
        self._values = tuple(values)

    def __getitem__(self, key):
        return self._values[key] if isinstance(key, int) else super().__getitem__(key)

    def __iter__(self):
        return iter(self._values)


_AUTOINC = re.compile(r'INTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT', re.I)


def _translate(sql, has_params):
    s = _AUTOINC.sub('INT PRIMARY KEY AUTO_INCREMENT', sql)
    s = re.sub(r'INSERT\s+OR\s+IGNORE\s+INTO', 'INSERT IGNORE INTO', s, flags=re.I)
    s = re.sub(r'INSERT\s+OR\s+REPLACE\s+INTO', 'REPLACE INTO', s, flags=re.I)
    s = re.sub(r"datetime\('now'\)", 'NOW()', s, flags=re.I)
    if has_params:  # pymysql formats with %, so literal % must be doubled and ? becomes %s
        s = s.replace('%', '%%').replace('?', '%s')
    return s


class _Cursor:
    def __init__(self, raw):
        self._raw = raw
        self._rows = []
        self.lastrowid = None
        self.rowcount = -1
        self.description = None

    def execute(self, sql, params=None):
        if re.match(r'\s*PRAGMA', sql, re.I):
            self._rows = []
            return self
        params = tuple(params) if params is not None else None
        self._raw.execute(_translate(sql, params is not None), params)
        self.lastrowid, self.rowcount, self.description = self._raw.lastrowid, self._raw.rowcount, self._raw.description
        cols = [d[0] for d in (self.description or [])]
        self._rows = [Row(cols, r) for r in self._raw.fetchall()] if cols else []
        return self

    def executemany(self, sql, seq):
        self._raw.executemany(_translate(sql, True), [tuple(x) for x in seq])
        self.rowcount = self._raw.rowcount
        return self

    def fetchone(self):
        return self._rows.pop(0) if self._rows else None

    def fetchall(self):
        rows, self._rows = self._rows, []
        return rows

    def fetchmany(self, size=1):
        rows, self._rows = self._rows[:size], self._rows[size:]
        return rows

    def __iter__(self):
        return iter(self.fetchall())

    def close(self):
        self._raw.close()


class _Connection:
    row_factory = None  # accepted and ignored: rows are always Row

    def __init__(self, raw):
        self._raw = raw

    def cursor(self):
        return _Cursor(self._raw.cursor())

    def execute(self, sql, params=None):
        return self.cursor().execute(sql, params)

    def commit(self):
        self._raw.commit()

    def rollback(self):
        self._raw.rollback()

    def close(self):
        # keep the TLS connection for the next request on this thread; drop anything left uncommitted
        try:
            self._raw.rollback()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        (self.rollback if exc_type else self.commit)()


_local = threading.local()


def _mysql_connection():
    import certifi
    import pymysql
    conn = getattr(_local, 'conn', None)
    if conn is not None:
        try:
            conn._raw.ping(reconnect=True)
            return conn
        except Exception:
            _local.conn = None
    raw = pymysql.connect(host=MYSQL['host'], port=MYSQL['port'], user=MYSQL['user'], password=MYSQL['password'],
                          database=MYSQL['database'], charset='utf8mb4', autocommit=False, connect_timeout=15,
                          ssl={'ca': certifi.where()})
    _local.conn = _Connection(raw)
    return _local.conn

def get_db_connection():
    """Get the database connection (TiDB/MySQL when configured, otherwise SQLite) with CSV fallback support"""
    try:
        if USING_MYSQL:
            return _mysql_connection()
        # Ensure directory exists
        DB_DIR.mkdir(parents=True, exist_ok=True)
        
        connection = sqlite3.connect(str(DB_PATH))
        connection.row_factory = sqlite3.Row  # Enable dictionary-like access
        return connection
    except Exception as e:
        print(f"Error while connecting to SQLite: {e}")
        print("Will fallback to CSV data when needed")
        return None

def get_db_connection_safe():
    """Get database connection or use CSV fallback"""
    conn = get_db_connection()
    if conn is None:
        print("Database unavailable - using CSV fallback")
    return conn

def create_database():
    """Create the database file if it doesn't exist"""
    try:
        DB_DIR.mkdir(parents=True, exist_ok=True)
        # SQLite creates the file automatically on first connection
        conn = get_db_connection()
        if conn:
            conn.close()
            print(f"Database '{DB_PATH}' created or already exists")
    except Exception as e:
        print(f"Error creating database: {e}")
        raise

def create_tables():
    """Create all required tables"""
    connection = get_db_connection()
    if not connection:
        print("Failed to connect to database. Cannot create tables.")
        print("Please check database file permissions.")
        return
    
    cursor = connection.cursor()
    
    # Users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email VARCHAR(255) UNIQUE NOT NULL,
        username VARCHAR(100),
        password_hash VARCHAR(255),
        first_name VARCHAR(100),
        last_name VARCHAR(100),
        is_oauth_user BOOLEAN DEFAULT 0,
        oauth_provider VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Universities table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS universities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        university_id VARCHAR(50),
        university_name VARCHAR(255),
        official_website VARCHAR(500),
        email_inquiry VARCHAR(255),
        phone_number VARCHAR(50),
        address TEXT,
        country VARCHAR(100),
        state VARCHAR(100),
        city VARCHAR(100),
        zip_code VARCHAR(20),
        latitude REAL,
        longitude REAL,
        campus_type VARCHAR(50),
        established VARCHAR(20),
        duration_undergraduation_course VARCHAR(50),
        duration_postgraduation_course VARCHAR(50),
        duration_phd_course VARCHAR(50),
        duration_diploma_course VARCHAR(50),
        duration_online_course VARCHAR(50),
        admission_req TEXT,
        cgpa VARCHAR(20),
        ielts VARCHAR(20),
        sat_gre_gmat VARCHAR(50),
        deadline_sem1 VARCHAR(100),
        academic_calendar VARCHAR(50),
        medium VARCHAR(50),
        tuition_fee_annual VARCHAR(50),
        living_cost_annual VARCHAR(50),
        total_estimated_cost VARCHAR(50),
        scholarships TEXT,
        intl_services TEXT,
        accommodation TEXT,
        airport_pickup VARCHAR(20),
        pre_arrival TEXT,
        documents_required TEXT,
        image_url VARCHAR(500),
        program_level VARCHAR(50),
        course TEXT
    )
    ''')
    
    # Create indexes
    try:
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_country ON universities(country)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_city ON universities(city)')
    except Exception as e:
        print(f'Index creation warning: {e}')
    
    # Onboarding responses table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS onboarding_responses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        question_1_preferred_countries TEXT,
        question_2_study_level VARCHAR(100),
        question_3_preferred_stream VARCHAR(255),
        question_4_duration_years INTEGER,
        question_5_budget_min REAL,
        question_5_budget_max REAL,
        question_6_important_factors TEXT,
        question_7_admission_readiness VARCHAR(100),
        question_8_language_proficiency VARCHAR(100),
        question_9_campus_life VARCHAR(100),
        question_10_special_interests TEXT,
        question_11_scholarship_need BOOLEAN,
        question_12_start_date VARCHAR(50),
        completed BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    ''')
    
    # University matches table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS university_matches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        university_id INTEGER NOT NULL,
        match_score REAL,
        match_reason TEXT,
        is_favorite BOOLEAN DEFAULT 0,
        is_shortlisted BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (university_id) REFERENCES universities(id) ON DELETE CASCADE,
        UNIQUE(user_id, university_id)
    )
    ''')
    
    # User preferences table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_preferences (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL UNIQUE,
        filter_countries TEXT,
        filter_budget_min REAL,
        filter_budget_max REAL,
        filter_study_level VARCHAR(100),
        filter_accommodation_type VARCHAR(100),
        filter_scholarship_required BOOLEAN,
        sort_by VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    ''')
    
    # User favorites table - stores favorite universities
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_favorites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        university_id_str VARCHAR(100) NOT NULL,
        university_name VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        UNIQUE(user_id, university_id_str)
    )
    ''')
    
    # Fee comparisons table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS fee_comparisons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        university_ids TEXT NOT NULL,
        comparison_data TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    ''')
    
    # Visa assessments table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS visa_assessments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        country VARCHAR(100),
        visa_type VARCHAR(100),
        probability_score REAL,
        assessment_data TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    ''')
    
    # Resume templates table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS resume_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        template_name VARCHAR(255) NOT NULL,
        template_description TEXT,
        template_html TEXT,
        template_css TEXT,
        preview_image VARCHAR(500),
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # User resumes table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_resumes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        template_id INTEGER,
        resume_data TEXT NOT NULL,
        resume_title VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (template_id) REFERENCES resume_templates(id)
    )
    ''')
    
    # User documents table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        document_type VARCHAR(100),
        document_name VARCHAR(255),
        file_path VARCHAR(500),
        file_size INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    ''')
    
    # Interview responses table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS interview_responses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        question_id INTEGER,
        response_text TEXT,
        score INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    ''')
    
    connection.commit()
    cursor.close()
    connection.close()
    print("All tables created successfully")
