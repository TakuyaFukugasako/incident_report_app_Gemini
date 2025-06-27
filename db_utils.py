import sqlite3
import pandas as pd
import streamlit as st

DB_FILE = "incident_reports.db"

def get_db_connection():
    """データベースへの接続を取得する"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row # 列名でアクセスできるようにする
    return conn

def init_db():
    """データベースの初期化（テーブル作成）を行う"""
    conn = get_db_connection()
    # 報告フォームの項目に合わせて列を定義
    conn.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT,
            occurrence_datetime TIMESTAMP,
            reporter_name TEXT,
            job_type TEXT,
            connection_with_accident TEXT,
            total_experience TEXT,
            years_at_current_job TEXT,
            patient_ID TEXT,
            patient_name TEXT,
            location TEXT,
            situation TEXT,
            countermeasure TEXT,
            content_details TEXT,
            cause_details TEXT,
            manual_relation TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
      # ▼▼▼ drafts テーブルを新しく作成 ▼▼▼
    # reportsテーブルとほぼ同じ構成だが、NULLを許可し、username列を追加
    conn.execute('''
        CREATE TABLE IF NOT EXISTS drafts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            draft_name TEXT,
            level TEXT,
            occurrence_datetime TIMESTAMP,
            reporter_name TEXT,
            job_type TEXT,
            connection_with_accident TEXT,
            total_experience TEXT,
            years_at_current_job TEXT,
            patient_ID TEXT,
            patient_name TEXT,
            location TEXT,
            situation TEXT,
            countermeasure TEXT,
            content_details TEXT,
            cause_details TEXT,
            manual_relation TEXT,
            last_saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def add_report(report_data):
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO reports (
            level, occurrence_datetime, reporter_name, job_type, connection_with_accident,
            total_experience, years_at_current_job, patient_ID, patient_name, location,
            situation, countermeasure, content_details, cause_details, manual_relation
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', tuple(report_data.get(k) for k in [
        'level', 'occurrence_datetime', 'reporter_name', 'job_type', 'connection_with_accident',
        'total_experience', 'years_at_current_job', 'patient_ID', 'patient_name', 'location',
        'situation', 'countermeasure', 'content_details', 'cause_details', 'manual_relation'
    ]))
    conn.commit()
    conn.close()
        
def save_draft(username, draft_data):
    """下書きを保存または更新する"""
    conn = get_db_connection()
    draft_id = draft_data.get('id')
    
    # 保存するキーのリスト
    keys = [
        'draft_name', 'level', 'occurrence_datetime', 'reporter_name', 'job_type',
        'connection_with_accident', 'total_experience', 'years_at_current_job',
        'patient_ID', 'patient_name', 'location', 'situation', 'countermeasure',
        'content_details', 'cause_details', 'manual_relation'
    ]
    
    if draft_id:
        # 更新
        update_cols = ", ".join([f"{key}=?" for key in keys])
        values = [draft_data.get(k) for k in keys] + [draft_id, username]
        conn.execute(f'UPDATE drafts SET {update_cols}, last_saved_at=CURRENT_TIMESTAMP WHERE id=? AND username=?', tuple(values))
    else:
        # 新規作成
        insert_cols = ", ".join(keys)
        placeholders = ", ".join(["?"] * len(keys))
        values = [draft_data.get(k) for k in keys]
        conn.execute(f'INSERT INTO drafts (username, {insert_cols}) VALUES (?, {placeholders})', (username, *values))
    
    conn.commit()
    conn.close()

def get_user_drafts(username):
    """特定のユーザーの下書き一覧を取得する"""
    conn = get_db_connection()
    df = pd.read_sql('SELECT id, draft_name, last_saved_at FROM drafts WHERE username = ? ORDER BY last_saved_at DESC', conn, params=(username,))
    conn.close()
    return df

def load_draft(draft_id, username):
    """特定の下書きデータを取得する"""
    conn = get_db_connection()
    draft = conn.execute('SELECT * FROM drafts WHERE id = ? AND username = ?', (draft_id, username)).fetchone()
    conn.close()
    return dict(draft) if draft else None

def delete_draft(draft_id, username):
    """特定の下書きを削除する"""
    conn = get_db_connection()
    conn.execute('DELETE FROM drafts WHERE id = ? AND username = ?', (draft_id, username))
    conn.commit()
    conn.close()
    
@st.cache_data
def get_all_reports(dummy_version=0):
    """全ての報告データをDataFrameとして取得する"""
    conn = get_db_connection()
    df = pd.read_sql('SELECT * FROM reports ORDER BY occurrence_datetime DESC', conn)
    conn.close()
    return df