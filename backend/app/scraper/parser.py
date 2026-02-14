"""
netkeibaのHTMLをパースして構造化データに変換するモジュール
"""

import re
from dataclasses import dataclass, field

from bs4 import BeautifulSoup, Tag


@dataclass
class ParsedEntryResult:
    """レース結果の1エントリー分のパース結果 (service.pyとフィールド名を統一)"""
    finish_position: int | None
    bracket_number: int | None
    horse_number: int | None
    horse_id: str
    horse_name: str
    sex_age: str | None # service.py uses this string
    weight_carried: float
    jockey: str
    finish_time: str | None
    margin: str | None
    popularity: int | None
    odds: float | None
    trainer: str
    horse_weight: float | None
    horse_weight_diff: int | None
    status: str
    
    # Optional / Compatibility fields
    passing_order: str | None = None
    last_3f: float | None = None
    
    # Additional fields internal to parser if needed, but keeping it clean for service.py
    # sex: str 
    # age: int
    # These were used internally but service expects sex_age string, so we construct it.


@dataclass
class ParsedRaceInfo:
    """レース情報のパース結果 (service.pyが期待する構造)"""
    race_id: str
    name: str 
    date: str | None
    venue: str | None
    course_type: str | None
    distance: int | None
    direction: str | None
    weather: str | None
    track_condition: str | None
    race_class: str | None
    num_entries: int = 0


@dataclass
class ParsedRaceResultPage:
    """レース結果ページのパース結果"""
    race_info: ParsedRaceInfo
    entries: list[ParsedEntryResult] = field(default_factory=list)


# Alias for compatibility with service.py
ParsedRacePage = ParsedRaceResultPage


def parse_race_result_page(html: str, race_id: str) -> ParsedRaceResultPage:
    """
    netkeibaのレース結果ページHTMLをパースする
    """
    soup = BeautifulSoup(html, "html.parser")

    # --- 基本情報の抽出 ---
    race_name_elem = soup.select_one(".RaceName")
    race_name = race_name_elem.get_text(strip=True) if race_name_elem else "Unknown Race"

    # レース詳細
    race_date = None
    venue = "Tokyo" # 仮
    course_type = "Turf" # 仮
    distance = 2000
    direction = "Right"
    weather = "Fine"
    track_condition = "Good"
    race_class = "Open"
    
    # TODO: Extract real metadata if needed

    entries = _parse_result_table(soup)
    num_entries = len(entries)

    race_info = ParsedRaceInfo(
        race_id=race_id,
        name=race_name,
        date=race_date,
        venue=venue,
        course_type=course_type,
        distance=distance,
        direction=direction,
        weather=weather,
        track_condition=track_condition,
        race_class=race_class,
        num_entries=num_entries
    )

    return ParsedRaceResultPage(
        race_info=race_info,
        entries=entries
    )


def _parse_race_info(soup: BeautifulSoup, race_id: str):
    pass


def _parse_result_table(soup: BeautifulSoup) -> list[ParsedEntryResult]:
    """結果テーブル (result_table) をパースする"""
    entries: list[ParsedEntryResult] = []

    # 結果テーブルの各行
    table = soup.select_one("table.race_table_01, table.RaceTable01")
    if table is None:
        return entries

    rows = table.select("tr")
    
    data_rows = rows[1:]  # ヘッダー行をスキップ
    for row in data_rows:
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
        # 着順とステータス
        finish_pos_text = cells[0].get_text(strip=True)
        status = "result"
        finish_position: int | None = None
        
        if finish_pos_text.isdigit():
            finish_position = int(finish_pos_text)
        else:
            if "取" in finish_pos_text:
                status = "scratched"
            elif "除" in finish_pos_text:
                status = "excluded"
            elif "中" in finish_pos_text:
                status = "dnf"
            else:
                pass

        # 枠番
        bracket_number = _safe_int(cells[1].get_text(strip=True))

        # 馬番
        horse_number_val = None
        raw_horse_num = cells[2].get_text(strip=True)
        # 数字のみ抽出して変換
        num_match = re.search(r"\d+", raw_horse_num)
        if num_match:
            horse_number_val = int(num_match.group(0))
        
        if horse_number_val is None:
            return None

        # 馬名・馬ID
        horse_name_elem = cells[3].select_one("a")
        horse_name = ""
        horse_id = ""
        if horse_name_elem:
            horse_name = horse_name_elem.get_text(strip=True)
            href = horse_name_elem.get("href")
            if isinstance(href, str):
                match = re.search(r"/horse/(\d+)", href)
                if match:
                    horse_id = match.group(1)
        
        # 性齢
        sex_age = cells[4].get_text(strip=True) # "牡3"
        
        # 斤量
        weight_carried = _safe_float(cells[5].get_text(strip=True)) or 55.0

        # 騎手
        jockey_elem = cells[6].select_one("a")
        jockey = ""
        # jockey_id unused in current ParsedEntryResult but extracted if needed
        if jockey_elem:
            jockey = jockey_elem.get_text(strip=True)

        # タイム
        finish_time = cells[7].get_text(strip=True)
        if not finish_time:
            finish_time = None

        # 着差
        margin = cells[8].get_text(strip=True)
        
        # 人気
        popularity = _safe_int(cells[9].get_text(strip=True))
        
        # オッズ
        odds = _safe_float(cells[10].get_text(strip=True))
        
        passing_order = None 
        last_3f = None

        # 調教師
        trainer = ""
        if len(cells) > 13:
             trainer_elem = cells[13].select_one("a")
             if trainer_elem:
                 trainer = trainer_elem.get_text(strip=True)

        # 馬体重
        horse_weight = None
        horse_weight_diff = None
        
        if len(cells) > 11:
             hw_text = cells[11].get_text(strip=True)
             if hw_text and hw_text != "計不":
                 match = re.search(r"(\d+)\(([-+]?\d+)\)", hw_text)
                 if match:
                     horse_weight = float(match.group(1))
                     horse_weight_diff = int(match.group(2))
                 else:
                     try:
                         horse_weight = float(hw_text)
                     except:
                         pass

        return ParsedEntryResult(
            finish_position=finish_position,
            bracket_number=bracket_number,
            horse_number=horse_number_val,
            horse_id=horse_id,
            horse_name=horse_name,
            sex_age=sex_age,
            weight_carried=weight_carried,
            jockey=jockey,
            finish_time=finish_time,
            margin=margin,
            popularity=popularity,
            odds=odds,
            trainer=trainer,
            horse_weight=horse_weight,
            horse_weight_diff=horse_weight_diff,
            status=status,
            passing_order=passing_order,
            last_3f=last_3f
        )

    except (ValueError, IndexError):
        return None


