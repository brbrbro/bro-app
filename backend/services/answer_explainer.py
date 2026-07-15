import os
import json
from openai import OpenAI


def _get_config():
    return {
        'api_key': os.environ.get('AI_API_KEY', os.environ.get('ARK_API_KEY', '')),
        'base_url': os.environ.get('AI_BASE_URL', os.environ.get('ARK_BASE_URL', '')),
        'model': os.environ.get('AI_MODEL', os.environ.get('ARK_MODEL', ''))
    }


class AnswerExplainer:
    def __init__(self):
        self.config = _get_config()
        self.client = None

    def _get_client(self):
        if self.client is None and self.config['api_key']:
            kwargs = {'api_key': self.config['api_key']}
            if self.config.get('base_url'):
                kwargs['base_url'] = self.config['base_url']
            self.client = OpenAI(**kwargs)
        return self.client

    def complete(self, question):
        if question.get('answer') and question.get('explanation'):
            return {
                'answer': question.get('answer', ''),
                'explanation': question.get('explanation', '')
            }

        client = self._get_client()
        if not client or not self.config.get('model'):
            return {
                'answer': question.get('answer', ''),
                'explanation': question.get('explanation', '')
            }

        prompt = (
            '请根据下方题目给出标准答案和简短解析。\n'
            '只返回 JSON，不要 Markdown，不要额外说明。\n'
            '格式：{"answer":"...","explanation":"..."}\n\n'
            f'题目：{question.get("content", "")}\n'
            f'选项：{json.dumps(question.get("options", []), ensure_ascii=False)}\n'
            f'科目：{question.get("subject", "")}\n'
        )

        try:
            response = client.chat.completions.create(
                model=self.config['model'],
                messages=[
                    {'role': 'system', 'content': '你是专业的题目解答助手，回答严谨、简洁。'},
                    {'role': 'user', 'content': prompt}
                ],
                temperature=0.2
            )
            content = response.choices[0].message.content.strip()
            content = content.strip('`')
            if content.startswith('json'):
                content = content[4:].strip()
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
