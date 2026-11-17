import sqlite3
from pathlib import Path
from datetime import datetime, timezone
DB = Path.home() / 'AppData' / 'Local' / 'BhumajiAI' / 'DevOpsInterviewAssistant' / 'history.db'
def connect():
    DB.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB)
    db.execute('CREATE TABLE IF NOT EXISTS answers (id INTEGER PRIMARY KEY, at TEXT, kind TEXT, question TEXT, answer TEXT)')
    return db
def save(kind, question, answer):
    with connect() as db:
        db.execute('INSERT INTO answers(at,kind,question,answer) VALUES (?,?,?,?)', (datetime.now(timezone.utc).isoformat(),kind,question,answer))
def recent(limit=100):
    with connect() as db:
        return db.execute('SELECT at,kind,question,answer FROM answers ORDER BY id DESC LIMIT ?', (limit,)).fetchall()
