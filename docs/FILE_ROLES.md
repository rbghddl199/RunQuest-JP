# ファイル構成の整理

## バックエンド

| パス | 役割 |
| --- | --- |
| `backend/manage.py` | Django 管理コマンドの実行エントリポイント |
| `backend/config/settings.py` | DB・認証・CORS・ロギング・パフォーマンス計測の設定 |
| `backend/config/urls.py` | 全体の URL ルーティングと API ドキュメント連携 |
| `backend/core/models.py` | ユーザー、コース、ランニング記録、コミュニティ、チャットボット、推薦の DB モデル |
| `backend/core/serializers.py` | モデルデータの API JSON 変換と入力値検証 |
| `backend/core/views.py` | 認証・コース・推薦・ランニング・コミュニティ・チャットボット API の実装 |
| `backend/core/urls.py` | core アプリの API URL ルーティング |
| `backend/core/recommendations.py` | アンケート・記録・位置情報に基づくコース推薦ロジック |
| `backend/core/running.py` | 距離・ペース・カロリー・座標の計算 |
| `backend/core/gpx.py` | GPX ファイルの解析とコースデータへの変換 |
| `backend/core/chatbot.py` | チャットボット応答とコース推薦メッセージの生成 |
| `backend/core/weather.py` | 天気・大気質情報の正規化 |
| `backend/core/notifications.py` | 通知の生成と遷移リンクの構築 |
| `backend/core/performance.py` | 関数単位の実行時間計測ユーティリティ |
| `backend/core/middleware.py` | リクエスト単位のパフォーマンスログ用ミドルウェア |
| `backend/core/migrations/` | DB スキーマ変更履歴 |
| `backend/fixtures/runquest/` | デモ用ユーザー・コース・記録・コミュニティの fixture |
| `backend/scripts/` | GPX 反映、データ検証、パフォーマンス分析用の補助スクリプト |

## フロントエンド

| パス | 役割 |
| --- | --- |
| `frontend/src/main.js` | Vue、Pinia、Router の初期化 |
| `frontend/src/App.vue` | 最上位のアプリレイアウト |
| `frontend/src/router/index.js` | 画面 URL ルーティングと認証ガード |
| `frontend/src/services/api.js` | Axios API クライアントとトークン処理 |
| `frontend/src/services/kakaoMap.js` | Kakao Map SDK の読み込み |
| `frontend/src/stores/` | 認証・コース・ランニング・推薦・コミュニティ・チャットボットの状態管理 |
| `frontend/src/views/HomeView.vue` | ホームダッシュボード |
| `frontend/src/views/RecommendationView.vue` | 推薦コース画面 |
| `frontend/src/views/RunStartView.vue` | ランニング開始、GPX 適用、GPS/シミュレーション開始 |
| `frontend/src/views/RunActiveView.vue` | ランニング中のリアルタイム記録画面 |
| `frontend/src/views/RunCompletedView.vue` | ランニング完了・フィードバック・コース保存画面 |
| `frontend/src/views/MyCoursesView.vue` | ブックマーク・自作・GPX コースの管理 |
| `frontend/src/views/CommunityView.vue` | コミュニティ一覧、検索、フィルター |
| `frontend/src/views/CommunityDetailView.vue` | 投稿詳細、コメント、いいね、保存 |
| `frontend/src/views/ChatView.vue` | チャットボットとの対話と推薦コース表示 |
| `frontend/src/components/maps/` | コース地図とリアルタイムランニング地図コンポーネント |
| `frontend/src/utils/` | 単位変換、コース画像マッピング、プロフィール画像ユーティリティ |
| `frontend/public/` | 静的画像、アイコン、プロフィールフレーム |

## ドキュメント

| パス | 役割 |
| --- | --- |
| `README.md` | プロジェクト概要、機能、技術スタック、セットアップ手順 |
| `docs/API_SPEC.md` | 主要 API 仕様 |
| `docs/API.md` | API 詳細ガイド |
| `docs/ERD.md` | データベース ERD |
| `docs/ARCHITECTURE.md` | システム構成とデータフロー |
| `docs/DEPLOYMENT.md` | デプロイチェックリスト |
| `docs/PERFORMANCE_REPORT.md` | パフォーマンス計測結果と改善内容 |
| `docs/EXPECTED_QUESTIONS.md` | 発表時の想定質疑応答 |
| `docs/PRESENTATION.md` | デモの流れと発表要約 |
| `docs/ui-review/` | 最新デモ画面のスクリーンショット |
