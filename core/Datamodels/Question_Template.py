from __future__ import annotations
from typing import List, Tuple
import re

class QuestionTemplate:

    def __init__(self):
        self.__questions: List[str] = []
        self._search_space_regex: List[str] = []
        self._search_space_categories: List[str] = []
        self._answer_space_regex: List[str] = []
        self._answer_space_categories: List[str] = []
        self._specific_question_type: str = ''
        self._broader_question_type: str = ''
        self._dependency_to_category: List[str] = []
        self._weak_dependency_to_question_types: List[QuestionTemplate] = []
        self._strong_dependency_to_question_types: List[QuestionTemplate] = []
        self.__weak_dependency_to_question_type_reference: List[QuestionTemplate] = []
        self.__strong_dependency_to_question_type_reference: List[QuestionTemplate] = []
        self._normal_state: str = []
        self.__searchspace: List[str] = []
        self.__answerspace: List[str] = []


    def get_dependencies(self) -> List[QuestionTemplate]:

        return self._weak_dependency_to_question_types + self._strong_dependency_to_question_types

    def get_log(self) -> AnswerLog:
        return self.answer_log

    def has_strong_dependency_to(self, questionTemplate: QuestionTemplate):
        if questionTemplate in self._strong_dependency_to_question_types:
            return True
        return False

    def has_dependency_to_questionTemplate(self, questionTemplate: QuestionTemplate):
        if questionTemplate in self._weak_dependency_to_question_types:
            return True
        if questionTemplate in self._strong_dependency_to_question_types:
            return True
        return False


    def get_answers_in_sentences(self, answers) -> List[str]:
        res = []
        res2 = []
        for answer in answers:
            isInSearchSpaceRegex: bool = self._get_answer_in_search_space_regex(answer)
            isInSearchSpaceCategory: bool = self._get_answer_in_search_space_category(answer)
            if isInSearchSpaceRegex and isInSearchSpaceCategory:
                res2.append(answer)
            elif isInSearchSpaceRegex or isInSearchSpaceCategory:
                res.append(answer)
        if len(res2) > 0:
            return res2
        else:
            return res

    def _get_answer_in_search_space_category(self, answer):
        if self._answer_space_categories:
            for category in self._answer_space_categories:
                if category in answer.get_categories_in_answer():
                    return True
        return False


    def _get_answer_in_search_space_regex(self, answer):

        if self._answer_space_regex:
            for regex in self._answer_space_regex:
                try:
                    # Check the actual answer
                    # The additional Spaces are there, to prevent some unpredicted behaviour
                    # The Regex describe the shape or form of the answer
                    # E.g.
                    # '\d+(,|.){0,1}\d+ *(m)' -> describing a distance in meter, where the ' is the
                    #                            start or the end of the regex.
                    # This Regex would work fine for every normal case, like 10 m, 10.6 m, 1,123123m
                    # But also for things that are not expected, like 19 mushrooms, 3 measurements
                    # To prevent it we artifically add spaces at the beginning and the end of the regex and the string

                    if re.search(" " + regex + " ", " " + answer._textual_representation + " "):
                        return True

                    # If the answer is part of a complete kObj
                    # Check this one too
                    kObjs: List[KnowledgeObject] = answer.get_knowledgeObjects()
                    if len(kObjs) > 0:
                        for kObj in kObjs:
                            for label in kObj.labels:
                                if re.search(" " + regex + " ", " " + label + " "):
                                    return True
                except re.error:
                    print(regex)
                    print("""You probably have some Problems with your Regex Definition. 
                    Reasons could be:
                    - You used some special signs like:  ἄλφα
                    - The Regex doesnt work. Check it e.g. at regex101.com
                    - Some formatting errors. If so look in the ContextAnalyzer where the QuestionTemplates will be 
                    created and look up the self.answerSpaceRegex-Data. 
                    """)

        return False



    def has_dependency_to_category(self, category):
        return category in self._dependency_to_category

    def get_questions(self) -> List[str]:
        return self.__questions

    @property
    def search_regexs(self) -> List[str]:
        return self._search_space_regex

    @property
    def search_categories(self) -> List[str]:
        return self._search_space_categories

    def get_questionType(self) -> Tuple[str, str]:
        return (self._specific_question_type, self._broader_question_type)

    @classmethod
    def read_from_json(cls, json_data):
        _references = {}
        questionTemplates: List[QuestionTemplate] = []
        # Creates instances of the question Template
        for broader_category in json_data.values():
            for qTemp in broader_category.values():
                temp: QuestionTemplate = cls()
                temp.__questions = qTemp['question']
                temp.__searchspace = qTemp['preSearchSpace']
                temp.__answerspace = qTemp['expectedAnswerSpace']
                temp._normal_state = qTemp['normalState']
                temp._dependency_to_category = [_[1:-1] for _ in qTemp['dependend_from_variables']]
                temp._specific_question_type = qTemp['specific_questionType']
                temp._broader_question_type = qTemp['broader_questionType']
                temp.__weak_dependency_to_question_type_reference = qTemp['weak_dependency_to']
                temp.__strong_dependency_to_question_type_reference = qTemp['strong_dependency_to']

                temp._build_answer_space()
                temp._build_search_space()
                questionTemplates.append(temp)
                _references[temp._specific_question_type] = temp

        for temp in questionTemplates:
            if temp.has_dependency_constraints():
                temp._build_dependency_constraints(_references)

        return questionTemplates

    def _build_search_space(self) -> None:
        '''
        Splits and sets the search space in different types of expected search spaces
        :return: None
        '''
        #
        # The Questiontemplate handles two types of Searchcategories
        # 1. Answers, where the textual representation is equal to the expected answer
        #    E.g.
        #    "([0-9]{0,5}\\.|)[0-9]+ N"
        #    A Answer is a Regex that describes what a Normal Load should look like
        #
        # 2. Answers, where the category is equal to the expected answer
        #   E.g.
        #    "<OperationalParameter>"
        #    A Answer should be a Operational Parameter
        #
        # To handle it, we have a sperator between these two "<.*>"
        for expected_search in self.__searchspace:
            # Check if the expected answer is a Category
            if expected_search.startswith("<") and expected_search.endswith(">"):
                self._search_space_categories.append(expected_search[1:-1])
            # The other case is a regex.
            else:
                self._search_space_regex.append(expected_search)

    def _build_answer_space(self) -> None:
        '''
        Splits and sets the answer space in different types of expected answer spaces
        :return: None
        '''
        #
        # The Questiontemplate handles two types of Answers
        # 1. Answers, where the textual representation is equal to the expected answer
        #    E.g.
        #    "([0-9]{0,5}\\.|)[0-9]+ N"
        #    A Answer is a Regex that describes what a Normal Load should look like
        #
        # 2. Answers, where the category is equal to the expected answer
        #   E.g.
        #    "<OperationalParameter>"
        #    A Answer should be a Operational Parameter
        #
        # To handle it, we have a sperator between these two "<.*>"
        for expected_answer in self.__answerspace:
            # Check if the expected answer is a Category
            if expected_answer.startswith("<") and expected_answer.endswith(">"):
                self._answer_space_categories.append(expected_answer[1:-1])
            # The other case is a regex.
            else:
                self._answer_space_regex.append(expected_answer)

    def has_dependency_to_hypothesis(self) -> bool:
        if '<HYPOTHESIS>' in self.__strong_dependency_to_question_type_reference:
            return True
        return False

    def has_dependency_constraints(self) -> bool:
        return self.__weak_dependency_to_question_type_reference != [] or self.__strong_dependency_to_question_type_reference != []

    def _build_dependency_constraints(self, references) -> None:
        for question_type in self.__weak_dependency_to_question_type_reference:
            if question_type in references:
                self._weak_dependency_to_question_types.append(references[question_type])

        for question_type in self.__strong_dependency_to_question_type_reference:
            if question_type in references:
                self._strong_dependency_to_question_types.append(references[question_type])





