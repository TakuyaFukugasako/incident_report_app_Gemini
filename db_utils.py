import streamlit as st
import sqlite3
import pandas as pd
import datetime
import json

DB_NAME = "incident_reports.db"

def get_db_connection():
    """データベース接続を取得します"""
    return sqlite3.connect(DB_NAME)

def init_db():
    """
    データベースとテーブルを初期化します。
    reportsテーブルとdraftsテーブルがなければ作成します。
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # --- インシデント報告テーブル ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                occurrence_datetime DATETIME NOT NULL,
                reporter_name TEXT NOT NULL,
                job_type TEXT,
                level TEXT,
                location TEXT,
                connection_with_accident TEXT,
                years_of_experience TEXT,
                years_since_joining TEXT,
                patient_ID TEXT,
                patient_name TEXT,
                patient_gender TEXT,
                patient_age INTEGER,
                dementia_status TEXT,
                patient_status_change_accident TEXT,
                patient_status_change_patient_explanation TEXT,
                patient_status_change_family_explanation TEXT,
                content_category TEXT,
                content_details TEXT,
                cause_details TEXT,
                manual_relation TEXT,
                situation TEXT NOT NULL,
                countermeasure TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # --- 下書きテーブル ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS drafts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                data_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

# --- レポート関連 ---

def add_report(data: dict):
    """インシデント報告をデータベースに追加します"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # 辞書のキーと値からSQL文を生成
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?'] * len(data))
        sql = f"INSERT INTO reports ({columns}) VALUES ({placeholders})"
        cursor.execute(sql, tuple(data.values()))
        conn.commit()

# st.cache_data を使うことで、引数が変わらない限りDBアクセスをスキップできる
def get_all_reports():
    """全てのインシデント報告を取得します"""
    with get_db_connection() as conn:
        # index_col='id' を指定すると、DataFrameのインデックスがid列になる
        df = pd.read_sql("SELECT * FROM reports ORDER BY occurrence_datetime DESC", conn, index_col='id')
        return df

# --- 下書き関連 ---

def add_draft(title: str, data_json: str):
    """下書きをデータベースに追加します"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO drafts (title, data_json) VALUES (?, ?)",
            (title, data_json)
        )
        conn.commit()

def get_all_drafts() -> pd.DataFrame:
    """全ての下書きを取得します"""
    with get_db_connection() as conn:
        df = pd.read_sql("SELECT * FROM drafts ORDER BY created_at DESC", conn)
        return df

def delete_draft(draft_id: int):
    """指定されたIDの下書きを削除します"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM drafts WHERE id = ?", (draft_id,))
        conn.commit()

class DateTimeEncoder(json.JSONEncoder):
    """datetime, date, timeオブジェクトをJSONシリアライズ可能にするためのエンコーダー"""
    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date, datetime.time)):
            return obj.isoformat()
        return super(DateTimeEncoder, self).default(obj)