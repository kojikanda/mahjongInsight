import json
from pathlib import Path

MELD_TYPE = {0: "チー", 1: "ポン", 2: "明カン"}
GANG_TYPE = {2: "暗カン", 3: "加カン"}
ROUND_WIND = {0: "東", 1: "南", 2: "西", 3: "北"}


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
    doras = " ".join(h["doras"])
    # 得点状況
    scores = h["scores"]
    lines.append(
        f"=== {ROUND_WIND[chang]}{ju}局 {ben}本場 | ドラ:{doras} | スコア:{scores} ==="
    )

    # 配牌（東家=親だけ14枚、他は13枚）
    for seat_idx in range(4):
        tiles = " ".join(h.get(f"tiles{seat_idx}", []))
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
            seat, tile = d["seat"], d["tile"]
            lines.append(f"  {mark(seat)} S{seat} ツモ:{tile}")

        # 打牌
        elif name == ".lq.RecordDiscardTile":
            seat, tile = d["seat"], d["tile"]
            riichi = " 【リーチ宣言!】" if d.get("is_liqi") else ""
            tsumogiri = "(ツモ切)" if d.get("moqie") else ""
            lines.append(f"  {mark(seat)} S{seat} 打:{tile}{tsumogiri}{riichi}")

        # 鳴き(ポン・チー)
        elif name == ".lq.RecordChiPengGang":
            seat = d["seat"]
            meld = MELD_TYPE.get(d["type"], f"鳴き{d['type']}")
            tiles = " ".join(d["tiles"])
            from_seat = next((f for f in d["froms"] if f != seat), "?")
            lines.append(f"  {mark(seat)} S{seat} {meld}: {tiles} (S{from_seat}から)")

        # カン
        elif name == ".lq.RecordAnGangAddGang":
            seat = d["seat"]
            gang = GANG_TYPE.get(d["type"], "カン")
            lines.append(f"  {mark(seat)} S{seat} {gang}: {d['tiles']}")

        # 和了
        elif name == ".lq.RecordHule":
            for hule in d["hules"]:
                seat = hule["seat"]
                hand = " ".join(hule["hand"])
                hu_tile = hule["hu_tile"]
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
                hand = " ".join(p.get("hand", []))
                lines.append(f"    {mark(i)} S{i}: {tenpai} {hand}")
            if "delta_scores" in d:
                lines.append(f"      スコア変動: {d['delta_scores']}")

    return lines
