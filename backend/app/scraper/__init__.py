"""
スクレイパー共通設定
"""

# netkeiba.com のベースURL
NETKEIBA_BASE_URL = "https://db.netkeiba.com"
NETKEIBA_RACE_URL = "https://race.netkeiba.com"

# リクエスト設定
REQUEST_TIMEOUT = 30  # 秒
REQUEST_DELAY_MIN = 1.0  # リクエスト間の最小待機秒数
REQUEST_DELAY_MAX = 2.5  # リクエスト間の最大待機秒数
MAX_RETRIES = 3  # リトライ回数

# User-Agent（一般的なブラウザを模倣）
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# 会場コードのマッピング
VENUE_CODE_MAP: dict[str, str] = {
    "01": "札幌",
    "02": "函館",
    "03": "福島",
    "04": "新潟",
    "05": "東京",
    "06": "中山",
    "07": "中京",
    "08": "京都",
    "09": "阪神",
    "10": "小倉",
}
