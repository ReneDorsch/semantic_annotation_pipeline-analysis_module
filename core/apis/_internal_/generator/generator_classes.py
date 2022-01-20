from __future__ import annotations

import itertools
import re
from typing import List, Union, Set, Dict

from core.Datamodels.Answer_Document import AnswerLog
from core.Datamodels.Archive.Answer_Document_Archive import AnswerDocumentArchive
from core.Datamodels.Datamodels import TextContext, Question, TableContext
from core.Datamodels.Question_Template import QuestionTemplate
from core.Datamodels.Topological_Map import TopologicalMap
from core.Datamodels.hypothesis_modell import Hypothesis


def has_placeholder(question: str) -> bool:
    regex = "\[.+\]"
    if re.search(regex, question):
        return True
    return False


def get_placeholders(question: str) -> List[str]:
    """ Get the placeholders. """
    placeholders: List[str] = []
    regex = "[A-Z_]{2,}"
    
    for match in re.finditer(regex, question):
        start: int = match.start()
        end: int = match.end()
        placeholder: str = question[start: end]
        placeholders.append(placeholder)
    
    return placeholders


def get_unparamterized_question(question: str) -> str:
    """ Removes any placeholder form the question """
    res: str = ""
    regex = "\[.+\]"
    match = re.search(regex, question)
    if match is not None:
        _placeholder_areas: str = match.group()
        start: int = 0
        for _match in _placeholder_areas.split("|"):
            #end: int = _match.end()
            
            #_placeholder_area: str = _placeholder_areas[start: end]
            _placeholder_area = re.sub("\||\[|\]|\_", "", _match)

            if not any([word.isupper() for word in _placeholder_area.split(" ")]):
                res = question[:match.start()] + _placeholder_area + question[match.end():]
                break
            #start = end
    else:
        res = question
    return res


def get_parameterized_question(question: str, placeholder: str, parameter: str) -> str:
    """ Replaces the lsit the placeholders through the given parameter. """
    res: str = ""
    regex = "\[.+\]"
    match = re.search(regex, question)
    try:
        _placeholder_areas: str = match.group()
    except:
        print("ok")
    start: int = 0
    for _match in _placeholder_areas.split("|"):
        #end: int = _match.end()
        #_placeholder_area: str = _placeholder_areas[start: end]
        _placeholder_area = re.sub("\||\[|\]", "", _match)

        if any([word == placeholder for word in _placeholder_area.split(" ")]):
            parameterized = _placeholder_area.replace(placeholder, parameter)
            res = question[:match.start()] + parameterized + question[match.end():]
            break
        #start = end
    return res


