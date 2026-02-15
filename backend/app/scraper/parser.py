"""
netkeibaのHTMLをパースして構造化データに変換するモジュール
"""

import re
from dataclasses import dataclass, field

from bs4 import BeautifulSoup, Tag

from app.scraper import VENUE_CODE_MAP


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
    if not race_name_elem:
        race_name_elem = soup.select_one("dl.racedata h1")
    if not race_name_elem:
        race_name_elem = soup.select_one(".racedata_title")
    
    race_name = race_name_elem.get_text(strip=True) if race_name_elem else "Unknown Race"

    # レース詳細の抽出
    race_data01 = soup.select_one(".RaceData01")
    race_data02 = soup.select_one(".RaceData02")
    
    # Older pages structure (e.g. 2018)
    # <div class="data_intro">
    #   <dl class="racedata"> ... <h1>...</h1> ... </dl>
    #   <p class="smalltxt">...</p>
    # </div>
    data_intro = soup.select_one(".data_intro")
    
    # デフォルト値 (Japanese)
    race_date = None
    venue = "東京" 
    course_type = "芝"
    distance = 2000
    direction = "左"
    weather = "晴"
    track_condition = "良"
    race_class = "オープン"
    
    # 会場はrace_idから推定可能
    if len(race_id) >= 6:
        venue_code = race_id[4:6]
        venue = VENUE_CODE_MAP.get(venue_code, "Unknown")

    # 日付・クラス解析
    # Modern: .smalltxt inside .RaceList_Item or similar (not always robust)
    # Parsing logic tries .smalltxt generally
    smalltxt = soup.select_one(".smalltxt")
    
    # Loop through text candidates for date/class
    date_class_text = ""
    if smalltxt:
        date_class_text = smalltxt.get_text(strip=True)
    elif data_intro:
        # data_intro often contains the text directly or in a <p>
        date_class_text = data_intro.get_text(strip=True)

    if date_class_text:
        text = date_class_text
        date_match = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", text)
        if date_match:
            y, m, d = date_match.groups()
            race_date = f"{y}-{m.zfill(2)}-{d.zfill(2)}"
        
        # クラス推定
        if "G1" in text or "GI" in text:
            race_class = "G1"
        elif "G2" in text or "GII" in text:
            race_class = "G2"
        elif "G3" in text or "GIII" in text:
            race_class = "G3"
        elif "オープン" in text:
            race_class = "オープン"
        elif "3勝" in text or "1600万" in text:
            race_class = "3勝クラス"
        elif "2勝" in text or "1000万" in text:
            race_class = "2勝クラス"
        elif "1勝" in text or "500万" in text:
            race_class = "1勝クラス"
        elif "未勝利" in text:
            race_class = "未勝利"
        elif "新馬" in text:
            race_class = "新馬"

    # 詳細情報 (距離, 天候, 馬場) 解析
    # Modern: .RaceData01
    # Older: .data_intro text (often mixed with date)
    detail_text = ""
    if race_data01:
        detail_text += race_data01.get_text(strip=True)
    if data_intro:
        detail_text += " " + data_intro.get_text(strip=True)
        
    if detail_text:
        text = detail_text
        
        # 距離・コース
        dist_match = re.search(r"(芝|ダ|障)(\d+)", text)
        if dist_match:
            ctype_jp = dist_match.group(1)
            distance = int(dist_match.group(2))
            if ctype_jp == "ダ":
                course_type = "ダート"
            elif ctype_jp == "障":
                course_type = "障害"
            else:
                course_type = "芝"
        
        # 方向
        if "右" in text:
            direction = "右"
        elif "左" in text:
            direction = "左"
        elif "直" in text:
            direction = "直線"
            
        # 天候
        if "天候:晴" in text or "天候 : 晴" in text:
            weather = "晴"
        elif "天候:曇" in text or "天候 : 曇" in text:
            weather = "曇"
        elif "天候:雨" in text or "天候 : 雨" in text:
            weather = "雨"
        elif "天候:小雨" in text or "天候 : 小雨" in text:
            weather = "小雨"
        elif "天候:雪" in text or "天候 : 雪" in text:
            weather = "雪"
            
        # 馬場状態
        if "良" in text:
            track_condition = "良"
        elif "稍重" in text: 
            track_condition = "稍重"
        elif "重" in text:
            track_condition = "重"
        elif "不良" in text:
            track_condition = "不良"

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
    
    # Header parsing
    header_row = rows[0]
    headers = [th.get_text(strip=True) for th in header_row.select("th, td")]
    
    col_map = {}
    for i, h in enumerate(headers):
        if "着順" in h: col_map["finish_position"] = i
        elif "枠番" in h: col_map["bracket_number"] = i
        elif "馬番" in h: col_map["horse_number"] = i
        elif "馬名" in h: col_map["horse_name"] = i
        elif "性齢" in h: col_map["sex_age"] = i
        elif "斤量" in h: col_map["weight_carried"] = i
        elif "騎手" in h: col_map["jockey"] = i
        elif "タイム" in h: col_map["finish_time"] = i
        elif "着差" in h: col_map["margin"] = i
        elif "人気" in h: col_map["popularity"] = i
        elif "オッズ" in h or "単勝" in h: col_map["odds"] = i
        elif "後3F" in h or "上り" in h: col_map["last_3f"] = i
        elif "通過" in h: col_map["passing_order"] = i
        elif "厩舎" in h or "調教師" in h: col_map["trainer"] = i
        elif "馬体重" in h: col_map["horse_weight"] = i
        
    data_rows = rows[1:]
    for row in data_rows:
        entry = _parse_result_row(row, col_map)
        if entry:
            entries.append(entry)

    return entries


