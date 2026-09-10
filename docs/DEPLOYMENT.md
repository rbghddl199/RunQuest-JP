# RunQuest デプロイチェックリスト

現在のプロジェクトはローカルデモを前提に構成されています。実際にデプロイする場合は、以下の項目を順に確認してください。

## 環境変数

| 変数 | 説明 |
| --- | --- |
| `DJANGO_DEBUG=False` | 本番環境ではデバッグモードを無効にします。 |
| `DJANGO_SECRET_KEY` | 十分に長いランダム文字列を設定します。 |
| `DJANGO_ALLOWED_HOSTS` | デプロイ先ドメインとサーバーホストを登録します。 |
| `DJANGO_CORS_ALLOWED_ORIGINS` | フロントエンドのデプロイ先アドレスを登録します。 |
| `VITE_API_BASE_URL` | HTTPS のバックエンド API アドレスを設定します。 |
| `VITE_KAKAO_MAP_APP_KEY` | Kakao Map JavaScript キーを設定します。 |
| `OPENAI_API_KEY` | 外部 AI フィードバックを使用する場合に設定します。 |

## デプロイ前の作業

1. `.env` が Git に含まれていないことを確認する。
2. `python manage.py check` を実行する。
3. `python manage.py test core` を実行する。
4. `npm run build` を実行する。
5. 本番用 DB を使用する場合はマイグレーションを適用する。
6. `python manage.py collectstatic --noinput` を実行する。
7. Kakao Developers にフロントエンドの HTTPS ドメインを登録する。
8. ブラウザの GPS 利用のため HTTPS で配信する。

## ローカルコンテナ実行

```powershell
docker compose up --build
```

## fixture データの読み込み

```powershell
cd backend
python manage.py load_runquest_fixtures --reset
```

## デプロイ後の確認事項

| 確認項目 | 確認内容 |
| --- | --- |
| ログイン | JWT の発行とトークン更新が正常か確認 |
| 地図 | Kakao Map がデプロイ先ドメインで読み込まれるか確認 |
| GPS | HTTPS 環境で位置情報権限とリアルタイム座標取得を確認 |
| コミュニティ | 一覧・詳細・投稿・コメント・いいねの動作確認 |
| チャットボット | 外部 AI 設定の有無と fallback 応答を確認 |
| ログ | 低速リクエストとエラーログを確認 |
