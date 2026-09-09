#!/usr/bin/env python3
"""네이버 블로그 글을 홈페이지로 가져온다.

  python3 scripts/sync_naver.py            # 최근 글만 (RSS, 매일 자동 실행용)
  python3 scripts/sync_naver.py --all      # 전체 글 (최초 1회 이관용)
  python3 scripts/sync_naver.py --all --limit 50   # 앞에서 50편만 시험

가져온 글은 data/posts.json 에, 사진은 assets/img/blog/ 에 저장된다.
파이썬 표준 라이브러리만 쓴다.
"""
import argparse
import html
import json
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from xml.etree import ElementTree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMGDIR = os.path.join(ROOT, "assets", "img", "blog")
POSTS = os.path.join(ROOT, "data", "posts.json")
SITE = json.load(open(os.path.join(ROOT, "data", "site.json"), encoding="utf-8"))
CATS = SITE["cats"]

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

# 분야 분류 규칙 — 위에서부터 먼저 맞는 것으로 정한다.
RULES = [
    (1, ["후유장해", "장해율", "장해지급률", "장해분류표", "동요관절", "압박골절", "골절",
         "절단", "추상장해", "흉터", "반흔", "마비", "편마비", "척수", "인대", "관절",
         "고정술", "무혈성괴사", "장해진단"]),
    (2, ["교통사고", "합의금", "대인배상", "과실비율", "상실수익", "향후치료비", "휴업손해",
         "개호비", "자동차보험", "자전거 사고"]),
    (3, ["배상책임", "일상생활배상", "시설소유", "화재배상", "임차인 배상", "자기부담금"]),
    (4, ["고지의무", "계약 해지", "계약해지", "부활", "소멸시효", "현장심사", "의료자문",
         "사망보험금", "면책 통보", "부지급 통보", "손해사정사 선임", "청구권"]),
    (0, ["진단비", "암진단", "일반암", "유사암", "소액암", "제자리암", "상피내암", "경계성",
         "신생물", "종양", "림프종", "뇌경색", "뇌출혈", "심근경색", "협심증", "뇌혈관",
         "허혈성", "진단코드", "조직검사", "입원의료비", "실손"]),
]
# 지역 키워드가 제목에 있으면 홈페이지로 가져오지 않는다.
REGION = ["부산", "울산", "대구", "창원", "서울", "경남", "경기", "인천", "광주", "대전", "김해", "양산"]

# 본문에서 걷어낼 인사말·서명 문장
DROP_LINE = re.compile(
    r"^(안녕하세요|안녕하십니까).{0,80}(입니다|입니다\.)\s*$|"
    r"^.{0,40}(드림|올림)\s*$|"
    r"^무료\s*상담.{0,40}$|"
    r"^(상담|문의)\s*(전화|번호).{0,40}$|"
    r"^\s*010[-\s]?\d{3,4}[-\s]?\d{4}\s*$|"
    r"^항상 든든한 동반자가 되어드리겠습니다\.?\s*$")

DROP_WORD = re.compile(r"판례|승소|소송 대리|법률 자문|무조건|100% 보장|반드시 지급")


def fetch(url, tries=3, binary=False):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": UA, "Referer": "https://blog.naver.com/",
                "Accept-Language": "ko-KR,ko;q=0.9"})
            with urllib.request.urlopen(req, timeout=30, context=CTX) as r:
                raw = r.read()
            return raw if binary else raw.decode("utf-8", "replace")
        except Exception as e:  # noqa: BLE001
            if i == tries - 1:
                print("  ! 실패 %s (%s)" % (url[:70], e))
                return None
            time.sleep(2 * (i + 1))


def classify(title, body):
    t = title + " " + body[:800]
    for cat, words in RULES:
        if any(w in t for w in words):
            return cat
    return 0


def is_region_post(title):
    return any(r in title for r in REGION)


def clean_text(s):
    s = html.unescape(re.sub(r"<[^>]+>", " ", s))
    return re.sub(r"[ \t​\xa0]+", " ", s).strip()


def save_image(url, logno, idx):
    url = url.split("?")[0]
    ext = os.path.splitext(url)[1].lower()
    if ext not in (".jpg", ".jpeg", ".png", ".gif", ".webp"):
        ext = ".jpg"
    name = "%s_%d%s" % (logno, idx, ext)
    dest = os.path.join(IMGDIR, name)
    if not os.path.exists(dest):
        data = fetch(url + "?type=w966", binary=True) or fetch(url, binary=True)
        if not data or len(data) < 2000:
            return None
        os.makedirs(IMGDIR, exist_ok=True)
        with open(dest, "wb") as f:
            f.write(data)
        time.sleep(0.3)
    return "/assets/img/blog/" + name


