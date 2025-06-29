import sqlite3
import pandas as pd
import streamlit as st

DB_PATH = "incident_reports.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # 本提出テーブル
    c.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            occurrence_datetime TIMESTAMP NOT NULL,
            reporter_name TEXT NOT NULL,
            job_type TEXT,
            level TEXT,
            location TEXT,
            connection_with_accident TEXT,
            content_details TEXT,
            cause_details TEXT,
            manual_relation TEXT,
            situation TEXT,
            countermeasure TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # ▼下書きテーブル
    c.execute('''
    CREATE TABLE IF NOT EXISTS drafts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        data_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    conn.commit()
    conn.close()

def add_report(data): #repor_data?
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
    INSERT INTO reports (
        occurrence_datetime, reporter_name, job_type, level, location,
        connection_with_accident, content_details, cause_details,
        manual_relation, situation, countermeasure
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['occurrence_datetime'], data['reporter_name'], data['job_type'],
        data['level'], data['location'], data['connection_with_accident'],
        data['content_details'], data['cause_details'],
        data['manual_relation'], data['situation'], data['countermeasure']
    ))
    conn.commit()
    conn.close()

def get_all_reports(_=None):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query('SELECT * FROM reports ORDER BY created_at DESC', conn)
    conn.close()
    return df

# 下書き用
def add_draft(title, data_json):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO drafts (title, data_json) VALUES (?, ?)', (title, data_json))
    conn.commit()
    conn.close()

def get_all_drafts():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query('SELECT * FROM drafts ORDER BY created_at DESC', conn)
    conn.close()
    return df

def delete_draft(draft_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM drafts WHERE id = ?', (draft_id,))
    conn.commit()
    conn.close()