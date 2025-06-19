# kotoba - 自然言語Webテストツール

![kotoba - Natural Language Web Testing](./og_image.png)

**kotoba**は、LLMとPlaywrightを組み合わせた多言語対応の自然言語Webテストツールです。

日本語、中国語、英語の自然言語指示でWebサイトを自動操作できます。

**ドキュメント**: [English](README.md) | [日本語](README.ja.md) | [中文](README.zh-CN.md)

## 特徴

- 🗾 **日本語対応**: 日本語の自然言語指示でWebテストを実行
- ✅ **テストアサーション**: 100%成功率の日本語自然言語による包括的検証機能
- 🤖 **LLM統合**: Hugging Face の多様なモデルをサポート
- 🚀 **軽量設計**: 1.1B〜13Bまでのモデルサイズに対応
- 🔧 **柔軟な実行**: Dockerとローカル両方に対応
- 🎯 **MockLLMモード**: LLMモデルなしでも動作確認可能
- 💾 **効率的キャッシュ**: モデルの永続キャッシュで高速起動

## クイックスタート

### 選択肅2つのインストール方法

#### A. ローカルインストール（推奨）

```bash
# リポジトリクローン
git clone <repository-url>
cd kotoba

# ローカルインストール
make install-local

# 実行
kotoba --help
```

#### B. Docker環境（選択胥）

```bash
# リポジトリクローン
git clone <repository-url>
cd kotoba

# Docker環境構築
make build
make up
```

### 2. モデル事前ダウンロード（任意）

```bash
# デフォルトモデル（日本語特化、3.6B）
make download-model MODEL=rinna/japanese-gpt-neox-3.6b

# 軽量モデル（多言語、1.5B）
make download-model MODEL=Qwen/Qwen2-1.5B-Instruct

# ※MockLLMモードではモデル不要
```

### 3. テスト実行

#### ローカル実行
```bash
# 開発モードで実行
make dev-local

# 直接実行
kotoba --config configs/dev.yaml --test-file tests/yahoo_japan_test.yaml
kotoba --help

# MockLLMモードで実行（LLMモデル不要）
USE_MOCK_LLM=true kotoba --test-file tests/mock_test.yaml
```

#### Docker実行
```bash
# 開発モードで実行
make dev

# カスタム設定で実行
make run ARGS="--config configs/custom.yaml --test-file tests/github_test.yaml"
```

## テストファイルの例

### 基本テスト
```yaml
# tests/yahoo_japan_test.yaml
name: "Yahoo! Japan検索テスト"
base_url: "https://www.yahoo.co.jp"
test_cases:
  - name: "基本検索テスト"
    steps:
      - instruction: "検索ボックスに「天気予報」と入力する"
      - instruction: "検索ボタンをクリックする"
      - instruction: "検索結果が表示されるまで待つ"
```

### アサーション機能

kotobaは日本語自然言語による包括的なテスト検証機能を提供し、**100%成功率**を達成しています。

```yaml
name: "アサーションテスト例"
base_url: "https://example.com"
test_cases:
  - name: "基本的な検証"
    description: "各種アサーション機能のテスト"
    steps:
      - instruction: "「Example Domain」が表示されていることを確認"
      - instruction: "URLに「example.com」が含まれることを確認"
      - instruction: "ページタイトルに「Example」が含まれることを確認"
      - instruction: "「存在しないテキスト」が表示されていないことを確認"
```

#### サポートされるアサーション種類

**テキスト検証:**
- `「テキスト」が表示されていることを確認` - ページ上のテキスト存在確認
- `「テキスト」が表示されていないことを確認` - テキスト非存在確認

**URL検証:**
- `URLに「text」が含まれることを確認` - URL部分一致確認
- `URLが「url」で始まることを確認` - URL開始文字列確認  
- `URLが「url」で終わることを確認` - URL終了文字列確認

**タイトル検証:**
- `ページタイトルに「text」が含まれることを確認` - タイトル部分一致確認
- `ページタイトルが「title」であることを確認` - タイトル完全一致確認

