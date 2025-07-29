import os
import json
import jwt
from datetime import datetime
import urllib
import requests
from dotenv import load_dotenv

# .envファイルを読み込む
load_dotenv()

BASE_API_URL = "https://www.worksapis.com/v1.0"
BASE_AUTH_URL = "https://auth.worksmobile.com/oauth2/v2.0"

# --- 内部ヘルパー関数 ---

def _get_jwt(client_id, service_account_id, privatekey):
    current_time = datetime.now().timestamp()
    jws = jwt.encode({
        "iss": client_id, "sub": service_account_id, 
        "iat": current_time, "exp": current_time + 3600
    }, privatekey, algorithm="RS256")
    return jws

def _get_access_token(client_id, client_secret, scope, jws):
    url = f'{BASE_AUTH_URL}/token'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    params = {
        "assertion": jws,
        "grant_type": urllib.parse.quote("urn:ietf:params:oauth:grant-type:jwt-bearer"),
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": scope,
    }
    r = requests.post(url=url, data=params, headers=headers)
    r.raise_for_status()
    return r.json().get("access_token")

def _get_upload_url_and_file_id(file_name, bot_id, access_token):
    url = f"{BASE_API_URL}/bots/{bot_id}/attachments"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    response = requests.post(url, headers=headers, json={"fileName": file_name})
    response.raise_for_status()
    data = response.json()
    return data["uploadUrl"], data["fileId"]

def _upload_file_multipart(upload_url, file_path, access_token):
    with open(file_path, "rb") as f:
        headers = {"Authorization": f"Bearer {access_token}"}
        files = {'FileData': (os.path.basename(file_path), f, 'application/pdf')}
        response = requests.post(upload_url, headers=headers, files=files)
        response.raise_for_status()

def _send_bot_message_to_channel(content, bot_id, channel_id, access_token):
    url = f"{BASE_API_URL}/bots/{bot_id}/channels/{channel_id}/messages"
    headers = {'Content-Type' : 'application/json', 'Authorization' : f"Bearer {access_token}"}
    r = requests.post(url=url, data=json.dumps(content), headers=headers)
    r.raise_for_status()

# --- 外部呼び出し用の公開関数 ---

def send_file_to_channel(file_path: str, channel_id: str, bot_id: str = None):
    """
    指定されたファイルを指定されたチャンネル（トークルーム）に送信する。
    Args:
        file_path (str): 送信するファイルのパス。
        channel_id (str): 送信先のチャンネルID。
        bot_id (str, optional): 使用するBotのID。指定しない場合は環境変数から読み込む。
    Returns:
        bool: 成功した場合はTrue、失敗した場合はFalse。
    """
    try:
        print(f"--- 開始: ファイル送信処理 (To Channel: {channel_id}) ---")
        # 環境変数から設定を読み込み
        client_id = os.environ.get("LW_API_20_CLIENT_ID")
        client_secret = os.environ.get("LW_API_20_CLIENT_SECRET")
        service_account_id = os.environ.get("LW_API_20_SERVICE_ACCOUNT_ID")
        privatekey_raw = os.environ.get("LW_API_20_PRIVATEKEY")
        
        # bot_idが引数で指定されていない場合は環境変数から読み込む
        actual_bot_id = bot_id if bot_id else os.environ.get("LW_API_20_BOT_ID")
        
        if not all([client_id, client_secret, service_account_id, privatekey_raw, actual_bot_id]):
            raise ValueError("必要な環境変数が設定されていないか、Bot IDが指定されていません。")
        
        privatekey = privatekey_raw.replace('\n', '\n')

        # 1. アクセストークン取得
        print("1. アクセストークンを取得中...")
        jwt_token = _get_jwt(client_id, service_account_id, privatekey)
        access_token = _get_access_token(client_id, client_secret, "bot", jwt_token)
        if not access_token:
            raise ValueError("アクセストークンの取得に失敗しました。")
        print("   -> 取得成功")

        # 2. アップロードURLとfileIdを取得
        file_name = os.path.basename(file_path)
        print(f"2. {file_name} のアップロードURLを取得中...")
        upload_url, file_id = _get_upload_url_and_file_id(file_name, bot_id, access_token)
        print(f"   -> 取得成功 (fileId: {file_id})")

        # 3. ファイルをアップロード
        print("3. ファイルをアップロード中...")
        _upload_file_multipart(upload_url, file_path, access_token)
        print("   -> アップロード成功")

        # 4. メッセージを送信
        print("4. ファイルメッセージをチャンネルに送信中...")
        file_content = {"content": {"type": "file", "fileId": file_id}}
        _send_bot_message_to_channel(file_content, bot_id, channel_id, access_token)
        print("   -> 送信成功")
        
        print("--- 完了: 全ての処理が成功しました ---")
        return True

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return False

def send_text_message_to_channel(text_message: str, channel_id: str, bot_id: str = None):
    """
    指定されたテキストメッセージを指定されたチャンネル（トークルーム）に送信する。
    Args:
        text_message (str): 送信するテキストメッセージ。
        channel_id (str): 送信先のチャンネルID。
        bot_id (str, optional): 使用するBotのID。指定しない場合は環境変数から読み込む。
    Returns:
        bool: 成功した場合はTrue、失敗した場合はFalse。
    """
    try:
        print(f"--- 開始: テキストメッセージ送信処理 (To Channel: {channel_id}) ---")
        # 環境変数から設定を読み込み
        client_id = os.environ.get("LW_API_20_CLIENT_ID")
        client_secret = os.environ.get("LW_API_20_CLIENT_SECRET")
        service_account_id = os.environ.get("LW_API_20_SERVICE_ACCOUNT_ID")
        privatekey_raw = os.environ.get("LW_API_20_PRIVATEKEY")
        
        # bot_idが引数で指定されていない場合は環境変数から読み込む
        actual_bot_id = bot_id if bot_id else os.environ.get("LW_API_20_BOT_ID")
        
        if not all([client_id, client_secret, service_account_id, privatekey_raw, actual_bot_id]):
            raise ValueError("必要な環境変数が設定されていないか、Bot IDが指定されていません。")
        
        privatekey = privatekey_raw.replace('\n', '\n')

        # 1. アクセストークン取得
        print("1. アクセストークンを取得中...")
        jwt_token = _get_jwt(client_id, service_account_id, privatekey)
        access_token = _get_access_token(client_id, client_secret, "bot", jwt_token)
        if not access_token:
            raise ValueError("アクセストークンの取得に失敗しました。")
        print("   -> 取得成功")

        # 2. テキストメッセージを送信
        print("2. テキストメッセージをチャンネルに送信中...")
        text_content = {"content": {"type": "text", "text": text_message}}
        _send_bot_message_to_channel(text_content, bot_id, channel_id, access_token)
        print("   -> 送信成功")
        
        print("--- 完了: 全ての処理が成功しました ---")
        return True

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return False