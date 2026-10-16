import time
from typing import List, Dict, Optional
from .db import DatabaseManager


class QueueManager:
    """
    Quản lý hàng đợi xử lý hàng loạt (Batch Queue Processing):
    - Thả 10 truyện vào hàng đợi, để máy chạy qua đêm.
    - Chạy nền, tiếp tục (resume) nếu máy tính bị tắt đột ngột.
    """

    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or DatabaseManager()

    def add_to_queue(self, project_id: int, title: str) -> int:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO batch_queue (project_id, title, status, progress) VALUES (?, ?, 'pending', 0)",
                (project_id, title)
            )
            conn.commit()
            return cursor.lastrowid

    def get_pending_tasks(self) -> List[Dict]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM batch_queue WHERE status IN ('pending', 'processing') ORDER BY id ASC"
            )
            return [dict(row) for row in cursor.fetchall()]

    def update_status(self, task_id: int, status: str, progress: int = 0, error: str = None):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE batch_queue
                SET status = ?, progress = ?, error_message = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (status, progress, error, task_id)
            )
            conn.commit()
