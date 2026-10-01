#!/usr/bin/env python3
"""박성일 손해사정사 홈페이지 정적 사이트 생성기.

  python3 scripts/build.py

data/ 의 내용과 parts/ 의 조각을 합쳐 public/ 에 완성된 사이트를 만든다.
public/ 은 Cloudflare Pages 가 그대로 서비스한다.
"""
import html
import json
import os
import re
import shutil
from datetime import datetime, timezone, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "public")
KST = timezone(timedelta(hours=9))


def load(*p):
    with open(os.path.join(ROOT, *p), encoding="utf-8") as f:
        t = f.read()
    if "{{" not in t:
        return t
    return (t.replace("{{KAKAO_SVG}}", KAKAO_SVG)
             .replace("{{TEL}}", SITE["tel"])
             .replace("{{KAKAO}}", SITE["kakao"]))


def jload(*p):
    return json.loads(load(*p))


SITE = jload("data", "site.json")
CATS = SITE["cats"]
SLUGS = SITE["cat_slugs"]
DOMAIN = SITE["domain"].rstrip("/")
E = html.escape


def asset_v(rel):
    """파일이 바뀌면 주소도 바뀌게 해서 브라우저가 옛 파일을 쓰지 않게 한다."""
    import hashlib
    try:
        h = hashlib.md5(open(os.path.join(ROOT, rel), "rb").read()).hexdigest()[:8]
    except OSError:
        return ""
    return "?v=" + h


def won(v):
    return f"{v:,}원"


def money_kr(v):
    eok, man = v // 100_000_000, (v % 100_000_000) // 10_000
    return f"{eok}억 {man:,}만 원" if eok else f"{man:,}만 원"


# ---------------------------------------------------------------- 공통 조각
KAKAO_SVG = ('<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">'
             '<path d="M12 3C6.5 3 2 6.6 2 11c0 2.8 1.9 5.3 4.7 6.7L5.8 21l4.3-2.7c.6.1 1.2.1 1.9.1 '
             '5.5 0 10-3.6 10-8S17.5 3 12 3z"/></svg>')

NAV = [("/about/", "소개"), ("/about/#credentials", "자격 · 면허"), ("/cases/", "지급 내역"),
       ("/reviews/", "상담 후기"), ("/about/#services", "업무 분야"), ("/blog/", "손해사정 칼럼"),
       ("/contact/#faq", "자주 묻는 질문")]


def header():
    nav = NAV if posts() else [x for x in NAV if x[0] != "/blog/"]
    links = "".join('<a href="%s">%s</a>' % (u, t) for u, t in nav)
    mlinks = "".join('<a href="%s">%s</a>' % (u, t) for u, t in nav)
    return f'''<header class="topbar">
  <div class="wrap">
    <a class="brand" href="/">{E(SITE["name"])} <small>{E(SITE["tagline"])}</small></a>
    <nav class="navlinks">{links}</nav>
    <div class="topbtns">
      <a class="topcall ghost" href="tel:{SITE["tel"]}">{SITE["tel"]}</a>
      <a class="topcall" href="/contact/">상담 신청</a>
      <button class="menubtn" id="menubtn" aria-label="전체 메뉴 열기" aria-expanded="false" aria-controls="mmenu">
        <span class="bars" aria-hidden="true"><i></i><i></i><i></i></span><span class="lbl">메뉴</span>
      </button>
    </div>
  </div>
</header>
<div class="mmenu" id="mmenu" hidden>
  <div class="mm-top">
    <span>전체 메뉴</span>
    <button class="mm-x" id="mmclose" aria-label="메뉴 닫기">×</button>
  </div>
  <nav class="mm-links">{mlinks}</nav>
  <div class="mm-cta">
    <a class="mm-call" href="tel:{SITE["tel"]}">전화 상담 {SITE["tel"]}</a>
    <a class="mm-form" href="/contact/">상담 신청하기</a>
  </div>
</div>'''


def footer():
    V_APP = APP_V[0]
    blogs = "".join('<a href="%s" target="_blank" rel="noopener">블로그 · %s</a>'
                    % (b["url"], E(b["name"])) for b in SITE["blogs"])
    return f'''<footer>
  <div class="wrap">
    <div class="fbrand">{E(SITE["name"])}</div>
    <div class="frow"><span>{E(SITE["office"])}</span><span>상담문의 {SITE["tel"]}</span><span>전국 상담 가능</span></div>
    <div class="frow"><a href="{SITE["kakao"]}" target="_blank" rel="noopener">카카오톡 오픈채팅</a>{blogs}<a href="/privacy/">개인정보 처리방침</a></div>
    <div class="fcopy">© {datetime.now(KST).year} {E(SITE["name"])}. 본 사이트의 지급 내역과 사례는 실제 처리 건을 식별정보 없이 정리한 것으로, 개별 사안의 결과를 보장하지 않습니다.</div>
  </div>
</footer>
<div class="stickybar">
  <a class="sb-call" href="tel:{SITE["tel"]}">전화상담</a>
  <a class="sb-kko" href="{SITE["kakao"]}" target="_blank" rel="noopener">{KAKAO_SVG}카톡상담</a>
</div>
<div class="lb" id="lb" role="dialog" aria-label="이미지 크게 보기"><button class="x" aria-label="닫기">×</button><img alt=""></div>
<script src="/assets/app.js{V_APP}" defer></script>'''