def parse_post(blog_id, logno):
    """글 한 편의 제목·날짜·본문·사진을 가져온다."""
    raw = fetch("https://m.blog.naver.com/%s/%s" % (blog_id, logno))
    if not raw:
        return None
    m = re.search(r'<meta property="og:title" content="([^"]*)"', raw)
    title = html.unescape(m.group(1)).strip() if m else ""
    title = re.sub(r"\s*:\s*네이버 블로그\s*$", "", title)
    if not title:
        return None
    m = re.search(r'class="se_publishDate[^"]*"[^>]*>([^<]+)<', raw) or \
        re.search(r'class="date[^"]*"[^>]*>([^<]+)<', raw)
    date = ""
    if m:
        d = re.search(r"(\d{4})\.\s*(\d{1,2})\.\s*(\d{1,2})", m.group(1))
        if d:
            date = "%s-%02d-%02d" % (d.group(1), int(d.group(2)), int(d.group(3)))
    if not date:
        m = re.search(r'"publishDate"\s*:\s*"?(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})', raw)
        date = ("%s-%02d-%02d" % (m.group(1), int(m.group(2)), int(m.group(3)))) if m else \
               datetime.now().strftime("%Y-%m-%d")

    m = re.search(r'<div class="se-main-container">(.*?)</div>\s*<!--\s*/SE-MAIN', raw, re.S) or \
        re.search(r'<div class="se-main-container">(.*)', raw, re.S) or \
        re.search(r'<div id="postViewArea"[^>]*>(.*)', raw, re.S)
    if not m:
        return None
    src = m.group(1)

    blocks, imgs, idx = [], [], 0
    for tag in re.finditer(r'<(p|h[1-4]|img)\b[^>]*>(.*?)</\1>|<img\b[^>]*>', src, re.S):
        chunk = tag.group(0)
        if chunk.startswith("<img"):
            u = re.search(r'(?:data-lazy-src|data-src|src)="([^"]+)"', chunk)
            if u and "postfiles" in u.group(1) or (u and "blogfiles" in u.group(1)):
                idx += 1
                p = save_image(u.group(1), logno, idx)
                if p:
                    imgs.append(p)
                    blocks.append('<img src="%s" alt="" loading="lazy">' % p)
            continue
        text = clean_text(chunk)
        if not text or DROP_LINE.match(text):
            continue
        if len(text) < 3:
            continue
        tagname = tag.group(1)
        if tagname and tagname.startswith("h"):
            blocks.append("<h2>%s</h2>" % html.escape(text))
        else:
            blocks.append("<p>%s</p>" % html.escape(text))

    # 서명부: 뒤에서부터 인사·연락처 문단 정리
    while blocks and re.search(r"010[-\s]?\d{3,4}|드림|올림|무료\s*상담", clean_text(blocks[-1])):
        blocks.pop()

    body = "\n".join(blocks)
    plain = clean_text(body)
    if len(plain) < 200:
        return None
    summary = re.sub(r"\s+", " ", plain)[:150].rstrip() + "…"
    warn = sorted(set(DROP_WORD.findall(plain)))
    return {"id": str(logno), "date": date, "title": title, "summary": summary,
            "body": body, "image": imgs[0] if imgs else "",
            "cat": classify(title, plain), "example": False,
            "source": "https://blog.naver.com/%s/%s" % (blog_id, logno),
            "review": warn}


def list_from_rss(blog_id):
    raw = fetch("https://rss.blog.naver.com/%s.xml" % blog_id)
    if not raw:
        return []
    try:
        root = ElementTree.fromstring(raw.encode("utf-8"))
    except ElementTree.ParseError:
        return []
    out = []
    for it in root.iter("item"):
        link = (it.findtext("link") or "").strip()
        m = re.search(r"/(\d{9,})", link)
        if m:
            out.append(m.group(1))
    return out


def list_all(blog_id, hard_limit=2000):
    """전체 글 번호를 목록 API 로 훑는다."""
    out, page, seen = [], 1, set()
    while len(out) < hard_limit:
        url = ("https://blog.naver.com/PostTitleListAsync.naver?blogId=%s"
               "&viewdate=&currentPage=%d&categoryNo=0&parentCategoryNo=&countPerPage=30" % (blog_id, page))
        raw = fetch(url)
        if not raw:
            break
        nos = re.findall(r'"logNo"\s*:\s*"?(\d{9,})', raw)
        nos = [n for n in nos if n not in seen]
        if not nos:
            break
        seen.update(nos)
        out.extend(nos)
        print("  목록 %d쪽 · 누적 %d편" % (page, len(out)))
        page += 1
        time.sleep(0.6)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--blog", default="sonsa2204", help="네이버 블로그 아이디")
    ap.add_argument("--all", action="store_true", help="전체 글 (최초 이관)")
    ap.add_argument("--limit", type=int, default=0, help="가져올 최대 편수")
    ap.add_argument("--keep-region", action="store_true", help="지역 키워드 글도 포함")
    a = ap.parse_args()

    old = json.load(open(POSTS, encoding="utf-8")) if os.path.exists(POSTS) else []
    have = {p["id"]: p for p in old if not p.get("example")}
    print("기존 글 %d편" % len(have))

    ids = list_all(a.blog) if a.all else list_from_rss(a.blog)
    print("블로그에서 %d편 확인" % len(ids))
    todo = [i for i in ids if i not in have]
    if a.limit:
        todo = todo[:a.limit]
    print("새로 가져올 글 %d편" % len(todo))

    added, skipped = 0, 0
    for n, logno in enumerate(todo, 1):
        p = parse_post(a.blog, logno)
        if not p:
            print("  [%d/%d] %s — 건너뜀(본문 없음)" % (n, len(todo), logno))
            continue
        if not a.keep_region and is_region_post(p["title"]):
            skipped += 1
            print("  [%d/%d] %s — 지역 글 제외" % (n, len(todo), p["title"][:32]))
            continue
        have[logno] = p
        added += 1
        flag = "  ⚠확인필요:%s" % ",".join(p["review"]) if p["review"] else ""
        print("  [%d/%d] %s · %s · %s%s" % (n, len(todo), p["date"], CATS[p["cat"]], p["title"][:36], flag))
        time.sleep(0.8)

    out = sorted(have.values(), key=lambda p: p["date"], reverse=True)
    if not out:
        out = old
    with open(POSTS, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("\n추가 %d편 · 지역 글 제외 %d편 · 전체 %d편 저장" % (added, skipped, len(out)))
    flagged = [p for p in out if p.get("review")]
    if flagged:
        print("표현 확인이 필요한 글 %d편:" % len(flagged))
        for p in flagged[:20]:
            print("  - %s (%s)" % (p["title"][:40], ",".join(p["review"])))


if __name__ == "__main__":
    sys.exit(main())
