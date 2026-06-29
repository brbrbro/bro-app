import fitz

from services.file_processor import FileProcessor


def test_pdf_empty_text_page_is_rendered_as_image(tmp_path, monkeypatch):
    upload_dir = tmp_path / 'uploads'
    image_dir = tmp_path / 'images'
    monkeypatch.setattr(FileProcessor, 'UPLOAD_DIR', str(upload_dir))
    monkeypatch.setattr(FileProcessor, 'IMAGE_DIR', str(image_dir))

    pdf_path = tmp_path / 'scan.pdf'
    doc = fitz.open()
    doc.new_page(width=200, height=100)
    doc.save(pdf_path)
    doc.close()

    result = FileProcessor().process_file(str(pdf_path), 'pdf')
    assert result['pages'] == 1
    assert result['text_content'][0]['text'] == ''
    assert len(result['images']) == 1
    assert result['images'][0]['path'].endswith('.png')
