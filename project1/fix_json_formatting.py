import pandas as pd
import json
import re
import os
from collections import Counter

def parse_ingredient_text(ingredient_text):
    """
    재료 텍스트를 파싱하여 구조화된 정보 추출
    """
    if not ingredient_text or not ingredient_text.strip():
        return None

    ingredient_text = ingredient_text.strip()

    result = {
        'name': '',
        'amount': '',
        'unit': '',
        'description': ''
    }

    # 괄호 안의 설명 추출
    description_match = re.search(r'\(([^)]+)\)', ingredient_text)
    if description_match:
        result['description'] = description_match.group(1)
        ingredient_text = ingredient_text.replace(description_match.group(0), '').strip()

    # 숫자와 단위 추출
    amount_match = re.search(r'([0-9./]+)\s*([a-zA-Z가-힣]+)', ingredient_text)
    if amount_match:
        result['amount'] = amount_match.group(1)
        result['unit'] = amount_match.group(2)
        result['name'] = ingredient_text[:amount_match.start()].strip()
    else:
        result['name'] = ingredient_text

    return result

def structure_ingredients(rcp_parts_dtls):
    """
    RCP_PARTS_DTLS 텍스트를 구조화된 재료 정보로 변환
    """
    if pd.isna(rcp_parts_dtls) or not str(rcp_parts_dtls).strip():
        return {'categories': []}

    lines = str(rcp_parts_dtls).strip().split('\n')
    categories = []
    current_category = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if ',' in line:
            ingredients = []
            for ingredient in line.split(','):
                parsed = parse_ingredient_text(ingredient.strip())
                if parsed and parsed['name']:
                    ingredients.append(parsed)

            if current_category:
                current_category['ingredients'].extend(ingredients)
            else:
                categories.append({
                    'category': '기본재료',
                    'ingredients': ingredients
                })
        else:
            parsed = parse_ingredient_text(line)
            if parsed and parsed['amount']:
                if current_category:
                    current_category['ingredients'].append(parsed)
                else:
                    categories.append({
                        'category': '기본재료',
                        'ingredients': [parsed]
                    })
            else:
                current_category = {
                    'category': line,
                    'ingredients': []
                }
                categories.append(current_category)

    return {'categories': categories}

def analyze_structured_ingredients(df):
    """
    구조화된 재료 정보 분석

    Args:
        df: 구조화된 재료 정보가 포함된 DataFrame

    Returns:
        dict: 분석 결과
    """
    analysis = {
        '총_레시피_수': len(df),
        '카테고리_통계': {},
        '재료_통계': {},
        '단위_통계': {},
        '평균_재료_수': 0
    }

    all_categories = []
    all_ingredients = []
    all_units = []
    total_ingredient_count = 0

    for idx, row in df.iterrows():
        try:
            # 작은따옴표를 큰따옴표로 바꿔서 JSON 파싱
            ingredients_str = row['ingredients_structured']
            json_str = ingredients_str.replace("'", '"')
            structured = json.loads(json_str)
            recipe_ingredient_count = 0

            for category in structured['categories']:
                all_categories.append(category['category'])
                recipe_ingredient_count += len(category['ingredients'])

                for ingredient in category['ingredients']:
                    all_ingredients.append(ingredient['name'])
                    if ingredient['unit']:
                        all_units.append(ingredient['unit'])

            total_ingredient_count += recipe_ingredient_count

        except Exception as e:
            continue

    # 통계 계산
    analysis['카테고리_통계'] = dict(Counter(all_categories).most_common(10))
    analysis['재료_통계'] = dict(Counter(all_ingredients).most_common(20))
    analysis['단위_통계'] = dict(Counter(all_units).most_common(10))
    analysis['평균_재료_수'] = round(total_ingredient_count / len(df), 2) if len(df) > 0 else 0

    return analysis

