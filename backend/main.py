from fastapi import FastAPI
from models import AnalyzeRequest, AnalyzeResponse
from services.gemini_service import analyze_haipai
from services.haipai_mock import get_mock_haipai

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
