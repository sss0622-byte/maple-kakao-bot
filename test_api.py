"""
로컬에서 스킬 서버 없이 넥슨 API 응답을 빠르게 확인하는 테스트 스크립트
실행: python test_api.py
"""

import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

NEXON_API_KEY = os.getenv("NEXON_API_KEY", "")
NEXON_BASE    = "https://open.api.nexon.com/maplestory/v1"
HEADERS       = {"x-nxopen-api-key": NEXON_API_KEY}


async def test_character(char_name: str):
    print(f"\n{'='*40}")
    print(f"테스트 캐릭터: {char_name}")
    print('='*40)

    async with httpx.AsyncClient(timeout=10) as client:

        # 1) ocid 조회
        r = await client.get(
            f"{NEXON_BASE}/id",
            params={"character_name": char_name},
            headers=HEADERS,
        )
        print(f"\n[1] OCID 조회 ({r.status_code})")
        if r.status_code != 200:
            print(f"  오류: {r.text}")
            return
        ocid = r.json()["ocid"]
        print(f"  ocid: {ocid[:20]}...")

        # 2) 기본 정보
        r = await client.get(
            f"{NEXON_BASE}/character/basic",
            params={"ocid": ocid},
            headers=HEADERS,
        )
        print(f"\n[2] 기본 정보 ({r.status_code})")
        if r.status_code == 200:
            d = r.json()
            print(f"  이름  : {d.get('character_name')}")
            print(f"  레벨  : {d.get('character_level')}")
            print(f"  직업  : {d.get('character_class')}")
            print(f"  서버  : {d.get('world_name')}")
            print(f"  길드  : {d.get('character_guild_name')}")
        else:
            print(f"  오류: {r.text}")

        # 3) 스탯 (전투력)
        r = await client.get(
            f"{NEXON_BASE}/character/stat",
            params={"ocid": ocid},
            headers=HEADERS,
        )
        print(f"\n[3] 스탯 ({r.status_code})")
        if r.status_code == 200:
            for s in r.json().get("final_stat", []):
                if s["stat_name"] == "전투력":
                    val = int(float(s["stat_value"]))
                    print(f"  전투력: {val:,}")
                    break
        else:
            print(f"  오류: {r.text}")

        # 4) 무릉도장
        r = await client.get(
            f"{NEXON_BASE}/character/dojang",
            params={"ocid": ocid},
            headers=HEADERS,
        )
        print(f"\n[4] 무릉도장 ({r.status_code})")
        if r.status_code == 200:
            d = r.json()
            print(f"  최고층: {d.get('dojang_best_floor')}층")
            print(f"  기록  : {d.get('dojang_best_time_record')}초")
        else:
            print(f"  오류: {r.text}")

    print(f"\n환산주스탯 링크: https://maplescouter.com/result?name={char_name}")


if __name__ == "__main__":
    char = input("테스트할 캐릭터 닉네임 입력: ").strip()
    if not char:
        char = "으낭다"  # 기본 테스트 캐릭터
    asyncio.run(test_character(char))
