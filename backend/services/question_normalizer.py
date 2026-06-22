class QuestionNormalizer:
    def to_parsed_payload(self, candidate, defaults):
        data = candidate.to_dict()
        return {
            'content': data['content'],
            'options': data['options'],
            'answer': data['answer'],
            'explanation': data['explanation'],
            'type': data['type'],
            'difficulty': data['difficulty'],
            'exam_type': defaults.get('exam_type', ''),
            'subject': defaults.get('subject', ''),
            'grade': defaults.get('grade', ''),
            'knowledge_point': defaults.get('knowledge_point', '不详'),
            'source_page': data['source_page'],
            'bbox': data['bbox'],
            'images': data['images'],
            'formula_latex': data['formula_latex'],
            'formula_images': data['formula_images'],
            'raw_ocr_text': data['raw_ocr_text'],
            'confidence_detail': data['confidence_detail'],
            'confidence': data['confidence']
        }
