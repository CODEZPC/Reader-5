import requests
import fake_useragent
from bs4 import BeautifulSoup

def get_soup(url):
    # 初始化 requests Session 与默认 headers，减少 403 风险
    session = requests.Session()
    default_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    try:
        ua = fake_useragent.UserAgent()
        ua_string = ua.random
    except Exception:
        ua_string = default_ua
    # 一些常见浏览器头部，session 默认使用
    session.headers.update(
        {
            "User-Agent": ua_string,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.8",
            "Referer": "https://www.qidiy.com/",
            "Connection": "keep-alive",
            "Accept-Encoding": "gzip, deflate",
            "Upgrade-Insecure-Requests": "1",
        }
    )
    # 当被目标站点强力拦截时，允许回退到 cloudscraper（如果已安装）
    use_cloudscraper_if_needed = True

    # 使用 session 和稳定的 headers，遇到 403 时尝试 cloudscraper 回退
    headers = {
        "User-Agent": ua_string,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.8",
        "Referer": "https://www.qidiy.com/",
    }
    # 先尝试用 session 获取（可以保留 cookie）
    try:
        # 尝试访问根域以获取可能的 cookie（如果 session 为空）
        try:
            if not session.cookies:
                session.get("https://www.qidiy.com/", timeout=8)
        except Exception:
            pass
        resp = session.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        status = None
        try:
            status = e.response.status_code
        except Exception:
            try:
                status = resp.status_code
            except Exception:
                status = None
        # 若为 403，且允许 cloudscraper 回退，则尝试使用 cloudscraper
        if status == 403 and use_cloudscraper_if_needed:
            try:
                import cloudscraper

                scraper = cloudscraper.create_scraper()
                resp = scraper.get(url, headers=headers, timeout=20)
                resp.raise_for_status()
            except Exception:
                # 若 cloudscraper 不可用或仍失败，抛出原始错误
                raise
        else:
            raise

    # 确保使用合适的编码解析，优先使用 requests 的检测编码，避免出现乱码
    try:
        detected = getattr(resp, "apparent_encoding", None)
        if detected:
            resp.encoding = detected
        else:
            resp.encoding = resp.encoding or "utf-8"
    except Exception:
        resp.encoding = resp.encoding or "utf-8"

    return BeautifulSoup(resp.text, "html.parser")