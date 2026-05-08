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

## ■ Gemini APIのSDKについて

`google-generativeai`はサポート完了しており、今は`google-genai`を使う必要がある。

## ■ 使えるモデルの一覧出力

```zsh
cd backend
uv run python -c "
from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

for m in client.models.list():
    print(m.name)
"
```

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

## ■ APIの呼び出し方

### ◯モックデータを用いた解析

下記のSwagger UIを使うか、コマンドを使うか、VSCode拡張機能のThunder Clinetを使う。

Gemini APIをストリーミングレスポンスで使う場合はコマンドの方が良いので、以下のコマンドを実行する。

```zsh
curl -X POST http://localhost:8000/analyze/stream \
-H "Content-Type: application/json" \
-d '{"game_id": "test-001"}' \
--no-buffer
```

### ◯簡易ファイルアップロードAPI

```zsh
curl -X POST http://localhost:8000/admin/uploadpaifu/stream \
-F "file=@docs/ref/paifu_ref_data.json" \
--no-buffer
```

# Fast APIに関すること

## ■ Swagger UI

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

# 雀魂牌譜データについて

## 1. 牌譜のJSONデータの作成

参考URL: https://wikiwiki.jp/majsoul-api/%E7%89%8C%E8%AD%9C%E3%82%92%E3%83%95%E3%82%A1%E3%82%A4%E3%83%AB%E3%81%AB%E4%BF%9D%E5%AD%98%E3%81%99%E3%82%8B%E3%81%AB%E3%82%83

今回牌譜データを収集するにあたり、方法を検討したが、結局上記URLの方法しか見当たらなかった。<br>
よって、今回は上記URLの方法に従い、JSONデータを作成する。

```javascript
function paifu(uuid = "") {
  if (!uuid) {
    uuid = prompt("UUID を入力してください。 / Please Enter a UUID.");
  }
  if (!uuid) {
    return;
  }
  uuid = uuid.replace(/^.*=(.*)_a.*$/, "$1");
  const pbWrapper = net.ProtobufManager.lookupType(".lq.Wrapper");
  const pbGameDetailRecords = net.ProtobufManager.lookupType(
    ".lq.GameDetailRecords",
  );
  function parseRecords(gameDetailRecords, json) {
    try {
      if (gameDetailRecords.version == 0) {
        for (let i in gameDetailRecords.records) {
          const record = pbWrapper.decode(gameDetailRecords.records[i]);
          const pb = net.ProtobufManager.lookupType(record.name);
          const data = JSON.parse(JSON.stringify(pb.decode(record.data)));
          json.records[i] = { name: record.name, data: data };
        }
      } else if (gameDetailRecords.version == 210715) {
        for (let i in gameDetailRecords.actions) {
          if (gameDetailRecords.actions[i].type == 1) {
            const record = pbWrapper.decode(
              gameDetailRecords.actions[i].result,
            );
            const pb = net.ProtobufManager.lookupType(record.name);
            const data = JSON.parse(JSON.stringify(pb.decode(record.data)));
            json.actions[i].result = { name: record.name, data: data };
          }
        }
      } else {
        throw "Unknown version: " + gameDetailRecords.version;
      }
    } catch (e) {
      console.log(e);
    }
    return json;
  }
  async function fetchData(url) {
    const response = await fetch(url);
    const arrayBuffer = await response.arrayBuffer();
    return new Uint8Array(arrayBuffer);
  }
  function download(data, uuid) {
    let a = document.createElement("a");
    a.href = URL.createObjectURL(
      new Blob([JSON.stringify(data, null, "  ")], { type: "text/plain" }),
    );
    a.download = "mahjongsoul_paifu_" + uuid + ".txt";
    a.style.display = "none";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }
  app.NetAgent.sendReq2Lobby(
    "Lobby",
    "fetchGameRecord",
    { game_uuid: uuid, client_version_string: GameMgr.Inst.getClientVersion() },
    async function (error, gameRecord) {
      if (gameRecord.data == "") {
        gameRecord.data = await fetchData(gameRecord.data_url);
      }
      const gameDetailRecordsWrapper = pbWrapper.decode(gameRecord.data);
      const gameDetailRecords = pbGameDetailRecords.decode(
        gameDetailRecordsWrapper.data,
      );
      let gameDetailRecordsJson = JSON.parse(JSON.stringify(gameDetailRecords));
      gameDetailRecordsJson = parseRecords(
        gameDetailRecords,
        gameDetailRecordsJson,
      );
      gameRecord.data = "";
      let gameRecordJson = JSON.parse(JSON.stringify(gameRecord));
      gameRecordJson.data = {
        name: gameDetailRecordsWrapper.name,
        data: gameDetailRecordsJson,
      };
      download(gameRecordJson, uuid);
    },
  );
}
```

## 2. Gemini APIへのプロンプト

上記の方法で、牌譜のJSONデータを作成することは可能だが、1半荘あたり50000万行を超えるデータとなってしまう。<br>
これほどの大きさになると、効率やコストに大きな影響を及ぼすので、JSONデータから戦術解析に必要な情報(配牌、ツモ、打牌、鳴き、リーチ、和了)だけを抽出するメソッドをPythonで作成する。

### ◯JSONの構造

```json
{
  "head": { ... プレイヤー情報・最終結果 ... },
  "data": {
    "data": {
      "actions": [
        { "type": 1, "result": { "name": "...", "data": { ... } } },  ← ゲームイベント
        { "type": 2, "user_input": { ... } },  ← ユーザー入力（冗長なので不要）
        { "type": 3, "user_event": { ... } },  ← 接続イベント（不要）
        ...
      ]
    }
  }
}
```

この中から抽出すべきは type: 1 の result だけ。<br>
出現する name は以下の通り。

| name                    | 意味                               |
| ----------------------- | ---------------------------------- |
| .lq.RecordNewRound      | 局開始（配牌・ドラ・スコア）       |
| .lq.RecordDealTile      | ツモ                               |
| .lq.RecordDiscardTile   | 打牌（is_liqi: true でリーチ宣言） |
| .lq.RecordChiPengGang   | チー(0) / ポン(1) / 明カン(2)      |
| .lq.RecordAnGangAddGang | 暗カン(2) / 加カン(3)              |
| .lq.RecordHule          | 和了                               |
| .lq.RecordNoTile        | 流局                               |
