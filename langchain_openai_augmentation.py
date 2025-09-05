from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.environ["OPENAI_API_KEY"]

SYSTEM_PROMPT = """당신은 감정 분석 텍스트 생성 전문 AI 어시스턴트입니다.
당신의 역할은 주어진 **context(참고 텍스트)**와 category1(중분류), category2(소분류) 정보를 기반으로, 동일한 감정 카테고리에 속하지만 새롭고 독창적인 context를 생성하는 것입니다.

**규칙**
1. 유사성 제한
- 새로 생성하는 context는 참고 context와 직접적으로 유사하거나 단순 변형해서는 안 됩니다.
- 기존 context에서 사용된 사건, 단어, 문장 구조는 재활용하지 마십시오.
- 의미적 유사성은 유지하되, 다른 사건, 다른 장소, 다른 등장인물, 다른 활동을 포함하여 작성해야 합니다.
- 단순 동의어 치환이나 사건 반복은 금지합니다.


2. 참고 context 활용
- 주어진 context는 감정적 힌트로만 사용하며, 사건이나 상황은 그대로 따라하지 마십시오.
- 장소, 활동, 등장인물, 사건 유형을 context와 겹치지 않게 다양화하십시오.

3. 카테고리 충실성
- 새 context는 반드시 category1과 category2의 감정을 명확히 드러내야 합니다.
- 누가 보더라도 해당 감정이라고 인식할 수 있어야 합니다.

4. 표현 다양성
- 다양한 문체(대화체, 독백, 관찰, 상황 설명 등)를 활용합니다.
- 문장은 자연스러운 한국어로, 구체적 상황, 장소, 인물, 활동을 포함하는 것이 좋습니다.
- 표현할 때 '승리/환호/박수'등과 같이 국한되지 않고, 신체적, 심리적, 감각적 체험을 다양하게 활용하십시오.

5. 중복 소분류 주의
- 일부 소분류는 여러 중분류에 속할 수 있습니다(예: "감동"은 기쁨과 중립 모두 포함).
- 이 경우 category1(중분류)에 맞는 뉘앙스와 맥락으로 작성해야 합니다.

6. 출력 형식
- context만 출력하며, 추가 설명은 하지 않습니다.
- 'Context:'도 앞에 붙이지 않고 출력합니다.
- 최대 150자를 넘지 않습니다.

**중분류별 소분류 목록**

- 기쁨 : 감동, 고마움, 공감, 기대감, 놀람, 만족감, 반가움, 신뢰감, 신명남, 안정감, 자랑스러움, 자신감, 즐거움, 통쾌함, 편안함
- 두려움 : 걱정, 공포, 놀람, 위축감, 초조함
- 미움(상대방) : 경멸, 냉담, 반감, 불신감, 비위상함, 시기심, 외면, 치사함
- 분노 : 날카로움, 발열, 불쾌, 사나움, 원망, 타오름
- 사랑 : 귀중함, 너그러움, 다정함, 동정(슬픔), 두근거림, 매력적, 아른거림, 열정적임, 호감
- 수치심 : 미안함, 부끄러움, 죄책감
- 슬픔 : 고통, 그리움, 동정(슬픔), 무기력, 수치심, 실망, 아픔, 억울함, 외로움, 절망, 허망, 후회
- 싫어함(상태) : 난처함, 답답함, 불편함, 서먹함, 싫증, 심심함
- 욕망 : 갈등, 궁금함, 기대감, 불만, 아쉬움, 욕심
- 중립 : 감동, 걱정, 고마움, 고통, 공감, 공포, 궁금함, 귀중함, 그리움, 난처함, 냉담, 놀람, 다정함, 답답함, 동정(슬픔), 만족감, 무기력, 미안함, 반가움, 불신감, 불쾌, 서먹함, 신뢰감, 안정감, 열정적인, 외로움, 위축감, 자랑스러움, 절망, 통쾌함, 편안함, 호감, 후회
"""

# 사용자 입력 템플릿
USER_PROMPT_TEMPLATE = """
Context: {context}
Category1: {category1}
Category2: {category2}
위 정보를 바탕으로 답변해주세요.
"""

class ContextGenerator:
    def __init__(self, model="gpt-4o", api_key=api_key, temperature=0.8, max_tokens=200, top_p=0.9):
        self.llm = ChatOpenAI(
            model=model,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p
        )
        # 프롬프트 템플릿을 인스턴스 변수로 생성
        self.prompt_template = PromptTemplate(
            input_variables=["context", "category1", "category2"],
            template=USER_PROMPT_TEMPLATE
        )

    def create_context(self, context, category1, category2):
        # 템플릿을 사용해서 프롬프트 생성
        formatted_prompt = self.prompt_template.format(
            context=context,
            category1=category1,
            category2=category2,
        )
        
        # 시스템 메시지와 사용자 메시지 생성
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=formatted_prompt)
        ]
        
        response = self.llm.invoke(messages)
        return response.content

# 사용 예제
if __name__ == "__main__":
    generator = ContextGenerator()
    
    context = "오늘 시험 결과를 받았는데 예상보다 점수가 높아서 정말 기뻤다."
    category1 = "기쁨"
    category2 = "만족감"
    
    new_context = generator.create_context(context, category1, category2)
    print(f"원본 Context: {context}")
    print(f"Category1: {category1}")
    print(f"Category2: {category2}")
    print(f"\n생성된 Context: {new_context}")