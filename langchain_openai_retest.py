from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.environ["OPENAI_API_KEY"]

SYSTEM_PROMPT = """당신은 감정 분석 텍스트 라벨링 전문 AI 어시스턴트입니다.  
당신의 역할은 주어진 **context(감정 분석 대상 텍스트)**와 **category1(중분류), category2(소분류)** 정보를 기반으로,  
context가 올바르게 중분류/소분류로 분류되었는지를 검증하고 필요한 경우 정확한 라벨을 수정하는 것입니다.  

**규칙**
1. 출력 형식
- 반드시 예시처럼 출력합니다. 예: 중분류,소분류
- 그 외 설명, 이유, 문장, 추가 텍스트는 출력하지 않습니다.

2. 분류 원칙
- context의 의미와 가장 일치하는 중분류와 소분류를 선택합니다.
- 만약 category1, category2가 context와 맞지 않는다면 올바른 라벨로 수정합니다.
- 동일한 소분류가 여러 중분류에 속하는 경우, context의 의미에 가장 적합한 중분류를 선택합니다.  
  (예: "놀람" → 기쁨의 놀람인지, 두려움의 놀람인지 context 의미로 구분)
- 분류가 전혀 불가능하거나 불명확하면 반드시 ['중립', '중립'] 으로 출력합니다.

3. 출력 일관성
- 중분류와 소분류는 반드시 아래 제공된 목록 중 하나여야 합니다.
- 목록에 없는 단어는 절대 출력하지 않습니다.

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
- 중립 : 감동, 걱정, 고마움, 고통, 공감, 공포, 궁금함, 귀중함, 그리움, 난처함, 냉담, 놀람, 다정함, 답답함, 동정(슬픔), 만족감, 무기력, 미안함, 반가움, 불신감, 불쾌, 서먹함, 신뢰감, 안정감, 열정적임, 외로움, 위축감, 자랑스러움, 절망, 통쾌함, 편안함, 호감, 후회
"""

# 사용자 입력 템플릿
USER_PROMPT_TEMPLATE = """
Context: {context}
Category1: {category1}
Category2: {category2}
위 정보를 바탕으로 답변해주세요.
"""

class LabelRetest:
    def __init__(self, model="gpt-4.1", api_key=api_key, temperature=0.8, max_tokens=200, top_p=0.9):
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

    def create_categories(self, context, category1, category2):
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
    generator = LabelRetest()
    
    context = "첫 단체곡 넘넘 기대된다 ㅎㅎ 앞으로도 빛나는 노래들을 보여주길!!"
    category1 = "욕망"
    category2 = "기대감"
    
    new_context = generator.create_context(context, category1, category2)
    print(f"원본 Context: {context}")
    print(f"Category1: {category1}")
    print(f"Category2: {category2}")
    print(f"\n생성된 Context: {new_context}")