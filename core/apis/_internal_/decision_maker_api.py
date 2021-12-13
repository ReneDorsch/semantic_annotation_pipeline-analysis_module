from __future__ import annotations

import datetime
from typing import Set, List, Tuple
from core.Datamodels.Topological_Map import KnowledgeObject
from core.Datamodels.Datamodels import Answer, TableAnswer, TextAnswer
from core.Datamodels.Answer_Document import AnswerDocument

import core.Datamodels.coordinating_model as cm
import copy
import json
import os
from core.config import OUTPUT_DIRECTORY


def _save_variables_as_json(variables, found_kObjs, variables_searchSpace, variables_frequency,
                            variables_question_answering, variables_from_toplogical_map):
    _knowledgeObjects = list(found_kObjs) + list(variables_question_answering) + list(variables_frequency) + \
                        list(variables_from_toplogical_map['get_kObjs_in_abstract']) + \
                        list(variables_from_toplogical_map['get_kObjs_in_summary']) + \
                        list(variables_from_toplogical_map['get_kObjs_in_goal_description'])

    knowledgeObjects = []
    for kObj in set(_knowledgeObjects):
        knowledgeObjects.append(kObj.save_for_api())

    data = [{
        'variables': list(variables),
        'found_kObjs_for_variables': [_.id for _ in found_kObjs],
        'variables_frequency': [_.id for _ in variables_frequency],
        'variables_searchSpace': [_.id for _ in variables_searchSpace],
        'variables_from_abstract': [_.id for _ in variables_from_toplogical_map['get_kObjs_in_abstract']],
        'variables_from_summary': [_.id for _ in variables_from_toplogical_map['get_kObjs_in_summary']],
        'variables_from_goal_description': [_.id for _ in
                                            variables_from_toplogical_map['get_kObjs_in_goal_description']],
        'variables_question_answering': [_.id for _ in variables_question_answering],
        'knowledgeObjects': knowledgeObjects
    }]
    time_stamp = datetime.datetime.now().strftime("%d_%H_%M_%S")
    with open(os.path.join(OUTPUT_DIRECTORY, f'{time_stamp}_variables.json'), 'w') as file:
        file.write(json.dumps(data, indent=4))


