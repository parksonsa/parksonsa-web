// 네이버 광고 클릭 기록 (부정클릭 확인용)
//
// 광고로 들어온 접속(n_media / n_query / NaPm 파라미터, 또는 네이버 광고 리퍼러)만
// 클릭 시각·IP·키워드를 Cloudflare KV(ADLOG)에 90일간 남긴다.
// ADLOG 가 연결 안 돼 있으면 아무 일도 하지 않고, 어떤 오류가 나도 사이트는 정상 표시된다.
//
// 내려받기: https://parksonsa.com/adlog-export?key=<ADLOG_KEY>&days=30  → CSV

const AD_PARAMS = ['n_media', 'n_query', 'n_keyword', 'n_rank', 'NaPm'];
const KEEP_SECONDS = 60 * 60 * 24 * 90;

export async function onRequest(context) {
  const { request, env } = context;
  const url = new URL(request.url);

  if (url.pathname === '/adlog-export') return exportLog(url, env);

  try {
    if (env.ADLOG && request.method === 'GET') {
      const ref = request.headers.get('Referer') || '';
      const isAd = AD_PARAMS.some((k) => url.searchParams.has(k)) ||
        /adcr\.naver\.com|ad\.search\.naver\.com/.test(ref);
      if (isAd) {
        const now = new Date();
        const rec = {
          t: now.toISOString(),
          ip: request.headers.get('CF-Connecting-IP') || '',
          kw: url.searchParams.get('n_query') || url.searchParams.get('n_keyword') || '',
          rank: url.searchParams.get('n_rank') || '',
          media: url.searchParams.get('n_media') || '',
          url: (url.pathname + url.search).slice(0, 300),
          ua: (request.headers.get('User-Agent') || '').slice(0, 300),
          cc: (request.cf && request.cf.country) || '',
        };
        const key = 'c:' + rec.t + ':' + Math.random().toString(36).slice(2, 8);
        // 내용은 metadata 에 넣어 목록 조회 한 번으로 내려받을 수 있게 한다
        context.waitUntil(env.ADLOG.put(key, '', { metadata: rec, expirationTtl: KEEP_SECONDS }));
      }
    }
  } catch (e) {
    // 기록 실패는 무시 (사이트 표시가 우선)
  }
  return context.next();
}

async function exportLog(url, env) {
  if (!env.ADLOG || !env.ADLOG_KEY || url.searchParams.get('key') !== env.ADLOG_KEY) {
    return new Response('Not found', { status: 404 });
  }
  const days = Math.min(parseInt(url.searchParams.get('days') || '30', 10) || 30, 90);
  const since = new Date(Date.now() - days * 864e5).toISOString();

  const rows = [];
  let cursor;
  do {
    const page = await env.ADLOG.list({ prefix: 'c:', cursor });
    for (const k of page.keys) {
      if (k.metadata && k.metadata.t >= since) rows.push(k.metadata);
    }
    cursor = page.list_complete ? undefined : page.cursor;
  } while (cursor);

  const kst = (iso) => new Date(new Date(iso).getTime() + 9 * 3600e3).toISOString().slice(0, 19).replace('T', ' ');
  const q = (v) => '"' + String(v == null ? '' : v).replace(/"/g, '""') + '"';
  const lines = ['클릭일시,키워드,IP,URL,순위,매체,국가,UserAgent'];
  for (const r of rows) {
    lines.push([kst(r.t), r.kw, r.ip, r.url, r.rank, r.media, r.cc, r.ua].map(q).join(','));
  }
  return new Response('﻿' + lines.join('\r\n'), {
    headers: {
      'Content-Type': 'text/csv; charset=utf-8',
      'Content-Disposition': 'attachment; filename="adclicks.csv"',
      'Cache-Control': 'no-store',
      'X-Robots-Tag': 'noindex',
    },
  });
}
