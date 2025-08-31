# pip install "psycopg[binary]"  # psycopg v3
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Union, Iterable, Tuple
import hashlib
import os
import psycopg
from psycopg import Connection
from psycopg.rows import tuple_row
from psycopg.errors import DatabaseError

class ImageStoreError(Exception):
    """Generic ImageStore failure."""

DDL_CREATE = """
CREATE TABLE IF NOT EXISTS images (
    sha256       TEXT PRIMARY KEY,
    img_filename TEXT NOT NULL,
    img_bytes    BYTEA NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""

DDL_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_images_filename_created_at ON images (img_filename, created_at DESC);",
]

SHA256_HEX_RE = "^[0-9a-f]{64}$"

@dataclass
class ImageStore:
    """
    Store/retrieve images in Postgres with BYTEA payload and SHA-256 key.
    - Hash computed on raw file bytes.
    - Upsert by sha256 (payload immutable; filename can refresh).
    """
    dsn_or_conn: Union[str, Connection]
    max_bytes: int = 50 * 1024 * 1024  # 50 MB guardrail

    def __post_init__(self):
        try:
            if isinstance(self.dsn_or_conn, str):
                self._conn = psycopg.connect(self.dsn_or_conn, autocommit=True)
                self._owns_conn = True
            else:
                self._conn = self.dsn_or_conn
                try:
                    self._conn.autocommit = True
                except Exception:
                    pass
                self._owns_conn = False
            self._ensure_schema()
        except DatabaseError as e:
            raise ImageStoreError(f"DB init failed: {e}") from e

    def _ensure_schema(self):
        with self._conn.cursor() as cur:
            cur.execute(DDL_CREATE)
            for stmt in DDL_INDEXES:
                cur.execute(stmt)
            # Add checksum format constraint if missing
            cur.execute("""
                DO $$
                BEGIN
                  IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint c
                      JOIN pg_class t ON t.oid = c.conrelid
                    WHERE t.relname = 'images' AND c.conname = 'chk_sha256_hex'
                  ) THEN
                    ALTER TABLE images
                    ADD CONSTRAINT chk_sha256_hex CHECK (sha256 ~ '^[0-9a-f]{64}$');
                  END IF;
                END$$;
            """)

    # ---------- internals ----------
    @staticmethod
    def _read_file_bytes(path: str, max_bytes: int) -> bytes:
        if not os.path.isfile(path):
            raise FileNotFoundError(path)
        size = os.path.getsize(path)
        if size > max_bytes:
            raise ImageStoreError(f"File too large: {size} > {max_bytes} bytes")
        with open(path, "rb") as f:
            return f.read()

    @staticmethod
    def _sha256(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def _to_bytes(db_value) -> bytes:
        # psycopg v3 maps BYTEA to memoryview by default
        if isinstance(db_value, (bytes, bytearray)):
            return bytes(db_value)
        try:
            return bytes(db_value)  # memoryview -> bytes
        except Exception:
            raise ImageStoreError("Unexpected BYTEA type from DB")

    @staticmethod
    def _validate_sha(sha256: str):
        import re
        if not re.match(SHA256_HEX_RE, sha256 or ""):
            raise ValueError("sha256 must be 64 lowercase hex characters")

    # ---------- public API ----------
    def add_image(self, file_path: str) -> str:
        """
        Read file, compute sha256 on raw bytes, store as BYTEA.
        Upsert by sha256 (retains payload, refreshes filename).
        Returns the sha256 key.
        """
        try:
            raw = self._read_file_bytes(file_path, self.max_bytes)
            sha = self._sha256(raw)
            filename = os.path.basename(file_path)
            sql = """
            INSERT INTO images (sha256, img_filename, img_bytes)
            VALUES (%s, %s, %s)
            ON CONFLICT (sha256)
            DO UPDATE SET img_filename = EXCLUDED.img_filename
            """
            with self._conn.cursor() as cur:
                cur.execute(sql, (sha, filename, psycopg.Binary(raw)))
            return sha
        except (DatabaseError, OSError) as e:
            raise ImageStoreError(f"add_image failed: {e}") from e

    def get_image_bytes(self, sha256: str) -> Optional[bytes]:
        """Return raw bytes by sha256, or None if not found."""
        self._validate_sha(sha256)
        try:
            with self._conn.cursor(row_factory=tuple_row) as cur:
                cur.execute("SELECT img_bytes FROM images WHERE sha256 = %s", (sha256,))
                row = cur.fetchone()
                return self._to_bytes(row[0]) if row else None
        except DatabaseError as e:
            raise ImageStoreError(f"get_image_bytes failed: {e}") from e

    def write_image_to(self, sha256: str, out_path: str) -> bool:
        """Retrieve by sha256 and write to out_path. Returns True if written, False if not found."""
        try:
            data = self.get_image_bytes(sha256)
            if data is None:
                return False
            os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
            with open(out_path, "wb") as f:
                f.write(data)
            return True
        except (DatabaseError, OSError) as e:
            raise ImageStoreError(f"write_image_to failed: {e}") from e

    # Helper — latest by filename (uses (filename, created_at DESC) index)
    def get_latest_by_filename_bytes(self, img_filename: str) -> Optional[bytes]:
        try:
            with self._conn.cursor(row_factory=tuple_row) as cur:
                cur.execute(
                    """
                    SELECT img_bytes
                    FROM images
                    WHERE img_filename = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    (img_filename,),
                )
                row = cur.fetchone()
                return self._to_bytes(row[0]) if row else None
        except DatabaseError as e:
            raise ImageStoreError(f"get_latest_by_filename_bytes failed: {e}") from e

    # Helper — enumerate all shas for a filename (debug/dedupe)
    def list_shas_for_filename(self, img_filename: str) -> Iterable[Tuple[str, str]]:
        """Yields (sha256, created_at_iso) newest first."""
        try:
            with self._conn.cursor(row_factory=tuple_row) as cur:
                cur.execute(
                    """
                    SELECT sha256, to_char(created_at, 'YYYY-MM-DD"T"HH24:MI:SSOF')
                    FROM images
                    WHERE img_filename = %s
                    ORDER BY created_at DESC
                    """,
                    (img_filename,),
                )
                yield from cur
        except DatabaseError as e:
            raise ImageStoreError(f"list_shas_for_filename failed: {e}") from e

    def close(self):
        if getattr(self, "_owns_conn", False):
            try:
                self._conn.close()
            except Exception:
                pass
