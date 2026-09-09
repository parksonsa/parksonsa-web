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


def won(v):
    return f"{v:,}원"


def money_kr(v):
    eok, man = v // 100_000_000, (v % 100_000_000) // 10_000
    return f"{eok}억 {man:,}만 원" if eok else f"{man:,}만 원"


# ---------------------------------------------------------------- 공통 조각
KAKAO_SVG = ('<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">'
             '<path d="M12 3C6.5 3 2 6.6 2 11c0 2.8 1.9 5.3 4.7 6.7L5.8 21l4.3-2.7c.6.1 1.2.1 1.9.1 '
             '5.5 0 10-3.6 10-8S17.5 3 12 3z"/></svg>')

NAV = [("/#about", "소개"), ("/#credentials", "자격 · 면허"), ("/#payouts", "지급 내역"),
       ("/#reviews", "상담 후기"), ("/#services", "업무 분야"), ("/blog/", "공식 블로그"),
       ("/#faq", "자주 묻는 질문")]


def header():
    links = "".join('<a href="%s">%s</a>' % (u, t) for u, t in NAV)
    return f'''<header class="topbar">
  <div class="wrap">
    <a class="brand" href="/">{E(SITE["name"])} <small>{E(SITE["tagline"])}</small></a>
    <nav class="navlinks">{links}</nav>
    <div class="topbtns">
      <a class="topcall ghost" href="tel:{SITE["tel"]}">{SITE["tel"]}</a>
      <a class="topcall" href="/#contact">상담 신청</a>
    </div>
  </div>
</header>'''


def footer():
    blogs = "".join('<a href="%s" target="_blank" rel="noopener">블로그 · %s</a>'
                    % (b["url"], E(b["name"])) for b in SITE["blogs"])
    return f'''<footer>
  <div class="wrap">
    <div class="fbrand">{E(SITE["name"])}</div>
    <div class="frow"><span>{E(SITE["office"])}</span><span>상담문의 {SITE["tel"]}</span><span>전국 상담 가능</span></div>
    <div class="frow"><a href="{SITE["kakao"]}" target="_blank" rel="noopener">카카오톡 오픈채팅</a>{blogs}</div>
    <div class="fcopy">© {datetime.now(KST).year} {E(SITE["name"])}. 본 사이트의 지급 내역과 사례는 실제 처리 건을 식별정보 없이 정리한 것으로, 개별 사안의 결과를 보장하지 않습니다.</div>
  </div>
</footer>
<div class="stickybar">
  <a class="sb-call" href="tel:{SITE["tel"]}">전화상담</a>
  <a class="sb-kko" href="{SITE["kakao"]}" target="_blank" rel="noopener">{KAKAO_SVG}카톡상담</a>
</div>
<div class="lb" id="lb" role="dialog" aria-label="이미지 크게 보기"><button class="x" aria-label="닫기">×</button><img alt=""></div>
<script src="/assets/app.js" defer></script>'''