class QuestionGenerator:

    """ Creates Question accoridng to a given context. """


    def get_questions(self, questionTemplate: QuestionTemplate, context: TextContext, archive: AnswerDocumentArchive) -> List[Question]:
        """ Creates a list of questions. """
        res: List[Question] = []
        for question in questionTemplate.get_questions():
            # In the case that the questions has any placeholder check if any of this placeholders can be answered
            if has_placeholder(question):
                placeholders: List[str] = get_placeholders(question)
                for logs in archive.values():
                    for log in logs:
                        for placeholder in placeholders:
                            has_answer: bool = log.has_answer()
                            for_placeholder: bool = placeholder in log.questionTemplate.get_questionType()

                            if for_placeholder and has_answer:
                                questions: List[Question] = self._get_parameterized_questions(question,
                                                                                    placeholder,
                                                                                    log.get_final_answer(),
                                                                                    context
                                                                                    )

                                if question != []:
                                    res.extend(questions)


            question = get_unparamterized_question(question)
            if len(question.rstrip().lstrip()) > 10:
                res.append(Question(question))

        return res


    def _get_parameterized_questions(self, _question: str, placeholder, answers: List[Answer],
                                     context: Union[TableContext, TextContext]) -> List[Question]:
        res: List[Question] = []

        for answer in answers:
            in_context: bool = context.contains(answer)
            if in_context:
                representations: List[str] = context.get_answer_representation(answer)
                for representation in representations:
                    question = get_parameterized_question(_question, placeholder, representation)
                    if len(question.rstrip().lstrip()) > 10:
                        res.append(Question(question))
        return res

    def get_questions_for_hypothesis(self, questionTemplate: QuestionTemplate, context: Union[TableContext, TextContext],
                                          hypothesis: Hypothesis) -> List[Question]:
        """ Creates a list of questions. """
        res: List[Question] = []
        variations: List[AnswerLog] = hypothesis.get_variations()

        hypothesis_combinations: List[Set[Answer]] = hypothesis.get_variations()

        if context.contains(hypothesis_combinations):
            representation: List[str] = context.get_answer_representation(hypothesis_combinations)
            for question in questionTemplate.get_questions():
                if has_placeholder(question):
                    question = get_parameterized_question(question, "HYPOTHESIS", " and ".join(representation))
                if len(question.rstrip().lstrip()) > 10:
                    res.append(Question(question))
        return res




    def _(self):
        c = """
    def get_table_questions(self, questionTemplate: QuestionTemplate, context: TableContext, archive: AnswerDocumentArchive) -> List[Question]:
        "" Creates a list of questions. ""
        return self.get_text_questions(questionTemplate=questionTemplate,
                                       context=context,
                                       archive=archive)

    def get_table_questions_for_hypothesis(self, questionTemplate: QuestionTemplate, contexts: List[TableContext],
                                          hypothesis: Hypothesis) -> List[Question]:
        "" Creates a list of questions. ""
        

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
        """


class ContextGenerator:
    """ Creates Contexts according to a given set of parameters. """

    def __init__(self):
        self.settings: Dict = {
            "context_size": 3,
            "context_type": "simple"
        }


    def get_tables(self, questionTemplate: QuestionTemplate, topMap: TopologicalMap) -> List[TableContext]:
        """ Get table contexts for a given searchquery. """
        found_tables: List[Table] = []
        contexts: List[TableContext] = []

        for regex in questionTemplate.search_regexs:
            found_tables.extend(topMap.get_tables_for_regex(regex))
        for category in questionTemplate.search_categories:
            found_tables.extend(topMap.get_tables_for_category(category))
        found_tables = set(found_tables)

        for table in found_tables:
            context = TableContext(table)
            contexts.append(context)

        return contexts

    def get_tables_for_hypothesis(self, questionTemplate: QuestionTemplate, topMap: TopologicalMap) -> List[TableContext]:
        """ Get tables for a given searchquery. """
        table_contexts: List[TableContext] = self.get_tables(questionTemplate=questionTemplate,
                                                             topMap=topMap
                                                             )



        pass

    def get_text(self,  questionTemplate: QuestionTemplate, topMap: TopologicalMap, settings: Dict = {}) -> List[TextContext]:
        """ Get Text Contexts for a given searchquery. """

        if "frame_size" in settings:
            frame_size = settings['frame_size']
        else:
            frame_size = self.settings['frame_size']

        if "context_type" in settings:
            context_type = settings['context_type']
        else:
            context_type = self.settings['context_type']
        found_sentences: List[Sentence] = []
        contexts: List[TextContext] = []

        # Get all sentences that contain a searchterm from the searchspace
        for regex in questionTemplate.search_regexs:
            found_sentences.extend(topMap.get_sentences_for_regex(regex))
        for category in questionTemplate.search_categories:
            found_sentences.extend(topMap.get_sentences_for_category(category))
        found_sentences = set(found_sentences)

        # Create the contexts
        for sentence in found_sentences:
            framing_sentences: List[Sentence] = sentence.get_framing_sentences(frame_size)
            textual_representation: str = " ".join([sent.get_form(context_type) for sent in framing_sentences])
            context = TextContext(framing_sentences, textual_representation, context_type)
            contexts.append(context)

        return contexts




    def get_text_for_hypothesis(self,  questionTemplate: QuestionTemplate, topMap: TopologicalMap) -> List[TextContext]:
        """ Get Text Contexts  for a given searchquery. """
        pass