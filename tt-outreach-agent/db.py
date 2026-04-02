"""
Database connection and operations - supports both Postgres and SQLite
"""
import os
import logging
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
DB_TYPE = "sqlite"  # Will be set based on connection attempt
DB_PATH = "test_outreach.db"

def get_db_connection():
    """Create a connection - tries Postgres first, falls back to SQLite"""
    global DB_TYPE

    if DATABASE_URL and DB_TYPE != "sqlite":
        try:
            conn = psycopg2.connect(DATABASE_URL)
            DB_TYPE = "postgres"
            return conn
        except Exception as e:
            logger.warning(f"Postgres connection failed: {e}. Using SQLite fallback.")
            DB_TYPE = "sqlite"

    # Use SQLite
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # Return rows as dicts
        return conn
    except Exception as e:
        logger.error(f"SQLite connection failed: {e}")
        raise


def init_db():
    """Create tables if they don't exist"""
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # SQLite-compatible CREATE TABLE
        cur.execute("""
            CREATE TABLE IF NOT EXISTS prospects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                apollo_id TEXT UNIQUE,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT,
                linkedin_url TEXT,
                job_title TEXT,
                company_name TEXT,
                company_domain TEXT,
                country TEXT,
                city TEXT,
                product_target TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'new',
                touchpoints INTEGER DEFAULT 0,
                last_contact_at TIMESTAMP,
                next_contact_at TIMESTAMP,
                draft_subject TEXT,
                draft_body TEXT,
                draft_channel TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT
            );
        """)

        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_prospects_status
            ON prospects(status);
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_prospects_product
            ON prospects(product_target);
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_prospects_next_contact
            ON prospects(next_contact_at);
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_prospects_email
            ON prospects(email);
        """)

        # Config table for tracking pagination
        cur.execute("""
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        conn.commit()
        logger.info("Database initialized successfully (SQLite)")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


# ══════════════════════════════════════════════════════════════
# PROSPECTS QUERIES
# ══════════════════════════════════════════════════════════════

def insert_prospect(apollo_id, first_name, last_name, email, linkedin_url,
                   job_title, company_name, company_domain, country, city,
                   product_target):
    """Insert a new prospect"""
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO prospects
            (apollo_id, first_name, last_name, email, linkedin_url, job_title,
             company_name, company_domain, country, city, product_target)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ;
        """, (apollo_id, first_name, last_name, email, linkedin_url,
              job_title, company_name, company_domain, country, city, product_target))

        conn.commit()
        return cur.lastrowid
    except Exception as e:
        logger.error(f"Failed to insert prospect: {e}")
        conn.rollback()
        return None
    finally:
        cur.close()
        conn.close()


def _row_to_dict(row):
    """Convert SQLite row to dict"""
    if isinstance(row, sqlite3.Row):
        return dict(row)
    return row

def get_prospects_by_status(status, limit=100):
    """Get prospects by status"""
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT * FROM prospects
            WHERE status = ?
            ORDER BY created_at ASC
            LIMIT ?;
        """, (status, limit))

        rows = cur.fetchall()
        return [_row_to_dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Failed to get prospects: {e}")
        return []
    finally:
        cur.close()
        conn.close()


def get_prospects_needing_followup():
    """Get prospects that need follow-up (scheduled)"""
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT * FROM prospects
            WHERE status IN ('sent', 'followed_up_1')
            AND next_contact_at <= datetime('now')
            AND touchpoints < 4
            ORDER BY next_contact_at ASC;
        """)

        rows = cur.fetchall()
        return [_row_to_dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Failed to get followup prospects: {e}")
        return []
    finally:
        cur.close()
        conn.close()


def update_prospect_status(prospect_id, status):
    """Update prospect status"""
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            UPDATE prospects
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?;
        """, (status, prospect_id))

        conn.commit()
        logger.info(f"Prospect {prospect_id} status updated to {status}")
    except Exception as e:
        logger.error(f"Failed to update prospect: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()


def update_prospect_draft(prospect_id, subject, body, channel='email'):
    """Update prospect draft content"""
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            UPDATE prospects
            SET draft_subject = ?, draft_body = ?, draft_channel = ?,
                status = 'drafted', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?;
        """, (subject, body, channel, prospect_id))

        conn.commit()
        logger.info(f"Prospect {prospect_id} draft updated")
    except Exception as e:
        logger.error(f"Failed to update prospect draft: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()


def update_prospect_sent(prospect_id, next_contact_days=7):
    """Mark prospect as sent and set next contact"""
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        next_contact = datetime.now() + timedelta(days=next_contact_days)
        cur.execute("""
            UPDATE prospects
            SET status = 'sent', touchpoints = touchpoints + 1,
                last_contact_at = CURRENT_TIMESTAMP, next_contact_at = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?;
        """, (next_contact, prospect_id))

        conn.commit()
        logger.info(f"Prospect {prospect_id} marked as sent")
    except Exception as e:
        logger.error(f"Failed to mark prospect as sent: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()


def check_prospect_exists(email=None, apollo_id=None):
    """Check if prospect already exists"""
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        if email:
            cur.execute("SELECT id FROM prospects WHERE email = ?;", (email,))
        elif apollo_id:
            cur.execute("SELECT id FROM prospects WHERE apollo_id = ?;", (apollo_id,))
        else:
            return False

        return cur.fetchone() is not None
    except Exception as e:
        logger.error(f"Failed to check prospect: {e}")
        return False
    finally:
        cur.close()
        conn.close()


def mark_prospect_replied(prospect_id, reply_text):
    """Mark prospect as replied"""
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            UPDATE prospects
            SET status = 'replied', notes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?;
        """, (reply_text, prospect_id))

        conn.commit()
        logger.info(f"Prospect {prospect_id} marked as replied")
    except Exception as e:
        logger.error(f"Failed to mark prospect as replied: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()


def mark_prospect_exhausted(prospect_id):
    """Mark prospect as exhausted (no more contact)"""
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            UPDATE prospects
            SET status = 'exhausted', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?;
        """, (prospect_id,))

        conn.commit()
        logger.info(f"Prospect {prospect_id} marked as exhausted")
    except Exception as e:
        logger.error(f"Failed to mark prospect as exhausted: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()


# ══════════════════════════════════════════════════════════════
# CONFIG QUERIES (for pagination state)
# ══════════════════════════════════════════════════════════════

def get_config(key):
    """Get config value"""
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT value FROM config WHERE key = ?;", (key,))
        result = cur.fetchone()
        if result:
            return result[0] if isinstance(result, tuple) else result['value']
        return None
    except Exception as e:
        logger.error(f"Failed to get config: {e}")
        return None
    finally:
        cur.close()
        conn.close()


def set_config(key, value):
    """Set config value"""
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT OR REPLACE INTO config (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP);
        """, (key, value))

        conn.commit()
        logger.info(f"Config {key} set to {value}")
    except Exception as e:
        logger.error(f"Failed to set config: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()


def get_stats():
    """Get basic statistics"""
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'new' THEN 1 ELSE 0 END) as new_count,
                SUM(CASE WHEN status = 'drafted' THEN 1 ELSE 0 END) as drafted_count,
                SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) as sent_count,
                SUM(CASE WHEN status = 'replied' THEN 1 ELSE 0 END) as replied_count
            FROM prospects;
        """)

        row = cur.fetchone()
        return _row_to_dict(row) if row else None
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        return None
    finally:
        cur.close()
        conn.close()
