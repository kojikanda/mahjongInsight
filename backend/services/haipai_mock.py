def get_mock_haipai(game_id: str) -> dict:
    """
    牌譜のモックデータを返すメソッド

    Args:
        game_id (str): ゲームID

    Returns:
        dict: 牌譜のモックデータ
    """

    return {
        "game_id": game_id,
        "players": ["Player1", "Player2", "Player3", "Player4"],
        "rounds": [
            {
                "round": "東1局",
                "winner": "Player1",
                "winning_hand": "タンヤオ ピンフ",
                "loser": "Player3",
                "points": 3900,
            },
            {
                "round": "東2局",
                "winner": "Player2",
                "winning_hand": "リーチ 一発 ツモ",
                "loser": None,
                "points": 2000,
            },
            {
                "round": "東3局",
                "winner": "Player4",
                "winning_hand": "チャンタ 三色",
                "loser": "Player1",
                "points": 5200,
            },
        ],
        "final_scores": {
            "Player1": 18000,
            "Player2": 35000,
            "Player3": 22000,
            "Player4": 25000,
        },
    }
