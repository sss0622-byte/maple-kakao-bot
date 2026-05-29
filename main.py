"""
메이플스토리 카카오 챗봇 스킬 서버
넥슨 오픈API + 카카오 i 오픈빌더 연동
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="메이플 카카오봇 스킬서버")

# ─────────────────────────────────────────
# 설정
# ─────────────────────────────────────────
NEXON_API_KEY = os.getenv("NEXON_API_KEY", "여기에_넥슨_API_키_입력")
NEXON_BASE    = "https://open.api.nexon.com/maplestory/v1"
HEADERS       = {"x-nxopen-api-key": NEXON_API_KEY}

SCOUTER_BASE  = "https://maplescouter.com"


# ─────────────────────────────────────────
# 넥슨 API 헬퍼
# ─────────────────────────────────────────
async def get_ocid(character_name: str) -> str | None:
    """캐릭터 이름 → ocid (고유 식별자) 변환"""
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"{NEXON_BASE}/id",
            params={"character_name": character_name},
            headers=HEADERS,
        )
        if r.status_code != 200:
            return None
        return r.json().get("ocid")


async def get_character_basic(ocid: str) -> dict | None:
    """기본 캐릭터 정보 조회"""
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"{NEXON_BASE}/character/basic",
            params={"ocid": ocid},
            headers=HEADERS,
        )
        if r.status_code != 200:
            return None
        return r.json()


async def get_character_stat(ocid: str) -> dict | None:
    """캐릭터 전투력 / 스탯 조회"""
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"{NEXON_BASE}/character/stat",
            params={"ocid": ocid},
            headers=HEADERS,
        )
        if r.status_code != 200:
            return None
        return r.json()


async def get_dojang(ocid: str) -> dict | None:
    """무릉도장 최고 기록 조회"""
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"{NEXON_BASE}/character/dojang",
            params={"ocid": ocid},
            headers=HEADERS,
        )
        if r.status_code != 200:
            return None
        return r.json()


# ─────────────────────────────────────────
# 카카오 응답 빌더
# ─────────────────────────────────────────
def simple_text(text: str) -> dict:
    return {
        "version": "2.0",
        "template": {"outputs": [{"simpleText": {"text": text}}]},
    }


def basic_card(title: str, description: str, buttons: list[dict]) -> dict:
    return {
        "version": "2.0",
        "template": {
            "outputs": [{
                "basicCard": {
                    "title": title,
                    "description": description,
                    "buttons": buttons,
                }
            }]
        },
    }


def list_card(header: str, items: list[dict], buttons: list[dict] | None = None) -> dict:
    card = {"header": {"title": header}, "items": items}
    if buttons:
        card["buttons"] = buttons
    return {
        "version": "2.0",
        "template": {"outputs": [{"listCard": card}]},
    }


def link_button(label: str, url: str) -> dict:
    return {"action": "webLink", "label": label, "webLinkUrl": url}


# ─────────────────────────────────────────
# 발화 파싱 헬퍼
# ─────────────────────────────────────────
def parse_name(utterance: str, prefix: str) -> str:
    """'!캐릭터 으낭다' → '으낭다'"""
    return utterance.replace(prefix, "").strip()


def get_utterance(body: dict) -> str:
    return body.get("userRequest", {}).get("utterance", "").strip()


# ─────────────────────────────────────────
# 라우터: 캐릭터 기본 정보 조회
# ─────────────────────────────────────────
@app.post("/character")
async def character_info(req: Request):
    """
    발화 예: !캐릭터 으낭다
    → 레벨, 직업, 서버 + 환산주스탯 링크 반환
    """
    body = await req.json()
    utterance = get_utterance(body)
    char_name = parse_name(utterance, "!캐릭터")

    if not char_name:
        return JSONResponse(simple_text("캐릭터 이름을 입력해주세요!\n예) !캐릭터 으낭다"))

    ocid = await get_ocid(char_name)
    if not ocid:
        return JSONResponse(simple_text(f"'{char_name}' 캐릭터를 찾을 수 없어요 😢\n닉네임 대소문자를 확인해주세요!"))

    info = await get_character_basic(ocid)
    stat = await get_character_stat(ocid)
    if not info:
        return JSONResponse(simple_text("캐릭터 정보를 불러오지 못했어요. 잠시 후 다시 시도해주세요."))

    name      = info.get("character_name", char_name)
    level     = info.get("character_level", "?")
    job       = info.get("character_class", "?")
    world     = info.get("world_name", "?")
    guild     = info.get("character_guild_name") or "없음"
    img_url   = info.get("character_image", "")

    # 전투력 파싱
    combat_power = "?"
    if stat:
        for s in stat.get("final_stat", []):
            if s.get("stat_name") == "전투력":
                combat_power = f"{int(float(s['stat_value'])):,}"
                break

    desc = (
        f"🌏 서버: {world}\n"
        f"⚔️ 직업: {job}\n"
        f"📊 레벨: {level}\n"
        f"💥 전투력: {combat_power}\n"
        f"🏰 길드: {guild}"
    )

    buttons = [
        link_button("환산주스탯 보기",   f"{SCOUTER_BASE}/result?name={name}"),
        link_button("보스컷 분석",       f"{SCOUTER_BASE}/optimizer?name={name}"),
        link_button("스펙업 순서",       f"{SCOUTER_BASE}/spec-order?name={name}"),
    ]

    return JSONResponse(basic_card(f"🍁 {name}", desc, buttons))


# ─────────────────────────────────────────
# 라우터: 보스컷 / 보스 최적화
# ─────────────────────────────────────────
@app.post("/boss")
async def boss_info(req: Request):
    """
    발화 예: !보스 으낭다
    → 환산주스탯 보스컷 + 보스세팅 최적화 링크
    """
    body = await req.json()
    utterance = get_utterance(body)
    char_name = parse_name(utterance, "!보스")

    if not char_name:
        return JSONResponse(simple_text("캐릭터 이름을 입력해주세요!\n예) !보스 으낭다"))

    # 캐릭터 존재 여부만 확인
    ocid = await get_ocid(char_name)
    if not ocid:
        return JSONResponse(simple_text(f"'{char_name}' 캐릭터를 찾을 수 없어요 😢"))

    items = [
        {"title": "📊 효율·보스컷 분석",    "description": "내 환산 기준 보스 입장 가능 여부",
         "action": "webLink", "webLinkUrl": f"{SCOUTER_BASE}/result?name={char_name}"},
        {"title": "🎯 보스세팅 최적화",      "description": "주간 보스 최적 선택 추천",
         "action": "webLink", "webLinkUrl": f"{SCOUTER_BASE}/optimizer?name={char_name}"},
        {"title": "💰 주간 보스 정산",        "description": "결정석 수익 계산",
         "action": "webLink", "webLinkUrl": f"{SCOUTER_BASE}/boss-income?name={char_name}"},
        {"title": "👥 파티 보스컷",           "description": "파티원 합산 보스컷 확인",
         "action": "webLink", "webLinkUrl": f"{SCOUTER_BASE}/multi-result"},
    ]

    return JSONResponse(list_card(f"🍁 {char_name} — 보스 분석", items))


# ─────────────────────────────────────────
# 라우터: 스펙업 / 효율 분석
# ─────────────────────────────────────────
@app.post("/spec")
async def spec_info(req: Request):
    """
    발화 예: !스펙 으낭다
    → 스펙업 순서 / 헥사코어 / 아이템 효율 링크
    """
    body = await req.json()
    utterance = get_utterance(body)
    char_name = parse_name(utterance, "!스펙")

    if not char_name:
        return JSONResponse(simple_text("캐릭터 이름을 입력해주세요!\n예) !스펙 으낭다"))

    ocid = await get_ocid(char_name)
    if not ocid:
        return JSONResponse(simple_text(f"'{char_name}' 캐릭터를 찾을 수 없어요 😢"))

    items = [
        {"title": "📈 스펙업 순서",          "description": "투자 우선순위 추천",
         "action": "webLink", "webLinkUrl": f"{SCOUTER_BASE}/spec-order?name={char_name}"},
        {"title": "🔷 헥사코어 순서",         "description": "6차 코어 강화 순서 분석",
         "action": "webLink", "webLinkUrl": f"{SCOUTER_BASE}/hexa?name={char_name}"},
        {"title": "⭐ 스타포스 효율",          "description": "강화 단계별 효율 분석",
         "action": "webLink", "webLinkUrl": f"{SCOUTER_BASE}/starforce?name={char_name}"},
        {"title": "💎 잠재·추가옵션 효율",     "description": "큐브 세팅 효율 분석",
         "action": "webLink", "webLinkUrl": f"{SCOUTER_BASE}/cube-fire?name={char_name}"},
        {"title": "🗺️ 사냥컷 분석",           "description": "사냥터별 원킬컷 확인",
         "action": "webLink", "webLinkUrl": f"{SCOUTER_BASE}/huntresult?name={char_name}"},
    ]

    return JSONResponse(list_card(f"🍁 {char_name} — 스펙 분석", items))


# ─────────────────────────────────────────
# 라우터: 무릉도장
# ─────────────────────────────────────────
@app.post("/dojang")
async def dojang_info(req: Request):
    """
    발화 예: !무릉 으낭다
    → 무릉도장 최고 기록
    """
    body = await req.json()
    utterance = get_utterance(body)
    char_name = parse_name(utterance, "!무릉")

    if not char_name:
        return JSONResponse(simple_text("캐릭터 이름을 입력해주세요!\n예) !무릉 으낭다"))

    ocid = await get_ocid(char_name)
    if not ocid:
        return JSONResponse(simple_text(f"'{char_name}' 캐릭터를 찾을 수 없어요 😢"))

    data = await get_dojang(ocid)
    if not data:
        return JSONResponse(simple_text("무릉도장 기록을 불러오지 못했어요."))

    best_floor  = data.get("dojang_best_floor", "기록 없음")
    best_time   = data.get("dojang_best_time_record", "")
    time_str    = f"\n⏱ 기록: {best_time}초" if best_time else ""

    desc = f"🏆 최고 기록: {best_floor}층{time_str}"

    buttons = [link_button("무릉 랭킹 보기", f"{SCOUTER_BASE}/result?name={char_name}")]
    return JSONResponse(basic_card(f"🍁 {char_name} — 무릉도장", desc, buttons))


# ─────────────────────────────────────────
# 라우터: 랭킹 조회
# ─────────────────────────────────────────
@app.post("/ranking")
async def ranking_info(req: Request):
    """
    발화 예: !랭킹 으낭다
    → 환산 랭킹 / 아이템 랭킹 링크
    """
    body = await req.json()
    utterance = get_utterance(body)
    char_name = parse_name(utterance, "!랭킹")

    items = [
        {"title": "🏅 헥사 환산 랭킹",       "description": "전 서버 환산 순위",
         "action": "webLink", "webLinkUrl": f"{SCOUTER_BASE}/total-ranking"},
        {"title": "🔍 내 캐릭터 환산",        "description": f"{char_name or '캐릭터명 입력'}의 환산 확인",
         "action": "webLink",
         "webLinkUrl": f"{SCOUTER_BASE}/result?name={char_name}" if char_name else SCOUTER_BASE},
        {"title": "👑 유니온 챔피언 랭킹",    "description": "유니온 챔피언 전 서버 순위",
         "action": "webLink", "webLinkUrl": f"{SCOUTER_BASE}/union-ranking"},
        {"title": "🎒 아이템 랭킹",           "description": "장비 아이템 보유 현황",
         "action": "webLink", "webLinkUrl": f"{SCOUTER_BASE}/item-ranking"},
    ]

    return JSONResponse(list_card("🍁 환산주스탯 랭킹", items))


# ─────────────────────────────────────────
# 라우터: 도움말
# ─────────────────────────────────────────
@app.post("/help")
async def help_info(req: Request):
    text = (
        "📖 사용 가능한 명령어\n"
        "━━━━━━━━━━━━━━\n"
        "👤 캐릭터 정보\n"
        "  !캐릭터 [닉네임]\n\n"
        "⚔️ 보스 분석\n"
        "  !보스 [닉네임]\n\n"
        "📈 스펙 분석\n"
        "  !스펙 [닉네임]\n\n"
        "🏯 무릉도장\n"
        "  !무릉 [닉네임]\n\n"
        "🏅 랭킹\n"
        "  !랭킹 [닉네임]\n"
        "━━━━━━━━━━━━━━\n"
        "💡 예시: !캐릭터 으낭다\n"
        "⚠️ 닉네임 대소문자 정확히 입력!"
    )
    return JSONResponse(simple_text(text))


# ─────────────────────────────────────────
# 헬스체크
# ─────────────────────────────────────────
@app.get("/")
async def root():
    return {"status": "ok", "service": "메이플 카카오봇 스킬서버"}
