import os
import json
import subprocess
from pathlib import Path

# Mortal の作業ディレクトリ（libriichi.so と mortal.py が同居している場所）
MORTAL_DIR = Path(__file__).parent.parent / "mortal_engine" / "mortal"
MORTAL_PY = MORTAL_DIR / "mortal.py"
MORTAL_VENV = (
    Path(__file__).parent.parent / "mortal_engine" / ".venv" / "bin" / "python"
)

# mjaiアクション名 → インデックスのマッピング（46 アクション）
# libriichi_helper.pyのmask_unicode_4pから引用
_ACTION_NAMES_4P = [
    "1m",
    "2m",
    "3m",
    "4m",
    "5m",
    "5mr",
    "6m",
    "7m",
    "8m",
    "9m",
    "1p",
    "2p",
    "3p",
    "4p",
    "5p",
    "5pr",
    "6p",
    "7p",
    "8p",
    "9p",
    "1s",
    "2s",
    "3s",
    "4s",
    "5s",
    "5sr",
    "6s",
    "7s",
    "8s",
    "9s",
    "E",
    "S",
    "W",
    "N",
    "P",
    "F",
    "C",
    "reach",
    "chi_low",
    "chi_mid",
    "chi_high",
    "pon",
    "kan_select",
    "hora",
    "ryukyoku",
    "none",
]


def analyze_paifu_mjai(mjai_text: str, player_seat: int) -> list[dict]:
    """
    mjaiのJSONLテキストをMortalに渡し、各打牌ターンのEVを返す。
    mortal.pyはmjai形式のJSONLをstdinから1行ずつ受け取り、各巡目の打牌候補とQ-valuesをJSONで返す。

    Args:
        mjai_text(str): mjai形式JSONLの文字列
        player_seat(int): 解析対象の席

    Returns:
        list[dict]: {
            'kyoku':         局番号 (例: 'E1-0')
            'turn':          巡目
            'actor':         打牌プレイヤー座席番号
            'player_action': 実際の打牌
            'mortal_action': Mortal推奨打（最高Q-value）
            'player_ev':     実際の打牌のQ-value
            'mortal_ev':     Mortal推奨打牌のQ-value
            'all_actions':   [{name, q_value}, ...] 有効アクション全件
        }
    """

    proc = subprocess.Popen(
        [str(MORTAL_VENV), str(MORTAL_PY), str(player_seat)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        cwd=str(MORTAL_DIR),
        text=True,
        encoding="utf-8",
        env={**os.environ, "MORTAL_REVIEW_MODE": "1"},
    )

    results = []
    input_lines = mjai_text.strip().split("\n")
    current_kyoku = ""
    turn = 0

    try:
        for idx, line in enumerate(input_lines):
            event = json.loads(line)

            # 局情報を追跡
            if event["type"] == "start_kyoku":
                bakaze = event["bakaze"]
                kyoku_n = event["kyoku"]
                honba = event["honba"]
                current_kyoku = f"{bakaze}{kyoku_n}-{honba}"
                turn = 0

            # ツモイベントで巡目をカウント
            if event["type"] == "tsumo" and event["actor"] == player_seat:
                turn += 1

            # Mortalに1行送る
            proc.stdin.write(line + "\n")
            proc.stdin.flush()

            # Mortalの応答を1行受け取る
            # print(f"受信待ち: line={line}")
            response_line = proc.stdout.readline().strip()
            if not response_line:
                continue

            response = json.loads(response_line)

            # dahai（打牌決定 / Mortalの打牌決定であり、プレイヤーの打牌ではない）の応答のみEVを記録
            # ※この打牌決定の応答が返ってくるのは、インプットが「ツモイベント」のとき
            if response.get("type") == "dahai" and response.get("actor") == player_seat:
                meta = response.get("meta", {})
                q_values = meta.get("q_values", [])
                mask_bits = meta.get("mask_bits", 0)

                # 有効アクションのQ-value一覧を構築
                all_actions = _extract_actions(q_values, mask_bits)

                # Mortal推奨打牌（最高Q-value）
                # → この値は現状使っていないのでマスク
                # mortal_action = (
                #     max(all_actions, key=lambda x: x["q_value"])["name"]
                #     if all_actions
                #     else None
                # )

                # プレイヤーの実際の打牌（次のdahaiイベントから取得）
                # ※ Mortalの応答は"Mortalならこうする"なので、response['pai'] が推奨打牌
                # 実際の打牌は次のRecordDiscardTileに相当するdahaiイベントのpai
                player_action = _find_player_action(input_lines, idx, player_seat)

                # プレイヤー実打牌のQ-value
                player_ev = next(
                    (a["q_value"] for a in all_actions if a["name"] == player_action),
                    None,
                )

                # 結果を追加
                results.append(
                    {
                        "kyoku": current_kyoku,
                        "turn": turn,
                        "actor": player_seat,
                        "player_action": player_action,
                        "mortal_action": response["pai"],  # Mortal 推奨打牌
                        "player_ev": player_ev,
                        "mortal_ev": max(
                            (a["q_value"] for a in all_actions), default=None
                        ),
                        "all_actions": all_actions,
                    }
                )

    finally:
        proc.stdin.close()
        proc.wait()

    return results


def _extract_actions(q_values: list[float], mask_bits: int) -> list[dict]:
    """
    Q-valuesとmask_bitsから有効アクションの一覧を生成する

    Args:
        q_values(list[float]): Q-valueのリスト
        mask_bits(int): マスクビット

    Returns:
        list[dict]: 有効アクションの一覧
    """

    if not q_values:
        return []

    # mask_bitsを46ビットのリストに変換
    mask = [(mask_bits >> i) & 1 == 1 for i in range(46)]

    # q_valuesの中から、マスクビットのチェックで有効となったものだけを取り出す
    actions = []
    q_idx = 0
    for name, is_valid in zip(_ACTION_NAMES_4P, mask):
        if is_valid:
            if q_idx < len(q_values):
                actions.append({"name": name, "q_value": q_values[q_idx]})
                q_idx += 1

    # actionsの中から、キー: q_valueの降順でソートする
    return sorted(actions, key=lambda x: x["q_value"], reverse=True)


def _find_player_action(
    all_lines: list[str], current_idx: int, player_seat: int
) -> str | None:
    """
    ツモイベント(tsumo)に対応する実際の打牌(dahai)をmjaiストリームから取得する。
    tsumoの直後に来る「actor == player_seat」のdahaiが該当。

    Args:
        all_lines(list[str]): インプットデータの全行
        current_idx(int): インプットデータのうち、現在処理を行っている行のインデックス
        player_seat(int): 解析対象の席

    Returns:
        list[dict]: 有効アクションの一覧
    """

    for line in all_lines[current_idx + 1 :]:
        event = json.loads(line)

        # player_seatのプレイヤーが実際に打牌したイベントかどうかをチェック
        # 別プレイヤーの打牌やリーチは飛ばす（リーチ宣言牌はplayerのものなので返す）
        if event["type"] == "dahai" and event.get("actor") == player_seat:
            return event["pai"]
        if event["type"] in ("end_kyoku", "end_game"):
            break
    return None
