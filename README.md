# 메이플 카카오봇 스킬 서버

넥슨 오픈API + 환산주스탯 + 카카오 i 오픈빌더 연동 스킬 서버

---

## 파일 구조

```
maple-kakao-bot/
├── main.py           ← 스킬 서버 메인 (FastAPI)
├── test_api.py       ← 로컬 API 테스트 스크립트
├── requirements.txt  ← 패키지 목록
├── render.yaml       ← Render.com 배포 설정
└── .env              ← API 키 (git에 올리지 말 것!)
```

---

## 1단계 — 넥슨 오픈API 키 발급

1. https://openapi.nexon.com 접속 → 로그인
2. 상단 `애플리케이션 > 애플리케이션 등록`
3. 이름 자유, 서비스 URL → 나중에 Render 주소로 교체 (일단 http://localhost 입력)
4. `메이플스토리` 체크 → 등록
5. 발급된 API 키를 `.env` 파일에 붙여넣기

```
NEXON_API_KEY=발급받은_키
```

---

## 2단계 — 로컬 테스트

```bash
# 패키지 설치
pip install -r requirements.txt

# API 동작 확인
python test_api.py

# 서버 실행
uvicorn main:app --reload --port 8000
```

서버 실행 후 http://localhost:8000/docs 에서 Swagger UI로 엔드포인트 확인 가능

---

## 3단계 — Render.com 무료 배포

1. https://render.com 가입 (GitHub 연동 권장)
2. GitHub에 이 폴더 업로드 (`.env`는 제외!)
3. Render → `New Web Service` → GitHub 레포 선택
4. 환경변수 `NEXON_API_KEY` 입력
5. 배포 완료 → `https://your-app.onrender.com` 주소 획득

---

## 4단계 — 카카오 i 오픈빌더 스킬 등록

https://i.kakao.com 접속 → 내 챗봇 → 스킬 관리

| 스킬 이름 | URL | 발화 예시 |
|-----------|-----|-----------|
| 캐릭터조회 | `https://your-app.onrender.com/character` | !캐릭터 으낭다 |
| 보스분석   | `https://your-app.onrender.com/boss`      | !보스 으낭다 |
| 스펙분석   | `https://your-app.onrender.com/spec`      | !스펙 으낭다 |
| 무릉도장   | `https://your-app.onrender.com/dojang`    | !무릉 으낭다 |
| 랭킹       | `https://your-app.onrender.com/ranking`   | !랭킹 |
| 도움말     | `https://your-app.onrender.com/help`      | !도움말 |

---

## 명령어 정리

| 명령어 | 설명 |
|--------|------|
| `!캐릭터 [닉네임]` | 레벨, 직업, 서버, 전투력 + 환산 링크 |
| `!보스 [닉네임]`   | 보스컷 / 보스세팅 최적화 / 주간정산 링크 |
| `!스펙 [닉네임]`   | 스펙업 순서 / 헥사코어 / 스타포스 효율 링크 |
| `!무릉 [닉네임]`   | 무릉도장 최고 기록 |
| `!랭킹 [닉네임]`   | 환산 랭킹 / 유니온 챔피언 링크 |
| `!도움말`          | 명령어 전체 안내 |

---

## 주의사항

- `.env` 파일은 절대 GitHub에 올리지 마세요 (`.gitignore`에 추가)
- 넥슨 오픈API는 캐릭터 데이터가 **하루 단위**로 갱신됩니다
- Render 무료 플랜은 15분 미사용 시 슬립 모드 → 첫 응답이 30초 걸릴 수 있음
  (유료 플랜 또는 UptimeRobot으로 핑 유지 가능)
