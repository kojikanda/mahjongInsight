import json
import os
from fastapi import FastAPI, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from models import AnalyzeRequest, AnalyzeResponse
from pathlib import Path
from services.gemini_service import (
    analyze_haipai,
    analyze_haipai_stream,
    analyze_paifu_text,
    analyze_paifu_text_stream,
)
from services.paifu_parser import extract_tactics_from_bytes
from services.haipai_mock import get_mock_haipai
from services.paifu_to_mjai import paifu_to_mjai
from services.mortal_service import analyze_paifu_mjai

# プロジェクトルート
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 対象プレイヤー名
MY_NICKNAME = "__わんち__"

# FastAPIインスタンス生成
app = FastAPI()


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    """
    牌譜解析API処理

    Args:
        request (AnalyzeRequest): APIリクエスト

    Returns:
        AnalyzeResponse: APIレスポンス
    """

    haipai_data = get_mock_haipai(request.game_id)
    analysis = analyze_haipai(haipai_data)
    return AnalyzeResponse(game_id=request.game_id, analysis=analysis)


@app.post("/analyze/stream")
async def analyze_stream(request: AnalyzeRequest) -> StreamingResponse:
    """
    牌譜解析API処理(ストリーミングレスポンス)

    Args:
        request (AnalyzeRequest): APIリクエスト

    Returns:
        StreamingResponse: APIレスポンス
    """

    haipai_data = get_mock_haipai(request.game_id)
    generator = analyze_haipai_stream(haipai_data)
    return StreamingResponse(generator, media_type="text/plain")


@app.post("/admin/uploadpaifu")
async def upload_paifu(file: UploadFile = File(...)):
    """
    JSONの牌譜データアップロードAPI

    Args:
        file (UploadFile, optional): アップロードされたファイル

    Returns:
        dict: 解析結果を格納したディクショナリ
    """

    content = await file.read()
    tactics_text = extract_tactics_from_bytes(content, my_nickname=MY_NICKNAME)

    # for debug: 抽出した文字列データをファイルに出力
    # _output_str_to_text_file(tactics_text)

    analysis = analyze_paifu_text(tactics_text)
    # analysis = "test"
    return {"analysis": analysis}


@app.post("/admin/uploadpaifu/stream")
async def upload_paifu_stream(file: UploadFile = File(...)):
    """
    JSONの牌譜データアップロードAPI(ストリーミングレスポンス)

    Args:
        file (UploadFile, optional): アップロードされたファイル

    Returns:
        StreamingResponse: 解析結果を格納したレスポンス
    """

    content = await file.read()
    tactics_text = extract_tactics_from_bytes(content, my_nickname=MY_NICKNAME)

    # # for debug: 抽出した文字列データをファイルに出力
    # _output_str_to_text_file(tactics_text)

    return StreamingResponse(
        analyze_paifu_text_stream(tactics_text), media_type="text/plain"
    )


@app.post("/admin/uploadtextpaifu")
async def upload_text_paifu(file: UploadFile = File(...)):
    """
    テキストの牌譜データアップロードAPI

    Args:
        file (UploadFile, optional): アップロードされたファイル

    Returns:
        dict: 解析結果を格納したディクショナリ
    """

    content = await file.read()
    tactics_text = content.decode("utf-8")

    analysis = analyze_paifu_text(tactics_text)
    return {"analysis": analysis}


@app.post("/admin/uploadtextpaifu/stream")
async def upload_text_paifu_stream(file: UploadFile = File(...)):
    """
    テキストの牌譜データアップロードAPI(ストリーミングレスポンス)

    Args:
        file (UploadFile, optional): アップロードされたファイル

    Returns:
        StreamingResponse: 解析結果を格納したレスポンス
    """

    content = await file.read()
    tactics_text = content.decode("utf-8")

    return StreamingResponse(
        analyze_paifu_text_stream(tactics_text), media_type="text/plain"
    )


@app.post("/convert/mjai")
async def convert_to_mjai(
    paifu_file: UploadFile = File(...),
    player_seat: int = Query(default=0, ge=0, le=3),
):
    """
    牌譜JSONをアップロードしてmjai形式のJSONLに変換し、サーバーのファイルに保存して変換結果を返す。

    Args:
        paifu_file(UploadFile): アップロードされたファイル
        player_seat(int): 解析対象となるプレイヤーの席順

    Returns:
        dict: {
            'mjai_test': 変換後のmjai形式の文字列
            'saved_path': 保存したファイルのパス
        }
    """

    content = await paifu_file.read()
    paifu_data = json.loads(content.decode("utf-8"))

    # 牌譜JSONをmjai形式のJSONLに変換
    mjai_text = paifu_to_mjai(paifu_data, player_seat)

    # アップロードされたファイル名を元に、出力するファイル名を決定
    stem = os.path.splitext(paifu_file.filename)[0]
    output_filename = stem + "_mjai.jsonl"

    # 変換結果をファイルとして保存（デバッグ・再利用用途）
    save_path = PROJECT_ROOT / "docs" / "ref" / output_filename
    save_path.write_text(mjai_text, encoding="utf-8")

    return {"mjai_text": mjai_text, "saved_path": str(save_path)}


@app.post("/analyze/mortal")
async def analyze_with_mortal(
    mjai_file: UploadFile = File(...),
    player_seat: int = Query(default=0, ge=0, le=3),
):
    """
    mjai形式のJSONLファイルをアップロードしてMortalで解析し、各打牌ターンのEV（期待値）をJSONで返す。

    Args:
        paifu_file(UploadFile): アップロードされたファイル
        player_seat(int): 解析対象となるプレイヤーの席順

    Returns:
        dict: {
            'results': 解析結果
        }
    """

    content = await mjai_file.read()
    mjai_text = content.decode("utf-8")
    results = analyze_paifu_mjai(mjai_text, player_seat)
    return {"results": results}


def _output_str_to_text_file(text: str):
    output_pass = PROJECT_ROOT / "docs" / "ref" / "paifu_compact.txt"
    with open(output_pass, "w", encoding="utf-8") as f:
        f.write(text)
