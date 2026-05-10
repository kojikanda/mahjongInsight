import json
from pathlib import Path

# 鳴きの種類
MELD_TYPE = {0: "チー", 1: "ポン", 2: "明カン"}
# 感の種類
GANG_TYPE = {2: "暗カン", 3: "加カン"}
# 場
ROUND_WIND = {0: "東", 1: "南", 2: "西", 3: "北"}
# 字牌の日本語名マッピング
JIHAI_NAMES = {
    "1z": "東",
    "2z": "南",
    "3z": "西",
    "4z": "北",
    "5z": "白",
    "6z": "發",
    "7z": "中",
}


def extract_tactics(json_path: str, my_nickname: str | None = None) -> str:
    """
    JSONファイルの牌譜データから戦術解析用コンパクトテキストを生成する。

    Args:
        json_path (str): 牌譜JSONファイルのパス
        my_nickname (str | None, optional): 自分のニックネーム

    Returns:
        str: コンパクトな戦術テキスト（全局分）
    """

    raw = json.loads(Path(json_path).read_text(encoding="utf-8"))
    return _extract_from_raw(raw, my_nickname)


def extract_tactics_from_bytes(data: bytes, my_nickname: str | None = None) -> str:
    """
    バイナリデータの牌譜データから戦術解析用コンパクトテキストを生成する。

    Args:
        data (bytes): 牌譜データのバイナリデータ
        my_nickname (str | None, optional): 自分のニックネーム

    Returns:
        str: コンパクトな戦術テキスト（全局分）
    """

    raw = json.loads(data.decode("utf-8"))
    return _extract_from_raw(raw, my_nickname)


def _extract_from_raw(raw: dict, my_nickname: str | None) -> str:
    """
    雀魂の牌譜JSONから戦術解析用コンパクトテキストを生成する。

    Args:
        raw: 牌譜JSONデータ
        my_nickname: 自分のニックネーム

    Returns:
        コンパクトな戦術テキスト（全局分）
    """

    # seat番号とニックネームの対応を作る
    accounts = raw["head"]["accounts"]
    seat_to_name = {acc["seat"]: acc["nickname"] for acc in accounts}

    # 自分のニックネーム二対応するseat番号を判定
    my_seat = None
    if my_nickname:
        for acc in accounts:
            if acc["nickname"] == my_nickname:
                my_seat = acc["seat"]
                break

    # type: 1 のゲームイベントのみ抽出（user_input / user_event は捨てる）
    game_events = [
        a["result"]
        for a in raw["data"]["data"]["actions"]
        if a.get("type") == 1 and "result" in a
    ]

    # RecordNewRound を区切りとして局ごとにリストへ分割
    rounds: list[list[dict]] = []
    current: list[dict] = []
    for ev in game_events:
        if ev["name"] == ".lq.RecordNewRound":
            if current:
                rounds.append(current)
            current = [ev]
        else:
            current.append(ev)
    if current:
        rounds.append(current)

    # 出力する内容を格納した配列
    lines: list[str] = []

    # 全プレイヤー名の行
    # ex. S0:player_name1 / S1:player_name2(自) / S2:player_name3 / S3:player_name4
    players_str = " / ".join(
        f"S{s}:{n}{'(自)' if s == my_seat else ''}"
        for s, n in sorted(seat_to_name.items())
    )
    lines.append(f"半荘ID: {raw['head']['uuid']}")
    lines.append(f"プレイヤー: {players_str}")
    lines.append("")

    # 1局単位で文字列フォーマットに変換
    for round_events in rounds:
        lines.extend(_format_round(round_events, my_seat))
        lines.append("")

    return "\n".join(lines)


