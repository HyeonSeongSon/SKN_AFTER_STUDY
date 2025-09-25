#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
레시피 데이터 CSV를 PostgreSQL 데이터베이스에 적재하는 스크립트

사용법:
    python load_recipes_data_clean.py

요구사항:
    - project1/data/rcp.csv 파일이 존재해야 함
    - PostgreSQL 데이터베이스가 실행 중이어야 함
    - 환경변수 DATABASE_URL이 설정되어 있어야 함
"""

import os
import sys
import json
import asyncio
import pandas as pd
from pathlib import Path
from databases import Database
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, Text
import psycopg2
import time

# 데이터베이스 연결 설정 (로컬 환경용)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://myuser:mypassword@localhost:5432/mydb")
database = Database(DATABASE_URL)
metadata = MetaData()
engine = create_engine(DATABASE_URL)

# recipes 테이블 정의 (models.py와 동일)
recipes = Table(
    "recipes",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("rcp_seq", String, unique=True, nullable=False),
    Column("rcp_nm", String, nullable=False),
    Column("rcp_way2", String, nullable=False),
    Column("rcp_pat2", String, nullable=False),
    Column("info_eng", Float, nullable=False),
    Column("info_car", Float, nullable=False),
    Column("info_pro", Float, nullable=False),
    Column("info_fat", Float, nullable=False),
    Column("info_na", Float, nullable=False),
    Column("rcp_parts_dtls", Text, nullable=False),
    Column("recipe_steps", Text, nullable=False),
    Column("rcp_na_tip", Text, nullable=True),
    Column("hash_tag", Text, nullable=True),
)

def wait_for_db(retries=10, delay=3):
    """
    DB가 준비될 때까지 재시도
    """
    for i in range(retries):
        try:
            conn = psycopg2.connect(
                dbname="mydb",
                user="myuser",
                password="mypassword",
                host="localhost",
                port="5432",
            )
            conn.close()
            print("Database is ready!")
            return
        except psycopg2.OperationalError:
            print(f"Database not ready, retrying in {delay} seconds...")
            time.sleep(delay)
    raise Exception("Database not ready after several retries")

def validate_csv_data(df):
    """
    CSV 데이터의 유효성을 검증

    Args:
        df: pandas DataFrame

    Returns:
        bool: 유효성 검증 통과 여부
    """
    required_columns = [
        'RCP_SEQ', 'RCP_NM', 'RCP_WAY2', 'RCP_PAT2',
        'INFO_ENG', 'INFO_CAR', 'INFO_PRO', 'INFO_FAT', 'INFO_NA',
        'RCP_PARTS_DTLS', 'recipe_steps'
    ]

    print("[*] CSV 데이터 유효성 검증 중...")

    # 필수 컬럼 확인
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"[X] 필수 컬럼이 누락되었습니다: {missing_columns}")
        return False

    # 데이터 타입 확인
    numeric_columns = ['INFO_ENG', 'INFO_CAR', 'INFO_PRO', 'INFO_FAT', 'INFO_NA']
    for col in numeric_columns:
        if not pd.api.types.is_numeric_dtype(df[col]):
            print(f"[X] {col} 컬럼이 숫자 타입이 아닙니다.")
            return False

    # NULL 값 확인
    null_counts = df[required_columns].isnull().sum()
    if null_counts.any():
        print(f"[!] NULL 값이 포함된 필수 컬럼들: {null_counts[null_counts > 0].to_dict()}")

    print(f"[OK] 유효성 검증 완료 - 총 {len(df)}개 레코드")
    return True

def clean_data_for_db(df):
    """
    데이터베이스 적재를 위해 데이터 정리

    Args:
        df: pandas DataFrame

    Returns:
        pandas DataFrame: 정리된 데이터프레임
    """
    print("[*] 데이터 정리 중...")

    df_clean = df.copy()

    # 컬럼명을 DB 테이블 스키마에 맞게 변경
    column_mapping = {
        'RCP_SEQ': 'rcp_seq',
        'RCP_NM': 'rcp_nm',
        'RCP_WAY2': 'rcp_way2',
        'RCP_PAT2': 'rcp_pat2',
        'INFO_ENG': 'info_eng',
        'INFO_CAR': 'info_car',
        'INFO_PRO': 'info_pro',
        'INFO_FAT': 'info_fat',
        'INFO_NA': 'info_na',
        'RCP_PARTS_DTLS': 'rcp_parts_dtls',
        'recipe_steps': 'recipe_steps',
        'RCP_NA_TIP': 'rcp_na_tip',
        'HASH_TAG': 'hash_tag'
    }

    df_clean = df_clean.rename(columns=column_mapping)

    # 필요한 컬럼만 선택
    required_cols = list(column_mapping.values())
    df_clean = df_clean[required_cols]

    # RCP_PARTS_DTLS가 딕셔너리 형태라면 JSON 문자열로 변환
    if df_clean['rcp_parts_dtls'].dtype == 'object':
        def convert_to_json_string(value):
            if pd.isna(value):
                return '{"categories":[]}'
            if isinstance(value, str):
                try:
                    # 이미 JSON 문자열인지 확인
                    json.loads(value)
                    return value
                except json.JSONDecodeError:
                    # 파이썬 딕셔너리 문자열일 수 있으므로 eval 시도
                    try:
                        dict_value = eval(value)
                        return json.dumps(dict_value, ensure_ascii=False)
                    except:
                        return '{"categories":[]}'
            elif isinstance(value, dict):
                return json.dumps(value, ensure_ascii=False)
            else:
                return '{"categories":[]}'

        df_clean['rcp_parts_dtls'] = df_clean['rcp_parts_dtls'].apply(convert_to_json_string)

    # NULL 값 처리
    df_clean['rcp_na_tip'] = df_clean['rcp_na_tip'].fillna('')
    df_clean['hash_tag'] = df_clean['hash_tag'].fillna('')

    # 문자열 컬럼의 빈 문자열을 None으로 변경 (nullable 컬럼의 경우)
    df_clean['rcp_na_tip'] = df_clean['rcp_na_tip'].replace('', None)
    df_clean['hash_tag'] = df_clean['hash_tag'].replace('', None)

    print(f"[OK] 데이터 정리 완료 - {len(df_clean)}개 레코드")
    return df_clean

async def insert_recipes_batch(df, batch_size=100):
    """
    배치 단위로 레시피 데이터를 데이터베이스에 삽입

    Args:
        df: pandas DataFrame
        batch_size: 배치 크기
    """
    await database.connect()

    try:
        total_rows = len(df)
        successful_inserts = 0
        failed_inserts = 0

        print(f"[*] 총 {total_rows}개 레코드를 {batch_size}개씩 배치 처리합니다...")

        # 배치별로 처리
        for start_idx in range(0, total_rows, batch_size):
            end_idx = min(start_idx + batch_size, total_rows)
            batch_df = df.iloc[start_idx:end_idx]

            print(f"[*] 배치 {start_idx//batch_size + 1}/{(total_rows-1)//batch_size + 1} 처리 중 ({start_idx+1}-{end_idx})")

            # 배치 데이터 준비
            batch_records = []
            for _, row in batch_df.iterrows():
                record = {
                    'rcp_seq': str(row['rcp_seq']),
                    'rcp_nm': str(row['rcp_nm']),
                    'rcp_way2': str(row['rcp_way2']),
                    'rcp_pat2': str(row['rcp_pat2']),
                    'info_eng': float(row['info_eng']),
                    'info_car': float(row['info_car']),
                    'info_pro': float(row['info_pro']),
                    'info_fat': float(row['info_fat']),
                    'info_na': float(row['info_na']),
                    'rcp_parts_dtls': str(row['rcp_parts_dtls']),
                    'recipe_steps': str(row['recipe_steps']),
                    'rcp_na_tip': str(row['rcp_na_tip']) if pd.notna(row['rcp_na_tip']) else None,
                    'hash_tag': str(row['hash_tag']) if pd.notna(row['hash_tag']) else None
                }
                batch_records.append(record)

            # 배치 삽입 실행
            try:
                await database.execute_many(recipes.insert(), batch_records)
                successful_inserts += len(batch_records)
                print(f"[OK] 배치 삽입 성공: {len(batch_records)}개 레코드")

            except Exception as e:
                failed_inserts += len(batch_records)
                print(f"[X] 배치 삽입 실패: {e}")
                print(f"   실패한 레코드 수: {len(batch_records)}")

        print(f"\n[*] 삽입 완료!")
        print(f"[OK] 성공: {successful_inserts}개")
        print(f"[X] 실패: {failed_inserts}개")
        print(f"[*] 성공률: {(successful_inserts/total_rows)*100:.1f}%")

    except Exception as e:
        print(f"[X] 데이터베이스 삽입 중 오류 발생: {e}")
        raise
    finally:
        await database.disconnect()

async def check_existing_data():
    """
    기존 데이터 확인
    """
    await database.connect()

    try:
        count = await database.fetch_val("SELECT COUNT(*) FROM recipes")
        print(f"[*] 현재 recipes 테이블에 {count}개의 레코드가 있습니다.")
        return count
    except Exception as e:
        print(f"[X] 데이터 확인 중 오류: {e}")
        return 0
    finally:
        await database.disconnect()

async def main():
    """
    메인 함수
    """
    print("[*] 레시피 데이터 적재를 시작합니다!")
    print("=" * 60)

    # 1. CSV 파일 확인
    csv_path = Path(__file__).parent / 'project1' / 'data' / 'rcp.csv'
    if not csv_path.exists():
        # 현재 디렉토리에서 찾기
        csv_path = Path('project1/data/rcp.csv')
        if not csv_path.exists():
            csv_path = Path('data/rcp.csv')
            if not csv_path.exists():
                print(f"[X] CSV 파일을 찾을 수 없습니다: {csv_path}")
                return

    print(f"[*] CSV 파일 경로: {csv_path}")

    # 2. 데이터베이스 연결 확인
    print("[*] 데이터베이스 연결을 확인 중...")
    try:
        wait_for_db()
    except Exception as e:
        print(f"[X] 데이터베이스 연결 실패: {e}")
        return

    # 3. 기존 데이터 확인
    existing_count = await check_existing_data()
    if existing_count > 0:
        response = input(f"[!] 이미 {existing_count}개의 레코드가 있습니다. 계속하시겠습니까? (y/N): ")
        if response.lower() != 'y':
            print("작업을 취소했습니다.")
            return

    # 4. CSV 데이터 로드
    print("[*] CSV 파일을 읽는 중...")
    try:
        df = pd.read_csv(csv_path)
        print(f"[OK] CSV 로드 완료: {len(df)}개 레코드, {len(df.columns)}개 컬럼")
    except Exception as e:
        print(f"[X] CSV 파일 읽기 실패: {e}")
        return

    # 5. 데이터 유효성 검증
    if not validate_csv_data(df):
        print("[X] 데이터 유효성 검증 실패")
        return

    # 6. 데이터 정리
    df_clean = clean_data_for_db(df)

    # 7. 데이터베이스에 삽입
    print("\n[*] 데이터베이스 삽입을 시작합니다...")
    await insert_recipes_batch(df_clean)

    # 8. 최종 확인
    final_count = await check_existing_data()
    print(f"\n[DONE] 작업 완료! 최종 레코드 수: {final_count}개")

if __name__ == "__main__":
    asyncio.run(main())