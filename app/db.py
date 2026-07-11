from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "db.sqlite3"

SCHEMA = """
CREATE TABLE IF NOT EXISTS patients (
  patient_id TEXT PRIMARY KEY,
  first_name TEXT,
  last_name TEXT,
  sex TEXT,
  birth_date TEXT
);

CREATE TABLE IF NOT EXISTS records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_row INTEGER UNIQUE,
  patient_id TEXT NOT NULL,
  service_date TEXT,
  approval_date TEXT,
  exam_code TEXT,
  exam_name TEXT,
  report TEXT,
  history TEXT,
  complaints TEXT,
  clinical_findings TEXT,
  recommendations TEXT,
  disease_info TEXT,
  treatment TEXT,
  lab_notes TEXT,
  discharge_meds TEXT,
  occupational TEXT,
  admission_reason TEXT,
  diagnosis TEXT,
  diagnostic_procedures TEXT,
  imported_at TEXT,
  FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
);

CREATE INDEX IF NOT EXISTS idx_records_patient ON records(patient_id);
CREATE INDEX IF NOT EXISTS idx_records_service_date ON records(service_date);
CREATE INDEX IF NOT EXISTS idx_records_exam_code ON records(exam_code);
CREATE INDEX IF NOT EXISTS idx_patients_name ON patients(last_name, first_name);

CREATE TABLE IF NOT EXISTS dicom_patient_links (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT NOT NULL,
  ref TEXT NOT NULL,
  patient_id TEXT NOT NULL,
  confidence INTEGER,
  note TEXT,
  confirmed_at TEXT,
  UNIQUE(source, ref),
  FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
);

CREATE INDEX IF NOT EXISTS idx_links_patient ON dicom_patient_links(patient_id);

CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('admin', 'reviewer', 'annotator')),
  display_name TEXT,
  email TEXT,
  is_active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT,
  last_login_at TEXT,
  totp_secret TEXT,
  totp_enrolled INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS annotation_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT NOT NULL,
  ref TEXT NOT NULL,
  annotation_id TEXT NOT NULL,
  action TEXT NOT NULL,
  username TEXT,
  ts TEXT NOT NULL,
  prev_snapshot TEXT,
  new_snapshot TEXT
);

CREATE INDEX IF NOT EXISTS idx_history_ann ON annotation_history(source, ref, annotation_id);
CREATE INDEX IF NOT EXISTS idx_history_ts ON annotation_history(ts);

CREATE TABLE IF NOT EXISTS notifications (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  recipient TEXT NOT NULL,
  ts TEXT NOT NULL,
  read_at TEXT,
  kind TEXT NOT NULL,
  title TEXT,
  body TEXT,
  link_source TEXT,
  link_ref TEXT,
  link_annotation_id TEXT,
  actor TEXT
);

CREATE INDEX IF NOT EXISTS idx_notif_recipient ON notifications(recipient, read_at);
CREATE INDEX IF NOT EXISTS idx_notif_ts ON notifications(ts);

CREATE TABLE IF NOT EXISTS worklist (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  patient_id TEXT NOT NULL,
  patient_name TEXT,
  sex TEXT,
  dob TEXT,
  study_date TEXT,
  modality TEXT,
  has_file INTEGER DEFAULT 0,
  has_report INTEGER DEFAULT 0,
  report_status TEXT,
  assigned_to TEXT,
  priority TEXT DEFAULT 'normal',
  status TEXT DEFAULT 'pending',
  notes TEXT,
  imported_at TEXT,
  source_row INTEGER,
  UNIQUE(patient_id, study_date, modality, source_row)
);
CREATE INDEX IF NOT EXISTS idx_worklist_assigned ON worklist(assigned_to, status);
CREATE INDEX IF NOT EXISTS idx_worklist_patient ON worklist(patient_id);
CREATE INDEX IF NOT EXISTS idx_worklist_date ON worklist(study_date);

CREATE TABLE IF NOT EXISTS pacs_servers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT UNIQUE NOT NULL,
  host TEXT NOT NULL,
  port INTEGER NOT NULL,
  aet TEXT NOT NULL,
  calling_aet TEXT DEFAULT 'MAMOGRAF_SCU',
  notes TEXT,
  added_by TEXT,
  added_at TEXT
);

CREATE TABLE IF NOT EXISTS annotation_templates (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  description TEXT,
  payload TEXT NOT NULL,
  created_by TEXT,
  created_at TEXT,
  is_shared INTEGER NOT NULL DEFAULT 1,
  UNIQUE(name, created_by)
);

CREATE INDEX IF NOT EXISTS idx_templates_shared ON annotation_templates(is_shared, created_by);

CREATE TABLE IF NOT EXISTS system_settings (
  key TEXT PRIMARY KEY,
  value TEXT,
  updated_by TEXT,
  updated_at TEXT
);

CREATE TABLE IF NOT EXISTS review_decisions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sop_uid TEXT NOT NULL,
  dicom_path TEXT,
  preprocessed_png_path TEXT,
  view TEXT,
  laterality TEXT,
  findings_json TEXT,
  pseudo_bboxes_json TEXT NOT NULL,
  final_bboxes_json TEXT,
  status TEXT NOT NULL DEFAULT 'pending'
       CHECK (status IN ('pending', 'accepted', 'edited', 'rejected')),
  reviewer TEXT,
  decided_at TEXT,
  comments TEXT,
  imported_at TEXT NOT NULL,
  source_queue TEXT,
  UNIQUE(sop_uid, source_queue)
);

CREATE INDEX IF NOT EXISTS idx_review_status ON review_decisions(status);
CREATE INDEX IF NOT EXISTS idx_review_reviewer ON review_decisions(reviewer);
CREATE INDEX IF NOT EXISTS idx_review_sop ON review_decisions(sop_uid);

-- Foydalanuvchi harakatlari auditi (kim, qachon, nima qildi)
CREATE TABLE IF NOT EXISTS audit_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  username TEXT,
  role TEXT,
  action TEXT,
  method TEXT,
  path TEXT,
  status INTEGER,
  ip TEXT,
  detail TEXT
);
CREATE INDEX IF NOT EXISTS idx_audit_ts ON audit_log(ts);
CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(username);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action);

-- Savatcha: o'chirilgan obyektlar (qayta tiklash uchun snapshot)
CREATE TABLE IF NOT EXISTS trash (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  deleted_by TEXT,
  resource_type TEXT NOT NULL,
  resource_id TEXT NOT NULL,
  label TEXT,
  snapshot TEXT NOT NULL,
  blob_path TEXT,
  restored_at TEXT,
  restored_by TEXT
);
CREATE INDEX IF NOT EXISTS idx_trash_type ON trash(resource_type, restored_at);
CREATE INDEX IF NOT EXISTS idx_trash_ts ON trash(ts);
"""

_init_lock = threading.Lock()
_initialized = False


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


_MIGRATIONS = [
    "ALTER TABLE users ADD COLUMN totp_secret TEXT",
    "ALTER TABLE users ADD COLUMN totp_enrolled INTEGER NOT NULL DEFAULT 0",
    # Brute-force himoyasi: ketma-ket xato urinishlar va vaqtinchalik qulf
    "ALTER TABLE users ADD COLUMN failed_logins INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE users ADD COLUMN locked_until TEXT",
]


def _apply_migrations(conn) -> None:
    for stmt in _MIGRATIONS:
        try:
            conn.execute(stmt)
        except Exception:
            pass


def init_db() -> None:
    global _initialized
    with _init_lock:
        if _initialized:
            return
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        with get_conn() as c:
            c.executescript(SCHEMA)
            _apply_migrations(c)
            c.commit()
        _initialized = True
