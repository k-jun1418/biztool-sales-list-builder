# BizTool Sales List Builder

地域・業種を指定して、企業情報・問い合わせURL・メールアドレスを CSV 出力する営業支援ツール。

---

## 機能

- Google Places API（New）による企業検索
- 問い合わせURL自動取得
- 問い合わせフォーム有無判定
- メールアドレス抽出
- 営業スコアリング（HP有無・フォーム有無・メール有無の複合評価）
- UTF-8 BOM 付き CSV 出力（Excel で直接開ける形式）

---

## 必要環境

- Python 3.11 以上
- Google Places API キー（**Places API New** を有効化済みのもの）

---

## クイックスタート

```
# 1. 仮想環境を作成・有効化
python -m venv .venv
.venv\Scripts\activate

# 2. 依存ライブラリをインストール（2コマンド両方必要）
pip install -r requirements.txt
pip install -e .

# 3. .env を作成（プロジェクトルートに）
# GOOGLE_API_KEY=あなたのAPIキー

# 4. 実行
python src/tools/main.py
```

> 詳細は [docs/install.md](docs/install.md) を参照してください。

---

## .env の設定

プロジェクトルートに `.env` ファイルを作成し、以下を記述:

```
GOOGLE_API_KEY=あなたのAPIキー
```

`.env.example` をコピーして `.env` にリネームしても構いません。

---

## 実行

```
python src/tools/main.py
```

実行後、以下を入力してください:

| 入力 | 例 |
|------|---|
| 地域 | `埼玉県 川口市` |
| 業種 | `不動産会社` |
| 取得件数 | `20` / `40` / `60` |

---

## 出力

CSVファイルは `output/` フォルダに出力されます:

```
output/sales_list_東京都新宿区_不動産会社_20260610_120000.csv
```

### CSV 出力項目

| 列名 | 内容 |
|------|------|
| place_id | Google Place ID |
| 会社名 | 店舗・企業名 |
| 住所 | 所在地 |
| 電話番号 | 電話番号 |
| ホームページ | WebサイトURL |
| HP有無 | あり / なし |
| 問い合わせURL | 問い合わせページURL |
| 問い合わせ有無 | あり / なし |
| フォーム有無 | あり / なし |
| メールアドレス | 抽出されたメールアドレス |
| メール有無 | あり / なし |
| 営業スコア | 0〜8点（HP+フォーム+メール有無の複合） |
| 評価 | Google マップ評価（星） |
| 口コミ数 | Google マップ口コミ数 |
| 業種タイプ | Google Places の types |
| 検索地域 | 入力した地域 |
| 検索業種 | 入力した業種 |
| 取得日時 | 実行日時 |

---

## ログ

エラーログは `logs/error.log` に追記されます。

---

## 設定ファイル

| ファイル | 説明 |
|---------|------|
| `config.json` | API動作設定（ページ数・タイムアウト等） |
| `config/score_config.json` | スコア計算の有効化・配点設定 |
| `config/lead_columns.json` | CSV列の定義・順序（変更注意） |

---

## フォルダ構成

```
<workspace>\packages\sales-list-builder\
├── .env                    ← 自分で作成（Gitには含めない）
├── .env.example            ← テンプレート
├── config.json             ← API動作設定
├── config\
│   ├── lead_columns.json   ← CSV列定義（他ツールとの共有定義）
│   └── score_config.json   ← スコア計算設定
├── src\
│   ├── tools\
│   │   └── main.py         ← エントリーポイント
│   └── sales_list_builder\ ← メインパッケージ
├── docs\
│   ├── install.md          ← 詳細インストール手順
│   └── troubleshooting.md  ← トラブルシューティング
├── output\                 ← CSV出力先（.gitignore）
├── logs\                   ← エラーログ（.gitignore）
├── requirements.txt
└── pyproject.toml
```

---

## 注意事項

- Google Places API の利用料金が発生する場合があります（$200/月の無料枠あり）
- 大量アクセスは対象サイトへ負荷をかける可能性があります（1件ずつ順次処理）
- 取得したメール・フォームへの送信時は特定電子メール法等の関連法令を遵守してください

---

## ドキュメント

- [インストール手順](docs/install.md)
- [トラブルシューティング](docs/troubleshooting.md)
