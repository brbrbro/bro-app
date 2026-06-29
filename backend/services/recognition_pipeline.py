from services.import_schema import QuestionCandidate
from services.question_segmenter import QuestionSegmenter
from services.ai_parser import AIParser


class RecognitionPipeline:
    def __init__(self, image_parser=None):
        self.segmenter = QuestionSegmenter()
        self.image_parser = image_parser or AIParser()

    def recognize(self, pages, subject=''):
        candidates = []
        text_pages = [p for p in pages if p.text and p.text.strip()]
        image_only_pages = [p for p in pages if not (p.text and p.text.strip()) and p.images]

        if text_pages:
            candidates.extend(self.segmenter.segment(text_pages))

        for page in image_only_pages:
            parsed_any = False
            for image in page.images:
                parsed_questions = self.image_parser.parse_image(image.path, subject=subject)
                for item in parsed_questions:
                    candidates.append(QuestionCandidate(
                        index=0,
                        content=item.get('content', ''),
                        options=item.get('options', []),
                        answer=item.get('answer', ''),
                        explanation=item.get('explanation', ''),
                        question_type=item.get('type', 'unknown'),
                        difficulty=item.get('difficulty', 3),
                        source_page=page.page,
                        raw_ocr_text=item.get('raw_text', ''),
                        images=[image],
                        confidence_detail={'text': 0.75, 'layout': 0.5, 'image': 0.9}
                    ))
                    parsed_any = True
            if not parsed_any:
                candidates.append(QuestionCandidate(
                    index=0,
                    content='[图片题待识别]',
                    options=[],
                    answer='',
                    explanation='',
                    question_type='unknown',
                    difficulty=3,
                    source_page=page.page,
                    raw_ocr_text='',
                    images=page.images,
                    confidence_detail={'text': 0.2, 'layout': 0.4, 'image': 0.8}
                ))

        candidates.sort(key=lambda candidate: candidate.source_page or 0)
        for index, candidate in enumerate(candidates, start=1):
            candidate.index = index
        return candidates
