from __future__ import annotations
from typing import List, Set
from core.Datamodels.Answer_Document import _AnswerDocument
import itertools
from core.schemas import LogFile

class HypothesisSpace:

    def __init__(self):
        self._answered_documents: List[_AnswerDocument] = []
        self._hypothesis: List[Hypothesis] = []
        self._variations: List[_AnswerDocument] = []
        self._static_parameters: List[_AnswerDocument] = []


    def has_answer_for_category(self, questionCategory) -> bool:
        for answer in self._answered_documents:
            if questionCategory == answer.questionTemplate.get_questionType()[0]:
                return True
        return False

    def get_answer_for_category(self, questionCategory) -> _AnswerDocument:
        for answer in self._answered_documents:
            if questionCategory == answer.questionTemplate.get_questionType()[0]:
                final_answers = answer.get_result()
                kObjs: List[KnowledgeObject] = []
                labels: List[str] = []
                for answer in final_answers:
                    kObjs.extend(answer.get_knowledgeObjects())
                    labels.append(answer.textual_representation)
                if len(kObjs) > 0:
                    return kObjs
                else:
                    return labels


    def get_answers(self) -> List[_AnswerDocument]:
        return self._answered_documents


    def save_answerDoc(self, doc: _AnswerDocument) -> None:
        if doc.type == 'VARIATION':
            self._variations.append(doc)
        elif doc.type == 'STATIC':
            self._static_parameters.append(doc)
        elif doc.type == 'OUTPUT':
            doc._hypothesis.add_answerDoc(doc)

        self._answered_documents.append(doc)


    def to_io(self) -> LogFile:
        return LogFile(**self.save_hypothesis_as_json())


    def save_hypothesis_as_json(self) -> dict:
        res = {}
        answered_documents = []
        _knowledgeObjects = []

        for document in self._answered_documents:
            if document._final_answer is not None:
                final_answer: List[int] = [_.get_id() for _ in document._final_answer]
            else:
                final_answer = []

            _knowledgeObjects.extend(document.get_knowledgeObjects_from_answers())
            answered_documents.append({
                'id': document.get_id(),
                'final_result': document._final_result,
                'final_answer': final_answer,
                'type': document.type,
                'mode': document.get_mode(),
                'question_template': document.questionTemplate.get_questionType(),

                'final_answer_knowledgeObject_table_ids': [answer.get_id() for answer in
                                                        document.final_answer_knowledgeObject_table],
                'final_answer_textual_representation_table': [document.final_answer_textual_representation_table],
                'final_result_knowledgeobject_table': document.final_result_knowledgeobject_table,
                'final_result_textual_representation_table': document.final_result_textual_representation_table,


                'final_answer_knowledgeObject_text_ids': [answer.get_id() for answer in
                                                       document.final_answer_knowledgeObject_text],
                'final_answer_textual_representation_text': document.final_answer_textual_representation_text,
                'final_result_knowledgeobject_text': document.final_result_knowledgeobject_text,
                'final_result_textual_representation_text': document.final_result_textual_representation_text,

                'table_answer_ids': [_.get_id() for _ in document._answers_in_tables],
                'text_answer_ids': [_.get_id() for _ in document._answers_in_text]
            })

        hypothesis = []
        for hypo in self._hypothesis:
            hypothesis.append(hypo.save_hypothesis_for_api())

        contexts = []
        answers = []
        questions = []
        for doc in self._answered_documents:
            for question, table_context in doc.table_contexts:
                contexts.append(table_context.save_for_api())
                questions.append(question.save_for_api())
            for question, text_context in doc.text_contexts:
                contexts.append(text_context.save_for_api())
                questions.append(question.save_for_api())

            for answer in doc._answers_in_text:
                answers.append(answer.save_for_api())
            for answer in doc._answers_in_tables:
                answers.append(answer.save_for_api())


        knowledgeObjects = []
        for kObj in set(_knowledgeObjects):
            knowledgeObjects.append(kObj.save_for_api())

        res['answer_documents'] = answered_documents
        res['hypothesis'] = hypothesis
        res['answers'] = answers
        res['questions'] = questions
        res['contexts'] = contexts
        res['knowledgeObjects'] = knowledgeObjects
        return res


    def _build_hypothesis(self) -> List[Hypothesis]:
        hypothesis: Set[Hypothesis] = set()
        # Build Questions so they are distinct to the other hypothesis
        # Clean the variationSet
        zwerg = []
        for variation in self._variations:

            # If there is only one answer to a variation, it is not a
            # variation, so it should be a staticParameter
            if len(variation.get_result()) <= 1:
                self._static_parameters.append(variation)
                zwerg.append(variation)

        for variation in zwerg:
            self._variations.remove(variation)

        # create each variation combination -> e.g for Pressure: [0.8Gpa, 1.47 Gpa]; for Humidity [0.2%, 0.8%]
        # -> creates a List of all Variations -> e.g. [[0.8Gpa, 1.47 Gpa], [0.2%, 0.8%]]
        variations = [var.get_result() for var in self._variations]
        variation_combinations = set(itertools.product(*variations))

        # create for each variation combination a single hypothesis
        # [[0.8Gpa, 1.47 Gpa], [0.2 %, 0.8 %]] -> [(0.8Gpa, 0.2%), (0.8Gpa, 0.8%), (1.47Gpa, 0.2%), (1.47Gpa, 0.8%)]
        for variable_parameter_set in variation_combinations:
            if len(variable_parameter_set) == 0:
                continue
            else:
                hypothesis.add(Hypothesis(variable_parameter_set, self._variations, self._static_parameters))

        self._hypothesis = hypothesis
        return hypothesis


