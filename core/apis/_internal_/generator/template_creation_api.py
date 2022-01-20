from __future__ import annotations

from typing import List, Tuple, Dict
from core.Datamodels.Archive.Answer_Document_Archive import AnswerDocumentArchive
from core.Datamodels.Question_Template import QuestionTemplate
from core.Datamodels.Topological_Map import TopologicalMap
from core.Datamodels.Datamodels import Question, Context, TextContext, TableContext, KnowledgeObject
from core.Datamodels.Answer_Document import AnswerLog
from core.Datamodels.hypothesis_modell import Hypothesis, HypothesisSpace
import re
from core.config import CONTEXT_WIDTH
from core.apis._internal_.generator.generator_classes import QuestionGenerator, ContextGenerator


class TemplateEngine:
    '''
    A template Engine is software designed to combine templates with a data model to produce result documents.
    The language that the templates are written in is known as a template language or templating language.
    For purposes of this article, a result document is any kind of formatted output, including documents, web pages,
    or source code (in source code generation), either in whole or in fragments.
    '''

    def __init__(self):
        self._topological_map: TopologicalMap = None
        self._templates: List[QuestionTemplate] = []
        self._archive: AnswerDocumentArchive = AnswerDocumentArchive()
        self.__dict_of_AnswerDocuments: Dict = {}
        self.__hypothesisSpace = HypothesisSpace()
        self._question_generator = QuestionGenerator()
        self._context_generator = ContextGenerator()

        '''
        _topological_map: Is a Representation of the whole document, annotated and connected through KnowledgeObjects.
                          It will be used as the datamodel for the template Engine.
        _templates: A list of QuestionTemplates that will be used to create the answer_document.
        _answer_document_archive: A archive preservering all build answer_documents.
        '''

    def update_hypothesisSpace(self, space: HypothesisSpace):
        self.__hypothesisSpace = space

    def update_dict(self, document: AnswerLog) -> None:
        if document in self.__dict_of_AnswerDocuments:
            return
        self.__dict_of_AnswerDocuments[document.questionTemplate] = document

    def _build_question_textcontext_tuple(self, questionTemplate, contexts=[], hypothesis=None) -> Question:
        context_question_tuples: List[Question] = []
        if len(contexts) > 0:
            for question in questionTemplate.get_questions():
                if self._has_placeholder(question):
                    # Replace the placeholder with the given Context
                    for context in contexts:
                        parameterized_questions: str = self.__get_parameterized_question(question, context,
                                                                                         hypothesis)
                        if parameterized_questions != ['']:
                            context_question_tuples.extend([(Question(para_question), context) for para_question in
                                                            parameterized_questions if para_question != ''])
                else:
                    context_question_tuples.extend([(Question(question), context) for context in contexts])

        return context_question_tuples

    def _build_question_tablecontext_tuple(self, questionTemplate, contexts=[], hypothesis=None) -> Question:
        context_question_tuples: List[Question] = []
        if len(contexts) > 0:
            for question in questionTemplate.get_questions():
                if self._has_placeholder(question):
                    # Replace the placeholder with the given Context
                    for context in contexts:
                        parameterized_questions: str = self.__get_parameterized_question(question, context,
                                                                                         hypothesis)
                        if parameterized_questions != ['']:
                            context_question_tuples.extend(
                                [(Question(para_question), context) for para_question in parameterized_questions
                                 if para_question != ''])
                else:
                    context_question_tuples.extend([(Question(question), context) for context in contexts])
        return context_question_tuples

    def _has_placeholder(self, question: str) -> bool:
        regex = "\[.+\]"
        if re.search(regex, question):
            return True
        return False

    def __get_parameterized_question(self, question: Question, context: Context, hypothesis: Hypothesis) -> str:

        # Overall Task Description:
        # First check if all necessary information is avaiable
        # If not return
        # Else update the question

        parameterized_questions: List[str] = []

        regex = "\[.+\]"
        parameters = re.search(regex, question).group()

        # If Hypothesis is in Parameters
        # Check if every needed part of the hyothesis is in the context
        # If not save an empty string
        if 'HYPOTHESIS' in parameters:
            hypothesis_name = self.__get_hypothesis_representation(context, hypothesis)
            if hypothesis_name != '':
                question = re.sub(regex, hypothesis_name, question)
                parameterized_questions.append(question)

        # If a parameter has already been found
        # Check if the parameter has been found in the context too
        # If not save an empty string
        else:
            parameters = parameters[1:-1].split('|')
            answers = []
            for parameter in parameters:
                if parameter.isupper():
                    if self.__hypothesisSpace.has_answer_for_category(parameter):
                        answers.append(True)
                        answer_list = self.__hypothesisSpace.get_answer_for_category(parameter)
                        for answer in answer_list:
                            if isinstance(answer, KnowledgeObject):
                                parameter_name = self.__get_contextualized_representation(context, answer)
                                if parameter_name != '':
                                    question = re.sub(regex, parameter_name, question)
                                    parameterized_questions.append(question)
                            else:
                                if answer.lower() in context.text.lower():
                                    question = re.sub(regex, parameter_name, question)
                                    parameterized_questions.append(question)
                    else:
                        answers.append(False)

            # If no parameter has already been found and a normal form (a question with no placeholder) is avaible
            # use the normal form

            if not all(answers) and len(answers) > 0:
                for parameter in parameters:
                    if not parameter.isupper():
                        question = re.sub(regex, parameter, question)
                        parameterized_questions.append(question)
        if parameterized_questions == []:
            parameterized_questions = ['']
        return parameterized_questions

    def __get_hypothesis_representation(self, context, hypothesis: Hypothesis) -> str:
        '''
        This Function provides several ways to get the representation of the hypothesis.
        It looks if all necessary Information for answering a Question for a hypothesis is given (that means, if every
        information needed to describe a specific variation setting is given).
        E.g.
        We have a Context for the COF (Coefficent of Friction) in the form:
            (Good Case)
            For MXene has a cof of 0.2 found for a pressure of 1.47 GPa and a rel. Humidity of 80%.
            (Bad Case)
            For MXene has a cof of 0.2 found for a pressure of 1.47 GPa.
        In addition we also know that we have a hypothesis with the variational parameters:
            - MXene (the other variation is 100Cr6)
            - 1.47 GPa (the other variation is 0.80 GPa)
            - 80 % (the other variation is 20%)

        For the good case we have found a context, that completly describes the hypothesis, whereas for the bad case
        not every Information is given (no rel. Humidity, so it can not be distinguished between the hypothesis of 20%
        and 80%).

        :param context: The context in which a answer for a hypothesis could be found
        :param hypothesis: The specific hypothesis
        :return: A specific name for the hypothesis.
                 An empty string if the hypothesis couldn't be build.

        '''

        # Check if it has a synonym
        # if hypothesis.has_synonym():
        #     synoynm: str = hypothesis.synonym
        #     if synoynm in context.text:
        #         return synoynm
        # else:
        contextualizations: List[str] = []
        variations: List[Answer] = hypothesis.get_variations()

        for variation in variations:
            has_context = False

            # Check if the answer of the Variation contains a kObj
            # If it is the case check its Representations and compare them with the given context
            # If nothing has found or there is no kObj check directly for the textual representation of the answer
            _prev_answer = variation.get_knowledgeObjects()
            if _prev_answer != []:
                for knowledgeObject in _prev_answer:
                    if knowledgeObject in context.get_knowledgeObjects():
                        contextualization = context.get_textual_representation(knowledgeObject)
                        if contextualization == '':
                            has_context = False
                        else:
                            contextualizations.append(contextualization)
                            has_context = True

            if has_context == False:
                _prev_answer = variation.textual_representation
                if _prev_answer.lower() in context.text.lower():
                    contextualizations.append(_prev_answer)
                    has_context = True

            if not has_context:
                return ''
        return ' and '.join(contextualizations)

    def __get_contextualized_representation(self, context, answer: KnowledgeObject):
        if answer in context.get_knowledgeObjects():
            return context.get_textual_representation(answer)
        else:
            return ''

    def _build_context(self, questionTemplate: QuestionTemplate, context_format='normal_form',
                       frame: int = 1) -> Context:
        # Old
        table_contexts = self.__get_table_contexts(questionTemplate, context_format)
        text_contexts = self.__get_text_contexts(questionTemplate, context_format, frame)

        return text_contexts, table_contexts

    def __get_table_contexts(self, questionTemplate: QuestionTemplate, context_format):
        found_tables: List[Table] = []
        contexts: List[TableContext] = []

        for regex in questionTemplate.search_regexs:
            found_tables.extend(self._topological_map.get_tables_for_regex(regex))
        for category in questionTemplate.search_categories:
            found_tables.extend(self._topological_map.get_tables_for_category(category))
        found_tables = set(found_tables)

        for table in found_tables:
            context = TableContext(table)
            contexts.append(context)

        return contexts

    def __get_text_contexts(self, questionTemplate: QuestionTemplate, context_format, frame: int = 1) -> List[
        TextContext]:
        found_sentences: List[Sentence] = []
        contexts: List[TextContext] = []

        for regex in questionTemplate.search_regexs:
            found_sentences.extend(self._topological_map.get_sentences_for_regex(regex))
        for category in questionTemplate.search_categories:
            found_sentences.extend(self._topological_map.get_sentences_for_category(category))
        found_sentences = set(found_sentences)

        for sentence in found_sentences:
            framing_sentences: List[Sentence] = sentence.get_framing_sentences(frame)
            textual_representation: str = " ".join([sent.get_form(context_format) for sent in framing_sentences])
            context = TextContext(framing_sentences, textual_representation, context_format)
            contexts.append(context)

        return contexts

    def _safe_in_archive(self, archive_file: Tuple[AnswerDocumentArchive, str]) -> None:
        self._archive[archive_file[1]] = archive_file[0]

    def build_answer_log(self, template: QuestionTemplate, task: str = 'normal', hypothesis: Hypothesis = None,
                         doc_type: str = '', mode: int = CONTEXT_WIDTH) -> AnswerLog:

        # Gets the contexts by searching the different types of Information Units (Table, Text) with the
        # predefined searchstrings

        c_generator: ContextGenerator = self._context_generator
        q_generator: QuestionGenerator = self._question_generator

        table_contexts: List[TableContext] = c_generator.get_tables(questionTemplate=template,
                                                                  topMap=self._topological_map
                                                                  )

        text_contexts: List[TextContext] = c_generator.get_text(questionTemplate=template,
                                                              topMap=self._topological_map,
                                                              settings={
                                                                                "frame_size": mode,
                                                                                "context_type": task
                                                                            })
        # old
        #text_contexts, table_contexts = self._build_context(template, task)

        table_question_context_tuple: List[Tuple[Question, TableContext]] = []
        text_question_context_tuple: List[Tuple[Question, TextContext]] = []


        for table_context in table_contexts:
            if hypothesis is None:
                questions: List[Question] = q_generator.get_questions(questionTemplate=template,
                                                                      context=table_context,
                                                                      archive=self._archive
                                                                     )
            else:

                questions: List[Question] = q_generator.get_questions_for_hypothesis(
                                                                                            questionTemplate=template,
                                                                                            context=table_context,
                                                                                            hypothesis=hypothesis
                                                                                        )
            for question in questions:
                table_question_context_tuple.append((question, table_context))

        for text_context in text_contexts:
            if hypothesis is None:
                questions: List[Question] = q_generator.get_questions(  questionTemplate=template,
                                                                        context=text_context,
                                                                        archive=self._archive
                                                                     )
            else:
                questions: List[Question] = q_generator.get_questions_for_hypothesis(
                                                                                            questionTemplate=template,
                                                                                            context=text_context,
                                                                                            hypothesis=hypothesis
                                                                                        )
            for question in questions:
                text_question_context_tuple.append((question, text_context))



        deprecated = """
        # For every identified context, look if a Question with one specific context can be build
        text_tuple: List[Tuple[Question, TextContext]] = self._build_question_textcontext_tuple(template,
                                                                                                text_contexts,
                                                                                                hypothesis)
        table_tuple: List[Tuple[Question, TableContext]] = self._build_question_tablecontext_tuple(template,
                                                                                                   table_contexts,
                                                                                                   hypothesis)
        """

        answer_document = AnswerLog(template=template,
                                    hypothesis=hypothesis,
                                    text_tuple=text_question_context_tuple,
                                    table_tuple=table_question_context_tuple,
                                    type=doc_type,
                                    mode=mode,
                                    question_templates=self._templates)

        archive_key: str = '_'.join(template.get_questionType())
        if archive_key not in self._archive:
            self._archive[archive_key] = [answer_document]
        else:
            self._archive[archive_key].append(answer_document)

        return answer_document

    def save_archive_as_json(self) -> dict:
        return self._archive.save_as_json()

    def set_templates(self, qTemplates: List[QuestionTemplate]) -> None:
        self._templates = qTemplates

    def set_topological_map(self, topMap: TopologicalMap) -> None:
        self._topological_map = topMap
