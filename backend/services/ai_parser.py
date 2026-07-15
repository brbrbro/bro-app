import os
import json
import re
from typing import List, Dict, Any
from openai import OpenAI


def _get_config():
    return {
        'api_key': os.environ.get('AI_API_KEY', os.environ.get('ARK_API_KEY', '')),
        'base_url': os.environ.get('AI_BASE_URL', os.environ.get('ARK_BASE_URL', '')),
        'model': os.environ.get('AI_MODEL', os.environ.get('ARK_MODEL', ''))
    }


class AIParser:
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

    def parse_text(self, text: str, subject: str = '') -> List[Dict[str, Any]]:
        client = self._get_client()
        if not client or not self.config.get('model'):
            return self._fallback_parse(text)

        prompt = f"""
请从以下文本中识别并解析所有题目。每道题目请提取：
1. 题目内容
2. 选项（如果是选择题）
3. 正确答案
4. 解析（如果有）
5. 题型（choice/blank/comprehensive）
6. 难度（1-5）

科目：{subject or '未指定'}

文本内容：
{text}

请按 JSON 数组格式返回：
[{{"content":"...","options":[{{"key":"A","text":"..."}}],"answer":"A","explanation":"...","type":"choice","difficulty":3}}]
只返回 JSON，不要其他说明。
"""
        try:
            response = client.chat.completions.create(
                model=self.config['model'],
                messages=[
                    {"role": "system", "content": "你是专业的教育题目解析助手。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            content = response.choices[0].message.content
            json_match = re.search(r'\[.*?\]', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return []
        except Exception as e:
            print(f"AI 解析错误: {e}")
            return self._fallback_parse(text)

    def parse_image(self, image_path: str, subject: str = '') -> List[Dict[str, Any]]:
        client = self._get_client()
        if not client or not self.config.get('model'):
            return []

        import base64
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')

        try:
            response = client.chat.completions.create(
                model=self.config['model'],
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"请识别图片中的题目，科目：{subject or '未指定'}。按 JSON 数组格式返回题目内容、选项、答案、解析、题型、难度。只返回 JSON。"},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                    ]
                }],
                max_tokens=4000
            )
            content = response.choices[0].message.content
            json_match = re.search(r'\[.*?\]', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return []
        except Exception as e:
            print(f"AI 图片解析错误: {e}")
            return []

    def _fallback_parse(self, text: str) -> List[Dict[str, Any]]:
        questions = []
        pattern = r'(?:^|\n)[ \t]*(\d+)[\.、．][ \t]*(.+?)(?=\n[ \t]*\d+[\.、．]|$)'
        matches = re.findall(pattern, text, re.DOTALL)
        for num, content in matches:
            questions.append({
                'content': content.strip(),
                'options': [],
                'answer': '',
                'explanation': '',
                'type': 'unknown',
                'difficulty': 3
            })
        return questions

    def batch_parse(self, file_result: Dict[str, Any], subject: str = '') -> List[Dict[str, Any]]:
        all_questions = []
        for page_data in file_result.get('text_content', []):
            text = page_data['text']
            if text.strip():
                questions = self.parse_text(text, subject)
                all_questions.extend(questions)
        for img_data in file_result.get('images', []):
            questions = self.parse_image(img_data['path'], subject)
            all_questions.extend(questions)
        return all_questions
