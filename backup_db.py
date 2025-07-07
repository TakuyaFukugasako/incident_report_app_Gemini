import os
import shutil
import datetime

# データベースファイルの名前
DB_NAME = "incident_reports.db"
# バックアップを保存するディレクトリ
BACKUP_DIR = "backups"

def backup_database():
    # バックアップディレクトリが存在しない場合は作成
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        print(f"バックアップディレクトリ '{BACKUP_DIR}' を作成しました。")

    # バックアップファイル名に日付を追加
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    backup_file_name = f"incident_reports_{today_str}.db"
    
    # 元のデータベースファイルのパス
    source_path = os.path.join(os.getcwd(), DB_NAME)
    # バックアップファイルの保存先パス
    destination_path = os.path.join(os.getcwd(), BACKUP_DIR, backup_file_name)

    try:
        # データベースファイルをコピー
        shutil.copy2(source_path, destination_path)
        print(f"データベース '{DB_NAME}' のバックアップを '{destination_path}' に作成しました。")
    except FileNotFoundError:
        print(f"エラー: データベースファイル '{DB_NAME}' が見つかりません。")
    except Exception as e:
        print(f"エラー: データベースのバックアップ中に問題が発生しました: {e}")

if __name__ == "__main__":
    backup_database()