class DecisionMaker:

    def __init__(self):
        self.infrastructure: cm.Infrastructure = None

    def _vote_variation(self, answers_1: List[Answer], answers_2: List[Answer]) -> Tuple[str, List[Answer]]:
        # To-Do: Evtl. we could check the frequency in addition
        # The answers have to be "gleich im aufbau"
        answerSet_1 = set([x[0] for x in answers_1])
        answerSet_2 = set([x[0] for x in answers_2])
        intersection_between_a1_a2 = answerSet_1.intersection(answerSet_2)
        res = list(intersection_between_a1_a2)
        if len(res) >= 1:
            return 'accepted', res
        else:
            return 'rejected', res

    def vote(self, answers_1: Answer, answers_2: Answer) -> Tuple[str, Answer]:
        res = []
        if len(answers_1) > 0 and len(answers_2) > 0:
            # Get the answers with the highest
            maxNumber_1 = max([count for answer, count in answers_1])
            maxNumber_2 = max([count for answer, count in answers_2])

            answerSet_1: Set['Answer'] = set([answer for answer, count in answers_1 if count == maxNumber_1])
            answerSet_2: Set['Answer'] = set([answer for answer, count in answers_2 if count == maxNumber_2])

            intersection_between_a1_a2 = answerSet_1.intersection(answerSet_2)
            res = list(intersection_between_a1_a2)

            if len(res) > 1:
                return 'no_distinct_answer', res
            elif len(res) == 1:
                return 'accepted', res
        return 'rejected', res

    def __make_decision_by_distance(self, answerDoc, result: List[Answer]):
        if len(result) == 0:
            return 'rejected', result

        prev_answers: List[AnswerDocument] = self.infrastructure.get_previous_answers_of_same_type(answerDoc)

        if len(prev_answers) <= 2:
            return 'wait', result
        else:

            best_answer = None
            prev_average_distance: float = 0
            for answer in result:
                # Get the distance to every prev_answer for every possible answer in the result
                sum_of_distances = 0
                for prev_answer in prev_answers:
                    for prev_final_answer in prev_answer.get_result():
                        distance_between_two_answers: int = Answer.get_distance(prev_final_answer, answer)
                        sum_of_distances += distance_between_two_answers
                if best_answer is None:
                    best_answer = answer
                    prev_average_distance = sum_of_distances / len(prev_answers)
                else:
                    average_distance = sum_of_distances / len(prev_answers)
                    if average_distance < prev_average_distance:
                        best_answer = answer
                        prev_average_distance = average_distance

            print("Checking Topological Map found a result: ", best_answer.textual_representation)
            return 'accepted', [best_answer]

    def _n_modular_redundancy_by_context(self, answers_by_context: List['Answer']) -> Tuple:
        '''
        A generalisiation of the Triple Modular redundancy algorithmn to n modulars.
        It identifies the most common answer, without considering empty answers
        :param answers_by_context: A List of Answers from the same context
        :return: Decision, Answer
                The Decision can be:
                Accepted    |   ....
                Rejected    |   ....
        '''

        _zwerg = copy.copy(answers_by_context)
        answers = {}

        # Get all Answers that are the "same" (same = similiar textual representations)
        while len(_zwerg) > 0:
            answer_1: Answer = _zwerg.pop(0)
            if answer_1._textual_representation == '': continue
            answers[answer_1] = []
            for answer_2 in _zwerg:
                if answer_1.is_part_of(answer_2):
                    answers[answer_1].append(answer_2)

            for answer in answers[answer_1]:
                _zwerg.remove(answer)

        # Map the Dict to a list where each unique answer has the number of shared answers
        answers = [(answer, len(value)) for answer, value in answers.items()]

        # Make a Decision according to the list of possible answers
        if answers:
            answers.sort(key=lambda x: x[1], reverse=True)
            comp = lambda x: True if answers[0][1] > x[1] else False

            # Takes the Answer with the highest score
            if all([comp(answer) for answer in answers[1:]]):
                if answers[0][0]._textual_representation != '':
                    return answers[0][0], 'accepted'

                # If there is not distinct best answer
                else:
                    return None, 'rejected'
        return None, 'rejected'

    def make_decision(self, answerDoc: AnswerDocument) -> Tuple[str, AnswerDocument]:
        answers = []
        t_answers = []

        # Summarize the TextAnswers by the context and the most common answer between them
        answersSortedByContext = answerDoc.get_text_answers_sorted_by_context()
        for answersByContext in answersSortedByContext.values():
            answer, note = self._n_modular_redundancy_by_context(answersByContext)
            if answer is not None:
                answers.append(answer)
        # Summarize the TextAnswers by the context and the most common answer between them
        t_answers_sorted_by_context = answerDoc.get_table_answers_sorted_by_context()
        for answersByContext in t_answers_sorted_by_context.values():
            t_answer, note = self._n_modular_redundancy_by_context(answersByContext)
            if t_answer is not None:
                t_answers.append(t_answer)

        # Check if the Answers fit to the
        table_decision, table_result = self.table_vote(answerDoc, t_answers)
        text_decision, text_result = self.text_vote(answerDoc, answers)

        if "FRICTION_RATE" == answerDoc.questionTemplate.get_questionType()[0]:
            print("ok")
        # For the Variation Answers (Answer where we allow multiple answers),
        # we have only to compare the answers
        if answerDoc.type == 'VARIATION':
            decision, answer = self.__get_nary_decision(table_decision, table_result, text_decision, text_result,
                                                        answerDoc.type)
        else:
            # This is part of an Action in response to the interpretation of the answer. I think this should be
            # seperated from the block decision
            if text_decision == 'wait':
                return self.infrastructure.send_data_to_waiting_spot(answerDoc)

            # If we don't allow variation, we calculate the best answer between all the possible anaswers
            decision, answer = self.__get_singular_decision(table_decision, table_result, text_decision, text_result,
                                                            answerDoc.type)

        print("Questiontype", answerDoc.questionTemplate.get_questionType())
        print("Final Result: ", [_.textual_representation for _ in answer])
        print("Decision: ", decision)
        print("\n\n")
        # Saves the result in the document
        answerDoc.set_final_result(decision)
        answerDoc.set_final_answer(answer)
        return self.infrastructure._send_data_to_scheduler(decision, answerDoc)

    def __get_nary_decision(self, table_decision: str, table_results: List[TableAnswer],
                            text_decision: str, text_results: List[TextAnswer], question_type: str):

        decision: str = 'rejected'
        result: List[Answer] = []

        # If both decisions have an accepted answer
        if table_decision == 'accepted' and text_decision == 'accepted':
            # Check first the intersection of both results
            # If there is some intersection use this as answer

            result = Answer.intersection(table_results, text_results)

        # If we have to choose variations
        # We consider a more conservative way. If there is no intersection found
        # take the union of the results
        if question_type == 'VARIATION' and result == []:
            result = table_results + text_results

        else:
            # If the intersection is empty but the table has a answer use this
            # If the table found an answer use this answer
            if result == []:
                result = list(set(table_results))

            # If no answer was until now found check the text results
            if result == []:
                result = list(set(text_results))

        if text_decision == 'wait' and result == []:
            decision = text_decision

        if result != []:
            decision = 'accepted'

        # If the decision to the text was 'wait' take this
        # In every other case return 'no_answer'

        return decision, result

    def __get_singular_decision(self, table_decision, table_results, text_decision, text_result, question_type: str):
        decision: str = 'rejected'
        result: List[Answer] = []

        # If serveral answers are found check the distance between the answer and previous found answers
        decision, result = self.__get_nary_decision(table_decision, table_results, text_decision, text_result,
                                                    question_type)

        if len(result) > 1:
            # To-Do: Check this
            #    result = self.__get_next_results(result)
            # If serveral Answers have the same distance to prev. answers then ????
            if len(result) > 1:
                result = [result[0]]
            else:
                result = [result[0]]
        return decision, result

    def _combine_answer_concepts_with_same_knowledgeObject(self,
                                                           answers: Tuple[List[Answer], List['KnowledgeObject']]) -> \
            List[
                Answer]:

        res = answers[0]
        res2 = []

        if len(answers[1]) == 0:
            return res, res2

        zwerg = copy.copy(answers[1])
        while True:

            answer_1, counter = zwerg.pop(0)
            for answer_2, count in zwerg:
                for kObj in answer_2.get_knowledgeObjects():
                    if kObj in answer_1.get_knowledgeObjects():
                        counter += count
                        zwerg.remove((answer_2, count))
                        break
            res2.append((answer_1, counter))
            # Termination Condition
            if len(zwerg) == 0:
                break

        return res, res2

    def table_vote(self, answerDoc: AnswerDocument, table_answers: List[Answer]) -> List[Answer]:
        '''
        What does it?
        Determines the resulting answer to a QuestionTemplate according to the tables in a document.
        :param questionTemplate: QuestionTemplate for a specific Question
        :param answers: List of Answers from Tables to the specific Question
        :return: A decision as a text and the Answer Object with regard to the Input Answers
                 Types of decisions:
                 Decision       |    Output
                 'accepted'     |   List of Answers
                 'no_answer'    |   empty List
        '''

        # Filter the answers by the frequency or by the searched type
        table_answers_by_frequency: List[Tuple[int, str]] = self.__get_answers_by_frequency(table_answers)
        table_answers_by_searchSpace: List[Tuple[int, str]] = self.__get_answers_by_search_space(
            answerDoc.questionTemplate, table_answers)

        # Join the filtered answers by textual representation and knowledgeObject Types
        table_answers_by_frequency = self._combine_answer_concepts_with_same_knowledgeObject(table_answers_by_frequency)
        table_answers_by_searchSpace = self._combine_answer_concepts_with_same_knowledgeObject(
            table_answers_by_searchSpace)

        # Make a decision
        if answerDoc.type == 'VARIATION':
            decision, result = self._vote_variation(table_answers_by_frequency[0], table_answers_by_searchSpace[0])
            decision2, result2 = self._vote_variation(table_answers_by_frequency[1], table_answers_by_searchSpace[1])
        else:
            decision, result = self.vote(table_answers_by_frequency[0], table_answers_by_searchSpace[0])
            decision2, result2 = self.vote(table_answers_by_frequency[1], table_answers_by_searchSpace[1])
        print("Table: \t", answerDoc.questionTemplate._specific_question_type, decision, result)
        print("Table: \t", answerDoc.questionTemplate._specific_question_type, decision2, result2)

        answerDoc.set_final_table_answers(result, result2)
        answerDoc.set_final_table_result(decision, decision2)

        decision, result = decision2, result2
        return decision, result

    def text_vote(self, answerDoc: AnswerDocument, answers: List[Answer]) -> List[Answer]:
        '''
        What does it?
        Determines the resulting answer to a QuestionTemplate according to the text in a document.
        :param questionTemplate: QuestionTemplate for a specific Question
        :param answers: List of Answers to the specific Question
        :return: A decision as a text and the Answer Object with regard to the Input Answers
                 Types of decisions:
                 Decision       |    Output
                 'accepted'     |   List of Answers
                 'no_answer'    |   empty List
                 'wait'         |   empty List

        '''
        # Filter the answers by the frequency or by the searched type
        answersByFrequency: List[Tuple[int, str]] = self.__get_answers_by_frequency(answers)
        answersBySearchSpace: List[Tuple[int, str]] = self.__get_answers_by_search_space(answerDoc.questionTemplate,
                                                                                         answers)

        # Join the filtered answers by textual representation and knowledgeObject Types
        answersByFrequency = self._combine_answer_concepts_with_same_knowledgeObject(answersByFrequency)
        answersBySearchSpace = self._combine_answer_concepts_with_same_knowledgeObject(answersBySearchSpace)

        specific, _ = answerDoc.questionTemplate.get_questionType()
        if specific == 'WEAR_RATE':
            print("ok")
        # Make a decision
        if answerDoc.type == 'VARIATION':
            decision, result = self._vote_variation(answersByFrequency[0], answersBySearchSpace[0])
            decision2, result2 = self._vote_variation(answersByFrequency[1], answersBySearchSpace[1])
        else:
            decision, result = self.vote(answersByFrequency[0], answersBySearchSpace[0])
            decision2, result2 = self.vote(answersByFrequency[1], answersBySearchSpace[1])

        # answer = self.analyseAnswerForKnowledgeObject(result)
        # If no distinct decision could be found (so we have answers but we don't know which one is right)
        # check the distance between the found Answers and previous found Answers of the same type.
        # Assumption: As nearer a found answer is to the prev. found Answers as more probably is it, to be the
        #             correct answer
        answerDoc.set_final_text_answers(result, result2)
        answerDoc.set_final_text_result(decision, decision2)

        if decision == 'no_distinct_answer':
            decision, result = self.__make_decision_by_distance(answerDoc, result2)
        else:
            decision, result = decision2, result2

        print("Text: \t", answerDoc.questionTemplate._specific_question_type, decision, result)
        print("Text: \t", answerDoc.questionTemplate._specific_question_type, decision2, result2)

        return decision, result

    def set_infrastructure(self, infrastructure: cm.Infrastructure):
        self.infrastructure = infrastructure

    def __get_answers_by_frequency(self, answers: List[Answer]) -> Tuple[List[str], List[KnowledgeObject]]:
        '''
        Get all possible Answers
        :param answers: List[Answer]
        :return: Two Lists of Answers sorted according to the frequency of the possible answers.
        The first one returns the Answers by there textual Form
        The second one returns the Answers by there Concept
        '''

        answers_by_textual_representation: List[str] = self.__sort_and_count_by_textual_representation(answers)
        answers_by_knowledgeObject: List[KnowledgeObject] = self.__sort_and_count_by_knowledgeObject(answers)
        return answers_by_textual_representation, answers_by_knowledgeObject

    def __get_answers_by_search_space(self, questionTemplate: QuestionTemplate, answersSpace: List[Answer]) -> Tuple[
        List[str], List[KnowledgeObject]]:
        '''
        Get all expected Answers
        :param questionTemplate:
        :return: Two Lists of Answers sorted according to the frequency of the expected answers.
        The first one returns the Answers by there textual Form
        The second one returns the Answers by there Concept
        '''
        # Filter the answers by looking at the predefined Searchspace
        answers = questionTemplate.get_answers_in_sentences(answersSpace)

        answers_by_textual_representation, answers_by_knowledgeObject = self.__get_answers_by_frequency(answers)
        return answers_by_textual_representation, answers_by_knowledgeObject

    def __sort_and_count_by_textual_representation(self, answers: List[Answer]) -> List[Answer]:
        res = {}
        # Counts the answers by the textual representation in normalized Form
        for answer in answers:
            if answer.normalized_form() not in res:
                res[answer.normalized_form()] = 1
            else:
                res[answer.normalized_form()] += 1
        res = [(_, __) for _, __ in res.items()]
        # Sorts the answers
        res.sort(key=lambda x: x[1], reverse=True)
        return res

    def __sort_and_count_by_knowledgeObject(self, answers: List[Answer]) -> List[Answer]:

        res = {}
        for answer in answers:
            if len(answer.get_knowledgeObjects()) > 0:
                for knowledgeObject in answer.get_knowledgeObjects():
                    # kObjID: str = str(knowledgeObject.id)
                    if knowledgeObject not in res:
                        res[knowledgeObject] = [answer]
                    else:
                        res[knowledgeObject].append(answer)

        res = [(answers[0], len(answers)) for answers in res.values()]

        # Sorts the answers
        res.sort(key=lambda x: x[1], reverse=True)

        # zwerg = []
        # for result in res:
        #     for answer in answers:
        #         if answer.normalized_form() == result[0]:
        #             zwerg.extend(answer.getKnowledgeObject())
        return res

    def make_decision_for_variable(self, variables_question_answering, variables_from_toplogical_map) -> Set[str]:
        variables_searchSpace: Set[KnowledgeObject] = self.__identify_variables_by_searchSpace(
            variables_from_toplogical_map)
        variables_frequency: Set[KnowledgeObject] = self.__identify_variables_by_frequency(
            variables_from_toplogical_map)
        variables_question_answering = set(variables_question_answering)
        found_kObjs: Set[KnowledgeObject] = self.__tmr_vote(variables_searchSpace, variables_frequency,
                                                            variables_question_answering)

        variables = set([kObj.category for kObj in found_kObjs])

        _save_variables_as_json(variables, found_kObjs, variables_searchSpace, variables_frequency,
                                variables_question_answering, variables_from_toplogical_map,
                                )
        self.infrastructure.send_variables_to_scheduler(variables)

    def __identify_variables_by_searchSpace(self, variables):
        kObjsAbstract = set(variables['get_kObjs_in_abstract'])
        kObjsProblemDefinition = set(variables['get_kObjs_in_summary'])
        kObjsSummary = set(variables['get_kObjs_in_goal_description'])
        intersectionBetweenAbstractAndProblemDefinition = kObjsAbstract.intersection(kObjsProblemDefinition)
        intersectionBetweenAbstractAndSummary = kObjsAbstract.intersection(kObjsSummary)
        intersectionBetweenSummaryAndProblemDefinition = kObjsSummary.intersection(kObjsProblemDefinition)
        return intersectionBetweenAbstractAndProblemDefinition.union(intersectionBetweenAbstractAndSummary).union(
            intersectionBetweenSummaryAndProblemDefinition)

    def __identify_variables_by_frequency(self, variables):
        return set(variables['get_top_5_kObjs'])

    def __tmr_vote(self, variables_1, variables_2, variables_3) -> Set:
        '''
        Triple Modular Mechanismn to get only variables that are at least in two answersets
        :param variables_1:
        :param variables_2:
        :param variables_3:
        :return: Returns a Set of distinct Variables
        '''

        new_var = variables_1.intersection(variables_2).union(variables_1.intersection(variables_3))
        return new_var.union(variables_2.intersection(variables_3))
