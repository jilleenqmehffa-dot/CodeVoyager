from uuid import UUID

from pydantic import BaseModel

from app.models.code_symbols import CodeSymbolType


class TextSearchResultSchema(BaseModel):
    file_id: UUID
    file_path: str
    line_number: int
    matched_text: str


class SymbolSearchResultSchema(BaseModel):
    symbol_id: UUID
    symbol_name: str
    symbol_type: CodeSymbolType
    file_id: UUID
    file_path: str
    start_line: int
    end_line: int
