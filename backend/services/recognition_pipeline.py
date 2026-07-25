import os
from services.import_schema import QuestionCandidate
from services.question_segmenter import QuestionSegmenter
from services.ai_parser import AIParser


def _try_ocr(image_path, lang='chi_tra+eng'):
    try:
        import pytesseract
        from PIL import Image
        pytesseract.pytesseract.tesseract_cmd = os.environ.get(
            'TESSERACT_CMD',
            r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        )
        tessdata_prefix = os.environ.get('TESSDATA_PREFIX')
        config = f'--tessdata-dir "{tessdata_prefix}" --psm 6' if tessdata_prefix else '--psm 6'
        with Image.open(image_path) as img:
            return pytesseract.image_to_string(img, lang=lang, config=config)
    except Exception as e:
        print(f"OCR error: {e}")
        return ''


class RecognitionPipeline:
    def __init__(self, image_parser=None):
        self.segmenter = QuestionSegmenter()
        self.image_parser = image_parser or AIParser()

    def recognize(self, pages, subject=''):
        candidates = []
        text_pages = []
        image_only_pages = []

        for page in pages:
            if page.text and page.text.strip():
                text_pages.append(page)
            elif page.images:
                image_only_pages.append(page)

        for page in image_only_pages:
            ocr_text = ''
            for image in page.images:
                ocr_text += _try_ocr(image.path) + '\n'
            if ocr_text.strip():
                text_pages.append(__import__('services.import_schema', fromlist=['DocumentPage']).DocumentPage(
                    page=page.page,
                    text=ocr_text,
                    images=page.images
                ))
            else:
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

        if text_pages:
            candidates.extend(self.segmenter.segment(text_pages))

        candidates.sort(key=lambda candidate: candidate.source_page or 0)
        for index, candidate in enumerate(candidates, start=1):
            candidate.index = index
        return candidates