def fix_json_formatting():
    """
    JSON 포맷팅 문제를 해결하는 메인 함수
    """
    print("JSON formatting fix in progress...")

    # 기본 데이터 로드
    data_dir = r'C:\Users\user\Desktop\SKN_AFTER_STUDY\project1\data'
    basic_file = os.path.join(data_dir, '레시피_통합본.csv')

    print(f"Loading basic data: {basic_file}")
    df = pd.read_csv(basic_file, encoding='utf-8-sig')
    print(f"Data loaded successfully: {df.shape}")

    # 재료 구조화 적용
    print("Applying ingredient structuring...")
    structured_ingredients = []

    for idx, row in df.iterrows():
        try:
            structured = structure_ingredients(row['RCP_PARTS_DTLS'])
            # JSON 대신 Python 딕셔너리 문자열로 변환 (작은따옴표 사용)
            dict_str = str(structured).replace('"', "'")
            structured_ingredients.append(dict_str)

            if (idx + 1) % 100 == 0:
                print(f"Progress: {idx + 1}/{len(df)} completed ({((idx + 1)/len(df)*100):.1f}%)")

        except Exception as e:
            print(f"Error at index {idx}: {e}")
            structured_ingredients.append("{'categories':[]}")

    # 새 컬럼 추가
    df['ingredients_structured'] = structured_ingredients

    # 개선된 파일로 저장 (작은따옴표 버전)
    output_file = os.path.join(data_dir, '레시피_구조화_완료_최종.csv')
    df.to_csv(output_file, index=False, encoding='utf-8-sig')

    print(f"Improved file saved: {output_file}")
    print(f"Saved data: {len(df):,} recipes, {len(df.columns)} columns")

    # 검증
    print("\nValidating saved file...")
    df_test = pd.read_csv(output_file, encoding='utf-8-sig')

    test_results = []
    for i in range(min(5, len(df_test))):
        try:
            sample_str = df_test['ingredients_structured'].iloc[i]
            # 작은따옴표를 큰따옴표로 바꿔서 JSON 파싱
            json_str = sample_str.replace("'", '"')
            parsed = json.loads(json_str)
            test_results.append(f"  Recipe {i+1}: Dict parsing SUCCESS ({len(parsed['categories'])} categories)")
        except Exception as e:
            test_results.append(f"  Recipe {i+1}: Dict parsing FAILED - {e}")

    print("\nTest results:")
    for result in test_results:
        print(result)

    # 샘플 딕셔너리 출력
    if test_results:
        print(f"\nFirst recipe dict sample:")
        sample_str = df_test['ingredients_structured'].iloc[0]
        print(sample_str[:500] + "...")

        # JSON 변환해서 구조 확인
        json_str = sample_str.replace("'", '"')
        parsed_sample = json.loads(json_str)
        print(f"\nStructure: {len(parsed_sample['categories'])} categories")
        for i, cat in enumerate(parsed_sample['categories']):
            print(f"  {i+1}. {cat['category']}: {len(cat['ingredients'])} ingredients")

    # 재료 분석 결과 생성 및 저장
    print(f"\nGenerating ingredient analysis...")
    analysis_results = analyze_structured_ingredients(df_test)

    # 분석 결과를 JSON으로 저장
    analysis_file = os.path.join(data_dir, '재료_분석_결과_개선.json')
    with open(analysis_file, 'w', encoding='utf-8') as f:
        json.dump(analysis_results, f, ensure_ascii=False, indent=2)

    print(f"Analysis results saved: {analysis_file}")

    # 분석 결과 출력
    print(f"\nIngredient Analysis Results:")
    print("=" * 50)
    print(f"Total recipes: {analysis_results['총_레시피_수']:,}")
    print(f"Average ingredients per recipe: {analysis_results['평균_재료_수']}")

    print(f"\nTop 5 categories:")
    for category, count in list(analysis_results['카테고리_통계'].items())[:5]:
        print(f"  - {category}: {count} times")

    print(f"\nTop 10 ingredients:")
    for ingredient, count in list(analysis_results['재료_통계'].items())[:10]:
        print(f"  - {ingredient}: {count} times")

    print(f"\nTop 5 units:")
    for unit, count in list(analysis_results['단위_통계'].items())[:5]:
        print(f"  - {unit}: {count} times")

    print(f"\nJSON formatting fix completed!")
    return output_file, analysis_file

if __name__ == "__main__":
    fix_json_formatting()