def _safe_int(text: str) -> int | None:
    try:
        return int(text)
    except (ValueError, TypeError):
        return None


def _safe_float(text: str) -> float | None:
    try:
        return float(text)
    except (ValueError, TypeError):
        return None


def parse_race_list_page(html: str) -> list[str]:
    """
    レース一覧ページからレースIDのリストを取得する。
    """
    soup = BeautifulSoup(html, "html.parser")
    race_ids: list[str] = []

    links = soup.select("a[href*='/race/']")
    for link in links:
        href = str(link.get("href", ""))
        match = re.search(r"/race/(\d{12})", href)
        if match:
            rid = match.group(1)
            if rid not in race_ids:
                race_ids.append(rid)

    return race_ids


@dataclass
class ParsedHorseHistoryEntry:
    """馬のプロフィールページにある過去成績の1行"""
    race_id: str
    date: str
    venue: str
    race_name: str
    horse_number: int
    bracket_number: int | None
    odds: float | None
    popularity: int | None
    finish_position: int | None
    jockey: str
    weight_carried: float | None
    distance: int
    course_type: str
    track_condition: str
    finish_time: str | None
    margin: str | None
    passing_order: str | None
    last_3f: float | None
    horse_weight: int | None
    horse_weight_diff: int | None
    status: str = "result"


@dataclass
class ParsedHorsePage:
    """馬のプロフィールページのパース結果"""
    horse_id: str
    name: str
    sex: str | None
    age: int | None
    trainer: str | None
    sire: str | None
    dam: str | None
    history: list[ParsedHorseHistoryEntry] = field(default_factory=list)


def parse_horse_page(html: str, horse_id: str) -> ParsedHorsePage:
    """
    馬のプロフィールページ (db.netkeiba.com/horse/XXXX/) をパースする。
    """
    soup = BeautifulSoup(html, "html.parser")

    # 基本情報
    name = ""
    name_tag = soup.select_one(".horse_title h1")
    if name_tag:
        name = name_tag.get_text(strip=True)

    # プロフィール詳細
    txt_txt = soup.select_one(".db_prof_area_02 .txt_01")
    sex = None
    age = None
    if txt_txt:
        text = txt_txt.get_text(strip=True)
        m = re.match(r"(牡|牝|セ)(\d+)歳", text)
        if m:
            sex = m.group(1)
            age = int(m.group(2))

    trainer = ""
    trainer_link = soup.select_one("a[href*='/trainer/']")
    if trainer_link:
        trainer = trainer_link.get_text(strip=True).replace("(", "").replace(")", "")

    # 血統
    sire = ""
    dam = ""
    blood_table = soup.select_one(".blood_table")
    if blood_table:
        blood_links = blood_table.select("a")
        if len(blood_links) >= 2:
            sire = blood_links[0].get_text(strip=True)
            dam = blood_links[1].get_text(strip=True)

    history: list[ParsedHorseHistoryEntry] = []
    
    return ParsedHorsePage(
        horse_id=horse_id,
        name=name,
        sex=sex,
        age=age,
        trainer=trainer,
        sire=sire,
        dam=dam,
        history=history
    )
