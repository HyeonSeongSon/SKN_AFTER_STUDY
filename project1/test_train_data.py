#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
train_data_100.jsonl을 사용한 쿼리 테스트

각 쿼리별 검색 결과 개수를 출력하고 0개 결과인 쿼리를 수집
"""

import asyncio
import aiohttp
import json
import sqlite3
import re
from typing import List, Dict, Any

BASE_URL = "http://localhost:8000"

def load_train_data(file_path: str) -> List[Dict]:
    """JSONL 파일에서 학습 데이터 로드 (다중 라인 JSON 지원)"""
    train_data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 중괄호로 구분하여 각 JSON 객체를 분리
    json_objects = []
    brace_count = 0
    start_idx = 0

    for i, char in enumerate(content):
        if char == '{':
            if brace_count == 0:
                start_idx = i
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0:
                json_str = content[start_idx:i+1]
                try:
                    data = json.loads(json_str)
                    train_data.append(data)
                except json.JSONDecodeError as e:
                    print(f"JSON 파싱 오류: {e}")
                    continue

    return train_data

def create_in_memory_db(recipes: List[Dict]) -> sqlite3.Connection:
    """메모리 내 SQLite 데이터베이스 생성 및 데이터 삽입"""
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()

    # 테이블 생성
    cursor.execute('''
        CREATE TABLE recipes (
            RCP_SEQ INTEGER,
            RCP_NM TEXT,
            RCP_WAY2 TEXT,
            RCP_PAT2 TEXT,
            INFO_ENG REAL,
            INFO_CAR REAL,
            INFO_PRO REAL,
            INFO_FAT REAL,
            INFO_NA REAL,
            RCP_PARTS_DTLS TEXT,
            recipe_steps TEXT,
            RCP_NA_TIP TEXT,
            HASH_TAG TEXT
        )
    ''')

    # 데이터 삽입
    for recipe in recipes:
        cursor.execute('''
            INSERT INTO recipes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            recipe.get('rcp_seq', 0),
            recipe.get('rcp_nm', ''),
            recipe.get('rcp_way2', ''),
            recipe.get('rcp_pat2', ''),
            recipe.get('info_eng', 0),
            recipe.get('info_car', 0),
            recipe.get('info_pro', 0),
            recipe.get('info_fat', 0),
            recipe.get('info_na', 0),
            recipe.get('rcp_parts_dtls', ''),
            recipe.get('recipe_steps', ''),
            recipe.get('rcp_na_tip', ''),
            recipe.get('hash_tag', '')
        ))

    conn.commit()
    return conn

def execute_sql_query(conn: sqlite3.Connection, sql_query: str) -> List[Dict]:
    """SQL 쿼리 실행하여 결과 반환"""
    try:
        cursor = conn.cursor()
        cursor.execute(sql_query)
        columns = [description[0] for description in cursor.description]
        results = cursor.fetchall()

        # 딕셔너리 형태로 변환
        return [dict(zip(columns, row)) for row in results]
    except Exception as e:
        print(f"SQL 실행 오류: {sql_query}")
        print(f"오류 내용: {e}")
        return []

async def test_train_data():
    """train_data_100.jsonl의 각 쿼리를 테스트"""

    # 학습 데이터 로드
    train_data = load_train_data('data/train_data_100.jsonl')

    print(f"총 {len(train_data)}개의 학습 데이터를 로드했습니다.")
    print("=" * 80)

    # API에서 레시피 데이터 가져오기
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_URL}/recipes/") as response:
            if response.status != 200:
                print("FastAPI 서버에서 레시피 데이터를 가져올 수 없습니다.")
                print("서버가 실행 중인지 확인해주세요.")
                return

            recipes = await response.json()
            print(f"API에서 {len(recipes)}개의 레시피를 가져왔습니다.")

    # 메모리 내 데이터베이스 생성
    conn = create_in_memory_db(recipes)

    # 결과 통계
    total_queries = len(train_data)
    zero_result_queries = []
    result_counts = []

    print("\n쿼리별 결과 개수 테스트:")
    print("-" * 80)

    for i, data in enumerate(train_data, 1):
        input_text = data['input']
        sql_query = data['output']

        # SQL 쿼리 실행
        results = execute_sql_query(conn, sql_query)
        result_count = len(results)
        result_counts.append(result_count)

        print(f"{i:3d}. [{result_count:3d}개] {input_text}")
        print(f"     SQL: {sql_query}")

        # 0개 결과인 경우 따로 수집
        if result_count == 0:
            zero_result_queries.append({
                'index': i,
                'input': input_text,
                'sql': sql_query,
                'count': result_count
            })

        # 처음 몇 개 결과 예시 출력 (결과가 있는 경우)
        if result_count > 0 and result_count <= 3:
            for j, result in enumerate(results[:3], 1):
                recipe_name = result.get('RCP_NM', '이름없음')
                print(f"     - {recipe_name}")
        elif result_count > 3:
            for j, result in enumerate(results[:2], 1):
                recipe_name = result.get('RCP_NM', '이름없음')
                print(f"     - {recipe_name}")
            print(f"     ... 외 {result_count-2}개")

        print()

    # 연결 종료
    conn.close()

    # 통계 출력
    print("=" * 80)
    print("테스트 결과 통계")
    print("=" * 80)
    print(f"총 쿼리 개수: {total_queries}")
    print(f"0개 결과 쿼리: {len(zero_result_queries)}개")
    print(f"1개 이상 결과 쿼리: {total_queries - len(zero_result_queries)}개")
    print(f"평균 결과 개수: {sum(result_counts) / len(result_counts):.1f}개")
    print(f"최대 결과 개수: {max(result_counts)}개")
    print(f"최소 결과 개수: {min(result_counts)}개")

    # 0개 결과 쿼리들 상세 출력
    if zero_result_queries:
        print("\n" + "=" * 80)
        print(f"0개 결과가 나온 쿼리들 ({len(zero_result_queries)}개)")
        print("=" * 80)

        for query_info in zero_result_queries:
            print(f"{query_info['index']:3d}. {query_info['input']}")
            print(f"     SQL: {query_info['sql']}")
            print()

        # 0개 결과 쿼리들을 파일로 저장
        with open('data/zero_result_queries.json', 'w', encoding='utf-8') as f:
            json.dump(zero_result_queries, f, ensure_ascii=False, indent=2)

        print(f"0개 결과 쿼리들이 'data/zero_result_queries.json'에 저장되었습니다.")

    # 결과 분포 출력
    print("\n결과 개수 분포:")
    print("-" * 40)
    count_distribution = {}
    for count in result_counts:
        count_range = f"{count}개" if count <= 5 else f"6개 이상"
        if count == 0:
            count_range = "0개"
        elif count <= 5:
            count_range = f"{count}개"
        elif count <= 10:
            count_range = "6-10개"
        elif count <= 20:
            count_range = "11-20개"
        else:
            count_range = "21개 이상"

        count_distribution[count_range] = count_distribution.get(count_range, 0) + 1

    for range_name, count in sorted(count_distribution.items()):
        print(f"{range_name}: {count}개 쿼리")

async def main():
    """메인 실행 함수"""
    try:
        await test_train_data()

        print("\n" + "=" * 80)
        print("모든 쿼리 테스트 완료!")

    except Exception as e:
        print(f"오류 발생: {e}")
        print("FastAPI 서버가 실행 중인지 확인해주세요.")
        print("서버 실행: docker-compose up 또는 uvicorn app.main:app --reload")

if __name__ == "__main__":
    asyncio.run(main())