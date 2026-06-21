from services.document_ingestor import DocumentIngestor


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
