import os
import json
import re
from typing import List, Dict, Any
from openai import OpenAI

class AIParser:
    """使用 AI 识别和解析题目"""
    
    def __init__(self):
        self.api_key = os.environ.get('OPENAI_API_KEY', '')
        self.client = None
        self.model = 'gpt-4-vision-preview'
    
    def _get_client(self):
        if not self.client and self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        return self.client
    
    def parse_text(self, text: str, subject: str = '') -> List[Dict[str, Any]]:
        """从文本中解析题目"""
        client = self._get_client()
        if not client:
            return self._fallback_parse(text)
        
        prompt = f"""
        请从以下文本中识别并解析所有题目。每道题目请提取：
        1. 题目内容
        2. 选项（如果是选择题）
        3. 正确答案
        4. 解析（如果有）
        5. 题型（选择题/填空题/解答题）
        6. 难度（1-5）
        
        科目：{subject or '未指定'}
        
        文本内容：
        {text}
        
        请按 JSON 格式返回，格式如下：
        [
          {{
            "content": "题目内容",
            "options": ["A. xxx", "B. xxx", "C. xxx", "D. xxx"],
            "answer": "A",
            "explanation": "解析内容",
            "type": "choice",
            "difficulty": 3
          }}
        ]
        
        只返回 JSON，不要其他说明。
        """
        
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的教育题目解析助手。"},
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
        """从图片中解析题目"""
        client = self._get_client()
        if not client:
            return []
        
        import base64
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": f"请识别图片中的题目，科目：{subject or '未指定'}。按 JSON 格式返回题目内容、选项、答案、解析。"},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000
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
        """当 AI 不可用时，使用简单的规则解析"""
        questions = []
        pattern = r'(?:^|\n)\s*(\d+)[\.\、\.\.]\s*(.+?)(?=\n\s*\d+[\.\、\.\.]|$)'
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
        """批量解析文件内容"""
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
