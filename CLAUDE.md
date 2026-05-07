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
- AI: Google Gemini API (langchain-google-genai または google-generativeai)

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

### 第1回 (2026-05-07) — バックエンド MVP 完成

#### 完了した作業

**環境構築**
- uv 0.11.11 インストール
- Python 3.13.13 インストール（uv 管理）
- `backend/` ディレクトリを uv プロジェクトとして初期化
- 依存パッケージ追加: fastapi, uvicorn, python-dotenv, google-generativeai, pydantic

**実装ファイル**

| ファイル | 内容 |
|---|---|
| `backend/.env` | GEMINI_API_KEY を記載（git管理外） |
| `backend/.env.example` | APIキーのテンプレート（git管理内） |
| `backend/.gitignore` | .env, .venv 等を除外 |
| `backend/models.py` | Pydantic モデル（AnalyzeRequest, AnalyzeResponse） |
| `backend/services/__init__.py` | パッケージ定義（空ファイル） |
| `backend/services/haipai_mock.py` | ダミー牌譜データを返すモック関数 |
| `backend/services/gemini_service.py` | Gemini API 呼び出しロジック |
| `backend/main.py` | FastAPI エントリーポイント（/analyze エンドポイント） |
| `.vscode/launch.json` | VS Code デバッグ設定 |

**動作確認**
- `/analyze` エンドポイント（POST）が正常に動作することを確認
- Gemini API（gemini-2.5-flash）との連携を確認
- Swagger UI（`http://localhost:8000/docs`）での動作確認済み

#### 現在のプロジェクト構造

```
mahjongInsight/
├── .vscode/
│   └── launch.json
├── CLAUDE.md
└── backend/
    ├── .env               （git管理外）
    ├── .env.example
    ├── .gitignore
    ├── .venv/             （git管理外）
    ├── pyproject.toml
    ├── main.py
    ├── models.py
    └── services/
        ├── __init__.py
        ├── gemini_service.py
        └── haipai_mock.py
```

#### 次回以降の候補

- フロントエンド（React + Vite）の雛形作成
- 実際の雀魂牌譜データの取得・パース
- ストリーミングレスポンスの実装
- Vector DB（ChromaDB）との連携

---
