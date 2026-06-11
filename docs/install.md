# インストール手順（Windows 向け）

別PCで初めてセットアップする方向けの手順書です。

> **`<workspace>` について**  
> このドキュメントでは `<workspace>` をワークスペースのルートフォルダとして記載しています。  
> 実際に配置したフォルダに読み替えてください。  
> 例: `C:\KOTO_WORKS`、`D:\Projects\KOTO_WORKS`

---

## 必要なもの（事前準備）

| 必要なもの | バージョン | 確認コマンド |
|-----------|-----------|------------|
| Python | 3.11 以上 | `python --version` |
| pip | Python に付属 | `pip --version` |
| Google Places API キー | Places API（New）有効化済み | Google Cloud Console で確認 |

> **注意**: Python は公式サイト（https://www.python.org/downloads/）から入手してください。  
> インストール時に「**Add Python to PATH**」にチェックを入れてください。

---

## 手順 1: プロジェクトを取得する

### Git がある場合
```
cd <workspace>\packages
git clone <リポジトリURL>
cd sales-list-builder
```

### Git がない場合
ZIP をダウンロードして任意のフォルダに展開し、そのフォルダをコマンドプロンプトで開く。

---

## 手順 2: 仮想環境を作成する

```
python -m venv .venv
```

作成後、仮想環境を有効化する:

```
.venv\Scripts\activate
```

> プロンプトの先頭に `(.venv)` が表示されていれば有効化成功です。

---

## 手順 3: 依存ライブラリをインストールする

**以下の2コマンドを順番に実行してください（両方必要です）。**

```
pip install -r requirements.txt
pip install -e .
```

> `pip install -e .` は `src/sales_list_builder` パッケージをインポート可能にするために必要です。  
> `requirements.txt` だけでは `ModuleNotFoundError: No module named 'sales_list_builder'` が発生します。

---

## 手順 4: .env ファイルを作成する

プロジェクトのルートフォルダに `.env` という名前のファイルを作成し、以下を記述します:

```
GOOGLE_API_KEY=あなたのAPIキーをここに貼り付け
```

> `.env` ファイルはプロジェクトルート（`README.md` と同じ階層）に置いてください。  
> `.env.example` が存在するのでそれをコピーして名前を変更してください。

### Google API キーの取得手順（初回のみ）

1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. プロジェクトを作成（または既存を選択）
3. 「APIとサービス」→「ライブラリ」から「**Places API (New)**」を有効化
   - ⚠️ 旧「Places API」ではなく「**New**」の方が必要です
4. 「APIとサービス」→「認証情報」から APIキーを作成
5. 作成したキーを `.env` に貼り付け

---

## 手順 5: 動作確認（初回テスト）

```
python src/tools/main.py
```

実行すると以下の入力を求められます:

```
=== BizTool Sales List Builder ===
地域を入力してください（例：埼玉県 川口市）:
業種を入力してください（例：不動産会社）:
取得件数（20 / 40 / 60）:
```

入力後、`output/` フォルダに CSV ファイルが生成されれば成功です。

---

## ターミナルで日本語が文字化けする場合

Windows のコマンドプロンプトで日本語が `????` や `????` と表示される場合は、実行前に以下のコマンドを入力してください:

```
set PYTHONIOENCODING=utf-8
chcp 65001
```

または PowerShell の場合:
```
$env:PYTHONIOENCODING = "utf-8"
chcp 65001
```

> **補足**: CSV ファイル自体は UTF-8 BOM 付きで正しく出力されます。文字化けはターミナルの表示のみの問題で、ツールの動作には影響ありません。

---

## 毎回の実行手順（2回目以降）

```
# 1. 仮想環境を有効化
.venv\Scripts\activate

# 2. ツールを実行
python src/tools/main.py
```

---

## config.json の主要設定

| 設定キー | 既定値 | 説明 |
|---------|-------|------|
| `max_pages` | 1 | APIのページ取得数（1ページ＝20件） |
| `request_timeout` | 10 | HTTPタイムアウト秒数 |
| `request_retry_count` | 3 | APIエラー時のリトライ回数 |
| `save_raw_response` | false | APIレスポンスをJSONで保存するか |

---

## score_config.json の主要設定

| 設定キー | 既定値 | 説明 |
|---------|-------|------|
| `enable_contact_check` | true | 問い合わせURL・フォーム解析の有効化 |
| `enable_email_extract` | true | メールアドレス抽出の有効化 |
| `enable_score` | true | 営業スコア計算の有効化 |

---

## EXE化について（将来対応）

このツールは EXE 化（PyInstaller 等）を前提に設計されています。

**対応済み箇所:**
- `config_loader.py`, `score_loader.py`, `lead_columns_loader.py` は `sys.frozen` を判定し、EXE 実行時にはEXEと同階層の `config.json`, `config/` を参照します。

**EXE化時の注意点（未対応）:**
- `csv_export.py` の `output/` フォルダと `app_logger.py` の `logs/` フォルダはカレントディレクトリ基準です。EXE 化する場合、これらもEXEと同階層に生成されるよう修正が必要になります。

EXE 化ツールの候補: [PyInstaller](https://pyinstaller.org/)

```
pip install pyinstaller
pyinstaller --onefile --name biztool_sales_list src/tools/main.py
```

> EXE 化時は `config/` フォルダを EXE と同じ場所に配置してください。
