"""
HTMLパーサー

netkeiba.com のHTMLからレースデータを抽出するパーサー群。
HTTP通信から分離されており、単体でテスト可能。
"""

import re
from dataclasses import dataclass, field

from bs4 import BeautifulSoup, Tag


@dataclass
class ParsedRaceInfo:
    """パース済みレース情報"""

    race_id: str
    name: str
    date: str  # "YYYY-MM-DD" 形式
    venue: str
    course_type: str  # "芝" or "ダート"
    distance: int  # メートル
    direction: str  # "右", "左", "直線"
    weather: str  # "晴", "曇", "雨" etc.
    track_condition: str  # "良", "稍重", "重", "不良"
    race_class: str  # "G1", "オープン" etc.
    num_entries: int


@dataclass
class ParsedEntryResult:
    """パース済み出走馬 + 結果データ"""

    horse_id: str
    horse_name: str
    bracket_number: int | None
    horse_number: int
    jockey: str
    weight_carried: float | None
    odds: float | None
    popularity: int | None
    finish_position: int | None  # None = 取消・除外
    finish_time: str | None
    margin: str | None
    passing_order: str | None  # "3-3-2-1"
    last_3f: float | None
    horse_weight: int | None
    horse_weight_diff: int | None
    sex_age: str | None  # "牡3" etc.
    trainer: str | None


@dataclass
class ParsedRacePage:
    """1レースページのパース結果"""

    race_info: ParsedRaceInfo
    entries: list[ParsedEntryResult] = field(default_factory=list)


def parse_race_result_page(html: str, race_id: str) -> ParsedRacePage:
    """
    レース結果ページ (db.netkeiba.com/race/XXXX/) をパースする。

    Args:
        html: ページのHTML文字列
        race_id: レースID

    Returns:
        ParsedRacePage: パース済みレースデータ
    """
    soup = BeautifulSoup(html, "html.parser")

    race_info = _parse_race_info(soup, race_id)
    entries = _parse_result_table(soup)
    race_info.num_entries = len(entries)

    return ParsedRacePage(race_info=race_info, entries=entries)


def _parse_race_info(soup: BeautifulSoup, race_id: str) -> ParsedRaceInfo:
    """レース情報をパースする"""
    # レース名
    name = ""
    race_name_tag = soup.select_one(".racedata fc .race_title, h1.racedata_title")
    if race_name_tag is None:
        # 別パターン: race_name クラス
        race_name_tag = soup.select_one(".racename, .RaceName")
    if race_name_tag:
        name = race_name_tag.get_text(strip=True)

    # レース日付 — race_id から推定
    # race_id format: YYYYVVKKDDRR (Y=年, V=会場, K=回, D=日, R=レース番号)
    year = race_id[:4]
    date_str = f"{year}-01-01"  # デフォルト。実際はページから取得

    # ページ内の日付を探す
    date_tag = soup.select_one(".smalltxt, .Race_Date, p.smalltxt")
    if date_tag:
        date_text = date_tag.get_text(strip=True)
        date_match = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", date_text)
        if date_match:
            y, m, d = date_match.groups()
            date_str = f"{y}-{int(m):02d}-{int(d):02d}"

    # 会場 — race_id から取得
    venue_code = race_id[4:6]
    from app.scraper import VENUE_CODE_MAP

    venue = VENUE_CODE_MAP.get(venue_code, "不明")

    # コース情報（例: "芝右2000m"、"ダ左1200m"）
    course_type = "芝"
    distance = 0
    direction = ""
    weather = ""
    track_condition = ""
    race_class = ""

    # レース詳細情報のパース
    race_data_spans = soup.select("diary_snap_cut span, .RaceData01 span, span")
    for span in race_data_spans:
        text = span.get_text(strip=True)
        # コース情報
        course_match = re.search(r"(芝|ダート|ダ)\s*(右|左|直線)?\s*(\d{3,5})m", text)
        if course_match:
            ct = course_match.group(1)
            course_type = "ダート" if ct in ("ダ", "ダート") else "芝"
            direction = course_match.group(2) or ""
            distance = int(course_match.group(3))

        # 天候
        weather_match = re.search(r"天候\s*[:：]\s*(\S+)", text)
        if weather_match:
            weather = weather_match.group(1)

        # 馬場状態
        condition_match = re.search(r"(芝|ダート|ダ)\s*[:：]\s*(良|稍重|重|不良)", text)
        if condition_match:
            track_condition = condition_match.group(2)

    # レースクラス（グレード）
    class_tag = soup.select_one(".racedata .grade, .Icon_GradeType, span.GradeIcon")
    if class_tag:
        race_class = class_tag.get_text(strip=True)
    else:
        # テキストからクラスを推定
        full_text = soup.get_text()
        for grade in ["G1", "G2", "G3", "GI", "GII", "GIII", "オープン", "リステッド"]:
            if grade in full_text:
                race_class = grade.replace("GI", "G1").replace("GII", "G2").replace("GIII", "G3")
                break

    return ParsedRaceInfo(
        race_id=race_id,
        name=name,
        date=date_str,
        venue=venue,
        course_type=course_type,
        distance=distance,
        direction=direction,
        weather=weather,
        track_condition=track_condition,
        race_class=race_class,
        num_entries=0,
    )


