import json
import os

from google import genai
from dotenv import load_dotenv

GEMINI_API_MODEL = "gemini-2.5-flash"
# GEMINI_API_MODEL = "gemini-2.0-flash"
# GEMINI_API_MODEL = "gemini-2.5-flash-lite"

# .envファイル読み込み
load_dotenv()

# Gemini APIのクライアントを生成
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def analyze_haipai(haipai_data: dict) -> str:
    """
    Gemini APIを使って、牌譜データの解析を行う

    Args:
        haipai_data (dict): 牌譜データ

    Returns:
        str: 解析結果
    """

    # 牌譜データをJSON文字列に変換
    haipai_json = json.dumps(haipai_data, ensure_ascii=False, indent=2)

    # プロンプト構築
    prompt = f"""
以下は麻雀の対局データです。                                                                                 
                                                                                                             
{haipai_json}
                                                                                                             
この対局での大きなミスや、改善できるポイントを3つ挙げてください。
"""

    # Gemini API呼び出し
    try:
        response = client.models.generate_content(
            model=GEMINI_API_MODEL, contents=prompt
        )
    except Exception as e:
        print("Gemini API呼び出しでエラー", e)
        raise

    return response.text


def analyze_haipai_stream(haipai_data: dict):
    """
    Gemini APIを使って、牌譜データの解析を行う。
    応答はストリーミングで返す。

    Args:
        haipai_data (dict): 牌譜データ

    Returns:
        str: 解析結果
    """

    # 牌譜データをJSON文字列に変換
    haipai_json = json.dumps(haipai_data, ensure_ascii=False, indent=2)

    prompt = f"""                                                                                   
  以下は麻雀の対局データです。
                                                                                                      
  {haipai_json}
                                                                                                      
  この対局での大きなミスや、改善できるポイントを3つ挙げてください。
  """

    # Gemini API呼び出し
    try:
        for chunk in client.models.generate_content_stream(
            model=GEMINI_API_MODEL, contents=prompt
        ):
            if chunk.text:
                yield chunk.text
    except Exception as e:
        print("Gemini API呼び出しでエラー", e)
        raise


def analyze_paifu_text(paifu_text: str) -> str:
    """
    Gemini APIを使って、牌譜データの解析を行う。

    Args:
        paifu_text (str): 牌譜の文字列データ

    Returns:
        str: 解析結果
    """

    prompt = f"""
あなたは競技麻雀のプロレベルの戦術解析エージェントです。
以下の牌譜データを元に、★マーク付きプレイヤーの打牌を厳格に評価してください。

【解析対象データ】
{paifu_text}

【データの凡例】
- S0〜S3: 各プレイヤーのシート番号（配牌行に自風を記載）
- ★: 解析対象プレイヤー
- 牌の表記: 1m〜9m=萬子, 1p〜9p=筒子, 1s〜9s=索子, 東/南/西/北/白/發/中=字牌, 赤5m/赤5p/赤5s=赤ドラ
- ツモ切: ツモった牌をそのまま切ったこと
- 和了したとき
  - S0 【和了】ツモ | 手牌...: プレイヤーS0がツモ上がりした
  - S0 【和了】ロン | 手牌...: プレイヤーS0がロン上がりした
  - S0 【和了】ツモ リーチ | 手牌...: プレイヤーS0がリーチしている状況でツモ上がりした
  - S0 【和了】ロン リーチ | 手牌...: プレイヤーS0がリーチしている状況でロン上がりした

【解析のガイドライン】
1. **局の状況**: 各局の先頭に局、本場、ドラ(ドラ表示牌ではなく実際のドラ)、局開始時のスコアがあります。
2. **評価基準**: 現代の「押し引き（期待値ベース）」に基づき、現代の競技麻雀における「放銃回避コスト＜アガリ期待値」という定量的な押し引き基準で判断してく
  ださい。
3. **間違いの指摘**: 明らかな牌効率ミス（有効牌を減らす打牌）や、無防備な押し（放銃リスクと見返りの不一致）を具体的に特定してください。

【出力形式】
以下の3点を、対象の局と局内の巡目（例: 東1局 1本場 〇〇巡目）を明記して挙げてください。
- 押し引きの判断
- リーチ判断
- 牌効率・手作りのミス
"""

    try:
        response = client.models.generate_content(
            model=GEMINI_API_MODEL, contents=prompt
        )
    except Exception as e:
        print("Gemini API呼び出しでエラー", e)
        raise

    return response.text


def analyze_paifu_text_stream(paifu_text: str):
    """
    Gemini APIを使って、牌譜データの解析を行う。
    応答はストリーミングで返す。

    Args:
        paifu_text (str): 牌譜の文字列データ

    Returns:
        str: 解析結果
    """

    prompt = f"""
あなたは競技麻雀のプロレベルの戦術解析エージェントです。
以下の牌譜データを元に、★マーク付きプレイヤーの打牌を厳格に評価してください。

【解析対象データ】
{paifu_text}

【データの凡例】
- S0〜S3: 各プレイヤーのシート番号（配牌行に自風を記載）
- ★: 解析対象プレイヤー
- 牌の表記: 1m〜9m=萬子, 1p〜9p=筒子, 1s〜9s=索子, 東/南/西/北/白/發/中=字牌, 赤5m/赤5p/赤5s=赤ドラ
- ツモ切: ツモった牌をそのまま切ったこと
- 和了したとき
  - S0 【和了】ツモ | 手牌...: プレイヤーS0がツモ上がりした
  - S0 【和了】ロン | 手牌...: プレイヤーS0がロン上がりした
  - S0 【和了】ツモ リーチ | 手牌...: プレイヤーS0がリーチしている状況でツモ上がりした
  - S0 【和了】ロン リーチ | 手牌...: プレイヤーS0がリーチしている状況でロン上がりした

【解析のガイドライン】
1. **局の状況**: 各局の先頭に局、本場、ドラ(ドラ表示牌ではなく実際のドラ)、局開始時のスコアがあります。
2. **評価基準**: 現代の「押し引き（期待値ベース）」に基づき、現代の競技麻雀における「放銃回避コスト＜アガリ期待値」という定量的な押し引き基準で判断してく
  ださい。
3. **間違いの指摘**: 明らかな牌効率ミス（有効牌を減らす打牌）や、無防備な押し（放銃リスクと見返りの不一致）を具体的に特定してください。

【出力形式】
以下の3点を、対象の局と局内の巡目（例: 東1局 1本場 〇〇巡目）を明記して挙げてください。
- 押し引きの判断
- リーチ判断
- 牌効率・手作りのミス
"""

    try:
        for chunk in client.models.generate_content_stream(
            model=GEMINI_API_MODEL, contents=prompt
        ):
            if chunk.text:
                yield chunk.text
    except Exception as e:
        print("Gemini API呼び出しでエラー", e)
        raise
