import os
import json
from openai import OpenAI


class AnswerExplainer:
    def __init__(self):
        self.api_key = os.environ.get('OPENAI_API_KEY', '')
        self.client = None
        self.model = os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')

    def _get_client(self):
        if not self.client and self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        return self.client

    def complete(self, question):
        if question.get('answer') and question.get('explanation'):
            return {
                'answer': question.get('answer', ''),
                'explanation': question.get('explanation', '')
            }

        client = self._get_client()
        if not client:
            return {
                'answer': question.get('answer', ''),
                'explanation': question.get('explanation', '')
            }

        prompt = f"""
请根据题目内容给出标准答案和简短解析。
只返回 JSON，不要 Markdown，不要额外说明。
格式：{{"answer":"...","explanation":"..."}}

题目：{question.get('content', '')}
选项：{json.dumps(question.get('options', []), ensure_ascii=False)}
科目：{question.get('subject', '')}
"""
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {'role': 'system', 'content': '你是专业的高中题目解答助手。'},
                    {'role': 'user', 'content': prompt}
                ],
                temperature=0.2
            )
            content = response.choices[0].message.content.strip()
            data = json.loads(content)
            return {
                'answer': data.get('answer', question.get('answer', '')),
                'explanation': data.get('explanation', question.get('explanation', ''))
            }
        except Exception:
            return {
                'answer': question.get('answer', ''),
                'explanation': question.get('explanation', '')
            }
