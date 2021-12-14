from __future__ import annotations
from typing import List, Tuple
from core.Datamodels.Answer_Document import _AnswerDocument
import core.apis._internal_.decision_maker_api as DM
import core.apis._internal_.scheduler_api as SD
from core.apis._internal_.QA_Pipeline.QA_Fabric import QuestionFabric

class Infrastructure:


    def __init__(self, decisonmaker, scheduler, qa_fabric):
        self.decision_maker: DM.DecisionMaker = decisonmaker
        self.scheduler: SD.Scheduler = scheduler
        self.qa_fabric: QuestionFabric = qa_fabric
        self.parking_spot: List[_AnswerDocument] = []
        self.topological_map: TopologicalMap = None
        self.scheduler.set_infrastructure(self)
        self.qa_fabric.set_infrastructure(self)
        self.decision_maker.set_infrastructure(self)

    def set_topological_map(self, topMap: TopologicalMap) -> None:
        self.topological_map = topMap

    def get_previous_answers_of_same_type(self, answerDoc: _AnswerDocument) -> List[_AnswerDocument]:
        return self.scheduler.get_previous_answers_of_same_type(answerDoc)

    def send_waiting_data_to_decision_maker(self):
        for answerDoc in self.parking_spot:
            self._send_data_to_decision_maker(answerDoc)

    def send_data_to_waiting_spot(self, data: _AnswerDocument):
        # If the answerDocument is the first time in the parking spot
        # its ok, but if it will try to be a second time in it, reject the answerDoc
        if data not in self.parking_spot:
            self.parking_spot.append(data)
        else:
            # Breaking condition for the waiting answers
            self._send_data_to_scheduler('rejected', data)

    def _send_data_to_scheduler(self, decision: str, data: _AnswerDocument):
        if data in self.parking_spot:
            self.parking_spot.remove(data)

        if decision == 'accepted':
            self.scheduler.accepted_answer(data)

        elif decision == 'rejected':
        #    self.scheduler.rejected_answer(data)
            self.scheduler.update_answer_document(data)
        elif decision == 'variables':
            self.scheduler._get_variables(data)
        else:
            self.scheduler.update_answer_document(decision, data)


    def _send_data_to_decision_maker(self, data: _AnswerDocument):
        self.decision_maker.make_decision(data)


    def _send_data_to_qa_fabric(self, data: _AnswerDocument):
        self.qa_fabric.load_question_template_in_queue(data)
        self.qa_fabric.wait_until_question_answering_finishes()


    def _send_to_topological_map(self, description: str):
        if description == 'get_kObjs_in_abstract':
            return self.topological_map.get_kObjs_in_abstract()
        elif description == 'get_kObjs_in_summary':
            return self.topological_map.get_kObjs_in_summary()
        elif description == 'get_kObjs_in_goal_description':
            return self.topological_map.get_kObjs_in_goal_description()
        elif description == 'get_top_5_kObjs':
            return self.topological_map.getTopNknowledgeObjects(n=5)

    def send_variation_decisions_to_decisionmaker(self, path_description: List[str], variables_question_answering):
        variables_from_path = {}
        for destination in path_description:
            variables_from_path[destination] = self._send_to_topological_map(destination)
        self.decision_maker.make_decision_for_variable(variables_question_answering, variables_from_path)


    def send_variables_to_scheduler(self, variables):
        self.scheduler.set_variables(variables)


    def interpret_decision(self, data: List[Tuple[str, _AnswerDocument]]):
        for decision, answer in data:
            if decision == 'to_qa':
                self._send_data_to_qa_fabric(answer)
            elif decision == 'to_decision_maker':
                self._send_data_to_decision_maker(answer)
            else:
                self._send_data_to_scheduler(decision, answer)


    def get_waiting_answerDocs(self) -> List[_AnswerDocument]:
        return self.parking_spot




