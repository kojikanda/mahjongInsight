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

    prompt = f"""以下は麻雀の対局データです（戦術的な情報のみ抽出済み）。                           
                                                                                                      
  {paifu_text}                                                                                        
                                                                                                      
  ★マーク付きのプレイヤーの対局全体を分析し、以下の観点で改善点を3つ挙げてください。
  - 押し引きの判断                                                                                    
  - リーチ判断（かけるべきでなかった、またはかけるべきだった場面）                                    
  - 牌効率や手作りのミス                                                                              
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

    prompt = f"""以下は麻雀の対局データです（戦術的な情報のみ抽出済み）。
                                                                                                      
  {paifu_text}
                                                                                                      
  ★マーク付きのプレイヤーの対局全体を分析し、以下の観点で改善点を3つ挙げてください。
  - 押し引きの判断
  - リーチ判断（かけるべきでなかった、またはかけるべきだった場面）
  - 牌効率や手作りのミス                                                                              
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