def tracking():
    """광고 성과 추적 스크립트. site.json 의 naver_wa(네이버 공통키), ga4_id 가 있을 때만 넣는다.
    전환(전화·카톡·상담폼) 신호는 app.js 의 trk() 가 보낸다."""
    out = ""
    if SITE.get("naver_wa"):
        out += '''
<script src="//wcs.naver.net/wcslog.js"></script>
<script>if(!wcs_add)var wcs_add={};wcs_add["wa"]="%s";if(!_nasa)var _nasa={};
if(window.wcs){if(wcs.inflow){wcs.inflow("%s");}wcs_do(_nasa);}</script>''' % (
            SITE["naver_wa"], DOMAIN.split("//")[-1])
    if SITE.get("ga4_id"):
        out += '''
<script async src="https://www.googletagmanager.com/gtag/js?id=%s"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}
gtag('js',new Date());gtag('config','%s');</script>''' % (SITE["ga4_id"], SITE["ga4_id"])
    return out


def page(path, title, desc, body, *, og_image=None, jsonld=None, published=None,
         canonical_url=None, noindex=False):
    """완성된 HTML 한 페이지를 public/ 아래에 쓴다.

    canonical_url 을 주면 그 주소를 원문으로 지정한다. 네이버 블로그에서 가져온
    글에 원문(네이버) 주소를 넣어, 검색엔진이 홈페이지 글을 중복으로 보지 않게 한다.
    """
    canonical = canonical_url or (DOMAIN + path)
    img = og_image or (DOMAIN + "/assets/img/photo/hero.jpg")
    verify = ""
    if SITE.get("naver_verify"):
        verify += '\n<meta name="naver-site-verification" content="%s">' % SITE["naver_verify"]
    if SITE.get("google_verify"):
        verify += '\n<meta name="google-site-verification" content="%s">' % SITE["google_verify"]
    ld = '\n<script type="application/ld+json">%s</script>' % json.dumps(
        jsonld, ensure_ascii=False) if jsonld else ""
    pub = '\n<meta property="article:published_time" content="%s">' % published if published else ""
    if SITE.get("form_endpoint"):
        body = body.replace('<form id="cform">',
                            '<form id="cform" action="%s" method="POST">' % SITE["form_endpoint"])
    doc = f'''<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{canonical}">
<meta name="robots" content="{"noindex, follow" if noindex else "index, follow, max-image-preview:large, max-snippet:-1"}">{verify}
<meta property="og:type" content="{'article' if published else 'website'}">
<meta property="og:site_name" content="{E(SITE["name"])}">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{img}">
<meta property="og:locale" content="ko_KR">{pub}
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&family=Noto+Serif+KR:wght@500;600;700&display=swap">
<link rel="stylesheet" href="/assets/style.css{asset_v("assets/style.css")}">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="alternate" type="application/rss+xml" title="{E(SITE["name"])} 손해사정 칼럼" href="/rss.xml">{ld}{tracking()}
</head>
<body>
{header()}
{body}
{footer()}
</body>
</html>'''
    dest = os.path.join(OUT, path.strip("/"), "index.html") if path != "/" else os.path.join(OUT, "index.html")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w", encoding="utf-8") as f:
        f.write(doc)
    return path


# ---------------------------------------------------------------- 지급 내역
def payouts_section():
    cases = jload("data", "payouts.json")
    total = sum(c["amount"] for c in cases)
    ndocs = sum(len(c["docs"]) for c in cases)
    cards = []
    for c in cases:
        docs = ""
        for d in c["docs"]:
            src = "/assets/img/payout/" + d["img"]
            st = {"top": "", "bottom": ' style="object-position:bottom"',
                  "contain": ' style="object-fit:contain;padding:8px"'}.get(d.get("fit", "top"), "")
            docs += ('<div class="d" data-full="%s"><img src="%s" alt="%s" loading="lazy"%s>'
                     '<span>%s</span></div>' % (src, src, E(d["label"]), st, E(d["label"])))
        note = '<small>%s</small>' % E(c["amount_note"]) if c.get("amount_note") else ""
        cards.append('<div class="pay"><div class="docs">%s</div><div class="meta">'
                     '<span class="k">%s</span><h3>%s</h3><div class="amt">%s%s</div>'
                     '<p class="ctx">%s</p></div></div>'
                     % (docs, E(c["kind"]), E(c["title"]), won(c["amount"]), note, E(c["context"])))
    return f'''<section id="payouts">
  <div class="wrap">
    <div class="sec-head">
      <div class="eyebrow">지급 내역</div>
      <h2>결과는 지급내역서와 합의서로 보여드립니다.</h2>
      <p>실제 처리한 건의 보험사 지급내역서, 입금내역, 교통사고 합의서입니다. 성명·증권번호·계좌·날짜 등 개인정보와 특정 가능한 정보는 모두 가렸습니다.</p>
    </div>
    <div class="paystats">
      <div><div class="l">공개 내역서</div><div class="v">{ndocs}<small>장</small></div></div>
      <div><div class="l">지급 · 합의 건수</div><div class="v">{len(cases)}<small>건</small></div></div>
      <div><div class="l">지급 · 합의 합계</div><div class="v">{money_kr(total)}</div></div>
    </div>
    <div class="grid g3 cut9" id="payg">{''.join(cards)}</div>
    <button class="more-btn" data-for="payg" data-full="{len(cases)}">지급 내역 전체 {len(cases)}건 보기</button>
    <p class="pay-note">위 금액은 공개한 내역서와 합의서에 적힌 지급액·합의금의 합계이며, 보험사가 지급을 결정하거나 당사자가 합의한 결과입니다. 사안마다 약관·가입 시점·의무기록이 다르므로 개별 사안의 결과를 보장하지 않습니다. 이미지를 누르면 크게 보실 수 있습니다.</p>
  </div>
</section>'''


