import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from ..config import DATA_DIR, SETTINGS


class DatabaseManager:
    """Quản lý cơ sở dữ liệu SQLite: Dự án, Lịch sử phiên bản kịch bản, Hàng đợi xử lý."""

    def __init__(self, db_path: Optional[Path] = None):
        cfg_path = SETTINGS.get("database", {}).get("path", "data/vodie.db")
        self.db_path = db_path or (DATA_DIR / Path(cfg_path).name)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Khởi tạo các bảng cơ sở dữ liệu."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Bảng Dự án (Projects)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                mood TEXT DEFAULT 'kinh_di_nang',
                raw_script TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # Bảng Lịch sử phiên bản kịch bản (Script Versions)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS script_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                version_number INTEGER,
                script_content TEXT,
                director_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
            """)

            # Bảng Hàng đợi xử lý (Batch Queue)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS batch_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                title TEXT,
                status TEXT DEFAULT 'pending', -- pending, processing, completed, failed
                progress INTEGER DEFAULT 0,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            conn.commit()

    def create_project(self, title: str, raw_script: str, mood: str = "kinh_di_nang") -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO projects (title, raw_script, mood) VALUES (?, ?, ?)",
                (title, raw_script, mood)
            )
            project_id = cursor.lastrowid
            # Lưu version 1
            cursor.execute(
                "INSERT INTO script_versions (project_id, version_number, script_content) VALUES (?, 1, ?)",
                (project_id, raw_script)
            )
            conn.commit()
            return project_id

    def list_projects(self) -> List[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects ORDER BY updated_at DESC")
            return [dict(row) for row in cursor.fetchall()]
