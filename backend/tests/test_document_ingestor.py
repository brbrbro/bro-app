from services.document_ingestor import DocumentIngestor


class FakeProcessor:
    def process_file(self, file_path, file_type):
        return {
            'text_content': [{'page': 2, 'text': '2. 测试题\n答案：A'}],
            'images': [{'page': 2, 'path': '/tmp/img.png', 'url': '/static/images/img.png'}]
        }


def test_ingest_pdf_delegates_to_processor_and_maps_embedded_images():
    pages = DocumentIngestor(processor=FakeProcessor()).ingest('/tmp/fake.pdf', 'pdf')
    assert len(pages) == 1
    assert pages[0].page == 2
    assert '测试题' in pages[0].text
    assert len(pages[0].images) == 1
    assert pages[0].images[0].image_type == 'embedded'
    assert pages[0].images[0].url == '/static/images/img.png'


def test_ingest_txt_file(tmp_path):
    p = tmp_path / 'questions.txt'
    p.write_text('1. 1+1=?\n答案：2', encoding='utf-8')
    pages = DocumentIngestor().ingest(str(p), 'txt')
    assert len(pages) == 1
    assert pages[0].page == 1
    assert '1+1' in pages[0].text


def test_ingest_image_file_creates_page(tmp_path):
    from PIL import Image
    img = Image.new('RGB', (100, 80), color='white')
    p = tmp_path / 'q.png'
    img.save(p)
    pages = DocumentIngestor().ingest(str(p), 'png')
    assert len(pages) == 1
    assert pages[0].page == 1
    assert len(pages[0].images) == 1
    assert pages[0].images[0].image_type == 'source_image'