# ---------------------------------------------------------------- 처리 사례
def cases_section():
    cs = jload("data", "cases.json")
    cards = []
    for c in cs:
        note = ('<dt>참고</dt><dd class="also">%s</dd>' % E(c["note"])) if c.get("note") else ""
        cards.append(
            '<div class="case"><div class="case-top"><span class="cat">%s</span>'
            '<span class="dt">%s</span></div><h3>%s</h3>'
            '<dl><dt>보험사 주장</dt><dd>%s</dd><dt>쟁점</dt><dd>%s</dd>'
            '<dt>검토 내용</dt><dd>%s</dd><dt>결과</dt><dd class="res">%s</dd>%s</dl></div>'
            % (E(CATS[c["cat"]]), E(c["when"]), E(c["title"]), E(c["claim"]),
               E(c["issue"]), E(c["review"]), E(c["result"]), note))
    return f'''<section id="cases" class="alt">
  <div class="wrap">
    <div class="sec-head">
      <div class="eyebrow">처리 사례</div>
      <h2>결과보다 먼저, 어떤 논리로 뒤집었는지를 보여드립니다.</h2>
      <p>보험사가 무엇을 근거로 거절했고, 그에 대해 무엇을 다시 확인했는지를 그대로 적었습니다. 비슷한 통보를 받으셨다면 참고가 되실 겁니다.</p>
    </div>
    <div class="grid g2 cut6" id="casg">{''.join(cards)}</div>
    <button class="more-btn" data-for="casg" data-full="{len(cs)}">처리 사례 전체 {len(cs)}건 보기</button>
    <p class="pay-note">위 사례는 실제 처리한 건을 개인 식별정보 없이 정리한 것입니다. 사안마다 약관·가입 시점·의무기록이 다르므로 개별 사안의 결과를 보장하지 않으며, 검토 결과 실익이 없다고 판단되면 그대로 말씀드립니다.</p>
  </div>
</section>'''


# ---------------------------------------------------------------- 상담 후기
def reviews_section():
    R = jload("data", "reviews.json")
    cards = []
    for r in R["items"]:
        stars = ('<span class="st">%s<i>%s</i></span>'
                 % ("★" * r["star"], "★" * (5 - r["star"])))
        text = "<br>".join(E(t) for t in r["text"].split("\n"))
        cards.append('<figure class="rv"><div class="rv-h">%s<span class="tp">%s</span></div>'
                     '<blockquote>%s</blockquote>'
                     '<figcaption>%s</figcaption></figure>'
                     % (stars, E(r["topic"]), text, E(r["who"])))
    return f'''<section id="reviews">
  <div class="wrap">
    <div class="sec-head">
      <div class="eyebrow">상담 후기</div>
      <h2>상담을 받으신 분들이 남긴 말입니다.</h2>
      <p>네이버 엑스퍼트에 쌓인 후기 <b>{R["count"]}건</b> · 평점 <b>{R["rating"]} / 5.0</b>. 그중 일부를 손대지 않고 그대로 옮겼습니다.</p>
    </div>
    <div class="rv-grid" id="rvg">{''.join(cards)}</div>
    <button class="rv-more" onclick="document.getElementById('rvg').classList.add('open');this.remove()">후기 더 보기</button>
    <p class="rv-note">{E(R["note"])} 전체 후기는
      <a href="{R["source_url"]}" target="_blank" rel="noopener nofollow">{E(R["source"])} 프로필</a>에서 직접 확인하실 수 있습니다.
      후기는 상담을 받으신 분의 개인적인 소감이며, 사안마다 약관·가입 시점·의무기록이 달라 같은 결과를 보장하지 않습니다.</p>
  </div>
</section>'''


# ---------------------------------------------------------------- 블로그
def md_body(src):
    """data/posts/*.md 본문을 아주 단순한 규칙으로 HTML 로 바꾼다."""
    out, ul = [], []

    def flush():
        if ul:
            out.append("<ul>%s</ul>" % "".join("<li>%s</li>" % x for x in ul))
            ul.clear()

    def inline(t):
        t = E(t)
        t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
        return re.sub(r"\[(.+?)\]\((\S+?)\)", r'<a href="\2">\1</a>', t)

    for block in re.split(r"\n\s*\n", src.strip()):
        block = block.strip()
        if not block:
            continue
        if block.startswith("### "):
            flush(); out.append("<h3>%s</h3>" % inline(block[4:].strip())); continue
        if block.startswith("## "):
            flush(); out.append("<h2>%s</h2>" % inline(block[3:].strip())); continue
        m = re.fullmatch(r"!\[([^\]]*)\]\((\S+)\)", block)
        if m:
            flush()
            out.append('<img src="%s" alt="%s" loading="lazy">' % (E(m.group(2)), E(m.group(1))))
            continue
        if block.startswith("- "):
            for line in block.split("\n"):
                if line.strip().startswith("- "):
                    ul.append(inline(line.strip()[2:]))
            flush(); continue
        flush()
        out.append("<p>%s</p>" % "<br>".join(inline(l) for l in block.split("\n")))
    flush()
    return "\n".join(out)


