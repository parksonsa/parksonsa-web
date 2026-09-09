# parksonsa.com — 박성일 손해사정사 홈페이지

## 폴더가 하는 일

| 폴더 | 내용 |
|---|---|
| `public/` | **실제로 인터넷에 올라가는 완성된 사이트.** Cloudflare Pages가 이 폴더만 봅니다. |
| `data/` | 사이트 설정(`site.json`), 지급 내역(`payouts.json`), 상담 후기(`reviews.json`), 블로그 글(`posts.json`) |
| `parts/` | 메인 페이지 각 섹션의 내용 |
| `assets/` | 사진·자격증·지급내역서 이미지, 공통 스타일 |
| `scripts/build.py` | `data` + `parts` → `public` 생성 |
| `scripts/sync_naver.py` | 네이버 블로그 글을 가져와 `data/posts.json` 에 저장 |
| `.github/workflows/sync.yml` | 매일 새벽 5시(한국시간) 자동으로 새 글 가져오고 사이트 다시 생성 |

## 설치 순서

### 1. GitHub 저장소 만들기
1. github.com → 우측 상단 **+** → **New repository**
2. Repository name: `parksonsa-web`, **Public**, 나머지 체크 안 함 → **Create repository**
3. 다음 화면에서 **uploading an existing file** 클릭
4. 압축을 푼 폴더 안의 **내용물 전체**를 드래그해서 올림 (폴더째 말고 안에 있는 것들)
5. 아래 **Commit changes** 클릭

> `.github` 폴더가 안 올라가면, 올린 뒤 **Add file → Create new file** 로
> `.github/workflows/sync.yml` 경로를 직접 입력하고 내용을 붙여넣으면 됩니다.

### 2. Cloudflare Pages 연결
1. Cloudflare 로그인 → 왼쪽 **Compute (Workers & Pages)** → **Create** → **Pages** 탭 → **Connect to Git**
2. GitHub 계정 연결 승인 → `parksonsa-web` 선택 → **Begin setup**
3. 설정값
   - Framework preset: **None**
   - Build command: **비워둠**
   - Build output directory: **`public`**
4. **Save and Deploy** → 1~2분 뒤 `parksonsa-web.pages.dev` 로 사이트가 뜹니다

### 3. 도메인 연결
1. Cloudflare 왼쪽 **Add a domain** → `parksonsa.com` 입력 → **Free** 요금제 선택
2. Cloudflare가 알려주는 **네임서버 2개**를 적어둠 (`xxx.ns.cloudflare.com` 형태)
3. 가비아 → My가비아 → 도메인 → **네임서버 설정** → "타사 네임서버 사용" → 위 2개 입력 → 저장
4. 10분~2시간 뒤 Cloudflare에 `Active` 표시
5. Cloudflare → Workers & Pages → `parksonsa-web` → **Custom domains** → **Set up a custom domain**
   → `parksonsa.com` 추가, 한 번 더 `www.parksonsa.com` 추가

### 4. 블로그 글 전체 가져오기 (최초 1회)
GitHub 저장소 → **Actions** 탭 → 왼쪽 "블로그 동기화 및 사이트 생성"
→ **Run workflow** → 가져올 범위 **all** → 실행. 글 수에 따라 10~40분 걸립니다.

이후에는 매일 새벽 5시에 새 글만 자동으로 붙습니다.

### 5. 검색엔진 등록
- **네이버 서치어드바이저** searchadvisor.naver.com → 사이트 등록 → 소유확인
  → 나오는 인증 문자열을 `data/site.json` 의 `naver_verify` 에 넣고 저장
  → 확인 완료 후 `sitemap.xml` 과 `rss.xml` 제출
- **구글 서치콘솔** search.google.com/search-console → 같은 방식, `google_verify` 에 입력

### 6. 상담 폼 연결
formspree.io 무료 가입 → 새 form 만들기 → 받은 주소(`https://formspree.io/f/xxxx`)를
`data/site.json` 의 `form_endpoint` 에 넣고 저장하면 폼 제출이 이메일로 옵니다.

## 내용 수정하는 법

`data/site.json` 이나 `parts/*.html` 을 GitHub 화면에서 고치고 **Commit** 하면,
자동으로 사이트가 다시 만들어져 몇 분 안에 반영됩니다.

내 컴퓨터에서 미리 보려면:

```bash
python3 scripts/build.py
cd public && python3 -m http.server 8000   # http://localhost:8000
```

## 주의

- `public/` 은 자동으로 만들어지는 폴더입니다. 직접 고치지 마세요 (다음 실행 때 지워집니다).
- 상담 후기를 더하거나 빼려면 `data/reviews.json` 의 `items` 를 고치면 됩니다. 후기는 고객이 쓴 그대로만 넣습니다.
- 글을 홈페이지에서 빼고 싶으면 `data/posts.json` 에서 해당 글 항목을 지우면 됩니다.
- 지역 키워드(부산·울산·대구·창원 등)가 제목에 있는 글은 자동으로 제외됩니다.
- 가져온 글 중 "판례·승소·무조건" 같은 표현이 있으면 동기화 로그에 ⚠ 로 표시됩니다. 확인 후 다듬으세요.