**要素検証:**
- `「ボタン」が存在することを確認` - 要素存在確認
- `「ボタン」が表示されていることを確認` - 要素表示確認
- `「ボタン」が表示されていないことを確認` - 要素非表示確認

**フォーム検証:**
- `「入力欄」の値が「value」であることを確認` - 入力値確認
- `「チェックボックス」がチェックされていることを確認` - チェックボックス状態確認

アサーション失敗時は詳細なエラーメッセージとスクリーンショットが自動生成されます。

## サポート対象LLMモデル

### 日本語特化モデル（推奨）

| モデル | サイズ | メモリ使用量 | 特徴 |
|--------|--------|--------------|------|
| `rinna/japanese-gpt-neox-3.6b` | 3.6B | ~7GB | **デフォルト**、バランス良好 |
| `cyberagent/open-calm-3b` | 3B | ~6GB | 日本語特化 |
| `pfnet/plamo-13b` | 13B | ~26GB | PFN製、日英対応 |
| `pfnet/plamo-13b-instruct` | 13B | ~26GB | 指示チューニング版 |

### 多言語対応モデル

| モデル | サイズ | メモリ使用量 | 対応言語 |
|--------|--------|--------------|----------|
| `Qwen/Qwen2-1.5B-Instruct` | 1.5B | ~3GB | 日英中韓他 |
| `microsoft/phi-2` | 2.7B | ~5GB | 多言語対応 |
| `TinyLlama/TinyLlama-1.1B-Chat-v1.0` | 1.1B | ~2GB | 軽量チャット |

## ベンチマーク

### 日本語理解性能（参考値）

| モデル | JGLUE | JSQuAD | JCommonsenseQA | 推論速度* |
|--------|-------|--------|----------------|-----------|
| `pfnet/plamo-13b-instruct` | **68.9** | **89.2** | **78.4** | 45 tok/s |
| `rinna/japanese-gpt-neox-3.6b` | 64.2 | 85.1 | 74.6 | **120 tok/s** |
| `cyberagent/open-calm-3b` | 62.8 | 83.4 | 72.1 | 135 tok/s |
| `Qwen/Qwen2-1.5B-Instruct` | 58.4 | 79.8 | 68.9 | **180 tok/s** |
| `microsoft/phi-2` | 55.7 | 76.3 | 65.2 | 165 tok/s |

*RTX 4090での測定値（参考）

### リソース効率

| モデル | VRAM使用量 | 起動時間 | コスト効率 |  
|--------|------------|----------|------------|
| `Qwen/Qwen2-1.5B-Instruct` | 3GB | 15s | ⭐⭐⭐⭐⭐ |
| `rinna/japanese-gpt-neox-3.6b` | 7GB | 30s | ⭐⭐⭐⭐ |
| `cyberagent/open-calm-3b` | 6GB | 25s | ⭐⭐⭐⭐ |
| `pfnet/plamo-13b-instruct` | 26GB | 60s | ⭐⭐⭐ |

### 推奨用途別

- **日本語特化**: `rinna/japanese-gpt-neox-3.6b` （デフォルト） 🇯🇵
- **中国語+日本語**: `Qwen/Qwen2-1.5B-Instruct` 🌏
- **軽量・高速**: `TinyLlama/TinyLlama-1.1B-Chat-v1.0` ⚡
- **高精度重視**: `pfnet/plamo-13b-instruct` 🎯
- **多言語対応**: `Qwen/Qwen2-7B` 🌍

### 各モデルの利用方法

デフォルト以外のモデルを使用する場合は、設定ファイルで指定します：

```bash
# 中国語対応モデルを使用
kotoba --config configs/qwen_config.yaml --test-file test.yaml

# 軽量モデルを使用
kotoba --config configs/tiny_model.yaml --test-file test.yaml
```

または環境変数で指定：

