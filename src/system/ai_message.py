from openai import AsyncOpenAI
from config import config
import logging

MAX_TOKENS = 2000

class AI:
    def __init__(self):
        ai_token = config.ai_token.get_secret_value()
        
        self.system_instructions = """
        Ты — лаконичный ментор. Твоя цель: направить ученика к решению, не давая ответа.
        СТРОГИЕ ПРАВИЛА:
        1. ЗАПРЕЩЕНО давать готовый ответ или финальный результат.
        2. ЗАПРЕЩЕНО использовать числа из вопроса в примерах.
        3. План ответа: 
           Навести человека на решение, обучить его.
        """
        
        self.client = AsyncOpenAI(
            api_key=ai_token,
            base_url="https://openrouter.ai/api/v1",
            timeout=60.0, 
            max_retries=3
        )
        self.MODEL = "mistralai/ministral-14b-2512"

    async def get_request_to_ai(self, quest: str) -> str:
        try:
            response = await self.client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": self.system_instructions},
                    {"role": "user", "content": quest}
                ],
                temperature=0.3,
                max_tokens=MAX_TOKENS
            )
            if response.choices[0].message.content is None: 
                logging.error("AI message is empty")
                return "Нейросеть задумалась. Попробуй еще раз через минуту."
            return response.choices[0].message.content.strip()
        except Exception as e:
            logging.error(f"AI Error: {e}")
            return "Нейросеть задумалась. Попробуй еще раз через минуту."