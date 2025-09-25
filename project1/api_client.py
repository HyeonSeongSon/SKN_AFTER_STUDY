#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI 엔드포인트를 통해 레시피 데이터를 조회하는 클라이언트 스크립트

사용법:
    python api_client.py

기능:
    1. 모든 레시피 목록 조회
    2. 특정 레시피 상세 조회
    3. 레시피 검색 및 필터링
"""

import asyncio
import aiohttp
import json
from typing import List, Dict, Optional
import pandas as pd

BASE_URL = "http://localhost:8000"

class RecipeAPIClient:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url

    async def get_all_recipes(self) -> List[Dict]:
        """모든 레시피 목록을 가져오기"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/recipes/") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"Error {response.status}: {await response.text()}")
                    return []

    async def get_recipe_by_id(self, recipe_id: int) -> Optional[Dict]:
        """특정 ID의 레시피 상세 정보 가져오기"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/recipes/{recipe_id}") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"Error {response.status}: {await response.text()}")
                    return None

    async def search_recipes_by_name(self, keyword: str) -> List[Dict]:
        """레시피 이름으로 검색"""
        all_recipes = await self.get_all_recipes()
        return [
            recipe for recipe in all_recipes
            if keyword.lower() in recipe['rcp_nm'].lower()
        ]

    async def filter_recipes_by_method(self, method: str) -> List[Dict]:
        """요리 방법으로 필터링"""
        all_recipes = await self.get_all_recipes()
        return [
            recipe for recipe in all_recipes
            if recipe['rcp_way2'] == method
        ]

    async def filter_recipes_by_category(self, category: str) -> List[Dict]:
        """요리 종류로 필터링"""
        all_recipes = await self.get_all_recipes()
        return [
            recipe for recipe in all_recipes
            if recipe['rcp_pat2'] == category
        ]

    async def get_recipes_by_nutrition_range(
        self,
        min_calories: Optional[float] = None,
        max_calories: Optional[float] = None
    ) -> List[Dict]:
        """칼로리 범위로 레시피 필터링"""
        all_recipes = await self.get_all_recipes()
        filtered = []

        for recipe in all_recipes:
            calories = recipe['info_eng']

            if min_calories is not None and calories < min_calories:
                continue
            if max_calories is not None and calories > max_calories:
                continue

            filtered.append(recipe)

        return filtered

async def demo_queries():
    """다양한 쿼리 예시 실행"""
    client = RecipeAPIClient()

    print("=" * 60)
    print("레시피 API 클라이언트 데모")
    print("=" * 60)

    # 1. 전체 레시피 수 확인
    print("\n1. 전체 레시피 수 확인")
    all_recipes = await client.get_all_recipes()
    print(f"   총 {len(all_recipes)}개의 레시피가 있습니다.")

    # 2. 첫 번째 레시피 상세 정보
    if all_recipes:
        print("\n2. 첫 번째 레시피 상세 정보")
        first_recipe = all_recipes[0]
        print(f"   ID: {first_recipe['id']}")
        print(f"   이름: {first_recipe['rcp_nm']}")
        print(f"   요리방법: {first_recipe['rcp_way2']}")
        print(f"   종류: {first_recipe['rcp_pat2']}")
        print(f"   칼로리: {first_recipe['info_eng']}kcal")

    # 3. 특정 레시피 ID로 조회
    print("\n3. 특정 레시피 ID로 조회 (ID=1)")
    recipe = await client.get_recipe_by_id(1)
    if recipe:
        print(f"   레시피명: {recipe['rcp_nm']}")
        print(f"   영양정보: 칼로리 {recipe['info_eng']}kcal, 탄수화물 {recipe['info_car']}g")

    # 4. 이름으로 검색
    print("\n4. '찌개' 키워드로 레시피 검색")
    stew_recipes = await client.search_recipes_by_name("찌개")
    print(f"   '{len(stew_recipes)}개의 찌개 레시피를 찾았습니다:")
    for recipe in stew_recipes[:3]:  # 첫 3개만 표시
        print(f"   - {recipe['rcp_nm']}")

    # 5. 요리 방법으로 필터링
    print("\n5. '볶기' 방법으로 요리 필터링")
    stir_fry_recipes = await client.filter_recipes_by_method("볶기")
    print(f"   {len(stir_fry_recipes)}개의 볶음 요리를 찾았습니다:")
    for recipe in stir_fry_recipes[:3]:  # 첫 3개만 표시
        print(f"   - {recipe['rcp_nm']}")

    # 6. 요리 종류로 필터링
    print("\n6. '반찬' 종류로 필터링")
    side_dish_recipes = await client.filter_recipes_by_category("반찬")
    print(f"   {len(side_dish_recipes)}개의 반찬 레시피를 찾았습니다:")
    for recipe in side_dish_recipes[:3]:  # 첫 3개만 표시
        print(f"   - {recipe['rcp_nm']}")

    # 7. 칼로리 범위로 필터링
    print("\n7. 200-300kcal 범위의 레시피 검색")
    low_cal_recipes = await client.get_recipes_by_nutrition_range(200, 300)
    print(f"   {len(low_cal_recipes)}개의 레시피를 찾았습니다:")
    for recipe in low_cal_recipes[:3]:  # 첫 3개만 표시
        print(f"   - {recipe['rcp_nm']} ({recipe['info_eng']}kcal)")

async def export_to_csv():
    """API에서 가져온 데이터를 CSV로 내보내기"""
    client = RecipeAPIClient()

    print("\n8. 데이터를 CSV로 내보내기")
    recipes = await client.get_all_recipes()

    if recipes:
        df = pd.DataFrame(recipes)
        csv_path = "exported_recipes.csv"
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"   {len(recipes)}개의 레시피를 '{csv_path}'로 내보냈습니다.")
        print(f"   컬럼: {list(df.columns)}")

async def main():
    """메인 실행 함수"""
    try:
        # 데모 쿼리 실행
        await demo_queries()

        # CSV 내보내기
        await export_to_csv()

        print("\n" + "=" * 60)
        print("모든 쿼리가 완료되었습니다!")

    except Exception as e:
        print(f"오류 발생: {e}")
        print("FastAPI 서버가 실행 중인지 확인해주세요 (http://localhost:8000)")

if __name__ == "__main__":
    asyncio.run(main())