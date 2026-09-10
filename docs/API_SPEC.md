# RunQuest API 仕様書

ベース URL は `/api/` です。認証が必要な API は `Authorization: Bearer <access_token>` ヘッダーを使用します。

## 認証

| Method | Endpoint | 説明 |
| --- | --- | --- |
| POST | `/auth/signup/` | 会員登録と JWT 発行 |
| POST | `/auth/login/` | ログインと JWT 発行 |
| POST | `/auth/token/refresh/` | access token の更新 |
| POST | `/auth/logout/` | refresh token の無効化 |
| GET | `/auth/me/` | 現在のユーザー情報取得 |
| GET/PATCH | `/auth/settings/` | ユーザー設定の取得と変更 |
| GET | `/auth/nickname-availability/` | ニックネーム重複確認 |
| POST | `/auth/password/change/` | パスワード変更 |

## ホーム・アンケート・天気

| Method | Endpoint | 説明 |
| --- | --- | --- |
| GET | `/home/` | ホームダッシュボードデータ |
| GET | `/survey/questions/` | アンケート質問一覧 |
| GET/POST | `/survey/response/` | アンケート結果の取得と保存 |
| GET | `/weather/current/` | 現在地基準の天気・大気質情報 |

## コース

| Method | Endpoint | 説明 |
| --- | --- | --- |
| GET | `/courses/` | 基本コース一覧 |
| GET | `/courses/{slug}/` | 基本コース詳細 |
| POST/DELETE | `/courses/{slug}/favorite/` | コースのブックマーク追加・解除 |
| GET | `/courses/favorites/` | ブックマークしたコース一覧 |
| GET/POST | `/custom-courses/` | ユーザーコースの一覧と作成 |
| GET/PATCH/DELETE | `/custom-courses/{id}/` | ユーザーコースの詳細、更新、削除 |

## 推薦

| Method | Endpoint | 説明 |
| --- | --- | --- |
| POST | `/recommendations/generate/` | アンケート・記録・位置情報に基づく推薦生成 |
| GET | `/recommendations/current/` | 現在の推薦取得 |
| POST | `/recommendations/next/` | 次の推薦へ移動 |

## ランニング

| Method | Endpoint | 説明 |
| --- | --- | --- |
| POST | `/runs/start/` | GPS またはシミュレーションランニングの開始 |
| GET | `/runs/active/` | 進行中のランニング取得 |
| PATCH | `/runs/{id}/progress/` | 座標、時間、一時停止状態の保存 |
| POST | `/runs/{id}/finish/` | ランニング終了と記録確定 |
| GET | `/runs/{id}/` | ランニング記録の詳細 |
| POST | `/runs/{id}/save-course/` | 自由ランニング記録をユーザーコースとして保存 |
| GET | `/profile/records/` | 自分のランニング記録一覧 |
| GET | `/profile/summary/` | 自分のランニング統計サマリー |
| GET | `/profile/attendance/` | 出席記録 |
| GET | `/profile/badges/` | バッジ一覧 |

## コミュニティ

| Method | Endpoint | 説明 |
| --- | --- | --- |
| GET/POST | `/community/posts/` | 投稿一覧と作成 |
| GET/PATCH/DELETE | `/community/posts/{id}/` | 投稿の詳細、更新、削除 |
| POST | `/community/posts/{id}/like/` | 投稿のいいねトグル |
| POST | `/community/posts/{id}/save/` | 投稿の保存トグル |
| POST | `/community/posts/{id}/comments/` | コメント投稿 |
| PATCH/DELETE | `/community/comments/{id}/` | コメントの更新と削除 |
| POST | `/community/comments/{id}/like/` | コメントのいいねトグル |

## チャットボットと通知

| Method | Endpoint | 説明 |
| --- | --- | --- |
| GET/POST/DELETE | `/chat/conversation/` | チャットボット会話の取得、送信、初期化 |
| GET | `/notifications/` | 通知一覧 |
| POST | `/notifications/read-all/` | 全通知の既読処理 |
| POST | `/notifications/{id}/read/` | 個別通知の既読処理 |

## レスポンスポリシー

| 状況 | Status Code |
| --- | --- |
| 取得成功 | `200 OK` |
| 作成成功 | `201 Created` |
| 削除成功 | `204 No Content` |
| 入力値エラー | `400 Bad Request` |
| 認証が必要 | `401 Unauthorized` |
| 権限なし | `403 Forbidden` |
| リソースなし | `404 Not Found` |
