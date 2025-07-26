import streamlit as st
import sqlite3
import pandas as pd
import os
import shutil
import datetime
import json
import time
import jwt
import requests
from dotenv import load_dotenv
import bcrypt # bcryptライブラリをインポート
import os # 環境変数を読み込むためにosモジュールをインポート
from weasyprint import HTML # PDF生成のためにWeasyPrintをインポート

# --- HTMLテンプレートの定義 ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>インシデント報告書 - ID: {id}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; margin: 20px; background-color: #f4f4f4; }}
        .container {{ max-width: 800px; margin: auto; background: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1, h2, h3 {{ color: #0056b3; border-bottom: 2px solid #eee; padding-bottom: 5px; margin-top: 20px; }}
        .section {{ margin-bottom: 20px; }}
        .field {{ margin-bottom: 10px; }}
        .field strong {{ display: inline-block; width: 150px; color: #555; }}
        .situation, .countermeasure {{ border: 1px solid #ddd; padding: 15px; border-radius: 5px; background-color: #f9f9f9; white-space: pre-wrap; }}
        .footer {{ text-align: center; margin-top: 30px; font-size: 0.8em; color: #777; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>インシデント報告書</h1>
        <div class="section">
            <h2>基本情報</h2>
            <div class="field"><strong>報告ID:</strong> {id}</div>
            <div class="field"><strong>発生日時:</strong> {occurrence_datetime}</div>
            <div class="field"><strong>報告者氏名:</strong> {reporter_name}</div>
            <div class="field"><strong>職種:</strong> {job_type}</div>
            <div class="field"><strong>影響度レベル:</strong> {level}</div>
            <div class="field"><strong>発生場所:</strong> {location}</div>
            <div class="field"><strong>事故との関連性:</strong> {connection_with_accident}</div>
            <div class="field"><strong>総実務経験:</strong> {years_of_experience}</div>
            <div class="field"><strong>入職年数:</strong> {years_since_joining}</div>
        </div>

        <div class="section">
            <h2>患者情報</h2>
            <div class="field"><strong>患者ID:</strong> {patient_ID}</div>
            <div class="field"><strong>患者氏名:</strong> {patient_name}</div>
            <div class="field"><strong>性別:</strong> {patient_gender}</div>
            <div class="field"><strong>年齢:</strong> {patient_age}</div>
            <div class="field"><strong>認知症の有無:</strong> {dementia_status}</div>
            <div class="field"><strong>事故などによる患者の状態変化:</strong> {patient_status_change_accident}</div>
            <div class="field"><strong>患者への説明:</strong> {patient_status_change_patient_explanation}</div>
            <div class="field"><strong>家族への説明:</strong> {patient_status_change_family_explanation}</div>
        </div>

        <div class="section">
            <h2>インシデントの詳細</h2>
            <div class="field"><strong>大分類:</strong> {content_category}</div>
            <div class="field"><strong>詳細内容:</strong> {content_details}</div>
            <div class="field"><strong>発生・発見の原因:</strong> {cause_details}</div>
            <div class="field"><strong>マニュアルとの関連:</strong> {manual_relation}</div>
        </div>

        <div class="section">
            <h2>状況と対策</h2>
            <h3>発生の状況と直後の対応</h3>
            <div class="situation">{situation}</div>
            <h3>今後の対策</h3>
            <div class="countermeasure">{countermeasure}</div>
        </div>

        <div class="footer">
            <p>報告書生成日時: {created_at}</p>
        </div>
    </div>
</body>
</html>
"""

def generate_report_html_content(report_data: dict) -> str:
    """レポートデータからHTMLコンテンツを生成します"""
    # 辞書内のNone値を空文字列に変換して、format()でエラーが出ないようにする
    formatted_data = {k: v if v is not None else "N/A" for k, v in report_data.items()}
    
    # 日付/時刻のフォーマット
    if 'occurrence_datetime' in formatted_data and formatted_data['occurrence_datetime'] != "N/A":
        try:
            dt_obj = datetime.datetime.fromisoformat(formatted_data['occurrence_datetime'])
            formatted_data['occurrence_datetime'] = dt_obj.strftime("%Y年%m月%d日 %H時%M分")
        except ValueError:
            pass # 変換できない場合はそのまま

    if 'created_at' in formatted_data and formatted_data['created_at'] != "N/A":
        try:
            dt_obj = datetime.datetime.fromisoformat(formatted_data['created_at'])
            formatted_data['created_at'] = dt_obj.strftime("%Y年%m月%d日 %H時%M分%S秒")
        except ValueError:
            pass # 変換できない場合はそのまま

    return HTML_TEMPLATE.format(**formatted_data)

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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

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

def add_user(username, password, role='general'):
    """新しいユーザーをデータベースに追加します。パスワードはハッシュ化されます。"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        try:
            cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                           (username, hashed_password, role))
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
        cursor.execute("SELECT id, username, password_hash, role FROM users WHERE username = ?", (username,))
        user_data = cursor.fetchone()
        if user_data:
            return dict(user_data)
        return None

def verify_password(plain_password, hashed_password):
    """平文パスワードとハッシュ化されたパスワードを比較して検証します。"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_lineworks_access_token():
    """Line Works APIのアクセストークンを取得します"""
    load_dotenv()
    consumer_key = os.getenv("LINEWORKS_SERVER_API_CONSUMER_KEY")
    client_secret = os.getenv("LINEWORKS_CLIENT_SECRET")
    service_account = os.getenv("LINEWORKS_SERVICE_ACCOUNT")
    private_key_path = os.getenv("LINEWORKS_PRIVATE_KEY_PATH")

    if not all([consumer_key, client_secret, service_account, private_key_path]):
        print("ERROR: Line Worksの認証情報(CONSUMER_KEY, CLIENT_SECRET, SERVICE_ACCOUNT, PRIVATE_KEY_PATH)が.envファイルに設定されていません。")
        return None

    try:
        with open(private_key_path, 'r') as f:
            private_key = f.read()
        print(f"DEBUG: .envから認証情報を読み込み、秘密鍵を '{private_key_path}' から読み込みました。")
    except FileNotFoundError:
        print(f"ERROR: 秘密鍵ファイルが見つかりません: {private_key_path}")
        return None
    except Exception as e:
        print(f"ERROR: 秘密鍵ファイルの読み込み中にエラーが発生しました: {e}")
        return None

    # JWTの生成
    payload = {
        "iss": consumer_key,
        "sub": service_account,
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600  # 1時間有効
    }
    
    try:
        token = jwt.encode(payload, private_key, algorithm="RS256")
        print(f"DEBUG: JWTを生成しました: {token[:30]}...")
    except Exception as e:
        print(f"ERROR: JWTの生成に失敗しました: {e}")
        return None

    # アクセストークンのリクエスト
    url = "https://auth.worksmobile.com/oauth2/v2.0/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "assertion": token,
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "client_id": consumer_key,
        "client_secret": client_secret,
        "scope": "bot bot.message file"  # 必要なスコープをスペースで区切って指定
    }
    
    print(f"DEBUG: アクセストークンをリクエストします。URL: {url}")
    
    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status() # エラーがあれば例外を発生
        access_token = response.json().get("access_token")
        print(f"DEBUG: アクセストークンを取得しました: {access_token[:15]}...")
        return access_token
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Line Worksのアクセストークン取得に失敗しました: {e}")
        print(f"Response Status: {response.status_code}, Response Body: {response.text}")
        return None

def upload_file_to_lineworks(access_token, file_path):
    """Line WorksにファイルをアップロードしてfileIdを取得します (2ステップ方式)"""
    load_dotenv()
    bot_no = os.getenv("LINEWORKS_BOT_NO")
    if not bot_no:
        print("ERROR: LINEWORKS_BOT_NOが.envファイルに設定されていません。")
        return None

    # --- ステップ1: アップロードURLとfileIdの取得 ---
    init_url = f"https://www.worksapis.com/v1.0/bots/{bot_no}/attachments"
    headers_init = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    try:
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
    except FileNotFoundError:
        print(f"ERROR: アップロードするファイルが見つかりません: {file_path}")
        return None

    data_init = {
        "fileName": file_name,
        "fileSize": file_size
    }

    print(f"DEBUG: [ステップ1] アップロードを初期化します。URL: {init_url}, Data: {json.dumps(data_init)}")
    
    try:
        response_init = requests.post(init_url, headers=headers_init, json=data_init)
        response_init.raise_for_status()
        response_data = response_init.json()
        upload_url = response_data.get("uploadUrl")
        file_id = response_data.get("fileId")
        if not upload_url or not file_id:
            print(f"ERROR: uploadUrlまたはfileIdの取得に失敗しました。Response: {response_data}")
            return None
        print(f"DEBUG: [ステップ1] 成功。uploadUrlとfileIdを取得しました。fileId: {file_id}")
    except requests.exceptions.RequestException as e:
        print(f"ERROR: [ステップ1] アップロード初期化に失敗しました: {e}")
        print(f"Response Status: {response_init.status_code}, Response Body: {response_init.text}")
        return None

    # --- ステップ2: ファイルコンテンツのアップロード ---
    headers_upload = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/pdf"
    }
    print(f"DEBUG: [ステップ2] ファイルコンテンツをアップロードします。URL: {upload_url}")
    
    try:
        with open(file_path, 'rb') as f:
            response_upload = requests.put(upload_url, headers=headers_upload, data=f)
            response_upload.raise_for_status()
        print(f"DEBUG: [ステップ2] ファイルコンテンツのアップロードに成功しました。")
        return file_id # 最終的にfileIdを返す
    except requests.exceptions.RequestException as e:
        print(f"ERROR: [ステップ2] ファイルコンテンツのアップロードに失敗しました: {e}")
        print(f"Response Status: {response_upload.status_code}, Response Body: {response_upload.text}")
        return None

def post_report_to_lineworks(report_data, pdf_path):
    """レポートのPDFをLine Works Botに投稿します"""
    load_dotenv()
    bot_no = os.getenv("LINEWORKS_BOT_NO")
    room_id = os.getenv("LINEWORKS_ROOM_ID")

    if not all([bot_no, room_id]):
        print("ERROR: Line WorksのBot NoまたはRoom IDが.envファイルに設定されていません。")
        return

    access_token = get_lineworks_access_token()
    if not access_token:
        return

    file_id = upload_file_to_lineworks(access_token, pdf_path)
    if not file_id:
        return

    # メッセージの送信
    url = f"https://www.worksapis.com/v1.0/bots/{bot_no}/rooms/{room_id}/messages"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    message_content = f"【新規承認レポート】\nレポートID: {report_data.get('id')}\n発生日時: {report_data.get('occurrence_datetime')}\n報告者: {report_data.get('reporter_name')}\n影響度レベル: {report_data.get('level')}\n\n詳細は添付のPDFファイルをご確認ください。"
    
    data = {
        "content": {
            "type": "text",
            "text": message_content
        },
        "fileIds": [file_id]
    }

    print(f"DEBUG: メッセージを投稿します。URL: {url}, Data: {json.dumps(data, indent=2)}")

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        print("Line Worksへのレポート投稿に成功しました。")
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Line Worksへのメッセージ投稿に失敗しました: {e}")
        print(f"Response Status: {response.status_code}, Response Body: {response.text}")

# --- レポート関連 ---

def get_report_by_id(report_id: int):
    """IDで特定のインシデント報告を取得します"""
    with get_db_connection() as conn:
        df = pd.read_sql("SELECT * FROM reports WHERE id = ?", conn, params=(report_id,))
        if not df.empty:
            return df.iloc[0].to_dict()
        return None

def generate_and_save_report_csv(report_data: dict, approver_id: int = None):
    """レポートデータをCSV形式で生成し、ファイルとして保存します"""
    if not report_data:
        print("DEBUG: generate_and_save_report_csv: report_data is empty.")
        return

    # --- ここにCSVファイルの保存先パスを指定してください ---
    # 例: output_dir = "C:\Users\YourName\Documents\ApprovedReports"
    # 例: output_dir = os.path.join(os.path.expanduser("~"), "Desktop", "ApprovedReports") # デスクトップに保存する場合
    output_dir = "\\\\192.168.11.200\\share\\ネット端末共有\\インシデント・アクシデント報告\\CSV" # デフォルトはアプリケーション実行ディレクトリ内のapproved_reports
    # ---------------------------------------------------
    
    print(f"DEBUG: generate_and_save_report_csv: Determined output_dir: {output_dir}")

    try:
        os.makedirs(output_dir, exist_ok=True)
        print(f"DEBUG: generate_and_save_report_csv: Directory created/exists: {output_dir}")
    except Exception as e:
        print(f"ERROR: generate_and_save_report_csv: Failed to create directory {output_dir}: {e}")
        return

    # ファイル名を発生日で生成
    occurrence_date_str = "unknown_date"
    if report_data.get('occurrence_datetime'):
        try:
            occurrence_dt = datetime.datetime.fromisoformat(report_data['occurrence_datetime'])
            occurrence_date_str = occurrence_dt.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            pass # 変換できない場合はデフォルト値を使用

    filename = f"{occurrence_date_str}_report_{report_data.get('id', 'unknown')}.csv"
    filepath = os.path.join(output_dir, filename)
    print(f"DEBUG: generate_and_save_report_csv: Constructed filepath: {filepath}")

    # DataFrameに変換してCSVとして保存
    df = pd.DataFrame([report_data])
    try:
        df.to_csv(filepath, index=False, encoding='utf-8-sig') # Excelで開けるようにutf-8-sig
        print(f"DEBUG: CSVレポートを保存しました: {filepath}")
    except Exception as e:
        print(f"ERROR: generate_and_save_report_csv: Failed to save CSV to {filepath}: {e}")

def generate_and_save_report_pdf(report_data: dict, approver_id: int = None):
    """レポートデータをPDF形式で生成し、ファイルとして保存します"""
    if not report_data:
        print("DEBUG: generate_and_save_report_pdf: report_data is empty.")
        return

    output_dir = "\\\\192.168.11.200\\share\\ネット端末共有\\インシデント・アクシデント報告\\レポート" # PDFの保存先パス
    # ユーザーごとのパス設定を考慮する場合は、generate_and_save_report_csvと同様のロジックを追加

    print(f"DEBUG: generate_and_save_report_pdf: Determined output_dir: {output_dir}")

    try:
        os.makedirs(output_dir, exist_ok=True)
        print(f"DEBUG: generate_and_save_report_pdf: Directory created/exists: {output_dir}")
    except Exception as e:
        print(f"ERROR: generate_and_save_report_pdf: Failed to create directory {output_dir}: {e}")
        return

    # ファイル名を発生日で生成
    occurrence_date_str = "unknown_date"
    if report_data.get('occurrence_datetime'):
        try:
            occurrence_dt = datetime.datetime.fromisoformat(report_data['occurrence_datetime'])
            occurrence_date_str = occurrence_dt.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            pass # 変換できない場合はデフォルト値を使用

    filename = f"{occurrence_date_str}_report_{report_data.get('id', 'unknown')}.pdf"
    filepath = os.path.join(output_dir, filename)
    print(f"DEBUG: generate_and_save_report_pdf: Constructed filepath: {filepath}")

    # HTMLコンテンツを生成
    html_content = generate_report_html_content(report_data)

    try:
        HTML(string=html_content).write_pdf(filepath)
        print(f"DEBUG: PDFレポートを保存しました: {filepath}")
        # Line Worksへの投稿処理を呼び出す
        post_report_to_lineworks(report_data, filepath)
    except Exception as e:
        print(f"ERROR: generate_and_save_report_pdf: Failed to save PDF to {filepath}: {e}")

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

        # ステータスが「承認済み」の場合、CSVとPDFを生成
        if data['status'] == '承認済み':
            report = get_report_by_id(report_id)
            if report:
                generate_and_save_report_csv(report, approver_id=None) # 過去データ報告からの追加なのでapprover_idはNone
                generate_and_save_report_pdf(report, approver_id=None) # PDFも生成

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

        # ステータスが「承認済み」になった場合、CSVとPDFを生成
        if 'status' in updates and updates['status'] == '承認済み':
            report = get_report_by_id(report_id)
            if report:
                generate_and_save_report_csv(report, approver_id)
                generate_and_save_report_pdf(report, approver_id) # PDFも生成

def get_all_reports():
    """全てのインシデント報告を取得します"""
    with get_db_connection() as conn:
        # index_col='id' を指定すると、DataFrameのインデックスがid列になる
        df = pd.read_sql("SELECT * FROM reports ORDER BY occurrence_datetime DESC", conn, index_col='id')
        return df

def update_report(report_id: int, data: dict):
    """指定されたIDのレポートを更新します"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        set_clauses = [f"{key} = ?" for key in data.keys()]
        sql = f"UPDATE reports SET {', '.join(set_clauses)} WHERE id = ?"
        
        values = list(data.values())
        values.append(report_id)
        
        cursor.execute(sql, tuple(values))
        conn.commit()

def delete_report(report_id: int):
    """指定されたIDのレポートを削除します"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM reports WHERE id = ?", (report_id,))
        conn.commit()

# --- ユーザー管理関連 ---

def get_all_users():
    """全てのユーザー情報を取得します（パスワードハッシュは含まない）"""
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row # カラム名をキーとしてアクセスできるようにする
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, role, created_at FROM users ORDER BY username")
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