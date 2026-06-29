import os
import re
import json
from typing import List, Dict, Any
import fitz  # PyMuPDF for PDF
from PIL import Image
import mammoth  # for Word

class FileProcessor:
    """处理上传的文件，提取文本和图片"""

    UPLOAD_DIR = os.environ.get('UPLOAD_DIR') or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads')
    IMAGE_DIR = os.environ.get('IMAGE_DIR') or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'images')
    
    def __init__(self):
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)
        os.makedirs(self.IMAGE_DIR, exist_ok=True)
    
    def process_file(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """处理文件，返回提取的文本和图片列表"""
        if file_type == 'pdf':
            return self._process_pdf(file_path)
        elif file_type in ['doc', 'docx']:
            return self._process_word(file_path)
        elif file_type in ['jpg', 'jpeg', 'png']:
            return self._process_image(file_path)
        elif file_type == 'txt':
            return self._process_text(file_path)
        else:
            raise ValueError(f"不支持的文件类型: {file_type}")
    
    def _process_pdf(self, file_path: str) -> Dict[str, Any]:
        """处理 PDF 文件"""
        doc = fitz.open(file_path)
        text_content = []
        images = []

        try:
            total_pages = len(doc)
            for page_num in range(total_pages):
                page = doc[page_num]
                text = page.get_text()
                text_content.append({
                    'page': page_num + 1,
                    'text': text
                })

                image_list = page.get_images()
                page_image_count = 0
                for img_index, img in enumerate(image_list, start=1):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]

                    image_filename = f"pdf_{os.path.basename(file_path)}_p{page_num}_{img_index}.{image_ext}"
                    image_path = os.path.join(self.IMAGE_DIR, image_filename)
                    with open(image_path, "wb") as f:
                        f.write(image_bytes)

                    images.append({
                        'page': page_num + 1,
                        'path': image_path,
                        'url': f'/static/images/{image_filename}'
                    })
                    page_image_count += 1

                if not text.strip() and page_image_count == 0:
                    render_filename = f"pdf_{os.path.basename(file_path)}_p{page_num}_render.png"
                    render_path = os.path.join(self.IMAGE_DIR, render_filename)
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                    pix.save(render_path)
                    images.append({
                        'page': page_num + 1,
                        'path': render_path,
                        'url': f'/static/images/{render_filename}'
                    })
        finally:
            doc.close()

        return {
            'type': 'pdf',
            'pages': total_pages,
            'text_content': text_content,
            'images': images
        }
    
    def _process_word(self, file_path: str) -> Dict[str, Any]:
        """处理 Word 文件"""
        with open(file_path, "rb") as docx_file:
            result = mammoth.convert_to_html(docx_file)
            html = result.value
            text = self._html_to_text(html)
            
        return {
            'type': 'word',
            'text_content': [{'page': 1, 'text': text}],
            'images': []
        }
    
    def _process_image(self, file_path: str) -> Dict[str, Any]:
        """处理图片文件"""
        filename = os.path.basename(file_path)
        dest_path = os.path.join(self.IMAGE_DIR, filename)
        Image.open(file_path).save(dest_path)
        
        return {
            'type': 'image',
            'text_content': [{'page': 1, 'text': ''}],
            'images': [{
                'page': 1,
                'path': dest_path,
                'url': f'/static/images/{filename}'
            }]
        }
    
    def _process_text(self, file_path: str) -> Dict[str, Any]:
        """处理文本文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        return {
            'type': 'text',
            'text_content': [{'page': 1, 'text': text}],
            'images': []
        }
    
    def _html_to_text(self, html: str) -> str:
        """将 HTML 转为纯文本"""
        text = re.sub(r'<[^>]+>', '', html)
        return text
    
    def save_upload(self, file_storage, filename: str) -> str:
        """保存上传的文件"""
        file_path = os.path.join(self.UPLOAD_DIR, filename)
        file_storage.save(file_path)
        return file_path
