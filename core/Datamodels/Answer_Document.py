from __future__ import annotations
from core.Datamodels.Datamodels import TableAnswer, TableContext, TextAnswer, Answer, TextContext, KnowledgeObject, Question
from core.Datamodels.Question_Template import QuestionTemplate
from typing import List, Tuple


class AnswerDocument:
    '''
    A Answer Document is a Instance of a QuestionTemplate combined with the background data. It will be used
    as the Datamodel for the QA and the decision making.
    '''
    IDCounter = 1
    def __init__(self, template: QuestionTemplate, hypothesis: Hypothesis,
                 text_tuple: List[Tuple[Question, TextContext]], table_tuple: List[Tuple[Question, TableContext]], type, mode):
        self._mode: int = mode
        self._questionTemplate: QuestionTemplate = template
        self._hypothesis = hypothesis
        self.type = type

        self.__id = AnswerDocument.IDCounter
        self._table_contexts: List[Tuple[Question, TableContext]] = table_tuple
        self._text_contexts: List[Tuple[Question, TextContext]] = text_tuple

        self._answers_in_tables: List[TableAnswer] = []
        self._answers_in_text: List[TextAnswer] = []
        self._answered_by_text: bool = False
        self._answered_by_table: bool = False

        self.final_answer_knowledgeObject_text: List[KnowledgeObject] = []
        self.final_answer_textual_representation_text: List[str] = []
        self.final_result_textual_representation_text: str = ''
        self.final_result_knowledgeobject_text: str = ''


        self.final_answer_knowledgeObject_table: List[KnowledgeObject] = []
        self.final_answer_textual_representation_table: List[str] = []
        self.final_result_textual_representation_table: str = ''
        self.final_result_knowledgeobject_table: str = ''

        self._final_answer: Union[Answer, List[Answer]] = None
        self._final_result: str = ''

        AnswerDocument.IDCounter += 1

    def get_id(self) -> int:
        return self.__id

    def get_hypothesis(self) -> Hypothesis:
        return self._hypothesis

    def get_mode(self) -> int:
        return self._mode

    def get_result(self) -> Answer:
        return self._final_answer

    def set_final_text_answers(self, text_result: List[str], knowledgeObject_result: List[KnowledgeObject] ):
        self.final_answer_textual_representation_text = text_result
        self.final_answer_knowledgeObject_text= knowledgeObject_result

    def set_final_text_result(self, rextual_result: str, kObj_result):
        self.final_result_textual_representation_text= rextual_result
        self.final_result_knowledgeobject_text= kObj_result

    def set_final_table_answers(self, text_result: List[str], knowledgeObject_result: List[KnowledgeObject]):
        self.final_answer_textual_representation_table = text_result
        self.final_answer_knowledgeObject_table = knowledgeObject_result

    def set_final_table_result(self, rextual_result: str, kObj_result):
        self.final_result_textual_representation_table = rextual_result
        self.final_result_knowledgeobject_table = kObj_result

    def set_final_answer(self, answer: Answer ):
        self._final_answer = answer

    def set_final_result(self, result: str):
        self._final_result = result


    def get_table_answers_sorted_by_context(self) -> Dict:
        res = {}
        for answer in self._answers_in_tables:
            if answer.context not in res:
                res[answer.context] = [answer]
            else:
                res[answer.context].append(answer)
        return res

    def get_text_answers_sorted_by_context(self) -> Dict:
        res = {}
        for answer in self._answers_in_text:
            if answer.context not in res:
                res[answer.context] = [answer]
            else:
                res[answer.context].append(answer)
        return res

    def get_knowledgeObjects_from_answers(self) -> List[KnowledgeObject]:
        kObjs: List[KnowledgeObject] = []
        for answer in self._answers_in_text:
            kObjs.extend(answer.get_knowledgeObjects())
        for answer in self._answers_in_tables:
            kObjs.extend(answer.get_knowledgeObjects())
        return kObjs

    def get_table_tuples(self):
        return self._table_contexts

    def get_text_tuples(self):
        return self._text_contexts

    def has_answer(self) -> bool:
        return self._answered_by_text and self._answered_by_table


    @property
    def questionTemplate(self) -> QuestionTemplate:
        return self._questionTemplate


    @property
    def answered_by_text(self) -> bool:
        return self._answered_by_text


    @property
    def answered_by_table(self) -> bool:
        return self._answered_by_table


    @property
    def table_contexts(self) -> List[TableContext]:
        return self._table_contexts

    @table_contexts.setter
    def table_contexts(self, value: List[TableContext]):
        self._table_contexts = value

    @property
    def text_contexts(self) -> List[TextContext]:
        return self._text_contexts

    @text_contexts.setter
    def text_contexts(self, value: List[TextContext]):
        self._text_contexts = value