def _parse_result_row(row: Tag, col_map: dict[str, int]) -> ParsedEntryResult | None:
    """結果テーブルの1行をパースする"""
    cells = row.select("td")
    if not cells:
        return None

    try:
        def get_cell(key: str, default_idx: int) -> Tag | None:
            idx = col_map.get(key, default_idx)
            if 0 <= idx < len(cells):
                return cells[idx]
            return None
            
        def get_text(key: str, default_idx: int) -> str:
            cell = get_cell(key, default_idx)
            return cell.get_text(strip=True) if cell else ""

        # 着順とステータス
        finish_pos_text = get_text("finish_position", 0)
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
        bracket_number = _safe_int(get_text("bracket_number", 1))

        # 馬番
        horse_number_val = None
        raw_horse_num = get_text("horse_number", 2)
        num_match = re.search(r"\d+", raw_horse_num)
        if num_match:
            horse_number_val = int(num_match.group(0))
        
        if horse_number_val is None:
            return None

        # 馬名・馬ID
        horse_cell = get_cell("horse_name", 3)
        horse_name = ""
        horse_id = ""
        if horse_cell:
            horse_name_elem = horse_cell.select_one("a")
            if horse_name_elem:
                horse_name = horse_name_elem.get_text(strip=True)
                href = horse_name_elem.get("href")
                if isinstance(href, str):
                    match = re.search(r"/horse/(\d+)", href)
                    if match:
                        horse_id = match.group(1)
            else:
                horse_name = horse_cell.get_text(strip=True)
        
        # 性齢
        sex_age = get_text("sex_age", 4)
        
        # 斤量
        weight_carried = _safe_float(get_text("weight_carried", 5)) or 55.0

        # 騎手
        jockey_cell = get_cell("jockey", 6)
        jockey = ""
        if jockey_cell:
            jockey_elem = jockey_cell.select_one("a")
            if jockey_elem:
                jockey = jockey_elem.get_text(strip=True)
            else:
                jockey = jockey_cell.get_text(strip=True)

        # タイム
        finish_time = get_text("finish_time", 7)
        if not finish_time:
            finish_time = None

        # 着差
        margin = get_text("margin", 8)
        
        # 人気
        popularity = _safe_int(get_text("popularity", 9))
        
        # オッズ
        odds = _safe_float(get_text("odds", 10))
        
        # Last 3F (New)
        last_3f_text = get_text("last_3f", 11) # Default to 11 if not mapped
        last_3f = _safe_float(last_3f_text) if last_3f_text else None

        # Passing order
        passing_order = get_text("passing_order", 12) or None
        if passing_order == "": passing_order = None

        # 調教師
        trainer_cell = get_cell("trainer", 13)
        trainer = ""
        if trainer_cell:
            trainer_elem = trainer_cell.select_one("a")
            if trainer_elem:
                trainer = trainer_elem.get_text(strip=True)
            else:
                trainer = trainer_cell.get_text(strip=True)

        # 馬体重
        # Default index depends on whether passing_order/last_3f exist
        # But we use checks.
        # If headers are present, col_map["horse_weight"] will be correct.
        # If not, we try 14 (standard) or scan
        hw_text = get_text("horse_weight", 14)
        horse_weight = None
        horse_weight_diff = None
        
        if hw_text and hw_text != "計不":
             match = re.search(r"(\d+)\(([-+]?\d+)\)", hw_text)
             if match:
                 horse_weight = float(match.group(1))
                 horse_weight_diff = int(match.group(2))
             else:
                 # Fallback for simple number (though rare for weight)
                 # Should differentiate from last_3f (e.g. > 300)
                 try:
                     val = float(hw_text)
                     if val > 100: # Weight is usually 400-500
                        horse_weight = val
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
    history_table = soup.select_one("table.db_h_race_results")
    if history_table:
        rows = history_table.select("tr")[1:] # Skip header
        for row in rows:
            cells = row.select("td")
            if len(cells) < 20: continue
            
            try:
                # 0:日付, 1:開催, 2:天気, 3:R, 4:レース名, 5:映像, 6:頭数, 7:枠番, 8:馬番, 9:オッズ, 10:人気, 11:着順 ...
                race_link = cells[4].select_one("a")
                if not race_link: continue
                race_id_match = re.search(r"/race/(\d+)", race_link.get("href", ""))
                if not race_id_match: continue
                
                # Date: 2024/05/19 -> 2024-05-19
                raw_date = cells[0].get_text(strip=True)
                date_str = raw_date.replace("/", "-")
                
                # Distance/Course: 芝2400
                dist_course = cells[14].get_text(strip=True)
                dc_match = re.match(r"(芝|ダ|障)(\d+)", dist_course)
                course_type = "芝"
                distance = 1600
                if dc_match:
                    ctype_jp = dc_match.group(1)
                    distance = int(dc_match.group(2))
                    if ctype_jp == "ダ": course_type = "ダート"
                    elif ctype_jp == "障": course_type = "障害"

                # Status & Position
                pos_text = cells[11].get_text(strip=True)
                status = "result"
                finish_position = None
                if pos_text.isdigit():
                    finish_position = int(pos_text)
                elif "取" in pos_text: status = "scratched"
                elif "除" in pos_text: status = "excluded"
                elif "中" in pos_text: status = "dnf"
                
                # Weight
                weight_text = cells[23].get_text(strip=True)
                h_weight = None
                h_weight_diff = None
                w_match = re.search(r"(\d+)\(([-+]?\d+)\)", weight_text)
                if w_match:
                    h_weight = int(w_match.group(1))
                    h_weight_diff = int(w_match.group(2))

                entry = ParsedHorseHistoryEntry(
                    race_id=race_id_match.group(1),
                    date=date_str,
                    venue=cells[1].get_text(strip=True),
                    race_name=cells[4].get_text(strip=True),
                    horse_number=_safe_int(cells[8].get_text(strip=True)) or 0,
                    bracket_number=_safe_int(cells[7].get_text(strip=True)),
                    odds=_safe_float(cells[9].get_text(strip=True)),
                    popularity=_safe_int(cells[10].get_text(strip=True)),
                    finish_position=finish_position,
                    jockey=cells[12].get_text(strip=True),
                    weight_carried=_safe_float(cells[13].get_text(strip=True)),
                    distance=distance,
                    course_type=course_type,
                    track_condition=cells[15].get_text(strip=True),
                    finish_time=cells[17].get_text(strip=True) or None,
                    margin=cells[18].get_text(strip=True) or None,
                    passing_order=cells[20].get_text(strip=True) or None,
                    last_3f=_safe_float(cells[22].get_text(strip=True)),
                    horse_weight=h_weight,
                    horse_weight_diff=h_weight_diff,
                    status=status
                )
                history.append(entry)
            except Exception:
                continue

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
