# 麻雀戦術ナレッジグラフアプリ開発

## 目的

React + FastAPI + Python を使用した「麻雀戦術ナレッジグラフアプリ」を開発する。<br>
目的は、雀魂の牌譜データをAI（Google Gemini）で解析し、戦術的な知見を抽出すること。

---

## 技術スタック

現状考えている技術スタックは以下。

1. 本番環境

- フロントエンド: React(Vite, shadcn/ui, TailwindCSS)
- バックエンド: Python(FastAPI), Vector DB(Qdrant Cloud), Neo4j(Chroma Cloud or Qdrant Cloud)
- AI: Google Gemini API (google-genai)

2. 開発環境

- Vector DBはChromaDBというライブラリを使う
- Neo4jはAuraDB Freeを使う
- その他は本番環境と同じ

---

## 作業の進め方

このプロジェクトは、React, Pythonなどの学習を兼ねています。<br>
そのため、**あなたはコードを教えるだけで実装はしないでください。**

以下の流れで作業を進めます。

1. 開発を進めるにあたり、環境構築が必要になった場合は、環境構築手順を整理して示してください。<br>
   また、環境構築に関しては、こちらで許可を出せば、あなたが環境構築を実行してください。
1. 環境構築が完了したら、コーディングを進めます。<br>
   こちらから何の機能を実装するかを指示しますが、段階的にコードを示してください。<br>
   その際、どのファイルにどのような変更をするのかを示してください。<br>
   また、なぜそのような変更をするのかを示してください。
1. 作業の区切りで、進捗状況をCLAUDE.mdに記載し、次回は続きから作業ができるようにしてください。

---

## やりたいこと

### ■概要

1. 戦術の抽出と構造化（Python: NLP / LangChain）

- 具体例: 「雀魂」の牌譜ログや、自分が書いた反省メモをAIに読み込ませます。
- AIの仕事:
  - 「押し引きの判断基準」「リーチ判断」「ベタオリの精度」などの概念を抽出。
  - 「6-9面待ちでの追いかけリーチ成功率」といった具体的な事象を構造化データに変換します。

2. 戦術ナレッジグラフ（Python: NetworkX / Neo4j）

- 可視化: 「安牌」→「筋（スジ）」→「裏筋」といった知識の繋がりや、「自分の弱点」と「特定の役」の相関関係をグラフ化します。
- メリット: 自分がどのシチュエーションでミスをしやすいか、知識がどう繋がっているかが一目でわかります。

3. 牌譜ベースのRAG（Python: Vector DB）

- 対話機能: 「自分が過去に放銃した時の共通点は？」と聞くと、過去の牌譜データから「發をポンされている時の押しが甘い」といった傾向を回答させます。

---

## 進捗状況

### 環境構築

- uv 0.11.11 インストール、Python 3.13.13 インストール（uv 管理）
- `backend/` ディレクトリを uv プロジェクトとして初期化
- 依存パッケージ: fastapi, uvicorn, python-dotenv, pydantic, python-multipart, google-genai
- `google-generativeai`（サポート終了）→ `google-genai` に移行
- Gemini API を Tier1 課金に変更（無料枠は `gemini-2.5-flash` が1日20リクエストと少ないため）
- `.vscode/settings.json` を追加（`python.defaultInterpreterPath` を `backend/.venv` に設定）
- `.vscode/launch.json` に `--reload-exclude mortal_engine` を追加（`mortal_engine/target/` の大量ファイルによる CPU 高負荷を防ぐため）
- `watchfiles` を追加（`uv add watchfiles`）: `--reload-exclude` を有効にするために必要

#### Mortal 環境構築

