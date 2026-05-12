import json

# 字牌の牌表記変換辞書
_Z_MAP = {
    "1z": "E",
    "2z": "S",
    "3z": "W",
    "4z": "N",
    "5z": "P",
    "6z": "F",
    "7z": "C",
}


def paifu_to_mjai(paifu_data: dict, player_seat: int) -> str:
    """
    雀魂の牌譜JSONをmjai形式(JSONL)に変換する。
    出力は1行1イベントのJSONL文字列。
    player_seatに指定した座席のみ実牌を表示し、他は"?"で隠す
    （牌譜解析の際にMortalへ渡す形式に合わせる）。

    Args:
        paifu_data(dict): 雀魂の牌譜JSON(トップレベルオブジェクト)
        player_seat(int): 解析対象プレイヤーの座席番号(0-3)

    Returns:
        mjai JSONL文字列（1行1イベント）
    """
    lines: list[str] = []

    # 対局開始データ
    accounts = paifu_data["head"]["accounts"]
    names = [""] * 4
    for acc in accounts:
        names[acc["seat"]] = acc["nickname"]

    lines.append(
        json.dumps(
            {"type": "start_game", "id": player_seat, "names": names},
            ensure_ascii=False,
        )
    )

    # 局ごとに処理
    actions = paifu_data["data"]["data"]["actions"]
    current_doras: list[str] = []
    current_scores: list[int] = [25000, 25000, 25000, 25000]
    # 直前の打牌者（ロン判定用）
    last_discard_seat: int = -1

    for idx, action in enumerate(actions):
        if "result" not in action:
            continue
        name = action["result"]["name"]
        data = action["result"]["data"]

        if name == ".lq.RecordNewRound":
            # 局開始
            # 局開始時の情報を出力
            lines.extend(_convert_new_round(data, player_seat))
            current_doras = _ms_tiles_to_mjai(data.get("doras", []))
            current_scores = list(data["scores"])
            last_discard_seat = -1

        elif name == ".lq.RecordDealTile":
            # ツモ
            seat = data["seat"]

            # カン後の新ドラ
            if "doras" in data:
                new_doras = _ms_tiles_to_mjai(data["doras"])
                for new_d in new_doras[len(current_doras) :]:
                    # 新ドラの情報を出力
                    lines.append(
                        json.dumps(
                            {"type": "dora", "dora_marker": new_d},
                            ensure_ascii=False,
                        )
                    )
                current_doras = new_doras

            # player_seatのプレイヤーのみ、実際の牌を出力し、その他のプレイヤーは"?"で出力する
            pai = _ms_tile_to_mjai(data["tile"]) if seat == player_seat else "?"
            lines.append(
                # ツモの情報を出力
                json.dumps(
                    {"type": "tsumo", "actor": seat, "pai": pai},
                    ensure_ascii=False,
                )
            )

        elif name == ".lq.RecordDiscardTile":
            # 打牌
            seat = data["seat"]
            pai = _ms_tile_to_mjai(data["tile"])
            # ツモ切りかどうかを判別
            tsumogiri = data.get("moqie", False)
            last_discard_seat = seat

            # リーチ宣言かどうかを判別
            if data.get("is_liqi", False):
                # リーチ宣言があった場合はリーチ宣言の情報を出力
                lines.append(
                    json.dumps(
                        {"type": "reach", "actor": seat},
                        ensure_ascii=False,
                    )
                )

            # 打牌の情報を出力
            lines.append(
                json.dumps(
                    {
                        "type": "dahai",
                        "actor": seat,
                        "pai": pai,
                        "tsumogiri": tsumogiri,
                    },
                    ensure_ascii=False,
                )
            )

            # リーチ宣言かどうかを判別
            if data.get("is_liqi", False):
                # 次のイベントがRecordHule（ロン）でない場合のみ、リーチ宣言牌が通ったことを出力
                if not _next_event_is_ron(actions, idx):
                    lines.append(
                        json.dumps(
                            {"type": "reach_accepted", "actor": seat},
                            ensure_ascii=False,
                        )
                    )

        elif name == ".lq.RecordChiPengGang":
            # チー・ポン・明カンの情報を出力
            lines.extend(_convert_chi_peng_gang(data))

        elif name == ".lq.RecordAnGangAddGang":
            # 加カン・暗カンの情報を出力
            lines.extend(_convert_an_gang_add_gang(data))

        elif name == ".lq.RecordHule":
            # 和了
            # 点数の差分を算出
            old_scores = data.get("old_scores", current_scores)
            new_scores = data.get("scores", current_scores)
            deltas = [new_scores[i] - old_scores[i] for i in range(4)]

            # 和了の内容をチェック
            for hule in data.get("hules", []):
                # 和了したプレイヤー
                winner = hule["seat"]
                # アガリ牌
                pai = _ms_tile_to_mjai(hule["hu_tile"])
                # ツモ上がりか
                is_tsumo = hule.get("zimo", False)
                # ツモ上がりしたときは自分、ロン上がりしたときは放銃したプレイヤー
                target = winner if is_tsumo else last_discard_seat
                # 和了の情報を出力
                lines.append(
                    json.dumps(
                        {
                            "type": "hora",
                            "actor": winner,
                            "target": target,
                            "pai": pai,
                            "deltas": deltas,
                        },
                        ensure_ascii=False,
                    )
                )

            # 局終了の情報を出力
            lines.append(json.dumps({"type": "end_kyoku"}, ensure_ascii=False))

            # 現在の得点状況を保持
            if "scores" in data:
                current_scores = list(data["scores"])

        elif name == ".lq.RecordNoTile":
            # 流局
            # 点数の差分を算出
            if data.get("scores"):
                deltas = list(data["scores"][0]["delta_scores"])
            else:
                deltas = [0, 0, 0, 0]

            # 流局の情報を出力
            lines.append(
                json.dumps({"type": "ryukyoku", "deltas": deltas}, ensure_ascii=False)
            )
            # 局終了の情報を出力
            lines.append(json.dumps({"type": "end_kyoku"}, ensure_ascii=False))

            # 現在の得点状況を保持
            if data.get("scores"):
                deltas = data["scores"][0]["delta_scores"]
                current_scores = [current_scores[i] + deltas[i] for i in range(4)]

    # 局終了の情報を出力
    lines.append(json.dumps({"type": "end_game"}, ensure_ascii=False))

    # 出力する情報を改行を入れた文字列に変換
    return "\n".join(lines)


