# トラブルシューティング

---

## エラー別の対処法

---

### `ModuleNotFoundError: No module named 'sales_list_builder'`

**原因**: `pip install -e .` が未実行のため、パッケージが認識されていない。

**対処**:
```
pip install -e .
```

> `pip install -r requirements.txt` だけでは不足です。両方のコマンドが必要です。

---

### `エラー: GOOGLE_API_KEY が .env に設定されていません。`

**原因**: `.env` ファイルがない、またはキーが空。

**対処**:
1. プロジェクトルート（`README.md` と同じ場所）に `.env` を作成
2. 中に以下を記述:
   ```
   GOOGLE_API_KEY=あなたのAPIキー
   ```
3. ファイル名が `.env.txt` になっていないか確認（拡張子なし）

---

### `PermissionError: Google APIキーが無効です。`（HTTP 403）

**原因**: APIキーが無効か、`Places API (New)` が有効化されていない。

**対処**:
1. Google Cloud Console でキーが有効か確認
2. 「APIとサービス」→「有効なAPI」に「**Places API (New)**」が表示されているか確認
   - ⚠️ 旧「Places API」と「Places API (New)」は別物です
3. APIキーに対してIPアドレス制限が設定されている場合、自PCのIPを許可リストに追加

---

### `RuntimeError: Google Places APIへの接続に失敗しました。`

**原因**: ネットワークエラーまたはAPIの一時障害。

**対処**:
1. インターネット接続を確認
2. 時間をおいて再実行
3. `config.json` の `request_retry_count` を増やしてみる（例: 5）
4. プロキシ環境の場合は環境変数 `HTTPS_PROXY` を設定:
   ```
   set HTTPS_PROXY=http://プロキシアドレス:ポート
   ```

---

### `RuntimeError: Google APIの利用上限、または一時的な制限に達しました。`（HTTP 429）

**原因**: Google Places API の1日の無料枠（$200相当）を超過、またはレートリミット。

**対処**:
1. Google Cloud Console で請求状況・使用量を確認
2. 取得件数（`max_results`）を減らして再実行
3. 翌日に再実行（日次上限の場合）

---

### CSV が出力されない / `output/` フォルダが空のまま

**原因**: API で 0件取得、またはエラーで途中終了。

**対処**:
1. `logs/error.log` を確認し、エラー内容を特定
2. 検索地域・業種の入力が正しいか確認（例: `東京都 新宿区` `不動産会社`）
3. 取得件数に `20` を入力して最小構成でテスト

---

### `FileNotFoundError: config.json が見つかりません。`

**原因**: 実行するカレントディレクトリが間違っている。

**対処**:
プロジェクトのルートフォルダ（`config.json` がある場所）からコマンドを実行してください。

```
cd <workspace>\packages\sales-list-builder
python src/tools/main.py
```

---

### `FileNotFoundError: score_config.json が見つかりません。`
### `FileNotFoundError: lead_columns.json が見つかりません。`

**原因**: `config/` フォルダが存在しない。

**対処**:
`config/` フォルダと以下の2ファイルが存在することを確認:
- `config/score_config.json`
- `config/lead_columns.json`

---

### CSV が文字化けする（Excel で開いた場合）

**原因**: CSV は UTF-8 BOM 付きで出力されています。通常は Excel で正しく開けますが、環境によっては文字化けする場合があります。

**対処**:
Excel で直接開かず、以下の手順で開く:
1. Excel を起動
2. 「データ」→「テキストまたは CSV から」
3. ファイルを選択
4. 「文字コード」を「UTF-8」に設定してインポート

---

### `SyntaxError` または `TypeError` が発生する

**原因**: Python のバージョンが 3.11 未満の可能性。

**確認**:
```
python --version
```

Python 3.11 未満の場合は、3.11 以上をインストールして仮想環境を作り直してください。

---

### 仮想環境の有効化が失敗する（`activate` でエラー）

**PowerShell の場合**:
```
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.venv\Scripts\Activate.ps1
```

**コマンドプロンプトを使う場合**:
```
.venv\Scripts\activate.bat
```

---

## ログファイルの場所

エラーログは `logs/error.log` に追記されます。  
問題が解消しない場合は、このファイルの内容を開発者に共有してください。

---

## クリーン環境テスト前のチェックリスト

別PCで動作確認をする前に、以下を確認してください:

- [ ] Python 3.11 以上がインストールされている
- [ ] `pip` が使える（`pip --version` で確認）
- [ ] プロジェクトルートに `.env` ファイルがある
- [ ] `.env` に有効な `GOOGLE_API_KEY` が設定されている
- [ ] `config/` フォルダに `lead_columns.json` と `score_config.json` がある
- [ ] `config.json` がプロジェクトルートにある
- [ ] `pip install -r requirements.txt` が完了している
- [ ] `pip install -e .` が完了している（`(.venv)` が表示された状態で実行）
- [ ] `python src/tools/main.py` で起動できる

---

## よくある誤り

| 誤り | 正しい方法 |
|------|---------|
| `python src/main.py` | `python src/tools/main.py` |
| `pip install -r requirements.txt` のみ | + `pip install -e .` も実行 |
| `.env.txt` というファイル名 | `.env`（拡張子なし） |
| 仮想環境を有効化せずにインストール | `.venv\Scripts\activate` してから `pip install` |
| 別フォルダから実行 | `<workspace>\packages\sales-list-builder` で実行 |
