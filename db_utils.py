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
    conn.commit()
    conn.close()

def add_report(report_data):
    # ▼▼▼ 確認用のprint文を追加 ▼▼▼
    print("--- add_report関数が呼ばれました ---")
    print(report_data)
    
    """新しい報告をデータベースに追加する"""
    conn = get_db_connection()
    # report_data辞書のキーとテーブルの列名が一致している必要がある
    try:
        conn.execute('''
            INSERT INTO reports (
                occurrence_datetime, reporter_name, job_type, level, location, 
                connection_with_accident, content_details, cause_details, 
                manual_relation, situation, countermeasure
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            report_data.get('occurrence_datetime'),
            report_data.get('reporter_name'),
            report_data.get('job_type'),
            report_data.get('level'),
            report_data.get('location'),
            report_data.get('connection_with_accident'),
            report_data.get('content_details'),
            report_data.get('cause_details'),
            report_data.get('manual_relation'),
            report_data.get('situation'),
            report_data.get('countermeasure')
        ))
        conn.commit()
        print("--- データベースへのcommitが成功しました ---") # 成功した場合のメッセージ
    except Exception as e:
        print(f"--- データベースエラー: {e} ---") # エラーが出た場合のメッセージ
        conn.rollback() # エラーが出たら変更を元に戻す
    finally:
        conn.close()

@st.cache_data # 結果をキャッシュして、DBへのアクセスを減らす
def get_all_reports(dummy_version=0): # (1) ダミーの引数を追加
    """全ての報告データをDataFrameとして取得する"""
    conn = get_db_connection()
    # pd.read_sql を使うと、SQLの実行結果を直接DataFrameに変換できる
    df = pd.read_sql('SELECT * FROM reports ORDER BY occurrence_datetime DESC', conn)
    conn.close()
    return df