def local_posts():
    """홈페이지에 먼저 쓴 글. data/posts/<주소이름>.md 한 편에 한 파일."""
    d = os.path.join(ROOT, "data", "posts")
    if not os.path.isdir(d):
        return []
    out = []
    for name in sorted(os.listdir(d)):
        if not name.endswith(".md") or name.startswith(("_", ".")):
            continue  # _ 로 시작하는 파일은 견본으로 보고 홈페이지에 올리지 않는다
        raw = open(os.path.join(d, name), encoding="utf-8").read()
        head, _, body = raw.partition("\n---")
        meta = {}
        for line in head.strip().splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                meta[k.strip()] = v.strip()
        title = meta.get("제목", "").strip()
        if not title:
            print("  ! %s — '제목:' 이 없어 건너뜁니다" % name)
            continue
        cat = 0
        norm = lambda t: re.sub(r"[\s·ㆍ・.,/]", "", t)   # 띄어쓰기·가운뎃점 차이는 무시
        want = norm(meta.get("분야", ""))
        for i, c in enumerate(CATS):
            if want and (want == norm(c) or want in norm(c) or norm(c) in want):
                cat = i
                break
        html_body = md_body(body)
        plain = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html_body)).strip()
        img = re.search(r'<img src="([^"]+)"', html_body)
        out.append({"id": name[:-3], "date": meta.get("날짜", "").strip() or
                    datetime.now(KST).strftime("%Y-%m-%d"),
                    "title": title,
                    "summary": meta.get("요약", "").strip() or (plain[:150].rstrip() + "…"),
                    "body": html_body, "image": img.group(1) if img else "",
                    "cat": cat, "example": False, "origin": "home", "source": ""})
    return out


_POSTS = None


def posts():
    global _POSTS
    if _POSTS is None:
        ps = jload("data", "posts.json")
        have = {p["id"] for p in ps}
        ps += [p for p in local_posts() if p["id"] not in have]
        ps.sort(key=lambda p: p["date"], reverse=True)
        _POSTS = ps
    return _POSTS


def post_url(p):
    return "/blog/%s/" % p["id"]


def post_card(p):
    thumb = ('<div class="pc-thumb"><img src="%s" alt="" loading="lazy"></div>' % p["image"]) if p.get("image") else ""
    return ('<a class="post-card" href="%s">%s<div class="pc-top"><span class="cat">%s</span>'
            '<span class="dt">%s</span></div><h3>%s</h3><p>%s</p></a>'
            % (post_url(p), thumb, E(CATS[p["cat"]]), p["date"].replace("-", "."),
               E(p["title"]), E(p["summary"])))


def blog_latest_section(ps):
    if not ps:
        return ""   # 칼럼이 한 편도 없으면 섹션 자체를 내보내지 않는다
    note = ""
    cards = "".join(post_card(p) for p in ps[:6])
    return f'''<section id="blog-latest">
  <div class="wrap">
    <div class="sec-head">
      <div class="eyebrow">손해사정 칼럼</div>
      <h2>진단코드 하나, 장해율 1%가 갈리는 지점을 기록합니다.</h2>
      <p>보험사 계열 심사 실무와 손해사정 현장에서 직접 정리한 글입니다. 비슷한 진단명이나 통보를 받으셨다면 먼저 읽어보세요.</p>
    </div>
    {note}
    <div class="grid g3">{cards}</div>
    <div class="blog-more"><a class="btn btn-line" href="/blog/">칼럼 전체 보기</a></div>
  </div>
</section>'''


def chips(active):
    ps = posts()
    counts = [sum(1 for p in ps if p["cat"] == i) for i in range(len(CATS))]
    out = ['<a class="chip%s" href="/blog/">전체<span class="n">%d</span></a>'
           % (" on" if active is None else "", len(ps))]
    for i, c in enumerate(CATS):
        out.append('<a class="chip%s" href="/blog/%s/">%s<span class="n">%d</span></a>'
                   % (" on" if active == i else "", SLUGS[i], E(c), counts[i]))
    return '<div class="chips">%s</div>' % "".join(out)


def blog_list_page(cat=None):
    ps = posts()
    sel = ps if cat is None else [p for p in ps if p["cat"] == cat]
    heading = "전체 글" if cat is None else CATS[cat]
    path = "/blog/" if cat is None else "/blog/%s/" % SLUGS[cat]
    lst = ('<div class="post-list">%s</div>' % "".join(post_card(p) for p in sel)) if sel else \
          '<div class="empty">이 분야의 글은 이관 후 채워집니다.</div>'
    body = f'''<main><section class="listpage">
  <div class="wrap">
    <div class="blog-head"><div><div class="eyebrow">손해사정 칼럼</div><h1>{E(heading)}</h1>
      <p>손해사정 실무에서 정리한 글을 분야별로 모았습니다.</p></div></div>
    {chips(cat)}
    {lst}
  </div>
</section></main>'''
    title = "%s | %s 손해사정 칼럼" % (heading, SITE["name"])
    desc = "%s 관련 손해사정 실무 글 %d편. 약관 기준과 진단코드, 장해분류표 적용을 정리했습니다." % (heading, len(sel))
    return page(path, title, desc, body)


