from db_utils import add_user, get_user_by_username, init_db

def create_initial_admin():
    init_db() # データベースとテーブルを初期化

    username = "admin"
    password = "Kco-0403"
    role = "admin"

    # ユーザーが既に存在するか確認
    existing_user = get_user_by_username(username)
    if existing_user:
        print(f"ユーザー '{username}' は既に存在します。")
        return
    # ユーザーを追加
    if add_user(username, password, role):
        print(f"管理者ユーザー '{username}' を正常に作成しました。")
    else:
        print(f"管理者ユーザー '{username}' の作成に失敗しました。")

if __name__ == "__main__":
    create_initial_admin()