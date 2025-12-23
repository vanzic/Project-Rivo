import sqlite3
import os
import logging

class TrendStore:
    """
    SQLite backend for storing trend IDs.
    Uses raw SQL commands without ORM.
    """
    def __init__(self, db_path='data/trends.db'):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initializes the database table if it doesn't exist."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS trends (
                        id TEXT PRIMARY KEY
                    )
                ''')
                
                # New table for normalized trend scores
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS trend_scores (
                        trend_key TEXT PRIMARY KEY,
                        score INTEGER DEFAULT 1,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        sources_json TEXT DEFAULT '[]',
                        titles_json TEXT DEFAULT '[]'
                    )
                ''')
                
                # Migration: Ensure columns exist
                try:
                    cursor.execute("PRAGMA table_info(trend_scores)")
                    columns = [row[1] for row in cursor.fetchall()]
                    
                    if 'last_updated' not in columns:
                        logging.info("Migrating: Adding last_updated")
                        cursor.execute("ALTER TABLE trend_scores ADD COLUMN last_updated TIMESTAMP DEFAULT '2025-01-01 00:00:00'")
                    
                    if 'first_seen' not in columns:
                        logging.info("Migrating: Adding first_seen")
                        cursor.execute("ALTER TABLE trend_scores ADD COLUMN first_seen TIMESTAMP DEFAULT '2025-01-01 00:00:00'")
                        
                    if 'sources_json' not in columns:
                        logging.info("Migrating: Adding sources_json")
                        cursor.execute("ALTER TABLE trend_scores ADD COLUMN sources_json TEXT DEFAULT '[]'")
                        
                    if 'titles_json' not in columns:
                        logging.info("Migrating: Adding titles_json")
                        cursor.execute("ALTER TABLE trend_scores ADD COLUMN titles_json TEXT DEFAULT '[]'")
                        
                    conn.commit()
                except Exception as migration_err:
                     logging.error(f"Migration error: {migration_err}")
                     
                conn.commit()
        except Exception as e:
            logging.error(f"Failed to initialize SQLite store: {e}")

    def load_all(self):
        # ... (unchanged)
        trends = set()
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT id FROM trends')
                rows = cursor.fetchall()
                for row in rows:
                    trends.add(row[0])
        except Exception as e:
            logging.error(f"Failed to load trends from SQLite: {e}")
        return trends

    def add_trend(self, trend_id):
        # ... (unchanged)
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT OR IGNORE INTO trends (id) VALUES (?)', (trend_id,))
                conn.commit()
        except Exception as e:
            logging.error(f"Failed to add trend to SQLite: {e}")

    def increment_score(self, trend_key: str, source: str = None, title: str = None):
        """
        Increments the score for a normalized trend key and updates metadata.
        """
        try:
            import json
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Fetch existing data
                cursor.execute('SELECT score, sources_json, titles_json FROM trend_scores WHERE trend_key = ?', (trend_key,))
                row = cursor.fetchone()
                
                if row:
                    score, src_json, ttl_json = row
                    new_score = score + 1
                    
                    sources = json.loads(src_json) if src_json else []
                    titles = json.loads(ttl_json) if ttl_json else []
                    
                    if source and source not in sources:
                        sources.append(source)
                    if title and title not in titles:
                        titles.append(title)
                        
                    cursor.execute('''
                        UPDATE trend_scores 
                        SET score = ?, last_updated = CURRENT_TIMESTAMP, sources_json = ?, titles_json = ? 
                        WHERE trend_key = ?
                    ''', (new_score, json.dumps(sources), json.dumps(titles), trend_key))
                    
                else:
                    # New Entry
                    sources = [source] if source else []
                    titles = [title] if title else []
                    cursor.execute('''
                        INSERT INTO trend_scores (trend_key, score, last_updated, first_seen, sources_json, titles_json) 
                        VALUES (?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ?, ?)
                    ''', (trend_key, json.dumps(sources), json.dumps(titles)))
                    
                conn.commit()
        except Exception as e:
            logging.error(f"Failed to increment score for {trend_key}: {e}")

    def get_score(self, trend_key: str) -> int:
        # ... (unchanged logic but keeping file integrity)
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT score FROM trend_scores WHERE trend_key = ?', (trend_key,))
                row = cursor.fetchone()
                return row[0] if row else 0
        except Exception as e:
            logging.error(f"Failed to get score for {trend_key}: {e}")
            return 0

    def get_top_trends_metadata(self, limit=5) -> list:
        """
        Retrieves top trends with full metadata.
        Returns list of dicts.
        """
        results = []
        try:
            import json
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT trend_key, score, sources_json, titles_json, first_seen, last_updated 
                    FROM trend_scores
                    WHERE last_updated >= datetime('now', '-48 hours')
                    ORDER BY score DESC
                    LIMIT ?
                ''', (limit,))
                rows = cursor.fetchall()
                
                for row in rows:
                    results.append({
                        "trend_key": row[0],
                        "score": row[1],
                        "sources": json.loads(row[2]) if row[2] else [],
                        "sample_titles": json.loads(row[3]) if row[3] else [],
                        "first_seen": row[4],
                        "last_seen": row[5]
                    })
        except Exception as e:
            logging.error(f"Failed to get top trends metadata: {e}")
        return results
