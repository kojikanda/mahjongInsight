import json
import os

import google.generativeai as genai
from dotenv import load_dotenv

# .envファイル読み込み
load_dotenv()

# Gemini APIキーをGeminiクライアントに設定
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
# 使用するモデルを指定
model = genai.GenerativeModel("gemini-2.5-flash")


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
        response = model.generate_content(prompt)
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

    """ストリーミングでGemini APIを呼び出すジェネレータ関数"""
    haipai_json = json.dumps(haipai_data, ensure_ascii=False, indent=2)

    prompt = f"""                                                                                   
  以下は麻雀の対局データです。
                                                                                                      
  {haipai_json}
                                                                                                      
  この対局での大きなミスや、改善できるポイントを3つ挙げてください。
  """

    # stream=True を指定することでストリーミングモードになる
    try:
        response = model.generate_content(prompt, stream=True)
    except Exception as e:
        print("Gemini API呼び出しでエラー", e)
        raise

    # チャンクを順次 yield する
    for chunk in response:
        if chunk.text:
            yield chunk.text
