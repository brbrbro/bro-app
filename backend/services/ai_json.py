import json
import re


def parse_ai_questions_json(text):
    cleaned = text.strip()
    cleaned = re.sub(r'^```\s*(?:json)?', '', cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r'```$', '', cleaned).strip()

    match = re.search(r'\[[\s\S]*\]', cleaned)
    if match:
        cleaned = match.group(0)

    data = json.loads(cleaned)
    if not isinstance(data, list):
        raise ValueError('AI output must be a list')

    normalized = []
    for item in data:
        if not isinstance(item, dict):
            continue
        normalized.append({
            'content': item.get('content', ''),
            'options': item.get('options', []),
            'answer': item.get('answer', ''),
            'explanation': item.get('explanation', ''),
            'type': item.get('type', 'unknown'),
            'difficulty': item.get('difficulty', 3)
        })
    return normalized
