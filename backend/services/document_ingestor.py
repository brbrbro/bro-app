import os
from PIL import Image
from services.import_schema import DocumentPage, ImageAsset
from services.file_processor import FileProcessor


class DocumentIngestor:
    def __init__(self, processor=None):
        self.processor = processor

    def _processor(self):
        if self.processor is None:
            self.processor = FileProcessor()
        return self.processor

    def ingest(self, file_path, file_type):
        file_type = file_type.lower()
        if file_type == 'txt':
            return self._ingest_txt(file_path)
        if file_type in ('png', 'jpg', 'jpeg'):
            return self._ingest_image(file_path)
        if file_type in ('pdf', 'doc', 'docx'):
            return self._ingest_via_file_processor(file_path, file_type)
        raise ValueError(f'Unsupported file type: {file_type}')

    def _ingest_txt(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        return [DocumentPage(page=1, text=text, images=[], blocks=[])]

    def _ingest_image(self, file_path):
        filename = os.path.basename(file_path)
        with Image.open(file_path) as image:
            image.verify()
        asset = ImageAsset(
            path=file_path,
            url=f'/uploads/{filename}',
            image_type='source_image',
            page=1
        )
        return [DocumentPage(page=1, text='', images=[asset], blocks=[], page_image_url=asset.url)]

    def _ingest_via_file_processor(self, file_path, file_type):
        result = self._processor().process_file(file_path, file_type)
        images_by_page = {}
        for img in result.get('images', []):
            page = img.get('page', 1)
            images_by_page.setdefault(page, []).append(ImageAsset(
                path=img.get('path', ''),
                url=img.get('url', ''),
                image_type='embedded',
                page=page
            ))

        pages = []
        for item in result.get('text_content', []):
            page_no = item.get('page', 1)
            pages.append(DocumentPage(
                page=page_no,
                text=item.get('text', ''),
                images=images_by_page.get(page_no, []),
                blocks=[]
            ))
        return pages