def _ms_tile_to_mjai(tile: str) -> str:
    """
    雀魂の牌表記からmjaiの牌表記へ変換する。
    赤ドラと字牌の表記を変換する。

    Args:
        tile(str): 雀魂の牌表記

    Returns:
        str: mjaiの牌表記
    """

    if tile == "0m":
        return "5mr"
    if tile == "0p":
        return "5pr"
    if tile == "0s":
        return "5sr"
    return _Z_MAP.get(tile, tile)


def _ms_tiles_to_mjai(tiles: list[str]) -> list[str]:
    """
    雀魂の牌表記からmjaiの牌表記へ変換する。
    赤ドラと字牌の表記を変換する。

    Args:
        tiles(list[str]): 雀魂の牌表記のリスト

    Returns:
        list[str]: mjaiの牌表記のリスト
    """

    return [_ms_tile_to_mjai(t) for t in tiles]


def _convert_new_round(data: dict, player_seat: int) -> list[str]:
    """
    局開始時の情報をmjai形式のJSONに変換する。
    親の14牌目は、1回目のツモとして処理する。

    Args:
        data(dict): 局開始イベントデータのディクショナリ
        player_seat(int): プレイヤーの席順

    Returns:
        list[str]: mjai形式のJSON。start_kyoku: 局開始時の情報, tsumo: 親の14牌目は(第1ツモとして扱う)。
    """

    # 各座席の配牌
    tiles_per_seat = [data.get(f"tiles{i}", []) for i in range(4)]
    # 親の座席を判別する
    # まず、配牌が14枚になっている座席を親と判断する
    # 配牌が14枚になっていない場合は、現在の局の情報から判別する
    # chang: 0=東場, 1=南場, ju: 東場、南場の1〜4局(0始まり)
    oya = next(
        (i for i, t in enumerate(tiles_per_seat) if len(t) == 14),
        (data["chang"] * 4 + data["ju"]) % 4,
    )

    # 各座席の配牌
    # player_seatの座席のみ実際の表記を設定する
    tehais = []
    for seat in range(4):
        if seat == player_seat:
            tehais.append(_ms_tiles_to_mjai(tiles_per_seat[seat][:13]))
        else:
            tehais.append(["?"] * 13)

    # ドラ
    dora_markers = _ms_tiles_to_mjai(data.get("doras", []))
    # 場風牌
    bakaze = ["E", "S", "W", "N"][data["chang"]]

    # 局開始の情報をまとめたJSON
    start_kyoku = {
        "type": "start_kyoku",
        "bakaze": bakaze,
        "dora_marker": dora_markers[0] if dora_markers else "?",
        "kyoku": data["ju"] + 1,
        "honba": data["ben"],
        "kyotaku": data.get("liqibang", 0),
        "oya": oya,
        "scores": list(data["scores"]),
        "tehais": tehais,
    }

    # 親の14枚目以降→最初のツモとして設定する(mjaiではstart_kyokuには13枚、14枚目はtsumoイベントで渡す)
    dealer_14th = _ms_tile_to_mjai(tiles_per_seat[oya][13])
    pai = dealer_14th if oya == player_seat else "?"
    tsumo = {"type": "tsumo", "actor": oya, "pai": pai}

    return [
        json.dumps(start_kyoku, ensure_ascii=False),
        json.dumps(tsumo, ensure_ascii=False),
    ]


