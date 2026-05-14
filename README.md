# BizTool Sales List Builder

地域・業種を指定して、
企業情報・問い合わせURLをCSV出力する営業支援ツール。

---

## 機能

- Google Places API検索
- 問い合わせURL抽出
- フォーム有無判定
- メール抽出
- 営業スコアリング
- CSV出力

---

## 必要環境

- Python 3.11+
- Google Places API (New)

---

## インストール（bash）

- pip install -r requirements.txt

---

## .env

プロジェクトルートに .env を作成してください。

- GOOGLE_API_KEY=YOUR_API_KEY

---

## 実行（bash）

- python src/main.py

---

## 出力

CSVファイルは以下へ出力されます。

- /output

---

## ログ

エラーログは以下へ出力されます。

- /logs/error.log

---

## CSV出力項目

- 会社名
- 住所
- 電話番号
- ホームページ
- HP有無
- 問い合わせURL
- 問い合わせ有無
- フォーム有無
- メールアドレス
- メール有無
- 営業スコア
- GoogleマップURL
- 評価
- 口コミ数
- 業種タイプ
- 検索地域
- 検索業種
- 取得日時

---

## 注意事項

- Google Places API の利用料金が発生する場合があります
- 大量アクセスは対象サイトへ負荷をかける可能性があります
- 営業メール・フォーム送信時は各種法令を遵守してください
