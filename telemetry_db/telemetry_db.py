# ============================================================================
# database.py - Shared database initialization
# ============================================================================
import os

import sqlite3
from contextlib import closing

DATABASE = 'telemetry.db'

class TelemetryDb:
    @staticmethod
    def init_db():
        """Initialize database with required tables"""
        TelemetryDb.cleanup_db()
        with closing(sqlite3.connect(DATABASE)) as conn:
            with closing(conn.cursor()) as cursor:
                # Table 1: metric_definitions
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS metric_definitions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        metric_name TEXT NOT NULL UNIQUE,
                        unit TEXT NOT NULL
                    )
                ''')

                # Table 2: metric_values
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS metric_values (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        metric_id INTEGER NOT NULL,
                        server_name TEXT NOT NULL,
                        value REAL NOT NULL,
                        timestamp TEXT NOT NULL,
                        FOREIGN KEY (metric_id) REFERENCES metric_definitions(id)
                    )
                ''')

                # Create indexes for performance
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_metric_values_server 
                    ON metric_values(server_name)
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_metric_values_timestamp 
                    ON metric_values(timestamp)
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_metric_values_metric_id 
                    ON metric_values(metric_id)
                ''')

                conn.commit()


    @staticmethod
    def get_db():
        """Get database connection with Row factory"""
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def cleanup_db():
        """Remove database file on exit"""
        if os.path.exists(DATABASE):
            os.remove(DATABASE)