def _format_round(events: list[dict], my_seat: int | None) -> list[str]:
    """
    1局単位で文字列フォーマットに変換する。

    Args:
        events (list[dict]): イベントのリスト
        my_seat (int | None): 自プレイヤーのシート番号(0~3)

    Returns:
        list[str]: コンパクトな戦術テキスト（1局分）
    """

    # 結果を格納する配列
    lines: list[str] = []

    # 局開始時(RecordNewRound)のデータ
    h = events[0]["data"]
    # 0=東場, 1=南場
    chang = h["chang"]
    # 東場、南場の1〜4局を1始まりに変換
    ju = h["ju"] + 1
    # 本場数
    ben = h["ben"]
    # ドラ
    current_indicators = list(h["doras"])
    doras = " ".join(
        # ドラ表示牌を実際のドラに変換
        _tile_display(_dora_indicator_to_dora(d))
        for d in current_indicators
    )
    # 得点状況
    scores = h["scores"]
    lines.append(
        f"=== {ROUND_WIND[chang]}{ju}局 {ben}本場 | ドラ:{doras} | スコア:{scores} ==="
    )

    # 配牌（東家=親だけ14枚、他は13枚）
    for seat_idx in range(4):
        tiles = " ".join(_tile_display(t) for t in h.get(f"tiles{seat_idx}", []))
        mark = "★" if seat_idx == my_seat else " "
        lines.append(f"  {mark} S{seat_idx} 配牌: {tiles}")
    lines.append("  " + "-" * 50)

    # ゲームイベントを順番に処理
    def mark(seat: int) -> str:
        return "★" if seat == my_seat else " "

    for ev in events[1:]:
        name = ev["name"]
        d = ev["data"]

        # ツモ
        if name == ".lq.RecordDealTile":
            seat, tile = d["seat"], _tile_display(d["tile"])

            # カン後のリンシャンツモで、dorasフィールドが存在し、件数が増えていたら新ドラを出力する
            if "doras" in d and len(d["doras"]) > len(current_indicators):
                # 増えたドラ表示牌を取り出す
                new_indicators = d["doras"][len(current_indicators) :]
                for indicator in new_indicators:
                    # ドラ表示牌を実際のドラに変換
                    new_dora = _tile_display(_dora_indicator_to_dora(indicator))
                    lines.append(f"  [新ドラ: {new_dora}]")
                current_indicators = list(d["doras"])

            lines.append(f"  {mark(seat)} S{seat} ツモ:{tile}")

        # 打牌
        elif name == ".lq.RecordDiscardTile":
            seat, tile = d["seat"], _tile_display(d["tile"])
            riichi = " 【リーチ宣言!】" if d.get("is_liqi") else ""
            tsumogiri = "(ツモ切)" if d.get("moqie") else ""
            lines.append(f"  {mark(seat)} S{seat} 打:{tile}{tsumogiri}{riichi}")

        # 鳴き(ポン・チー)
        elif name == ".lq.RecordChiPengGang":
            seat = d["seat"]
            meld = MELD_TYPE.get(d["type"], f"鳴き{d['type']}")
            tiles = " ".join(_tile_display(t) for t in d["tiles"])
            from_seat = next((f for f in d["froms"] if f != seat), "?")
            lines.append(f"  {mark(seat)} S{seat} {meld}: {tiles} (S{from_seat}から)")

        # カン
        elif name == ".lq.RecordAnGangAddGang":
            seat = d["seat"]
            gang = GANG_TYPE.get(d["type"], "カン")
            lines.append(f"  {mark(seat)} S{seat} {gang}: {_tile_display(d['tiles'])}")

        # 和了
        elif name == ".lq.RecordHule":
            for hule in d["hules"]:
                seat = hule["seat"]
                hand = " ".join(_tile_display(t) for t in hule["hand"])
                hu_tile = _tile_display(hule["hu_tile"])
                win_type = "ツモ" if hule["zimo"] else "ロン"
                riichi = " リーチ" if hule.get("liqi") else ""
                points = hule.get("point_sum", hule.get("point_rong", "?"))
                lines.append(
                    f"  {mark(seat)} S{seat} 【和了】{win_type}{riichi}"
                    f" | 手牌:{hand} | 和了牌:{hu_tile} | {points}点"
                )
            lines.append(f"      スコア変動: {d['delta_scores']}")

        # 流局
        elif name == ".lq.RecordNoTile":
            lines.append("  【流局】")
            for i, p in enumerate(d["players"]):
                tenpai = "テンパイ" if p.get("tingpai") else "ノーテン"
                hand = " ".join(_tile_display(t) for t in p.get("hand", []))
                lines.append(f"    {mark(i)} S{i}: {tenpai} {hand}")
            if "delta_scores" in d:
                lines.append(f"      スコア変動: {d['delta_scores']}")

    return lines


def _dora_indicator_to_dora(indicator: str) -> str:
    """
    ドラ表示牌から実際のドラを返す。

    Args:
        indicator (str): ドラ表示牌の文字列

    Returns:
        str: 実際のドラの文字列
    """

    suit = indicator[-1]  # 'm', 'p', 's', 'z'
    num = int(indicator[0])

    # 数牌
    if suit in ("m", "p", "s"):
        # 赤五(0)は5として扱う
        if num == 0:
            num = 5
        return f"{1 if num == 9 else num + 1}{suit}"

    # z牌(字牌)
    if 1 <= num <= 4:
        # 風牌: 4z(北)の次は1z(東)
        return f"{1 if num == 4 else num + 1}z"
    else:
        # 三元牌: 7z(中)の次は5z(白)
        return f"{5 if num == 7 else num + 1}z"


def _tile_display(tile: str) -> str:
    """
    牌が赤ドラの場合、赤5と分かる表記に修正する。

    Args:
        tile (str): 牌の文字列

    Returns:
        str: 修正後の文字列
    """
    if tile[0] == "0":
        # 0m→赤5m, 0p→赤5p, 0s→赤5s
        return f"赤5{tile[1]}"
    if tile in JIHAI_NAMES:
        return JIHAI_NAMES[tile]
    return tile