def page(path, title, desc, body, *, og_image=None, jsonld=None, published=None):
    """완성된 HTML 한 페이지를 public/ 아래에 쓴다."""
    canonical = DOMAIN + path
    img = og_image or (DOMAIN + "/assets/img/photo/hero.jpg")
    verify = ""
    if SITE.get("naver_verify"):
        verify += '\n<meta name="naver-site-verification" content="%s">' % SITE["naver_verify"]
    if SITE.get("google_verify"):
        verify += '\n<meta name="google-site-verification" content="%s">' % SITE["google_verify"]
    ld = '\n<script type="application/ld+json">%s</script>' % json.dumps(
        jsonld, ensure_ascii=False) if jsonld else ""
    pub = '\n<meta property="article:published_time" content="%s">' % published if published else ""
    doc = f'''<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{canonical}">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">{verify}
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
<link rel="stylesheet" href="/assets/style.css">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="alternate" type="application/rss+xml" title="{E(SITE["name"])} 공식 블로그" href="/rss.xml">{ld}
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
    <div class="grid g3">{''.join(cards)}</div>
    <p class="pay-note">위 금액은 공개한 내역서와 합의서에 적힌 지급액·합의금의 합계이며, 보험사가 지급을 결정하거나 당사자가 합의한 결과입니다. 사안마다 약관·가입 시점·의무기록이 다르므로 개별 사안의 결과를 보장하지 않습니다. 이미지를 누르면 크게 보실 수 있습니다.</p>
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
                     '<figcaption>%s<span class="wh">%s</span></figcaption></figure>'
                     % (stars, E(r["topic"]), text, E(r["who"]), E(r["when"])))
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
def posts():
    ps = jload("data", "posts.json")
    ps.sort(key=lambda p: p["date"], reverse=True)
    return ps


def post_url(p):
    return "/blog/%s/" % p["id"]


def post_card(p):
    thumb = ('<div class="pc-thumb"><img src="%s" alt="" loading="lazy"></div>' % p["image"]) if p.get("image") else ""
    return ('<a class="post-card" href="%s">%s<div class="pc-top"><span class="cat">%s</span>'
            '<span class="dt">%s</span></div><h3>%s</h3><p>%s</p></a>'
            % (post_url(p), thumb, E(CATS[p["cat"]]), p["date"].replace("-", "."),
               E(p["title"]), E(p["summary"])))


def blog_latest_section(ps):
    ex = any(p.get("example") for p in ps)
    note = ('<div class="note"><b>※ 아래 글은 화면 확인용 예시입니다.</b> 블로그 이관이 끝나면 실제 글 전체가 '
            '이 자리에 들어가고, 새 글은 매일 자동으로 추가됩니다.</div>') if ex else ""
    cards = "".join(post_card(p) for p in ps[:6])
    return f'''<section id="blog-latest">
  <div class="wrap">
    <div class="sec-head">
      <div class="eyebrow">공식 블로그</div>
      <h2>진단코드 하나, 장해율 1%가 갈리는 지점을 기록합니다.</h2>
      <p>보험사 심사 실무와 손해사정 현장에서 정리한 글입니다. 비슷한 진단명이나 통보를 받으셨다면 먼저 읽어보세요.</p>
    </div>
    {note}
    <div class="grid g3">{cards}</div>
    <div class="blog-more"><a class="btn btn-line" href="/blog/">전체 글 보기</a></div>
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
    <div class="blog-head"><div><div class="eyebrow">공식 블로그</div><h1>{E(heading)}</h1>
      <p>손해사정 실무에서 정리한 글을 분야별로 모았습니다.</p></div></div>
    {chips(cat)}
    {lst}
  </div>
</section></main>'''
    title = "%s | %s 공식 블로그" % (heading, SITE["name"])
    desc = "%s 관련 손해사정 실무 글 %d편. 약관 기준과 진단코드, 장해분류표 적용을 정리했습니다." % (heading, len(sel))
    return page(path, title, desc, body)


BODY_CTA = '''<div class="cta">
  <h3>비슷한 통보를 받으셨나요?</h3>
  <p>통보서와 진단서를 보내주시면 다시 청구할 여지가 있는지 먼저 말씀드립니다. 상담 단계에서는 비용이 없습니다.</p>
  <div class="row"><a class="btn btn-navy" href="tel:{tel}">전화 상담 {tel}</a>
  <a class="btn btn-kakao" href="{kakao}" target="_blank" rel="noopener">{svg}카카오톡 상담</a></div>
</div>'''


def post_page(p, prev, nxt):
    body_html = p.get("body") or (
        '<p>%s</p><div class="ph">이 자리에는 블로그 원문이 사진과 함께 그대로 들어갑니다.</div>' % E(p["summary"]))
    nav = '<div class="nav">'
    nav += ('<a href="%s"><small>이전 글</small>%s</a>' % (post_url(prev), E(prev["title"]))) if prev else "<span></span>"
    if nxt:
        nav += '<a href="%s" style="text-align:right"><small>다음 글</small>%s</a>' % (post_url(nxt), E(nxt["title"]))
    nav += "</div>"
    body = f'''<main><section class="listpage"><div class="wrap"><article class="article">
  <a class="back" href="/blog/">← 목록으로</a>
  <div class="meta"><span class="cat">{E(CATS[p["cat"]])}</span><span>{p["date"].replace("-", ".")}</span><span>{E(SITE["name"])}</span></div>
  <h1>{E(p["title"])}</h1>
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
          "mainEntityOfPage": DOMAIN + post_url(p),
          "articleSection": CATS[p["cat"]]}
    if img:
        ld["image"] = img
    return page(post_url(p), "%s | %s" % (p["title"], SITE["name"]), p["summary"],
                body, og_image=img, jsonld=ld, published=p["date"])


