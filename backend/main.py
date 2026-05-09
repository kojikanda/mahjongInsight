from fastapi import FastAPI, UploadFile, File
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
    牌譜データアップロードAPI

    Args:
        file (UploadFile, optional): アップロードされたファイル

    Returns:
        dict: 解析結果を格納したディクショナリ
    """

    content = await file.read()
    tactics_text = extract_tactics_from_bytes(content, my_nickname=MY_NICKNAME)

    # for debug: 抽出した文字列データをファイルに出力
    _output_str_to_text_file(tactics_text)

    analysis = analyze_paifu_text(tactics_text)
    # analysis = "test"
    return {"analysis": analysis}


@app.post("/admin/uploadpaifu/stream")
async def upload_paifu_stream(file: UploadFile = File(...)):
    """
    牌譜データアップロードAPI(ストリーミングレスポンス)

    Args:
        file (UploadFile, optional): アップロードされたファイル

    Returns:
        dict: 解析結果を格納したディクショナリ
    """

    content = await file.read()
    tactics_text = extract_tactics_from_bytes(content, my_nickname=MY_NICKNAME)

    # # for debug: 抽出した文字列データをファイルに出力
    # _output_str_to_text_file(tactics_text)

    return StreamingResponse(
        analyze_paifu_text_stream(tactics_text), media_type="text/plain"
    )


def _output_str_to_text_file(text: str):
    output_pass = PROJECT_ROOT / "docs" / "ref" / "paifu_compact.txt"
    with open(output_pass, "w", encoding="utf-8") as f:
        f.write(text)
