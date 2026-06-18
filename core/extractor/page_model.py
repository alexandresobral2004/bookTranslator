from pydantic import BaseModel
from typing import List, Optional, Tuple

class TextSpan(BaseModel):
    text: str
    font_name: str
    size: float
    bold: bool
    italic: bool
    color: int

class Block(BaseModel):
    block_type: str  # "text", "image", etc.
    bbox: Tuple[float, float, float, float]  # (x0, y0, x1, y1)
    spans: List[TextSpan] = []
    
    @property
    def text(self) -> str:
        """Retorna todo o texto concatenado do bloco."""
        return "".join(span.text for span in self.spans)

class Page(BaseModel):
    page_num: int
    width: float
    height: float
    blocks: List[Block] = []

    @property
    def text(self) -> str:
        """Retorna todo o texto da página."""
        return "\n\n".join(block.text for block in self.blocks if block.block_type == "text")