BODY_CTA = '''<div class="cta">
  <h3>비슷한 통보를 받으셨나요?</h3>
  <p>통보서와 진단서를 보내주시면 다시 청구할 여지가 있는지 먼저 말씀드립니다. 상담 단계에서는 비용이 없습니다.</p>
  <div class="row"><a class="btn btn-navy" href="tel:{tel}">전화 상담 {tel}</a>
  <a class="btn btn-kakao" href="{kakao}" target="_blank" rel="noopener">{svg}카카오톡 상담</a></div>
</div>'''


def is_mirror(p):
    """네이버 블로그에 먼저 올린 글의 사본인가. (홈페이지에 먼저 쓴 글은 origin='home')"""
    return bool(p.get("source")) and p.get("origin") != "home"


def post_page(p, prev, nxt):
    body_html = p.get("body") or (
        '<p>%s</p><div class="ph">이 자리에는 블로그 원문이 사진과 함께 그대로 들어갑니다.</div>' % E(p["summary"]))
    origin_note = ""
    if is_mirror(p):
        origin_note = ('<p class="origin">이 글은 네이버 블로그 <b>박성일손해사정사의 보험금 지급솔루션</b>에 '
                       '먼저 올린 글을 옮겨 실은 것입니다. '
                       '<a href="%s" target="_blank" rel="noopener">원문 보기</a></p>' % E(p["source"]))
    nav = '<div class="nav">'
    nav += ('<a href="%s"><small>이전 글</small>%s</a>' % (post_url(prev), E(prev["title"]))) if prev else "<span></span>"
    if nxt:
        nav += '<a href="%s" style="text-align:right"><small>다음 글</small>%s</a>' % (post_url(nxt), E(nxt["title"]))
    nav += "</div>"
    body = f'''<main><section class="listpage"><div class="wrap"><article class="article">
  <a class="back" href="/blog/">← 목록으로</a>
  <div class="meta"><span class="cat">{E(CATS[p["cat"]])}</span><span>{p["date"].replace("-", ".")}</span><span>{E(SITE["name"])}</span></div>
  <h1>{E(p["title"])}</h1>
  {origin_note}
  <div class="body">{body_html}</div>
  {BODY_CTA.format(tel=SITE["tel"], kakao=SITE["kakao"], svg=KAKAO_SVG)}
  {nav}
</article></div></section></main>'''
    img = DOMAIN + p["image"] if p.get("image") else None
    ld = {"@context": "https://schema.org", "@type": "Article",
          "headline": p["title"], "description": p["summary"],
          "datePublished": p["date"], "dateModified": p["date"],
          "author": {"@type": "Person", "name": SITE["name"],
                     "jobTitle": "손해사정사", "url": DOMAIN + "/#about"},
          "publisher": {"@type": "Organization", "name": SITE["name"], "url": DOMAIN},
          "mainEntityOfPage": p["source"] if is_mirror(p) else DOMAIN + post_url(p),
          "articleSection": CATS[p["cat"]]}
    if img:
        ld["image"] = img
    return page(post_url(p), "%s | %s" % (p["title"], SITE["name"]), p["summary"],
                body, og_image=img, jsonld=ld, published=p["date"],
                canonical_url=p["source"] if is_mirror(p) else None)


# ---------------------------------------------------------------- 메인
def home(ps):
    parts = [load("parts", "hero.html"),        # 1. 내 문제인가
             load("parts", "situations.html"),   # 2. 내 얘기다
             payouts_section(),                  # 3. 결과가 있나 (증거)
             cases_section(),                    # 4. 어떻게 뒤집었나
             load("parts", "about.html"),        # 5. 누가 하는가
             load("parts", "credentials.html"),  # 6. 자격은 있나
             reviews_section(),                  # 7. 사람은 어떤가
             load("parts", "services.html"),     # 8. 내 분야를 다루나
             load("parts", "process.html"),      # 9. 절차와 비용
             load("parts", "faq.html"),          # 10. 남은 의문
             blog_latest_section(ps),            # 11. 더 읽을거리
             load("parts", "contact.html")]      # 12. 연락
    body = "<main>%s</main>" % "\n".join(parts)
    ld = {"@context": "https://schema.org", "@type": "ProfessionalService",
          "name": SITE["name"], "url": DOMAIN,
          "telephone": "+82-" + SITE["tel"].lstrip("0").replace("-", "-", 1),
          "areaServed": {"@type": "Country", "name": "대한민국"},
          "description": "교보생명·KB손해보험 계열에서 현장심사 및 단체보험 심사를 했던 손해사정사. 질병·진단비, 상해·후유장해, 교통사고, 배상책임, 보험계약 분쟁의 삭감·면책 사유를 약관과 의무기록으로 재검토합니다.",
          "founder": {"@type": "Person", "name": "박성일", "jobTitle": "손해사정사",
                      "hasCredential": ["손해사정사(신체)", "임상병리사", "개인보험심사역"]},
          "image": DOMAIN + "/assets/img/photo/hero.jpg"}
    faq = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": []}
    for m in re.finditer(r'<summary>(.*?)</summary><div class="ans">(.*?)</div>',
                         load("parts", "faq.html"), re.S):
        faq["mainEntity"].append({"@type": "Question", "name": re.sub(r"<[^>]+>", "", m.group(1)).strip(),
                                  "acceptedAnswer": {"@type": "Answer",
                                                     "text": re.sub(r"<[^>]+>", "", m.group(2)).strip()}})
    return page("/", "박성일 손해사정사 | 손해사정사 무료 상담 · 보험금 삭감·면책 재검토",
                HOME_DESC,
                body, jsonld=[ld, faq])


