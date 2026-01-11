# YouTube Upload via GitHub Actions

GitHub ActionsでYouTube Data API v3を使用して動画をアップロードするシステムです。
Difyワークフローなどの外部サービスから呼び出すことができます。

## 機能

- Cloudinary等の外部URLから動画をダウンロード
- YouTube APIを使用して動画をアップロード
- タイトル、説明、タグ、カテゴリ、プライバシー設定のカスタマイズ
- Difyワークフローからの呼び出し対応
- 手動トリガー（テスト用）

## セットアップ

### 1. YouTube API認証情報の取得

#### 1.1 Google Cloud Projectの作成

1. [Google Cloud Console](https://console.cloud.google.com/)にアクセス
2. 新しいプロジェクトを作成
3. 「APIとサービス」→「ライブラリ」から「YouTube Data API v3」を有効化

#### 1.2 OAuth 2.0クライアントIDの作成

1. 「APIとサービス」→「認証情報」に移動
2. 「認証情報を作成」→「OAuth クライアント ID」を選択
3. アプリケーションの種類：「デスクトップアプリ」を選択
4. 名前を入力して作成
5. `クライアントID`と`クライアントシークレット`をメモ

#### 1.3 リフレッシュトークンの取得

リフレッシュトークンを取得するためのスクリプトを作成します：

```python
# get_refresh_token.py
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

def get_refresh_token(client_id, client_secret):
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

    credentials = flow.run_local_server(port=0)
    print(f"\nRefresh Token: {credentials.refresh_token}")
    return credentials.refresh_token

if __name__ == '__main__':
    client_id = input("Enter your Client ID: ")
    client_secret = input("Enter your Client Secret: ")
    get_refresh_token(client_id, client_secret)
```

実行方法：

```bash
pip install google-auth-oauthlib
python get_refresh_token.py
```

ブラウザが開くので、YouTubeアカウントでログインして権限を許可してください。
表示された`Refresh Token`をメモします。

### 2. GitHub Secretsの設定

リポジトリの「Settings」→「Secrets and variables」→「Actions」→「New repository secret」で以下を追加：

- `YOUTUBE_CLIENT_ID`: Google OAuth クライアントID
- `YOUTUBE_CLIENT_SECRET`: Google OAuth クライアントシークレット
- `YOUTUBE_REFRESH_TOKEN`: 取得したリフレッシュトークン

### 3. Personal Access Token（PAT）の作成（Difyから呼び出す場合）

repository_dispatchイベントをトリガーするため、PATが必要です：

1. GitHubの「Settings」→「Developer settings」→「Personal access tokens」→「Tokens (classic)」
2. 「Generate new token」→「Generate new token (classic)」
3. スコープで`repo`を選択
4. トークンを生成してメモ
5. このトークンをDifyに設定します

## 使用方法

### 手動トリガー（テスト用）

1. GitHubリポジトリの「Actions」タブに移動
2. 「YouTube Video Upload」ワークフローを選択
3. 「Run workflow」をクリック
4. 以下のパラメータを入力：
   - **video_url**: 動画のURL（Cloudinaryなど）
   - **title**: 動画タイトル
   - **description**: 動画説明（オプション）
   - **tags**: タグ（カンマ区切り、オプション）
   - **category_id**: カテゴリID（デフォルト: 22）
   - **privacy**: プライバシー設定（private/public/unlisted）

### Difyから呼び出す

DifyワークフローでHTTPリクエストノードを使用：

**エンドポイント:**
```
POST https://api.github.com/repos/{owner}/{repo}/dispatches
```

**ヘッダー:**
```
Authorization: Bearer {YOUR_GITHUB_PAT}
Accept: application/vnd.github.v3+json
Content-Type: application/json
```

**ボディ:**
```json
{
  "event_type": "upload-video",
  "client_payload": {
    "video_url": "https://res.cloudinary.com/xxx/video/upload/xxx.mp4",
    "title": "動画タイトル",
    "description": "動画の説明",
    "tags": "tag1,tag2,tag3",
    "category_id": "22",
    "privacy": "private",
    "callback_url": "https://your-dify-webhook-url.com/callback"
  }
}
```

**パラメータ説明:**

| パラメータ | 必須 | デフォルト | 説明 |
|----------|------|-----------|------|
| video_url | ✓ | - | 動画のURL（Cloudinary等） |
| title | ✓ | - | 動画タイトル |
| description | | "" | 動画の説明文 |
| tags | | "" | タグ（カンマ区切り） |
| category_id | | "22" | YouTubeカテゴリID |
| privacy | | "private" | プライバシー設定（private/public/unlisted） |
| callback_url | | - | アップロード完了後の結果を受け取るWebhook URL |

**YouTubeカテゴリID一覧:**

- 1: Film & Animation
- 2: Autos & Vehicles
- 10: Music
- 15: Pets & Animals
- 17: Sports
- 19: Travel & Events
- 20: Gaming
- 22: People & Blogs
- 23: Comedy
- 24: Entertainment
- 25: News & Politics
- 26: Howto & Style
- 27: Education
- 28: Science & Technology

**コールバックレスポンス形式:**

アップロード完了後、指定した`callback_url`に以下の形式でPOSTリクエストが送信されます。

成功時：
```json
{
  "success": true,
  "video_id": "dQw4w9WgXcQ",
  "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "title": "動画タイトル",
  "message": "Video uploaded successfully"
}
```

失敗時：
```json
{
  "success": false,
  "error": "エラーメッセージ",
  "title": "動画タイトル",
  "message": "Video upload failed"
}
```

Difyワークフローでこのレスポンスを受け取るには：
1. Webhookノードを作成してURLを取得
2. そのURLを`callback_url`として渡す
3. Webhookノードで`video_url`などの値を取得して次のノードで利用

### curl でのテスト

```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_GITHUB_PAT" \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Content-Type: application/json" \
  https://api.github.com/repos/YOUR_USERNAME/youtube-upload-test/dispatches \
  -d '{
    "event_type": "upload-video",
    "client_payload": {
      "video_url": "https://res.cloudinary.com/xxx/video/upload/xxx.mp4",
      "title": "テスト動画",
      "description": "これはテスト動画です",
      "tags": "test,github-actions",
      "privacy": "private",
      "callback_url": "https://webhook.site/your-unique-id"
    }
  }'
```

注: `callback_url`は[webhook.site](https://webhook.site/)などのテストサービスで動作確認できます。

## ローカルでの実行

```bash
# 依存関係をインストール
pip install -r requirements.txt

# 環境変数を設定
export YOUTUBE_CLIENT_ID="your_client_id"
export YOUTUBE_CLIENT_SECRET="your_client_secret"
export YOUTUBE_REFRESH_TOKEN="your_refresh_token"

# スクリプトを実行
python src/upload_youtube.py \
  --video-url "https://res.cloudinary.com/xxx/video/upload/xxx.mp4" \
  --title "テスト動画" \
  --description "これはテスト動画です" \
  --tags "test,local" \
  --privacy "private"
```

## トラブルシューティング

### 認証エラー

- `YOUTUBE_CLIENT_ID`、`YOUTUBE_CLIENT_SECRET`、`YOUTUBE_REFRESH_TOKEN`が正しく設定されているか確認
- リフレッシュトークンが有効か確認（期限切れの場合は再取得）

### ダウンロードエラー

- 動画URLが有効か確認
- Cloudinaryの動画が公開設定になっているか確認
- ネットワーク接続を確認

### アップロードエラー

- YouTube API quotaを確認（1日10,000ユニット）
- 動画形式がYouTubeでサポートされているか確認
- 動画サイズが制限内か確認（通常アカウント: 最大15分/256GB）

## ライセンス

MIT
