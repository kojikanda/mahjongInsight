# AI(LLM)に関すること

## ■ 用語

- ナレッジグラフとは、現実世界のエンティティ（人、場所、概念など）とその関連性（「～は～である」）をノード（点）とエッジ（線）でつなぎ、データ同士の意味的なネットワークを構築する技術
- RAG（Retrieval-Augmented Generation：検索拡張生成）とは、ChatGPTなどの大規模言語モデル（LLM）が回答を生成する際、事前に社内文書やデータベースなどの「外部情報」を検索し、その内容に基づいて回答を作成する技術。<br>
  最新情報や専門知識に基づいた高精度な回答が可能になり、AIの嘘（ハルシネーション）を低減できるため、業務効率化ツールとして注目されている。

## ■ Gemini APIキーの取得

1. Google AI Studio にアクセス
   Google AI Studio (aistudio.google.com) に、お使いのGoogleアカウントでログインします。

2. 利用規約の確認
   初回アクセス時は規約への同意を求められるので、内容を確認して進みます。

3. APIキーの作成
   画面左側のメニューにある 「Get API key」 をクリックします。

4. プロジェクトの選択または作成

- 「Create API key in new project」 をクリックすると、新しいGoogle Cloudプロジェクトが自動作成され、APIキーが発行されます。<br>
  →今回は「Default Gemini Project」で作成。
- 既存のプロジェクトがある場合は、それを選択して作成することも可能です。

5. キーのコピーと保管
   発行された AIza... で始まる文字列をコピーします。

【重要】 APIキーは他人に公開しないよう注意してください。GitHubにプッシュする際は、必ず .env ファイルに記述し、.gitignore で除外するように設定します。

### ◯開発時の注意点（無料枠について）

現在、Gemini API には 「Pay-as-you-go（従量課金）」 と 「Free of charge（無料枠）」 があります。

- 無料枠の範囲:
  - Gemini 1.5 Flash などの軽量モデルであれば、1分間に数回程度のリクエストなら無料で利用可能です（※2026年現在の規約に基づきます）。
  - 無料枠で使用する場合、入力したデータがモデルの改善に使用される可能性があるため、機密性の高い個人情報などは入力しないようにしてください（今回は牌譜データなので問題ないかと思います）。

---

<br>

# Pythonに関すること

## ■ インタプリタの指定

1. VS Code で Cmd + Shift + P を押す
2. Python: Select Interpreter と入力して選択
3. 一覧に出てくる以下のパスを選択する  
    ./backend/.venv/bin/python
   <br>

一覧に出ない場合は「Enter interpreter path...」→「Find...」で以下のパスを直接指定します。
/Volumes/DATA/programing/development/mahjongInsight/backend/.venv/bin/python

# Fast APIに関すること

## ■Swagger UI

ブラウザで以下にアクセスすると、GUIでAPIを叩くことができる。

http://localhost:8000/docs

### ◯Swagger UIの仕組み

FastAPI はコードを書くと、裏側で自動的に2つのことをやっている。

1. OpenAPI スキーマの自動生成

main.py に書いた以下の情報を読み取り、

- エンドポイントのパス（/analyze）
- HTTPメソッド（POST）
- リクエストの型（AnalyzeRequest）
- レスポンスの型（AnalyzeResponse）

これらを OpenAPI という標準フォーマットの JSON に変換する。<br>
http://localhost:8000/openapi.json でそのJSONを確認できる。

2. Swagger UI の自動ホスト

生成した OpenAPI JSON を読み込んで動く Swagger UI（HTMLとJS）を /docs で自動的に配信する。

```
あなたのコード（Pydanticモデル）
 ↓ FastAPIが自動変換
 OpenAPI JSON（/openapi.json）
↓ Swagger UIが読み込む
 GUI（/docs）
```

### ◯なぜ FastAPI がこれを内蔵しているのか

FastAPI の設計思想として「型情報からドキュメントとバリデーションを自動生成する」がある。<br>
AnalyzeRequestやAnalyzeResponseに**Pydantic**を使ったのはそのためで、型を書く＝ドキュメントが完成するという設計になっている。