HOME_DESC = ("교보생명·KB손해보험 계열에서 현장심사 및 단체보험 심사를 했던 손해사정사가 직접 상담합니다. "
             "진단비·후유장해·교통사고 보험금 삭감·면책을 약관과 의무기록으로 다시 검토합니다. "
             "상담 무료, 착수금 없는 후불 보수, 전국 상담.")


# ---------------------------------------------------------------- 하위 페이지
# 메뉴 항목을 각각 독립된 주소로 두어, 검색 결과에 바로가기 링크가 붙을 수 있게 한다.
def sub_page(path, eyebrow, h1, lead, title, desc, sections, cta=True):
    head = f'''<section class="subhead"><div class="wrap"><div class="blog-head"><div>
  <div class="eyebrow">{E(eyebrow)}</div><h1>{E(h1)}</h1><p>{E(lead)}</p></div></div></div></section>'''
    body = "<main class=\"sub\">%s\n%s\n%s</main>" % (head, "\n".join(sections), SUB_CTA if cta else "")
    return page(path, title, desc, body)


SUB_CTA = '''<section class="sub-cta"><div class="wrap"><div class="cta">
  <div><b>지금 받은 통보, 근거부터 확인해 보세요.</b><p>상담은 무료이며, 가능성이 낮으면 낮다고 말씀드립니다.</p></div>
  <div class="cta-btns"><a class="btn btn-navy" href="/contact/">상담 신청</a><a class="btn btn-line" href="tel:{{TEL}}">전화 {{TEL}}</a></div>
</div></div></section>'''


def sub_pages():
    global SUB_CTA
    SUB_CTA = SUB_CTA.replace("{{TEL}}", SITE["tel"])
    out = []
    out.append(sub_page("/about/", "소개", "박성일 손해사정사",
        "교보생명·KB손해보험 계열에서 심사 실무를 한 손해사정사이자 임상병리사입니다.",
        "손해사정사 소개 | 박성일 손해사정사",
        "교보생명·KB손해보험 계열 현장심사·단체보험 심사 경력, 손해사정사(신체)·임상병리사·개인보험심사역 자격을 갖춘 박성일 손해사정사를 소개합니다.",
        [load("parts", "about.html"), load("parts", "credentials.html"), load("parts", "services.html")]))
    out.append(sub_page("/cases/", "지급 내역 · 처리 사례", "실제로 받아낸 보험금",
        "보험사 지급내역서와 처리 과정을 개인정보 없이 공개합니다.",
        "보험금 지급 내역 · 처리 사례 | 박성일 손해사정사",
        "암진단비·뇌심혈관 진단비·후유장해·교통사고 합의금까지, 실제 처리한 건의 지급 내역과 보험사 주장·쟁점·결과를 정리했습니다.",
        [payouts_section(), cases_section()]))
    out.append(sub_page("/reviews/", "상담 후기", "의뢰인이 남긴 후기",
        "네이버 엑스퍼트에 의뢰인이 직접 남긴 후기를 고치지 않고 옮겼습니다.",
        "상담 후기 | 박성일 손해사정사",
        "네이버 엑스퍼트에서 의뢰인이 직접 남긴 박성일 손해사정사 상담 후기입니다. 내용은 고치지 않고 그대로 옮겼습니다.",
        [reviews_section()]))
    out.append(sub_page("/contact/", "상담 신청", "손해사정사 무료 상담 신청",
        "받으신 통보서와 상황을 남겨주시면 약관 기준으로 먼저 검토해 연락드립니다.",
        "손해사정사 무료 상담 신청 | 박성일 손해사정사",
        "진단비·후유장해·교통사고 보험금 삭감·면책 상담 신청. 상담 무료, 착수금 없는 후불 보수, 전국 상담. 전화·카카오톡·온라인 신청 모두 가능합니다.",
        [load("parts", "contact.html"), load("parts", "process.html"), load("parts", "faq.html")], cta=False))
    return out