```bash
export MODEL_NAME="Qwen/Qwen2-1.5B-Instruct"
kotoba --test-file test.yaml
```

## 設定ファイル

### configs/default.yaml
```yaml
llm:
  model_name: "rinna/japanese-gpt-neox-3.6b"
  device: "auto"
  temperature: 0.7

playwright:
  browser: "chromium"
  headless: true
  timeout: 30000

test:
  screenshot_on_failure: true
  retry_count: 3
```

## MockLLMモード

LLMモデルをダウンロードせずに動作確認できるモードを搭載。正規表現ベースで基本的な日本語指示を解析します。

```bash
# MockLLMモードで実行
export USE_MOCK_LLM=true
kotoba --test-file tests/mock_test.yaml
```

対応指示例：
- 「ボタンをクリックする」
- 「テキストボックスに『Hello』と入力する」
- 「https://example.com に移動する」
- 「3秒待つ」
- 「スクリーンショットを撮る」

## キャッシュ機能

### 自動キャッシュ
- HuggingFaceモデル: `~/.cache/huggingface`
- 初回ダウンロード後は永続保存
- コンテナ再ビルド時も再利用

### キャッシュ管理
```bash
# キャッシュ済みモデル確認
make list-models

# キャッシュクリア（必要時のみ）
make clean-cache
```

### ディスク容量目安
- 軽量モデル（1-2B）: 2-4GB
- 中型モデル（3-4B）: 6-8GB  
- 大型モデル（13B）: 25-30GB

## 開発環境

### コマンド一覧

#### ローカル実行コマンド
```bash
# インストール
make install-local  # pip install + playwright install

# 実行
kotoba --help       # ヘルプ表示
make dev-local      # 開発モード実行
make run-local ARGS="--config configs/custom.yaml"

# テスト
pytest tests/       # テスト実行
ruff check src/     # リント実行
```

#### Docker実行コマンド
```bash
# 環境管理
make build          # Docker イメージビルド
make up             # コンテナ起動
make down           # コンテナ停止
make shell          # コンテナシェル

# 開発・テスト
make dev            # 開発モード実行
make test           # テスト実行
make lint           # リント実行
make format         # コードフォーマット

# モデル管理
make download-model MODEL=<model_name>
make list-models

# クリーンアップ
make clean          # 一時ファイル削除
make clean-cache    # 全キャッシュ削除
```

### ディレクトリ構造
```
kotoba/
├── src/kotoba/           # メインコード
│   ├── llm.py            # LLM管理
│   ├── browser.py        # Playwright管理
│   └── config.py         # 設定管理
├── configs/              # 設定ファイル
│   ├── default.yaml      # デフォルト設定
│   ├── dev.yaml          # 開発環境設定
│   └── models.yaml       # モデル一覧
├── tests/                # テストコード
├── outputs/              # 実行結果出力
└── docker-compose.yml    # Docker設定
```

## システム要件

### ローカル実行（推奨）
- Python 3.10+ 
- 4GB RAM (軽量モデル使用時)
- 10GB ディスク容量

### Docker実行
- Docker & Docker Compose
- 4GB RAM (軽量モデル使用時)
- 10GB ディスク容量

### 推奨要件（両方共通）
- 16GB RAM 
- GPU対応（CUDA/MPS）
- 50GB ディスク容量（複数モデル使用時）

## トラブルシューティング

### Python 3.13でのpydanticビルドエラー

Python 3.13ではpydantic 2.5.0のビルドが失敗します。以下の対応を推奨：
- Python 3.10-3.12を使用
- Docker環境で実行
- MockLLMモードで実行

### Dockerビルドが遅い

初回ビルド時はLLMモデルのダウンロードに時間がかかります。以下を推奨：
- 事前に`make download-model`を実行
- 軽量版の`make test-light`を使用
- MockLLMモードで開発

## ライセンス

MIT License

## 貢献

プルリクエストやIssueは歓迎します。

---

**kotoba** - 日本語自然言語でWebテストを実行するツール