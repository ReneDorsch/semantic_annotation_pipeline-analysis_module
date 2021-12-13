from typing import Optional, List
from pydantic import BaseModel, Field

class InputWord(BaseModel):
    id: int
    word: str
    normalized_word: str
    longform_word: str
    start_pos: int
    end_pos: int
    whitespace_after_word: int
    prev_word: Optional[int]
    knowledgeObject_reference: Optional[int]

class KnowledgeObject(BaseModel):
    id: int
    category: str
    labels: List[str]

class InputSentence(BaseModel):
    words: List[InputWord]
    knowledgeObject_references: List[int]

class InputParagraph(BaseModel):
    sentences: List[InputSentence]
    knowledgeObject_references: List[int]

class InputChapter(BaseModel):
    paragraphs: List[InputParagraph]
    knowledgeObject_references: List[int]

class InputCell(BaseModel):
    text: str
    category: str
    knowledgeObject_references: Optional[List[int]]


class InputLine(BaseModel):
    cells: List[InputCell]


class InputTable(BaseModel):
    #textual_representation: List[InputSentence]
    knowledgeObject_references: List[int]
    description: Optional[str]
    table_header: InputLine
    data: List[InputLine]
    units:  List[str]

class InputData(BaseModel):
    document_id: str
    chapters: List[InputChapter]
    knowledgeObjects: List[KnowledgeObject]
    abstract: Optional[InputChapter]
    tables: Optional[List[InputTable]]