def _convert_chi_peng_gang(data: dict) -> list[str]:
    """
    チー・ポン・明カンの情報をmjai形式のJSONに変換する

    Args:
        data(dict): チー・ポン・明カンイベントのディクショナリ

    Returns:
        list[str]: mjai形式のJSON。type: chi(チー), pon(ポン), daiminkan(明カン)。
    """

    seat = data["seat"]
    meld_type = data["type"]
    tiles = _ms_tiles_to_mjai(data["tiles"])
    froms = data["froms"]

    # 他家からの牌（stolen）を特定（froms[i] != seat の牌）
    stolen_idx = next(
        (i for i, f in enumerate(froms) if f != seat),
        len(froms) - 1,
    )
    target = froms[stolen_idx]
    pai = tiles[stolen_idx]
    consumed = [t for i, t in enumerate(tiles) if i != stolen_idx]

    if meld_type == 0:
        # チー
        event = {
            "type": "chi",
            "actor": seat,
            "target": target,
            "pai": pai,
            "consumed": consumed,
        }
    elif meld_type == 1:
        # ポン
        event = {
            "type": "pon",
            "actor": seat,
            "target": target,
            "pai": pai,
            "consumed": consumed,
        }
    else:
        # 明カン
        event = {
            "type": "daiminkan",
            "actor": seat,
            "target": target,
            "pai": pai,
            "consumed": consumed,
        }

    return [json.dumps(event, ensure_ascii=False)]


def _convert_an_gang_add_gang(data: dict) -> list[str]:
    """
    加カン・暗カンの情報をmjai形式のJSONに変換する。

    Args:
        data(dict): 加カン・暗カンイベントのディクショナリ

    Returns:
        list[str]: mjai形式のJSON
    """

    seat = data["seat"]
    kan_type = data["type"]
    # 'tiles' は単一文字列
    tile = _ms_tile_to_mjai(data["tiles"])

    if kan_type == 3:
        # 暗カン
        event = {"type": "ankan", "actor": seat, "consumed": [tile, tile, tile, tile]}
    else:
        # 加カン
        event = {"type": "kakan", "actor": seat, "pai": tile}

    return [json.dumps(event, ensure_ascii=False)]


def _next_event_is_ron(actions: list, current_idx: int) -> bool:
    """
    現在のインデックスより後に、最初に現れる有効なイベントがロン（RecordHule）かどうかを返す。
    リーチ宣言牌がロンされたかを判定するために使用する。

    Args:
        actions(list): actionのリスト
        current_idx(int): 現在実行中のインデックス

    Returns:
        _type_: _description_
    """

    for action in actions[current_idx + 1 :]:
        if "result" not in action:
            continue
        name = action["result"]["name"]
        data = action["result"]["data"]
        if name == ".lq.RecordHule":
            # zimo=False → ロン（ツモあがりではない）
            hules = data.get("hules", [])
            return any(not h.get("zimo", False) for h in hules)
        # ロン以外のイベントが先に現れれば、ロンではない
        return False

    # 後続にイベントが無い場合もロンではない
    return False
