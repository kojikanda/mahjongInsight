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

# 麻雀戦術解析について

## ■ 課題

雀魂の牌譜をGemini APIに読み込ませて解析させたが、想定以上に解析の精度が低い。<br>
1局の牌譜データをgemini-2.5-proに解析させるだけでも以下の課題が出てきた。

- 現物が理解できていない。
- リーチしているプレイヤーを理解できていない。
- ドラとのくっつきをかなり軽視している。
- 孤立牌が理解できていない。
- 安全重視の考え方が理解できていない。

このように基本的なことが理解・解釈できておらず、このままGemini APIに解析させるのは時間の無駄のような気がしたので、他の方法を模索した。

## ■ ChatGPTに相談

ChatGPTに他に麻雀解析のAIはないかと尋ねると、以下の回答が返ってきた。

```
あります。しかも、正直なところ「Geminiに直接牌譜を読ませて戦術判断させる」のは、かなり難しい部類です。

理由は、麻雀が

不完全情報ゲーム
多人数ゲーム
局収支と半荘収支がズレる
打点・速度・放銃率のトレードオフが複雑
“未来のツモ”を仮定した期待値計算が必要

という、LLMが苦手な要素の塊だからです。

なので、今の麻雀AI界隈では、
「LLM単体で解析」ではなく、

専用麻雀AIで局面評価
その結果をLLMで自然言語化

という2段構成が主流です。

今の構成だと、

>Geminiに直接「この打牌はなぜ悪い？」を考えさせている

可能性がありますが、ここがボトルネックかもしれません。
```

ChatGPTは、代わりの候補として「Mortal」を挙げてきた。<br>
どうも、MortalはGitHubに実装が公開されており、これが使える模様。<br>
つまり、以下のようにMortalとGemini APIの両方を使うことで、今までより格段に正確な解析ができるという判断。

```
Mortal
↓
打牌期待値
↓
構造化JSON
↓
Geminiで説明生成
↓
ナレッジグラフ化
```

## ■ Mortal導入

### ◯Mortalを直接使えるか調査

#### Claude Codeの検討結果

致命的な問題：Mortal モデルの重みが非公開。

Mortal の作者が公式 Gist で以下を明言しています：

```
「現時点でモデルの重みを公開する予定はない」
理由：オンライン麻雀でのチート防止
```

リリースページにもビルド済みバイナリなし。Hugging Face等にも存在しない。<br>
これにより、「Mortal をローカルで実行して打牌期待値を取得する」という当初の実装は現時点では不可能です。

### ◯Akagiの仕組み利用

これに対し、Akagi(https://github.com/shinkuan/Akagi)という牌譜解析ツールの仕組みが使えるとのこと。<br>
Akagiは内部で、Mortalのモデルデータを使用しており、Akagiのリリースzipにplaceholderモデルが入っている。<br>
プロトタイプの確認としては、このplaceholderモデルが使える。<br>
また、より精度の高いモデルは、AkagiのDiscordでダウンロードできるようになっており、Discordのコミュニティに参加すれば、誰でも取得可能とのこと。

### ◯環境構築

#### 環境構築の全体像

| 項目              | 内容                                    | 備考                         |
| ----------------- | --------------------------------------- | ---------------------------- |
| Rust toolchain    | rustup でインストール                   | libriichi のビルドに必須     |
| libriichi.so      | Mortal リポジトリを clone → cargo build | Python バインディング本体    |
| Python 3.12       | conda で管理                            | Mortal が Python 3.12 指定   |
| PyTorch           | pip でインストール                      | CPU 版で可（GPU あれば高速） |
| mortal.pth        | Akagi リリース zip から取得             | placeholder モデル           |
| Mortal スクリプト | GitHub から clone                       | mortal.py / model.py 等      |

#### ライセンス整理

| ツール             | ライセンス                | 今回の利用                                         |
| ------------------ | ------------------------- | -------------------------------------------------- |
| Mortal / libriichi | AGPL-3.0                  | サブプロセス呼び出し → 問題なし                    |
| Akagi              | AGPL-3.0 + Commons Clause | コードをコピーしない、変換ロジックを参考に独自実装 |
| mjai-reviewer      | Apache-2.0                | 参考のみ                                           |

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

## ■ サブプロセスの起動

```python
proc = subprocess.Popen(
        [str(MORTAL_VENV), str(MORTAL_PY), str(player_seat)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        cwd=str(MORTAL_DIR),
        text=True,
        encoding="utf-8",
    )
```

- パラメータ: args[0]
  - 値: MORTAL_VENV
  - 説明: 実行するPythonインタープリタのパス（mortal_engine専用venv）
- パラメータ: args[1]
  - 値: MORTAL_PY
  - 説明: 実行するスクリプト（mortal.py）のパス
- パラメータ: args[2]
  - 値: player_seat
  - 説明: mortal.py に渡すコマンドライン引数（解析対象の座席番号）
- パラメータ: stdin=PIPE
  - 値: -
  - 説明: 親プロセスから子プロセスへデータを書き込めるようにする（mjai JSONLを1行ずつ送る）
- パラメータ: stdout=PIPE
  - 値: -
  - 説明: 子プロセスからの出力を親プロセスで読み取れるようにする（Mortalのレスポンスを受け取る）
- パラメータ: stderr=DEVNULL
  - 値: -
  - 説明: 子プロセスのエラー出力を破棄する（mortal.pyのログを無視）
- パラメータ: cwd=MORTAL_DIR
  - 値: -
  - 説明: 子プロセスのカレントディレクトリを mortal/ に設定する（mortal.pth や config.toml の相対パス解決のため）
- パラメータ: text=True
  - 値: -
  - 説明: stdin/stdout をバイト列ではなく文字列として扱う
- パラメータ: encoding="utf-8"
  - 値: -
  - 説明: text=True 時の文字コード指定

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