# ---------------------------------------------------------------- 개인정보 처리방침
# 푸터에서만 연결하고, 검색엔진에는 노출하지 않는다(noindex · 사이트맵 제외).
PRIVACY_HTML = '''<p>박성일 손해사정사(이하 "본 사이트")는 상담 신청과 광고 운영 과정에서 필요한 최소한의 개인정보만 처리하며, 개인정보 보호법 등 관련 법령을 지킵니다.</p>
<h2>1. 처리하는 개인정보 항목</h2>
<ul>
<li><b>상담 신청</b> — 성함, 연락처, 상담 분야, 상담 내용 (상담 신청 폼에 직접 입력)</li>
<li><b>광고 클릭 기록</b> — 네이버 검색광고를 눌러 접속한 경우에 한해 접속 IP, 접속 일시, 검색어·광고 매체 정보, 브라우저 정보 (자동 수집)</li>
</ul>
<h2>2. 처리 목적</h2>
<ul>
<li>상담 접수와 회신, 상담 진행</li>
<li>광고 효과 측정, 무효·부정 클릭 확인과 차단</li>
</ul>
<h2>3. 보유 및 이용 기간</h2>
<ul>
<li><b>상담 신청 정보</b> — 상담 종료 후 3개월간 보관한 뒤 파기합니다.</li>
<li><b>광고 클릭 기록</b> — 수집일로부터 90일이 지나면 자동으로 삭제됩니다.</li>
</ul>
<h2>4. 처리 위탁 및 국외 이전</h2>
<p>원활한 서비스 운영을 위해 아래 업체에 처리를 위탁하며, 해당 업체의 서버가 국외에 있어 정보가 네트워크를 통해 국외로 전송됩니다.</p>
<ul>
<li><b>Formspree, Inc.</b> (미국) — 상담 신청 내용의 전송과 이메일 전달 · 이전 항목: 성함, 연락처, 상담 분야, 상담 내용 · 보유 기간: 위 3항의 기간</li>
<li><b>Cloudflare, Inc.</b> (미국 등) — 웹사이트 운영과 광고 클릭 기록 저장 · 이전 항목: 접속 IP, 접속 일시, 검색어·광고 매체 정보, 브라우저 정보 · 보유 기간: 90일</li>
</ul>
<p>국외 이전을 원하지 않으시면 상담 신청 폼 대신 전화나 카카오톡으로 상담하실 수 있습니다.</p>
<h2>5. 광고 성과 측정 도구</h2>
<p>본 사이트는 광고 성과를 확인하기 위해 네이버 광고 전환 추적 등 측정 도구를 사용할 수 있으며, 이 과정에서 쿠키가 사용될 수 있습니다. 브라우저 설정에서 쿠키 저장을 거부하실 수 있고, 이 경우에도 사이트 이용과 상담에는 지장이 없습니다.</p>
<h2>6. 제3자 제공</h2>
<p>본 사이트는 정보주체의 동의가 있거나 법령에 근거가 있는 경우를 제외하고 개인정보를 제3자에게 제공하지 않습니다.</p>
<h2>7. 파기 방법</h2>
<p>보유 기간이 끝난 개인정보는 지체 없이 파기하며, 전자 파일은 복구할 수 없는 방법으로 삭제합니다.</p>
<h2>8. 정보주체의 권리</h2>
<p>언제든지 본인의 개인정보에 대해 열람, 정정, 삭제, 처리정지를 요구하실 수 있으며, 아래 연락처로 요청하시면 지체 없이 조치합니다.</p>
<h2>9. 개인정보 보호책임자</h2>
<ul>
<li>성명: 박성일 손해사정사</li>
<li>연락처: {tel} · {email}</li>
</ul>
<h2>10. 시행일</h2>
<p>이 개인정보 처리방침은 2026년 10월 1일부터 적용됩니다.</p>'''


def privacy_page():
    body = f'''<main><section class="listpage"><div class="wrap"><article class="article">
  <a class="back" href="/">← 홈으로</a>
  <h1>개인정보 처리방침</h1>
  <div class="body">{PRIVACY_HTML.format(tel=SITE["tel"], email=E(SITE["email"]))}</div>
</article></div></section></main>'''
    return page("/privacy/", "개인정보 처리방침 | %s" % SITE["name"],
                "박성일 손해사정사 홈페이지의 개인정보 처리방침입니다.", body, noindex=True)


# ---------------------------------------------------------------- 부가 파일
def extras(urls, ps):
    now = datetime.now(KST)
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemap.org/schemas/sitemap/0.9">'.replace("sitemap.org", "sitemaps.org")]
    # 네이버 원문을 canonical 로 지정한 사본 글은 사이트맵에서 뺀다.
    mirrored = {post_url(p) for p in ps if is_mirror(p)}
    for u in urls:
        if u in mirrored:
            continue
        pri = "1.0" if u == "/" else ("0.8" if u.startswith("/blog") and u.count("/") == 2 else "0.7")
        sm.append("<url><loc>%s%s</loc><lastmod>%s</lastmod><priority>%s</priority></url>"
                  % (DOMAIN, u, now.strftime("%Y-%m-%d"), pri))
    sm.append("</urlset>")
    write("sitemap.xml", "\n".join(sm))
    write("robots.txt", "User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n" % DOMAIN)
    items = []
    for p in ps[:30]:
        d = datetime.strptime(p["date"], "%Y-%m-%d").replace(tzinfo=KST)
        items.append("<item><title>%s</title><link>%s%s</link><guid>%s%s</guid>"
                     "<pubDate>%s</pubDate><description>%s</description></item>"
                     % (E(p["title"]), DOMAIN, post_url(p), DOMAIN, post_url(p),
                        d.strftime("%a, %d %b %Y %H:%M:%S +0900"), E(p["summary"])))
    write("rss.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel>'
          '<title>%s 손해사정 칼럼</title><link>%s/blog/</link>'
          '<description>손해사정 실무에서 정리한 보험금 지급 기준</description><language>ko</language>%s'
          '</channel></rss>' % (E(SITE["name"]), DOMAIN, "".join(items)))
    write("_headers", "/assets/*\n  Cache-Control: public, max-age=31536000, immutable\n")
    write("assets/favicon.svg",
          '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
          '<rect width="64" height="64" rx="12" fill="#1F3A5F"/>'
          '<text x="32" y="44" font-size="34" font-family="serif" font-weight="700" '
          'fill="#fff" text-anchor="middle">박</text></svg>')


