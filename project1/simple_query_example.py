#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
간단한 API 쿼리 예제

FastAPI 서버에서 레시피 데이터를 가져오는 간단한 예제들
+ 특정 쿼리 조건들을 테스트하는 함수들 추가
"""

import asyncio
import aiohttp
import json
import re

BASE_URL = "http://localhost:8000"

async def simple_query_examples():
    """간단한 쿼리 예제들"""

    print("FastAPI 레시피 데이터 쿼리 예제")
    print("=" * 50)

    async with aiohttp.ClientSession() as session:

        # 1. 모든 레시피 가져오기 (첫 5개만)
        print("\n1. 전체 레시피 목록 (첫 5개)")
        async with session.get(f"{BASE_URL}/recipes/") as response:
            if response.status == 200:
                recipes = await response.json()
                print(f"   총 {len(recipes)}개 레시피 중 첫 5개:")
                for recipe in recipes[:5]:
                    print(f"   - ID {recipe['id']}: {recipe['rcp_nm']}")
            else:
                print(f"   오류: {response.status}")

        # 2. 특정 레시피 상세 조회
        print("\n2. ID=1 레시피 상세 정보")
        async with session.get(f"{BASE_URL}/recipes/1") as response:
            if response.status == 200:
                recipe = await response.json()
                print(f"   레시피명: {recipe['rcp_nm']}")
                print(f"   요리방법: {recipe['rcp_way2']}")
                print(f"   종류: {recipe['rcp_pat2']}")
                print(f"   칼로리: {recipe['info_eng']}kcal")
                print(f"   재료: {recipe['rcp_parts_dtls'][:100]}...")
            else:
                print(f"   오류: {response.status}")

        # 3. 영양 정보 분석
        print("\n3. 영양 정보 통계")
        async with session.get(f"{BASE_URL}/recipes/") as response:
            if response.status == 200:
                recipes = await response.json()

                calories = [r['info_eng'] for r in recipes]
                carbs = [r['info_car'] for r in recipes]
                proteins = [r['info_pro'] for r in recipes]

                print(f"   평균 칼로리: {sum(calories)/len(calories):.1f}kcal")
                print(f"   평균 탄수화물: {sum(carbs)/len(carbs):.1f}g")
                print(f"   평균 단백질: {sum(proteins)/len(proteins):.1f}g")

                print(f"   최고 칼로리 레시피: {max(recipes, key=lambda x: x['info_eng'])['rcp_nm']} ({max(calories)}kcal)")
                print(f"   최저 칼로리 레시피: {min(recipes, key=lambda x: x['info_eng'])['rcp_nm']} ({min(calories)}kcal)")

async def custom_search():
    """사용자 정의 검색"""

    print("\n4. 맞춤 검색")

    # 여기서 원하는 검색 조건을 설정할 수 있습니다
    search_keyword = "김치"  # 이 값을 원하는 키워드로 변경
    calorie_limit = 300      # 이 값을 원하는 칼로리 제한으로 변경

    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_URL}/recipes/") as response:
            if response.status == 200:
                recipes = await response.json()

                # 키워드가 포함된 저칼로리 레시피 찾기
                filtered_recipes = [
                    recipe for recipe in recipes
                    if search_keyword in recipe['rcp_nm'] and recipe['info_eng'] <= calorie_limit
                ]

                print(f"   '{search_keyword}' 키워드, {calorie_limit}kcal 이하 레시피:")
                for recipe in filtered_recipes[:5]:  # 상위 5개만
                    print(f"   - {recipe['rcp_nm']} ({recipe['info_eng']}kcal)")

async def test_specific_queries():
    """제공된 쿼리 조건들을 테스트하는 함수"""

    print("\n" + "=" * 60)
    print("제공된 쿼리 조건 테스트")
    print("=" * 60)

    async with aiohttp.ClientSession() as session:
        # 모든 레시피 데이터 가져오기
        async with session.get(f"{BASE_URL}/recipes/") as response:
            if response.status != 200:
                print("레시피 데이터를 가져올 수 없습니다.")
                return

            recipes = await response.json()

        # 1. 단백질이 20g 이상이고 열량이 300kcal 이하인 볶음 요리를 찾아줘
        print("\n1. 단백질 20g 이상, 열량 300kcal 이하인 볶음 요리:")
        print("   SQL: SELECT RCP_NM, INFO_PRO, INFO_ENG, RCP_WAY2 FROM recipes WHERE INFO_PRO >= 20 AND INFO_ENG <= 300 AND RCP_WAY2 = '볶기';")
        query1_results = [
            r for r in recipes
            if r['info_pro'] >= 20 and r['info_eng'] <= 300 and r['rcp_way2'] == '볶기'
        ]
        print(f"   찾은 레시피: {len(query1_results)}개")
        for recipe in query1_results[:3]:
            print(f"   - {recipe['rcp_nm']} (단백질: {recipe['info_pro']}g, 칼로리: {recipe['info_eng']}kcal)")

        # 2. 양파와 당근이 들어가는 국&찌개 요리 알려줘
        print("\n2. 양파와 당근이 들어가는 국&찌개 요리:")
        print("   SQL: SELECT r.RCP_NM, r.RCP_PAT2 FROM recipes r WHERE r.RCP_PAT2 = '국&찌개' AND r.RCP_PARTS_DTLS LIKE '%양파%' AND r.RCP_PARTS_DTLS LIKE '%당근%';")
        query2_results = []
        for r in recipes:
            if r['rcp_pat2'] == '국&찌개':
                ingredients_text = r['rcp_parts_dtls'].lower()
                if '양파' in ingredients_text and '당근' in ingredients_text:
                    query2_results.append(r)
        print(f"   찾은 레시피: {len(query2_results)}개")
        for recipe in query2_results[:3]:
            print(f"   - {recipe['rcp_nm']}")

        # 3. 소금이 3g 이하로 들어가는 반찬 메뉴 보여줘
        print("\n3. 소금이 들어가는 반찬 메뉴 (재료 정보 분석):")
        print("   SQL: SELECT r.RCP_NM FROM recipes r WHERE r.RCP_PAT2 = '반찬' AND r.RCP_PARTS_DTLS LIKE '%소금%';")
        query3_results = []
        for r in recipes:
            if r['rcp_pat2'] == '반찬' and '소금' in r['rcp_parts_dtls']:
                # 실제로는 JSON에서 소금의 양을 파싱해야 하지만 여기서는 단순히 포함 여부만 확인
                query3_results.append(r)
        print(f"   찾은 레시피: {len(query3_results)}개 (소금이 포함된 반찬)")
        for recipe in query3_results[:3]:
            print(f"   - {recipe['rcp_nm']}")

        # 4. 나트륨이 500mg 이하이고 저감 TIP이 있는 메뉴 보여줘
        print("\n4. 나트륨 500mg 이하, 저감 TIP이 있는 메뉴:")
        print("   SQL: SELECT RCP_NM, INFO_NA, RCP_NA_TIP FROM recipes WHERE INFO_NA <= 500 AND RCP_NA_TIP IS NOT NULL;")
        query4_results = [
            r for r in recipes
            if r['info_na'] <= 500 and r['rcp_na_tip'] is not None
        ]
        print(f"   찾은 레시피: {len(query4_results)}개")
        for recipe in query4_results[:3]:
            print(f"   - {recipe['rcp_nm']} (나트륨: {recipe['info_na']}mg)")

        # 5. 다진 마늘이 들어가는 볶음 요리 찾아줘
        print("\n5. 다진 마늘이 들어가는 볶음 요리:")
        print("   SQL: SELECT r.RCP_NM, r.RCP_WAY2 FROM recipes r WHERE r.RCP_WAY2 = '볶기' AND r.RCP_PARTS_DTLS LIKE '%다진 마늘%';")
        query5_results = []
        for r in recipes:
            if r['rcp_way2'] == '볶기' and '다진 마늘' in r['rcp_parts_dtls']:
                query5_results.append(r)
        print(f"   찾은 레시피: {len(query5_results)}개")
        for recipe in query5_results[:3]:
            print(f"   - {recipe['rcp_nm']}")

        # 6. 기본재료에 대파가 포함된 레시피 알려줘
        print("\n6. 기본재료에 대파가 포함된 레시피:")
        print("   SQL: SELECT r.RCP_NM FROM recipes r WHERE r.RCP_PARTS_DTLS LIKE '%기본재료%' AND r.RCP_PARTS_DTLS LIKE '%대파%';")
        query6_results = []
        for r in recipes:
            if '기본재료' in r['rcp_parts_dtls'] and '대파' in r['rcp_parts_dtls']:
                query6_results.append(r)
        print(f"   찾은 레시피: {len(query6_results)}개")
        for recipe in query6_results[:3]:
            print(f"   - {recipe['rcp_nm']}")

        # 7. 버터가 들어가고 열량이 500kcal 이하인 일품 요리 보여줘
        print("\n7. 버터가 들어가고 열량 500kcal 이하인 일품 요리:")
        print("   SQL: SELECT r.RCP_NM, r.INFO_ENG FROM recipes r WHERE r.RCP_PAT2 = '일품' AND r.INFO_ENG <= 500 AND r.RCP_PARTS_DTLS LIKE '%버터%';")
        query7_results = []
        for r in recipes:
            if (r['rcp_pat2'] == '일품' and r['info_eng'] <= 500 and
                '버터' in r['rcp_parts_dtls']):
                query7_results.append(r)
        print(f"   찾은 레시피: {len(query7_results)}개")
        for recipe in query7_results[:3]:
            print(f"   - {recipe['rcp_nm']} (칼로리: {recipe['info_eng']}kcal)")

        # 8. 고명으로 홍고추가 들어간 레시피 알려줘
        print("\n8. 고명으로 홍고추가 들어간 레시피:")
        print("   SQL: SELECT r.RCP_NM FROM recipes r WHERE r.RCP_PARTS_DTLS LIKE '%고명%' AND r.RCP_PARTS_DTLS LIKE '%홍고추%';")
        query8_results = []
        for r in recipes:
            if '고명' in r['rcp_parts_dtls'] and '홍고추' in r['rcp_parts_dtls']:
                query8_results.append(r)
        print(f"   찾은 레시피: {len(query8_results)}개")
        for recipe in query8_results[:3]:
            print(f"   - {recipe['rcp_nm']}")

        # 9. 열량이 가장 낮은 레시피 5개를 알려줘
        print("\n9. 열량이 가장 낮은 레시피 5개:")
        print("   SQL: SELECT RCP_NM, INFO_ENG FROM recipes ORDER BY INFO_ENG ASC LIMIT 5;")
        lowest_cal_recipes = sorted(recipes, key=lambda x: x['info_eng'])[:5]
        for i, recipe in enumerate(lowest_cal_recipes, 1):
            print(f"   {i}. {recipe['rcp_nm']} ({recipe['info_eng']}kcal)")

        # 10. 국&찌개 중에서 단백질이 15g 이상인 메뉴를 보여줘
        print("\n10. 국&찌개 중 단백질 15g 이상인 메뉴:")
        print("   SQL: SELECT RCP_NM, RCP_PAT2, INFO_PRO FROM recipes WHERE RCP_PAT2 = '국&찌개' AND INFO_PRO >= 15;")
        query10_results = [
            r for r in recipes
            if r['rcp_pat2'] == '국&찌개' and r['info_pro'] >= 15
        ]
        print(f"   찾은 레시피: {len(query10_results)}개")
        for recipe in query10_results[:3]:
            print(f"   - {recipe['rcp_nm']} (단백질: {recipe['info_pro']}g)")

async def main():
    """메인 실행 함수"""
    try:
        await simple_query_examples()
        await custom_search()
        await test_specific_queries()

        print("\n" + "=" * 50)
        print("모든 쿼리 테스트 완료!")

    except Exception as e:
        print(f"오류 발생: {e}")
        print("FastAPI 서버가 실행 중인지 확인해주세요.")
        print("서버 실행: docker-compose up 또는 uvicorn app.main:app --reload")

if __name__ == "__main__":
    asyncio.run(main())