from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ImageAsset:
    path: str
    url: str
    image_type: str = 'diagram'
    page: Optional[int] = None
    bbox: Optional[Dict[str, Any]] = None
    ocr_text: str = ''

    def to_dict(self) -> Dict[str, Any]:
        return {
            'path': self.path,
            'url': self.url,
            'type': self.image_type,
            'page': self.page,
            'bbox': self.bbox,
            'ocr_text': self.ocr_text
        }


@dataclass
class FormulaAsset:
    latex: str
    image_url: str = ''
    bbox: Optional[Dict[str, Any]] = None
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'latex': self.latex,
            'image_url': self.image_url,
            'bbox': self.bbox,
            'confidence': self.confidence
        }


@dataclass
class DocumentPage:
    page: int
    text: str
    images: List[ImageAsset] = field(default_factory=list)
    blocks: List[Dict[str, Any]] = field(default_factory=list)
    page_image_url: str = ''

    def to_dict(self) -> Dict[str, Any]:
        return {
            'page': self.page,
            'text': self.text,
            'images': [img.to_dict() for img in self.images],
            'blocks': self.blocks,
            'page_image_url': self.page_image_url
        }


@dataclass
class QuestionCandidate:
    index: int
    content: str
    options: List[Any] = field(default_factory=list)
    answer: str = ''
    explanation: str = ''
    question_type: str = 'unknown'
    difficulty: int = 3
    source_page: Optional[int] = None
    bbox: Optional[Dict[str, Any]] = None
    raw_ocr_text: str = ''
    images: List[ImageAsset] = field(default_factory=list)
    formulas: List[FormulaAsset] = field(default_factory=list)
    confidence_detail: Dict[str, float] = field(default_factory=dict)

    def confidence(self) -> float:
        if not self.confidence_detail:
            return 0.0
        return round(sum(self.confidence_detail.values()) / len(self.confidence_detail), 3)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'index': self.index,
            'content': self.content,
            'options': self.options,
            'answer': self.answer,
            'explanation': self.explanation,
            'type': self.question_type,
            'difficulty': self.difficulty,
            'source_page': self.source_page,
            'bbox': self.bbox,
            'raw_ocr_text': self.raw_ocr_text,
            'images': [img.to_dict() for img in self.images],
            'formula_latex': [f.latex for f in self.formulas if f.latex],
            'formula_images': [f.image_url for f in self.formulas if f.image_url],
            'formulas': [f.to_dict() for f in self.formulas],
            'confidence_detail': self.confidence_detail,
            'confidence': self.confidence()
        }
