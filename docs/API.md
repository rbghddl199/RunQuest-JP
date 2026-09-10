# RunQuest API ガイド

本ドキュメントは API の利用フローを説明します。OpenAPI ドキュメント全体は、ローカルサーバー起動後に `/api/docs/` または `/api/redoc/` で確認できます。

## 基本情報

| 項目 | 値 |
| --- | --- |
| ベースprefix | `/api/` |
| 認証方式 | JWT Bearer Token |
| ドキュメント | `/api/docs/`, `/api/redoc/`, `/api/schema/` |

## 認証フロー

1. ユーザーは `/api/auth/signup/` または `/api/auth/login/` で access token と refresh token を取得します。
2. フロントエンドは access token を `Authorization: Bearer <token>` ヘッダーに載せて API を呼び出します。
3. access token の期限が切れたら `/api/auth/token/refresh/` で更新します。
4. ログアウト時は `/api/auth/logout/` で refresh token を無効化します。

## 推薦 API フロー

1. `/api/survey/response/` にアンケート結果を保存します。
2. `/api/recommendations/generate/` に現在地を任意で渡します。
3. サーバーはアンケート、記録、位置情報、復帰ユーザーかどうかをもとに推薦セッションを生成します。
4. `/api/recommendations/current/` で現在の推薦を取得します。
5. `/api/recommendations/next/` で次の推薦を確認します。

推薦生成リクエストの例:

```json
{
  "latitude": 36.350411,
  "longitude": 127.384548
}
```

## ランニング API フロー

1. `/api/runs/start/` でランニングを開始します。
2. GPS モードでは、ブラウザの座標を定期的に `/api/runs/{id}/progress/` に保存します。
3. シミュレーションモードでは、選択したコースの座標を時間経過に応じて補間しながら progress を更新します。
4. `/api/runs/{id}/finish/` でランニングを終了します。
5. 自由ランニングでトラックポイントが十分にある場合は、`/api/runs/{id}/save-course/` でユーザーコースとして保存します。

ランニング開始リクエストの例:

```json
{
  "tracking_mode": "gps",
  "course_slug": "gapcheon-river"
}
```

ランニング終了のレスポンスには、記録・出席・新規獲得バッジ・AI フィードバック情報が含まれます。ただし移動距離が 100m 未満の場合は保存されず、キャンセル扱いのレスポンスが返されます。

## コミュニティ API フロー

コミュニティは投稿、コメント、いいね、保存、関連コース/ランニング記録との紐付けに対応しています。

一覧 API はレンダリング速度のため画像の原本や詳細な nested データを除外しており、投稿詳細 API でコメントと関連データを併せて取得します。

投稿作成リクエストの例:

```json
{
  "category": "course",
  "title": "甲川(カプチョン)の夕方ランニングおすすめ",
  "content": "風が涼しくて照明もきれいです。",
  "related_course": 1
}
```

## チャットボット API フロー

1. `/api/chat/conversation/` に GET で既存の会話を取得します。
2. 同じ endpoint に POST でユーザーメッセージを送信します。
3. サーバーはメッセージを解析し、必要に応じて推薦コースも併せて返します。
4. 外部 AI が無効な場合でも、ローカル fallback 応答で動作します。

## 通知 API フロー

通知はコメント、いいね、バッジ、推薦、システムイベントを含みます。フロントエンドは通知の `link` または `metadata` をもとに該当画面へ遷移します。
