#!/bin/bash
#
# GitHub Gist作成スクリプト
# YouTube Upload結果を保存するための固定Gistを作成します
#

set -e

echo "========================================"
echo "YouTube Upload Results Gist 作成ツール"
echo "========================================"
echo ""

# GitHub Personal Access Tokenの入力
echo "GitHub Personal Access Token (PAT) を入力してください。"
echo "PATは以下のスコープが必要です: gist"
echo ""
read -sp "GitHub PAT: " GITHUB_TOKEN
echo ""
echo ""

# Gistを作成
echo "Gistを作成しています..."

GIST_RESPONSE=$(curl -s -X POST https://api.github.com/gists \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "YouTube Upload Results Storage",
    "public": false,
    "files": {
      "README.md": {
        "content": "# YouTube Upload Results\n\nThis Gist stores the results of YouTube video uploads.\n\nFiles are automatically managed by GitHub Actions:\n- New results are added as `youtube-upload-{unique_id}.json`\n- Results older than 24 hours are automatically deleted\n\nDo not manually edit or delete this Gist."
      }
    }
  }')

# レスポンスチェック
if echo "$GIST_RESPONSE" | jq -e '.id' > /dev/null 2>&1; then
  GIST_ID=$(echo "$GIST_RESPONSE" | jq -r '.id')
  GIST_URL=$(echo "$GIST_RESPONSE" | jq -r '.html_url')

  echo ""
  echo "=========================================="
  echo "✓ Gistの作成に成功しました！"
  echo "=========================================="
  echo ""
  echo "Gist ID: $GIST_ID"
  echo "Gist URL: $GIST_URL"
  echo ""
  echo "=========================================="
  echo "次のステップ:"
  echo "=========================================="
  echo ""
  echo "1. GitHub リポジトリの Settings に移動"
  echo "2. Secrets and variables > Actions を開く"
  echo "3. New repository secret をクリック"
  echo "4. 以下の情報で Secret を作成:"
  echo ""
  echo "   Name: RESULTS_GIST_ID"
  echo "   Value: $GIST_ID"
  echo ""
  echo "=========================================="
else
  echo ""
  echo "✗ Gistの作成に失敗しました"
  echo ""
  echo "エラー詳細:"
  echo "$GIST_RESPONSE" | jq .
  exit 1
fi
