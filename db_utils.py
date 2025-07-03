import streamlit as st
import sqlite3
import pandas as pd
import datetime
import json
import bcrypt # bcryptライブラリをインポート
import os # 環境変数を読み込むためにosモジュールをインポート

DB_NAME = "incident_reports.db"

def get_db_connection():
    """データベース接続を取得します"""
    return sqlite3.connect(DB_NAME)

def init_db():
    """
    データベースとテーブルを初期化します。
    reportsテーブルとdraftsテーブル、usersテーブルがなければ作成します。
    既存のreportsテーブルにカラムが不足している場合は追加します。
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # --- インシデント報告テーブル ---
        cursor.execute('''
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
                content_details_shinsatsu TEXT,
                content_details_shochi TEXT,
                content_details_uketsuke TEXT,
                content_details_houshasen TEXT,
                content_details_rehabili TEXT,
                content_details_kanjataio TEXT,
                content_details_buhin TEXT,
                injury_details TEXT,
                injury_other_text TEXT,
                cause_details TEXT,
                manual_relation TEXT,
                situation TEXT NOT NULL,
                countermeasure TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT,
                approver1 TEXT,
                approved_at1 DATETIME,
                approver2 TEXT,
                approved_at2 DATETIME,
                manager_comments TEXT
            )
        ''')

        # --- usersテーブル ---
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                report_save_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # usersテーブルにreport_save_pathカラムを追加（もし存在しない場合）
        cursor.execute("PRAGMA table_info(users)")
        user_columns = [row[1] for row in cursor.fetchall()]
        if 'report_save_path' not in user_columns:
            cursor.execute("ALTER TABLE users ADD COLUMN report_save_path TEXT")

        # --- テーブルスキーマのマイグレーション (reportsテーブル) ---
        cursor.execute("PRAGMA table_info(reports)")
        columns = [row[1] for row in cursor.fetchall()]

        expected_columns_reports = {
            "years_of_experience": "TEXT",
            "years_since_joining": "TEXT",
            "patient_gender": "TEXT",
            "patient_age": "INTEGER",
            "dementia_status": "TEXT",
            "patient_status_change_accident": "TEXT",
            "patient_status_change_patient_explanation": "TEXT",
            "patient_status_change_family_explanation": "TEXT",
            "status": "TEXT",
            "approver1": "TEXT",
            "approved_at1": "DATETIME",
            "approver2": "TEXT",
            "approved_at2": "DATETIME",
            "manager_comments": "TEXT",
            "content_details_shinsatsu": "TEXT",
            "content_details_shochi": "TEXT",
            "content_details_uketsuke": "TEXT",
            "content_details_houshasen": "TEXT",
            "content_details_rehabili": "TEXT",
            "content_details_kanjataio": "TEXT",
            "content_details_kiki": "TEXT",
            "content_details_sonota": "TEXT",
            "injury_details": "TEXT",
            "injury_other_text": "TEXT"
        }

        for col_name, col_type in expected_columns_reports.items():
            if col_name not in columns:
                cursor.execute(f"ALTER TABLE reports ADD COLUMN {col_name} {col_type}")

        

        # --- 下書きテーブル ---
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS drafts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                data_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

# --- ユーザー関連 ---

def add_user(username, password, role='general', report_save_path=None):
    """新しいユーザーをデータベースに追加します。パスワードはハッシュ化されます。"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        try:
            cursor.execute("INSERT INTO users (username, password_hash, role, report_save_path) VALUES (?, ?, ?, ?)",
                           (username, hashed_password, role, report_save_path))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            # usernameがUNIQUE制約に違反した場合（既に存在する）
            return False

def get_user_by_username(username):
    """ユーザー名でユーザー情報を取得します。"""
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row # カラム名をキーとしてアクセスできるようにする
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password_hash, role, report_save_path FROM users WHERE username = ?", (username,))
        user_data = cursor.fetchone()
        if user_data:
            return dict(user_data)
        return None

