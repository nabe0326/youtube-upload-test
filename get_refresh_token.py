#!/usr/bin/env python3
"""
Google OAuth 2.0 Refresh Token取得スクリプト
YouTube Data API v3のリフレッシュトークンを取得します
"""

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

def get_refresh_token(client_id: str, client_secret: str):
    """
    Google OAuth 2.0のリフレッシュトークンを取得

    Args:
        client_id: Google Cloud ConsoleのOAuth 2.0クライアントID
        client_secret: Google Cloud ConsoleのOAuth 2.0クライアントシークレット

    Returns:
        リフレッシュトークン文字列
    """
    # OAuth 2.0フローの設定
    flow = InstalledAppFlow.from_client_config(
        {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost"]
            }
        },
        SCOPES
    )

    print("\n" + "="*60)
    print("YouTube API リフレッシュトークン取得ツール")
    print("="*60 + "\n")
    print("ブラウザが開きます。Googleアカウントでログインして、")
    print("YouTube動画のアップロード権限を許可してください。\n")

    # ローカルサーバーを起動して認証フローを実行
    credentials = flow.run_local_server(
        port=0,
        success_message='認証が完了しました。このウィンドウを閉じてターミナルに戻ってください。'
    )

    print("\n" + "="*60)
    print("✓ 認証が完了しました！")
    print("="*60 + "\n")
    print("以下のリフレッシュトークンをGitHub Secretsに設定してください：")
    print("\nシークレット名: YOUTUBE_REFRESH_TOKEN")
    print(f"値: {credentials.refresh_token}\n")
    print("="*60 + "\n")

    return credentials.refresh_token


def main():
    print("\n" + "="*60)
    print("YouTube API 認証情報の入力")
    print("="*60 + "\n")
    print("Google Cloud Consoleで取得した情報を入力してください。")
    print("取得方法: https://console.cloud.google.com/ > 認証情報\n")

    client_id = input("Client ID: ").strip()
    client_secret = input("Client Secret: ").strip()

    if not client_id or not client_secret:
        print("\n✗ エラー: Client IDとClient Secretは必須です", file=sys.stderr)
        return 1

    try:
        get_refresh_token(client_id, client_secret)
        return 0
    except Exception as e:
        print(f"\n✗ エラーが発生しました: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
