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
    status: str = "result"


@dataclass
class ParsedRacePage:
    """1レースページのパース結果"""

    race_info: ParsedRaceInfo
    entries: list[ParsedEntryResult] = field(default_factory=list)


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
    date_str = f"{year}-01-01"  # デフォルト

    # 日付パース: ページ内の特定クラス、またはヘッダー付近のテキストから探す
    # 例: "2024年12月22日"
    date_found = False
    
    # 優先セレクタ
    date_tags = soup.select(".smalltxt, .Race_Date, p.smalltxt, .race_head_inner")
    for tag in date_tags:
        text = tag.get_text(strip=True)
        date_match = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", text)
        if date_match:
            y, m, d = date_match.groups()
            date_str = f"{y}-{int(m):02d}-{int(d):02d}"
            date_found = True
            break
            
    # タイトル周辺のテキストからも探す（バックアップ）
    if not date_found:
        header_text = soup.select_one("div.racedata")
        if header_text:
            date_match = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", header_text.get_text())
            if date_match:
                y, m, d = date_match.groups()
                date_str = f"{y}-{int(m):02d}-{int(d):02d}"

    # 会場 — race_id から取得
    venue_code = race_id[4:6]
    from app.scraper import VENUE_CODE_MAP

    venue = VENUE_CODE_MAP.get(venue_code, "不明")

    # コース情報（例: "芝右2000m"、"ダ左1200m"、"芝2500m"）
    course_type = "芝"
    distance = 0
    direction = ""
    weather = ""
    track_condition = ""
    race_class = ""

    # レース詳細情報のパース
    # diary_snap_cut span: 通常の結果ページ
    # .RaceData01 span: 一部のページ
    race_data_spans = soup.select("diary_snap_cut span, .RaceData01 span, span, .racedata")
    
    # 全テキストを結合して検索するアプローチも試す（構造が崩れている場合用）
    full_header_text = ""
    if race_data_spans:
        full_header_text = " ".join([s.get_text(strip=True) for s in race_data_spans])

    # 距離・コース種別
    # "芝2500m", "ダート1800m", "芝右 外1600m" などに対応
    course_match = re.search(r"(芝|ダート|ダ)(?:[^0-9m]*?)(\d{3,5})m", full_header_text)
    if not course_match:
        # 個別のspanからも再トライ
        for span in race_data_spans:
            text = span.get_text(strip=True)
            m = re.search(r"(芝|ダート|ダ)(?:[^0-9m]*?)(\d{3,5})m", text)
            if m:
                course_match = m
                break
    
    if course_match:
        ct = course_match.group(1)
        course_type = "ダート" if ct in ("ダ", "ダート") else "芝"
        distance = int(course_match.group(2))
        
        # 方向 ("右", "左", "直線")
        if "右" in full_header_text:
            direction = "右"
        elif "左" in full_header_text:
            direction = "左"
        elif "直線" in full_header_text:
            direction = "直線"

    # 天候
    if "天候" in full_header_text:
        weather_match = re.search(r"天候\s*[:：]\s*(\S+)", full_header_text)
        if weather_match:
            weather = weather_match.group(1)
    
    # 馬場状態
    if "芝" in full_header_text or "ダート" in full_header_text:
        condition_match = re.search(r"(芝|ダート|ダ)\s*[:：]\s*(良|稍重|重|不良)", full_header_text)
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
        # 着順とステータス
        finish_pos_text = cells[0].get_text(strip=True)
        status = "result"
        finish_position = None
        
        if "取" in finish_pos_text:
            status = "scratched"
        elif "除" in finish_pos_text:
            status = "excluded"
        elif "中" in finish_pos_text:
            status = "dnf"
        else:
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
            status=status,
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
        # "牡3歳 鹿毛"
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

    # 過去成績
    history: list[ParsedHorseHistoryEntry] = []
    # db.netkeiba.com の馬ページは .db_h_race_results または table[summary="全成績"]
    # 複数のセレクタでテーブルを探す
    history_table = (
        soup.select_one("table.db_h_race_results") or 
        soup.find("table", class_="db_h_race_results") or
        soup.select_one("table[summary='全成績']")
    )
    
    # 見つからない場合は、最も列数（td）が多いテーブルを探す
    if not history_table:
        tables = soup.find_all("table")
        if tables:
            history_table = max(tables, key=lambda t: len(t.find_all("td")))

    if history_table:
        rows = history_table.find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 10: # 大幅に緩和
                continue
            
            try:
                # レースID (通常 4番目のセルにある a タグ)
                race_link = cells[4].select_one("a")
                if not race_link: continue
                rid_match = re.search(r"/race/(\d+)", race_link.get("href", ""))
                if not rid_match: continue
                race_id = rid_match.group(1)

                date_str = cells[0].get_text(strip=True).replace("/", "-")
                venue = cells[1].get_text(strip=True)
                race_name = cells[4].get_text(strip=True)
                
                # 枠番 (6) / 馬番 (7) / 人気 (9) / 着順 (10)
                bracket_number = _safe_int(cells[6].get_text(strip=True))
                horse_number = _safe_int(cells[7].get_text(strip=True)) or 0
                
                odds = _safe_float(cells[9].get_text(strip=True))
                pop = _safe_int(cells[8].get_text(strip=True)) # 人気とオッズが逆転している場合があるが、大体このあたり
                
                rank_text = cells[10].get_text(strip=True)
                status = "result"
                rank = None
                if "取" in rank_text:
                    status = "scratched"
                elif "除" in rank_text:
                    status = "excluded"
                elif "中" in rank_text:
                    status = "dnf"
                else:
                    rank = _safe_int(rank_text)
                jockey = cells[12].get_text(strip=True)
                weight = _safe_float(cells[13].get_text(strip=True))
                
                dist_text = cells[14].get_text(strip=True) # "芝2500"
                dist_match = re.search(r"(芝|ダ|障)(\d+)", dist_text)
                c_type = "芝"
                dist_val = 0
                if dist_match:
                    c_type = "ダート" if dist_match.group(1) == "ダ" else "芝"
                    dist_val = int(dist_match.group(2))
                
                track = cells[16].get_text(strip=True)
                f_time = cells[18].get_text(strip=True)
                margin = cells[19].get_text(strip=True)
                
                # 通過順は 21番目あたりにあることが多いが、可変なため探索
                passing = ""
                for idx in [21, 20, 22]:
                    if idx < len(cells):
                        val = cells[idx].get_text(strip=True)
                        if re.match(r"^\d+-\d+", val):
                            passing = val
                            break
                
                last3f = _safe_float(cells[23].get_text(strip=True))
                
                hw_text = cells[24].get_text(strip=True) # "504(+2)"
                hw_match = re.match(r"(\d+)\((.+)\)", hw_text)
                hw = None
                hw_diff = None
                if hw_match:
                    hw = int(hw_match.group(1))
                    hw_diff = int(hw_match.group(2))

                history.append(ParsedHorseHistoryEntry(
                    race_id=race_id,
                    date=date_str,
                    venue=venue,
                    race_name=race_name,
                    horse_number=horse_number,
                    bracket_number=bracket_number,
                    odds=odds,
                    popularity=pop,
                    finish_position=rank,
                    jockey=jockey,
                    weight_carried=weight,
                    distance=dist_val,
                    course_type=c_type,
                    track_condition=track,
                    finish_time=f_time,
                    margin=margin,
                    passing_order=passing,
                    last_3f=last3f,
                    horse_weight=hw,
                    horse_weight_diff=hw_diff,
                    status=status,
                ))
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