class Hypothesis:
    ID_Counter = 1
    def __init__(self, variables, answers_variation: List[_AnswerDocument], answers_static: List[_AnswerDocument]):
        self._id = Hypothesis.ID_Counter
        self.synonym: Answer = None

        self.variation: Set[_AnswerDocument] = self._set_variation_parameters(variables, answers_variation)
        self.staticBodyParameters: Set[_AnswerDocument] = self._set_static_body_parameters(answers_static)
        self.staticCounterBodyParameters: Set[_AnswerDocument] = self._set_static_counterbody_parameters(answers_static)
        self.staticParameters: Set[_AnswerDocument] = self._set_static_parameters(answers_static)
        self.frictionBehaviour: Set[_AnswerDocument] = set()
        self.wearBehaviour: Set[_AnswerDocument] = set()

        Hypothesis.ID_Counter += 1

    def save_hypothesis_for_api(self) -> dict:
        friction_behaviour = []
        wear_behaviour = []
        static_parameters = []
        variation = []


        for doc, answer in self.wearBehaviour:
            wear_behaviour.append({
                'answerDocument_id': doc.get_id(),
                'answer_id': answer.get_id() if answer is not None else ''
            })

        for doc, answer in self.frictionBehaviour:
            friction_behaviour.append({
                'answerDocument_id': doc.get_id(),
                'answer_id': answer.get_id() if answer is not None else ''
            })

        for doc, answer in self.staticBodyParameters:
            static_parameters.append({
                'answerDocument_id': doc.get_id(),
                'answer_id': answer.get_id() if answer is not None else ''
            })

        for doc, answer in self.staticCounterBodyParameters:
            static_parameters.append({
                'answerDocument_id': doc.get_id(),
                'answer_d': answer.get_id() if answer is not None else ''
            })

        for doc, answer in self.staticParameters:
            static_parameters.append({
                'answerDocument_id': doc.get_id(),
                'answer_id': answer.get_id() if answer is not None else ''
            })

        for doc, answer in self.variation:
            variation.append({
                'answerDocument_id': doc.get_id(),
                'answer_id': answer.get_id() if answer is not None else ''
            })



        return {
            'answer_documents': variation + static_parameters + friction_behaviour + wear_behaviour,
        }

    def get_variations(self) -> Set[_AnswerDocument]:
        return [_[1] for _ in self.variation]


    def add_answerDoc(self, answerDoc: _AnswerDocument):
        if answerDoc.questionTemplate._broader_question_type == 'FRICTION_BEHAVIOUR':
            if len(answerDoc.get_result()) > 0:
                self.frictionBehaviour.add((answerDoc, answerDoc._final_answer[0]))
            else:
                self.frictionBehaviour.add((answerDoc, None))

        elif answerDoc.questionTemplate._broader_question_type == 'WEAR_BEHAVIOUR':
            if len(answerDoc.get_result()) > 0:
                self.frictionBehaviour.add((answerDoc, answerDoc._final_answer[0]))
            else:
                self.frictionBehaviour.add((answerDoc, None))

    def _set_static_body_parameters(self, answers_static: List[_AnswerDocument]):
        res = set()
        for answerDoc in answers_static:
            if answerDoc.questionTemplate._broader_question_type == 'BODY':
                if len(answerDoc.get_result()) > 0:
                    res.add((answerDoc, answerDoc.get_result()[0]))
                else:
                    res.add((answerDoc, None))
        return res

    def _set_static_counterbody_parameters(self, answers_static: List[_AnswerDocument]):
        res = set()
        for answerDoc in answers_static:
            if answerDoc.questionTemplate._broader_question_type == 'COUNTERBODY':
                if len(answerDoc.get_result()) > 0:
                    res.add((answerDoc, answerDoc.get_result()[0]))
                else:
                    res.add((answerDoc, None))
        return res


    def _set_static_parameters(self, answers_static: List[_AnswerDocument]):
        res = set()
        for answerDoc in answers_static:
            if answerDoc.questionTemplate._broader_question_type != 'BODY' and \
                    answerDoc.questionTemplate._broader_question_type != 'COUNTERBODY':
                if len(answerDoc.get_result()) > 0:
                    res.add((answerDoc, answerDoc.get_result()[0]))
                else:
                    res.add((answerDoc, None))
        return res

    def _set_variation_parameters(self, variations, answers_variation: List[_AnswerDocument]):
        res = set()
        for answerDoc in answers_variation:
            for variation in variations:
                if variation in answerDoc._final_answer:
                    res.add((answerDoc, variation))
        return res



