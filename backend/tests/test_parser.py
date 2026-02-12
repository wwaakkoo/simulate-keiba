"""
HTMLパーサーのテスト

モックHTMLを使用してパースロジックを単体テストする。
netkeiba.comへの実際のアクセスは不要。
"""

from app.scraper.parser import (
    ParsedEntryResult,
    parse_race_list_page,
    parse_race_result_page,
)

# === モックHTML ===

MOCK_RACE_RESULT_HTML = """
<html>
<head><title>テスト記念(G1) レース結果</title></head>
<body>
<p class="smalltxt">2025年6月1日 1回東京1日目</p>
<h1 class="racedata_title">テスト記念</h1>
<span>芝右2000m</span>
<span>天候：晴</span>
<span>芝：良</span>
<span class="GradeIcon">G1</span>

<table class="race_table_01">
<tr><th>着順</th><th>枠番</th><th>馬番</th><th>馬名</th><th>性齢</th><th>斤量</th><th>騎手</th><th>タイム</th><th>着差</th><th>通過</th><th>上り</th><th>馬体重</th><th>単勝</th><th>人気</th><th>調教師</th></tr>
<tr>
  <td>1</td>
  <td>3</td>
  <td>5</td>
  <td><a href="/horse/2021104567/">テストディープ</a></td>
  <td>牡4</td>
  <td>57.0</td>
  <td>テスト騎手A</td>
  <td>1:59.5</td>
  <td></td>
  <td>3-3-2-1</td>
  <td>33.8</td>
  <td>468(-4)</td>
  <td>3.5</td>
  <td>1</td>
  <td><a href="/trainer/00001/">テスト調教師A</a></td>
</tr>
<tr>
  <td>2</td>
  <td>5</td>
  <td>9</td>
  <td><a href="/horse/2021104568/">テストアーモンド</a></td>
  <td>牝4</td>
  <td>55.0</td>
  <td>テスト騎手B</td>
  <td>1:59.8</td>
  <td>クビ</td>
  <td>5-5-4-2</td>
  <td>33.5</td>
  <td>456(+2)</td>
  <td>5.2</td>
  <td>2</td>
  <td><a href="/trainer/00002/">テスト調教師B</a></td>
</tr>
<tr>
  <td>3</td>
  <td>7</td>
  <td>13</td>
  <td><a href="/horse/2021104569/">テストコントレイル</a></td>
  <td>牡5</td>
  <td>58.0</td>
  <td>テスト騎手C</td>
  <td>2:00.1</td>
  <td>1 1/2</td>
  <td>1-1-1-3</td>
  <td>34.6</td>
  <td>480(0)</td>
  <td>12.4</td>
  <td>5</td>
  <td><a href="/trainer/00003/">テスト調教師C</a></td>
</tr>
</table>
</body>
</html>
"""

MOCK_RACE_LIST_HTML = """
<html>
<body>
<div class="race_list">
  <a href="/race/202506010101/">1R</a>
  <a href="/race/202506010102/">2R</a>
  <a href="/race/202506010103/">3R</a>
  <a href="/race/202506010104/">4R</a>
  <a href="/other/page/">その他リンク</a>
</div>
</body>
</html>
"""


# === テスト ===


class TestParseRaceResultPage:
    """レース結果ページのパーステスト"""

    def test_parse_race_info(self) -> None:
        """レース基本情報を正しくパースできること"""
        result = parse_race_result_page(MOCK_RACE_RESULT_HTML, "202505010101")
        info = result.race_info

        assert info.race_id == "202505010101"
        assert info.name == "テスト記念"
        assert info.venue == "東京"
        assert info.course_type == "芝"
        assert info.distance == 2000
        assert info.weather == "晴"
        assert info.track_condition == "良"

    def test_parse_entries_count(self) -> None:
        """出走馬の数が正しいこと"""
        result = parse_race_result_page(MOCK_RACE_RESULT_HTML, "202505010101")

        assert len(result.entries) == 3
        assert result.race_info.num_entries == 3

    def test_parse_first_place(self) -> None:
        """1着馬のデータが正しくパースされること"""
        result = parse_race_result_page(MOCK_RACE_RESULT_HTML, "202505010101")
        first: ParsedEntryResult = result.entries[0]

        assert first.finish_position == 1
        assert first.bracket_number == 3
        assert first.horse_number == 5
        assert first.horse_name == "テストディープ"
        assert first.horse_id == "2021104567"
        assert first.sex_age == "牡4"
        assert first.weight_carried == 57.0
        assert first.jockey == "テスト騎手A"
        assert first.finish_time == "1:59.5"
        assert first.passing_order == "3-3-2-1"
        assert first.last_3f == 33.8
        assert first.horse_weight == 468
        assert first.horse_weight_diff == -4
        assert first.odds == 3.5
        assert first.popularity == 1

    def test_parse_second_place(self) -> None:
        """2着馬の着差がパースされること"""
        result = parse_race_result_page(MOCK_RACE_RESULT_HTML, "202505010101")
        second = result.entries[1]

        assert second.finish_position == 2
        assert second.horse_name == "テストアーモンド"
        assert second.margin == "クビ"
        assert second.passing_order == "5-5-4-2"
        assert second.last_3f == 33.5

    def test_parse_third_place(self) -> None:
        """3着馬（逃げ馬）のデータが正しいこと"""
        result = parse_race_result_page(MOCK_RACE_RESULT_HTML, "202505010101")
        third = result.entries[2]

        assert third.finish_position == 3
        assert third.horse_name == "テストコントレイル"
        assert third.passing_order == "1-1-1-3"  # 逃げて3着
        assert third.last_3f == 34.6  # 上がりが遅い（脚がなくなった）
        assert third.horse_weight == 480
        assert third.horse_weight_diff == 0

    def test_empty_html(self) -> None:
        """空っぽのHTMLでもクラッシュしないこと"""
        result = parse_race_result_page("<html><body></body></html>", "000000000000")

        assert result.race_info.race_id == "000000000000"
        assert len(result.entries) == 0


class TestParseRaceListPage:
    """レース一覧ページのパーステスト"""

    def test_parse_race_ids(self) -> None:
        """レースIDを正しく抽出すること"""
        race_ids = parse_race_list_page(MOCK_RACE_LIST_HTML)

        assert len(race_ids) == 4
        assert "202506010101" in race_ids
        assert "202506010104" in race_ids

    def test_no_duplicates(self) -> None:
        """重複するレースIDが排除されること"""
        html = """
        <html><body>
        <a href="/race/202506010101/">1R</a>
        <a href="/race/202506010101/">1R duplicate</a>
        </body></html>
        """
        race_ids = parse_race_list_page(html)
        assert len(race_ids) == 1

    def test_empty_html(self) -> None:
        """レースリンクがないHTMLでは空リストが返ること"""
        race_ids = parse_race_list_page("<html><body>no races</body></html>")
        assert race_ids == []