- `backend/mortal_engine/` に [Equim-chan/Mortal](https://github.com/Equim-chan/Mortal) を git clone
- `libriichi` を Rust ソースからビルド（`cargo build -p libriichi --lib --release`）
  - 出力: `target/release/libriichi.dylib` → `mortal/libriichi.so` にコピー
- `backend/mortal_engine/.venv/` を Python 3.12 で作成（`uv venv --python 3.12`）
  - インストール済みパッケージ: `torch`（CPU版 2.2.2）、`numpy<2`（1.26.4）、`tqdm`、`toml`、`tensorboard`
- `mortal/config.toml` を新規作成（version=4, num_blocks=5, conv_channels=32）
- `mortal/gen_placeholder.py` を新規作成・実行してプレースホルダーモデル `mortal.pth` を生成
  - Brain（ResNet）+ DQN + GRP の重みをランダム初期化して保存
  - 実モデル重みは非公開のため、パイプライン検証用として使用

#### Mortal v4-best モデル差し替え（2026-05-13）

Akagi の Discord から入手した v4-best モデルに差し替えた。入手ファイルは `docs/ref_mortal/`（git管理外）に格納。

**差し替えたファイル（`backend/mortal_engine/mortal/` 配下）：**

- `model.py` → v4-best 版に差し替え（`Brain(version=4, conv_channels=192, num_blocks=40)`）
- `mortal.pth` → v4-best の実モデル重みに差し替え
- `libriichi.so` → **環境によって対応が異なる（重要）**
  - **macOS の場合**: v4-best 同梱の `libriichi.so` は Linux (ELF) 形式のため使用不可。Rust ソースから自前ビルドが必要
    ```bash
    cd backend/mortal_engine
    cargo build -p libriichi --lib --release
    cp target/release/libriichi.dylib mortal/libriichi.so
    ```
    ※ Rust 未インストールの場合は `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh` でインストール
  - **Linux の場合**: v4-best 同梱の `libriichi.so`（ELF形式）がそのまま使用可能

**`mortal.py` の修正が必要（本番環境でも同様）：**

v4-best の `mortal.pth` は numpy スカラー型を含むため、`weights_only=True` では読み込みエラーになる。以下2箇所を `weights_only=False` に変更する。

- 30行目（Brain/DQN の読み込み）:
  ```python
  state = torch.load(config['control']['state_file'], weights_only=False, map_location=torch.device('cpu'))
  ```
- 83行目（GRP の読み込み）:
  ```python
  grp_state = torch.load(config["grp"]["state_file"], weights_only=False, map_location=torch.device('cpu'))
  ```

また、v4-best の `mortal.pth` には GRP 重みが含まれていないため、GRP 読み込みを try/except で囲み、失敗時は `grp = None` にする（79〜107行目）。

### ソース修正内容

- `main.py`: `/analyze`・`/analyze/stream`・`/admin/uploadpaifu`・`/admin/uploadpaifu/stream` エンドポイントを実装
- `main.py`: `/convert/mjai`・`/analyze/mortal` エンドポイントを追加
  - `/convert/mjai`: 牌譜JSONをmjai JSONL形式に変換し `docs/ref/paifu_mjai.jsonl` に保存
  - `/analyze/mortal`: mjai JSONLをMortalで解析し、各打牌ターンのQ-valueを返す
- `services/gemini_service.py`: `genai.Client` ベースに移行、`analyze_paifu_text()` / `analyze_paifu_text_stream()` を実装
- `services/gemini_service.py` のプロンプトに牌の表記凡例を追加、押し引き基準の説明を具体化
- `services/paifu_parser.py` を新規作成（牌譜JSONを戦術解析用コンパクトテキストに変換）:
  - ドラ表示牌 → 実際のドラに変換（例: `7p`→`8p`、`9m`→`1m`、`4z`→`1z`）
  - 赤ドラを明示表示（例: `0m`→`赤5m`）
  - 字牌を日本語名で表示（例: `1z`→`東`、`5z`→`白`）
  - カン後の新ドラを `[新ドラ: XX]` として出力
  - 自分のプレイヤーを `★` マークで強調
  - 配牌行に各プレイヤーの自風を付与（例: `S0(東家)`）
  - スコア・スコア変動をプレイヤー別辞書形式で出力（例: `{S0: 21400, S1: 25000, ...}`）
  - 各イベント行に巡目を付与（ツモ・打牌・ポン/チー/明カン でカウント、親の初期値は1）
- `services/paifu_to_mjai.py` を新規作成（雀魂牌譜JSON → mjai JSONL変換）:
  - 牌表記変換: `0m`→`5mr`、`1z`→`E` など
  - 全局を変換（start_game → 局ごとのイベント → end_game）
  - player_seat 以外のツモ牌は `"?"` でマスク
  - リーチ宣言: `reach` → `dahai` → `reach_accepted` の順で出力
    - 次イベントがロン（RecordHule）の場合は `reach_accepted` を出力しない（`_next_event_is_ron()` で判定）
  - `hora` に `deltas`（スコア変動）フィールドを付与（GRP処理に必要）
  - `ryukyoku` に `deltas` フィールドを付与
- `services/mortal_service.py` を新規作成（Mortal サブプロセス経由でQ-value解析）:
  - `MORTAL_REVIEW_MODE=1` 環境変数で起動（全イベントにレスポンスを返させるため）
  - 1行送信 → 1行受信のループで mjai JSONL を処理
  - `response.type == "dahai"` かつ `actor == player_seat` のレスポンスからQ-valueを抽出
  - `_find_player_action(all_lines, current_idx, player_seat)`: インデックスで検索（文字列重複問題を回避）
  - 戻り値: 局・巡目・実打牌・Mortal推奨打牌・EV・全有効アクション一覧

### 現在のプロジェクト構造

```
mahjongInsight/
├── .vscode/
│   ├── launch.json
│   └── settings.json              （Python インタープリタ設定）
├── CLAUDE.md
├── docs/
│   └── ref/
│       ├── paifu_ref_data.json    （サンプル牌譜データ）
│       ├── paifu_data_202605061736.json  （テスト用牌譜データ）
│       ├── paifu_compact.txt      （デバッグ用出力、git管理外）
│       └── paifu_mjai.jsonl       （mjai変換結果、git管理外）
└── backend/
    ├── .env                       （git管理外）
    ├── .env.example
    ├── .gitignore
    ├── .venv/                     （git管理外）
    ├── pyproject.toml
    ├── main.py
    ├── models.py
    ├── mortal_engine/             （Mortal リポジトリ）
    │   ├── .venv/                 （Python 3.12 専用 venv、git管理外）
    │   └── mortal/
    │       ├── mortal.py
    │       ├── model.py
    │       ├── libriichi.so       （Rust ビルド済み）
    │       ├── mortal.pth         （v4-best 実モデル、git管理外）
    │       ├── config.toml
    │       └── gen_placeholder.py （mortal.pth 再生成スクリプト）
    └── services/
        ├── __init__.py
        ├── gemini_service.py
        ├── haipai_mock.py
        ├── paifu_parser.py
        ├── paifu_to_mjai.py       （新規）
        └── mortal_service.py      （新規）
```

### 次回以降の候補

- Gemini API との連携（Mortal の Q-value → Gemini で自然言語の説明を生成）
- ナレッジグラフ化（Neo4j AuraDB との連携）
- フロントエンド（React + Vite）の雛形作成
- Vector DB（ChromaDB）との連携
- `/admin/uploadpaifu` への管理者認証追加（`X-Admin-Key` ヘッダー）

---
