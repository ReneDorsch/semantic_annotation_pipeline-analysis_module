from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Tuple, Any

class documenTuple(BaseModel):
    answerDocument_id: int
    answer_id: int


class AnswerDocument(BaseModel):
    id: int
    final_result: str
    final_answer: List
    type: str
    question_template: Tuple[str, str]
    final_answer_knowledgeObject_table_ids: List[int]
    final_answer_knowledgeObject_text_ids: List[int]
    final_answer_textual_representation_text: Any
    final_answer_textual_representation_table: Any
    final_result_knowledgeobject_text: str
    final_result_knowledgeobject_table: str
    table_answer_ids: List[int]
    text_answer_ids: List[int]


class Answer(BaseModel):
    id: int
    textual_representation: str
    question_id: int
    knowledgeObject_ids: List[int]
    context_id: int
    answer_source: str


class Question(BaseModel):
    id: int
    question: str


class Context(BaseModel):
    id: int
    textual_representation: str
    knowledgeObject_ids: List[int]


class KnowledgeObject(BaseModel):
    id: int
    category: str
    labels: List[str]

class Hypothesis(BaseModel):
    answer_document_tuples: List[documenTuple] = Field(default=[])

class LogFile(BaseModel):
    answer_documents: List[AnswerDocument] = Field(
        description="A list of answers corresponding to the questiontemplates. ")
    hypothesis: List[Hypothesis] = Field(description="A List of Hypothesis that has been identified in the document. ")
    answers: List[Answer] = Field(description="A list of all generated answers for all the questions in the document. ")
    contexts: List[Context] = Field(description="A list of contexts corresponding to the answers and questions. ")
    questions: List[Question] = Field(description="A list of questions generated for the answer documents. ")
    knowledgeObjects: List[KnowledgeObject]
    document_id: str = ''

class AnswerDocumentList(BaseModel):
    answer_documents: List[AnswerDocument]
    document_id: str

class HypothesisList(BaseModel):
    hypothesis: List[Hypothesis]
    answer_documents: List[AnswerDocument]
    document_id: str





AnswerDocument.update_forward_refs()
LogFile.update_forward_refs()