def write(rel, text):
    dest = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w", encoding="utf-8") as f:
        f.write(text)


APP_JS = '''document.addEventListener('DOMContentLoaded',function(){
var AS={};try{var q=new URLSearchParams(location.search);
['n_media','n_query','n_rank','n_keyword','utm_source','utm_term'].forEach(function(k){if(q.get(k)){AS[k]=q.get(k);}});
if(Object.keys(AS).length){sessionStorage.setItem('adsrc',JSON.stringify(AS));}
else{AS=JSON.parse(sessionStorage.getItem('adsrc')||'{}');}}catch(e){}
var TL={};
function trk(kind){var n=Date.now();if(TL[kind]&&n-TL[kind]<10000){return;}TL[kind]=n;
try{if(window.wcs){var c={};c.cnv=wcs.cnv(kind==='kakao'?'5':'4','1');wcs_do(c);}}catch(e){}
if(window.gtag){gtag('event','generate_lead',{method:kind,ad_keyword:AS.n_query||AS.n_keyword||AS.utm_term||'(none)',
ad_media:AS.n_media||AS.utm_source||'(organic)',ad_rank:AS.n_rank||''});}}
document.addEventListener('click',function(e){var a=e.target.closest&&e.target.closest('a');if(!a){return;}
var h=a.getAttribute('href')||'';if(h.indexOf('tel:')===0){trk('phone');}
else if(h.indexOf('open.kakao.com')>-1){trk('kakao');}},true);
document.addEventListener('copy',function(){
if(/010[- .]?[0-9]{4}[- .]?[0-9]{4}/.test(String(window.getSelection()||''))){trk('phone_copy');}});
var mb=document.getElementById('menubtn'),mm=document.getElementById('mmenu'),
    mx=document.getElementById('mmclose');
if(mb&&mm){
  var open=function(){mm.hidden=false;document.body.style.overflow='hidden';
    mb.setAttribute('aria-expanded','true');};
  var close=function(){mm.hidden=true;document.body.style.overflow='';
    mb.setAttribute('aria-expanded','false');};
  mb.addEventListener('click',open);
  if(mx){mx.addEventListener('click',close);}
  mm.querySelectorAll('a').forEach(function(a){a.addEventListener('click',close);});
  document.addEventListener('keydown',function(e){if(e.key==='Escape'&&!mm.hidden){close();}});
}
var f=document.getElementById('cform');
if(f){var fm=document.getElementById('fmsg'),fb=document.getElementById('fbtn');
function say(t,ok){fm.textContent=t;fm.hidden=false;fm.className='formmsg'+(ok?' ok':' err');}
f.addEventListener('submit',function(e){e.preventDefault();var u=f.getAttribute('action');
if(!u){say('현재 온라인 접수 준비 중입니다. 전화(010-2754-1552)나 카카오톡으로 연락해 주세요.',false);return;}
fb.disabled=true;fb.textContent='접수 중…';
fetch(u,{method:'POST',body:new FormData(f),headers:{'Accept':'application/json'}}).then(function(r){
if(r.ok){f.reset();trk('form');say('상담 신청이 접수되었습니다. 확인 후 남겨주신 연락처로 연락드리겠습니다.',true);}
else{throw 0;}}).catch(function(){say('접수 중 문제가 생겼습니다. 번거로우시겠지만 전화(010-2754-1552)나 카카오톡으로 연락해 주세요.',false);})
.then(function(){fb.disabled=false;fb.textContent='상담 신청하기';});});}
document.querySelectorAll('.more-btn').forEach(function(b){b.addEventListener('click',function(){
document.getElementById(b.getAttribute('data-for')).classList.add('open');b.remove();});});
var lb=document.getElementById('lb'),lbi=lb.querySelector('img');
document.querySelectorAll('[data-full]').forEach(function(el){el.addEventListener('click',function(){
lbi.src=el.getAttribute('data-full');lb.classList.add('open');});});
lb.addEventListener('click',function(){lb.classList.remove('open');lbi.src='';});
document.addEventListener('keydown',function(e){if(e.key==='Escape'){lb.classList.remove('open');}});
});'''


APP_V = [""]


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    shutil.copytree(os.path.join(ROOT, "assets"), os.path.join(OUT, "assets"))
    write("assets/app.js", APP_JS)
    # 광고 클릭 기록 함수(functions/_middleware.js)는 페이지 요청에만 돌린다 (이미지·CSS 제외)
    write("_routes.json", json.dumps({"version": 1, "include": ["/*"],
          "exclude": ["/assets/*", "/sitemap.xml", "/rss.xml", "/robots.txt"]}))
    import hashlib
    APP_V[0] = "?v=" + hashlib.md5(APP_JS.encode()).hexdigest()[:8]
    ps = posts()
    urls = [home(ps)] + sub_pages()
    privacy_page()   # 사이트맵에는 넣지 않는다
    if ps:
        urls.append(blog_list_page(None))
        for i in range(len(CATS)):
            if any(p["cat"] == i for p in ps):
                urls.append(blog_list_page(i))
        for n, p in enumerate(ps):
            urls.append(post_page(p, ps[n + 1] if n + 1 < len(ps) else None, ps[n - 1] if n else None))
    extras(urls, ps)
    print("생성 완료: %d 페이지, 글 %d편 → public/" % (len(urls), len(ps)))


if __name__ == "__main__":
    main()