def verify_password(plain_password, hashed_password):
    """平文パスワードとハッシュ化されたパスワードを比較して検証します。"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

# --- レポート関連 ---

def get_report_by_id(report_id: int) -> dict | None:
    """指定されたIDのレポートを取得します"""
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row # カラム名をキーとしてアクセスできるようにする
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM reports WHERE id = ?", (report_id,))
        report_data = cursor.fetchone()
        if report_data:
            return dict(report_data)
        return None

def generate_and_save_report_csv(report_data: dict, approver_id: int = None):
    """レポートデータをCSV形式で生成し、ファイルとして保存します"""
    if not report_data:
        print("DEBUG: generate_and_save_report_csv: report_data is empty.")
        return

    output_dir = "approved_reports"
    if approver_id:
        with get_db_connection() as conn:
            conn.row_factory = sqlite3.Row # カラム名をキーとしてアクセスできるようにする
            cursor = conn.cursor()
            cursor.execute("SELECT report_save_path FROM users WHERE id = ?", (approver_id,))
            path_data = cursor.fetchone()
            if path_data and path_data['report_save_path']:
                output_dir = path_data['report_save_path']
    
    print(f"DEBUG: generate_and_save_report_csv: Determined output_dir: {output_dir}")

    try:
        os.makedirs(output_dir, exist_ok=True)
        print(f"DEBUG: generate_and_save_report_csv: Directory created/exists: {output_dir}")
    except Exception as e:
        print(f"ERROR: generate_and_save_report_csv: Failed to create directory {output_dir}: {e}")
        return

    # ファイル名に含めるためのタイムスタンプ
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"report_{report_data.get('id', 'unknown')}_{timestamp}.csv"
    filepath = os.path.join(output_dir, filename)
    print(f"DEBUG: generate_and_save_report_csv: Constructed filepath: {filepath}")

    # DataFrameに変換してCSVとして保存
    df = pd.DataFrame([report_data])
    try:
        df.to_csv(filepath, index=False, encoding='utf-8-sig') # Excelで開けるようにutf-8-sig
        print(f"DEBUG: CSVレポートを保存しました: {filepath}")
    except Exception as e:
        print(f"ERROR: generate_and_save_report_csv: Failed to save CSV to {filepath}: {e}")

def add_report(data: dict, status: str = '未読', created_at: datetime.datetime = None):
    """インシデント報告をデータベースに追加します"""
    data['status'] = status
    if created_at:
        data['created_at'] = created_at.isoformat()
    # 新しい詳細項目をJSON文字列として保存
    for key in ['content_details_shinsatsu', 'content_details_shochi', 'content_details_uketsuke', 'content_details_houshasen', 'content_details_rehabili', 'content_details_kanjataio', 'content_details_kiki', 'content_details_sonota', 'injury_details']:
        if key in data and isinstance(data[key], list):
            data[key] = json.dumps(data[key], ensure_ascii=False)
    if 'injury_other_text' in data and data['injury_other_text'] is None:
        data['injury_other_text'] = ""

    with get_db_connection() as conn:
        cursor = conn.cursor()
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?'] * len(data))
        sql = f"INSERT INTO reports ({columns}) VALUES ({placeholders})"
        cursor.execute(sql, tuple(data.values()))
        report_id = cursor.lastrowid # 新しく挿入されたレポートのIDを取得
        conn.commit()

        # ステータスが「承認済み」の場合、CSVを生成
        if data['status'] == '承認済み':
            report = get_report_by_id(report_id)
            if report:
                generate_and_save_report_csv(report, approver_id=None) # 過去データ報告からの追加なのでapprover_idはNone

def update_report_status(report_id: int, updates: dict, approver_id: int = None):
    """指定されたIDのレポートのステータスや承認者情報を更新します"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        set_clauses = [f"{key} = ?" for key in updates.keys()]
        sql = f"UPDATE reports SET {', '.join(set_clauses)} WHERE id = ?"
        
        values = list(updates.values())
        values.append(report_id)
        
        cursor.execute(sql, tuple(values))
        conn.commit()

        # ステータスが「承認済み」になった場合、CSVを生成
        if 'status' in updates and updates['status'] == '承認済み':
            report = get_report_by_id(report_id)
            if report:
                generate_and_save_report_csv(report, approver_id)

def get_all_reports():
    """全てのインシデント報告を取得します"""
    with get_db_connection() as conn:
        # index_col='id' を指定すると、DataFrameのインデックスがid列になる
        df = pd.read_sql("SELECT * FROM reports ORDER BY occurrence_datetime DESC", conn, index_col='id')
        return df

# --- ユーザー管理関連 ---

def get_all_users():
    """全てのユーザー情報を取得します（パスワードハッシュは含まない）"""
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row # カラム名をキーとしてアクセスできるようにする
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, role, report_save_path, created_at FROM users ORDER BY username")
        users_data = cursor.fetchall()
        return [dict(row) for row in users_data]

def update_user_role(user_id, new_role):
    """ユーザーのロールを更新します"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, user_id))
        conn.commit()

def update_user_password(user_id, new_password):
    """ユーザーのパスワードをリセットします（ハッシュ化して保存）"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hashed_password, user_id))
        conn.commit()

def update_user_report_save_path(user_id, new_path):
    """ユーザーのレポート保存パスを更新します"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET report_save_path = ? WHERE id = ?", (new_path, user_id))
        conn.commit()

def delete_user(user_id):
    """ユーザーを削除します"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()

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