def _parse_result_table(soup: BeautifulSoup) -> list[ParsedEntryResult]:
    """結果テーブル (result_table) をパースする"""
    entries: list[ParsedEntryResult] = []

    # 結果テーブルの各行
    table = soup.select_one("table.race_table_01, table.RaceTable01")
    if table is None:
        return entries

    rows = table.select("tr")[1:]  # ヘッダー行をスキップ
    for row in rows:
        entry = _parse_result_row(row)
        if entry:
            entries.append(entry)

    return entries


def _parse_result_row(row: Tag) -> ParsedEntryResult | None:
    """結果テーブルの1行をパースする"""
    cells = row.select("td")
    if len(cells) < 10:
        return None

    try:
        # 着順
        finish_pos_text = cells[0].get_text(strip=True)
        finish_position = _safe_int(finish_pos_text)

        # 枠番
        bracket_number = _safe_int(cells[1].get_text(strip=True))

        # 馬番
        horse_number_val = _safe_int(cells[2].get_text(strip=True))
        if horse_number_val is None:
            return None

        # 馬名・馬ID
        horse_link = cells[3].select_one("a")
        horse_name = cells[3].get_text(strip=True)
        horse_id = ""
        if horse_link and horse_link.get("href"):
            href = str(horse_link["href"])
            # /horse/XXXXXXXXXXX/ から馬IDを抽出
            id_match = re.search(r"/horse/(\w+)", href)
            if id_match:
                horse_id = id_match.group(1)

        # 性齢
        sex_age = cells[4].get_text(strip=True) if len(cells) > 4 else None

        # 斤量
        weight_carried = _safe_float(cells[5].get_text(strip=True)) if len(cells) > 5 else None

        # 騎手
        jockey = cells[6].get_text(strip=True) if len(cells) > 6 else None

        # タイム
        finish_time = cells[7].get_text(strip=True) if len(cells) > 7 else None
        if finish_time == "":
            finish_time = None

        # 着差
        margin = cells[8].get_text(strip=True) if len(cells) > 8 else None
        if margin == "":
            margin = None

        # 通過順 (9列目あたり、ページにより位置が変わることがある)
        passing_order = None
        last_3f = None
        horse_weight_val = None
        horse_weight_diff_val = None
        odds = None
        popularity = None
        trainer = None

        # 残りのカラムを柔軟にパース
        for i in range(9, len(cells)):
            text = cells[i].get_text(strip=True)

            # 通過順パターン: "3-3-2-1"
            if re.match(r"^\d+-\d+(-\d+)*$", text):
                passing_order = text
                continue

            # 上がり3F: "33.8" のような小数
            if passing_order and last_3f is None:
                f_val = _safe_float(text)
                if f_val and 25.0 < f_val < 50.0:
                    last_3f = f_val
                    continue

            # 馬体重パターン: "468(-4)" or "468(+4)"
            weight_match = re.match(r"(\d{3,4})\(([+-]?\d+)\)", text)
            if weight_match:
                horse_weight_val = int(weight_match.group(1))
                horse_weight_diff_val = int(weight_match.group(2))
                continue

            # オッズ: 小数点1桁の数値
            if odds is None:
                odds_val = _safe_float(text)
                if odds_val and odds_val > 1.0:
                    odds = odds_val
                    continue

            # 人気: 1桁〜2桁の整数
            if popularity is None and text.isdigit() and 1 <= int(text) <= 30:
                popularity = int(text)
                continue

            # 調教師
            trainer_link = cells[i].select_one("a")
            if trainer_link and "/trainer/" in str(trainer_link.get("href", "")):
                trainer = text
                continue

        return ParsedEntryResult(
            horse_id=horse_id,
            horse_name=horse_name,
            bracket_number=bracket_number,
            horse_number=horse_number_val,
            jockey=jockey or "",
            weight_carried=weight_carried,
            odds=odds,
            popularity=popularity,
            finish_position=finish_position,
            finish_time=finish_time,
            margin=margin,
            passing_order=passing_order,
            last_3f=last_3f,
            horse_weight=horse_weight_val,
            horse_weight_diff=horse_weight_diff_val,
            sex_age=sex_age,
            trainer=trainer,
        )

    except (ValueError, IndexError):
        return None


def _safe_int(text: str) -> int | None:
    """文字列を安全にintに変換。変換不可なら None"""
    try:
        return int(text)
    except (ValueError, TypeError):
        return None


def _safe_float(text: str) -> float | None:
    """文字列を安全にfloatに変換。変換不可なら None"""
    try:
        return float(text)
    except (ValueError, TypeError):
        return None


def parse_race_list_page(html: str) -> list[str]:
    """
    レース一覧ページからレースIDのリストを取得する。

    db.netkeiba.com の開催日ページ等からレースへのリンクを抽出。

    Args:
        html: ページのHTML文字列

    Returns:
        レースIDのリスト
    """
    soup = BeautifulSoup(html, "html.parser")
    race_ids: list[str] = []

    # レースへのリンクを検索
    links = soup.select("a[href*='/race/']")
    for link in links:
        href = str(link.get("href", ""))
        # /race/202506010101/ のようなパターン
        match = re.search(r"/race/(\d{12})", href)
        if match:
            rid = match.group(1)
            if rid not in race_ids:
                race_ids.append(rid)

    return race_ids