# ---------------------------------------------------------------- 메인
def home(ps):
    parts = [load("parts", "hero.html"),
             load("parts", "situations.html"),
             load("parts", "about.html"),
             load("parts", "credentials.html"),
             load("parts", "services.html"),
             payouts_section(),
             load("parts", "cases.html"),
             reviews_section(),
             blog_latest_section(ps),
             load("parts", "process.html"),
             load("parts", "faq.html"),
             load("parts", "contact.html")]
    body = "<main>%s</main>" % "\n".join(parts)
    if SITE.get("form_endpoint"):
        body = body.replace('<form id="cform">',
                            '<form id="cform" action="%s" method="POST">' % SITE["form_endpoint"])
    ld = {"@context": "https://schema.org", "@type": "ProfessionalService",
          "name": SITE["name"], "url": DOMAIN,
          "telephone": "+82-" + SITE["tel"].lstrip("0").replace("-", "-", 1),
          "areaServed": {"@type": "Country", "name": "대한민국"},
          "description": "보험사 심사 실무 출신 손해사정사. 질병·진단비, 상해·후유장해, 교통사고, 배상책임, 보험계약 분쟁의 삭감·면책 사유를 약관과 의무기록으로 재검토합니다.",
          "founder": {"@type": "Person", "name": "박성일", "jobTitle": "손해사정사",
                      "hasCredential": ["손해사정사(신체)", "임상병리사", "개인보험심사역"]},
          "image": DOMAIN + "/assets/img/photo/hero.jpg"}
    faq = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": []}
    for m in re.finditer(r'<summary>(.*?)</summary><div class="ans">(.*?)</div>',
                         load("parts", "faq.html"), re.S):
        faq["mainEntity"].append({"@type": "Question", "name": re.sub(r"<[^>]+>", "", m.group(1)).strip(),
                                  "acceptedAnswer": {"@type": "Answer",
                                                     "text": re.sub(r"<[^>]+>", "", m.group(2)).strip()}})
    return page("/", "박성일 손해사정사 | 보험금 삭감·면책 재검토, 전국 상담",
                "보험사 심사 실무 출신 손해사정사가 약관과 의무기록을 기준으로 삭감·면책 사유를 처음부터 다시 검토합니다. 상담 무료, 착수금 없는 후불 보수, 전국 상담.",
                body, jsonld=[ld, faq])


# ---------------------------------------------------------------- 부가 파일
def extras(urls, ps):
    now = datetime.now(KST)
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemap.org/schemas/sitemap/0.9">'.replace("sitemap.org", "sitemaps.org")]
    for u in urls:
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
          '<title>%s 공식 블로그</title><link>%s/blog/</link>'
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
var f=document.getElementById('cform');
if(f&&!f.getAttribute('action')){f.addEventListener('submit',function(e){e.preventDefault();
document.getElementById('fmsg').hidden=false;});}
var lb=document.getElementById('lb'),lbi=lb.querySelector('img');
document.querySelectorAll('[data-full]').forEach(function(el){el.addEventListener('click',function(){
lbi.src=el.getAttribute('data-full');lb.classList.add('open');});});
lb.addEventListener('click',function(){lb.classList.remove('open');lbi.src='';});
document.addEventListener('keydown',function(e){if(e.key==='Escape'){lb.classList.remove('open');}});
});'''


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    shutil.copytree(os.path.join(ROOT, "assets"), os.path.join(OUT, "assets"))
    write("assets/app.js", APP_JS)
    ps = posts()
    urls = [home(ps), blog_list_page(None)]
    for i in range(len(CATS)):
        urls.append(blog_list_page(i))
    for n, p in enumerate(ps):
        urls.append(post_page(p, ps[n + 1] if n + 1 < len(ps) else None, ps[n - 1] if n else None))
    extras(urls, ps)
    print("생성 완료: %d 페이지, 글 %d편 → public/" % (len(urls), len(ps)))


if __name__ == "__main__":
    main()
