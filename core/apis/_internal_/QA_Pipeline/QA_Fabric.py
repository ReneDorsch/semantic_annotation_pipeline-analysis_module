from __future__ import annotations
from typing import List
from queue import Queue
from threading import Thread
import time
from core.apis._internal_.QA_Pipeline.QA_Worker import table_question_worker, text_question_worker
from core.Datamodels.Question_Template import QuestionTemplate
import core.Datamodels.coordinating_model as IS
import torch


class QuestionFabric:
    '''
    The QuestonFabric is a Interface between the decisionmaker and the actual question answering.
    It will be used to manage the workers and the Tasks of collecting/distributing data from/to the workers.
    '''

    def __init__(self, number_of_workers: int = 1):
        self.__table_pipeline: Queue = Queue()
        self.__text_pipeline: Queue = Queue()
        self.__number_of_workers: int = number_of_workers
        self.__text_worker_threads: List[Thread] = []
        self.__table_worker_threads: List[Thread] = []
        self._docs_in_pipeline: List[QuestionTemplate] = []
        self.infrastructure: IS.Infrastructure = None
        '''
        pipelines: All active pipelines in the QuestionFabric. Every Pipeline is a Queue, to whom every Taskspecific-Thread
                   (in our case Table and Text) has access. So it is possible to make the QA parallel to the other tasks
        number_of_workers: The number of workers used in the Questionfabric. The number will be doubled if you also want to
                            use the table QA. If you want to deactivate it, use the option ... .
                            Be aware that every worker will be in a seperate Thread. To have not to much RAM usage (every
                            Worker needs about 1 Gigabyte) use only 1 or 2.
        __question_template_datalog: Makes a log to see which question_templates and how often have already been answered
        _decision_maker: Decisionmaker, who decides which Action have to be done next with a Questiontemplate 
          
        '''

    def set_infrastructure(self, infrastructure: Infrastructure):
        self.infrastructure = infrastructure

    def initalize_question_answering(self):
        '''
        Initalizes everything needed for the QA Answering.
        :return: None
        '''
        # Initialize the Text QA Worker
        for i in range(self.__number_of_workers):
            thread = Thread(target=text_question_worker, args=(self.__text_pipeline,))
            thread.start()
            self.__text_worker_threads.append(thread)
        # Initialize the Table QA Worker
        for i in range(self.__number_of_workers):
            thread = Thread(target=table_question_worker, args=(self.__table_pipeline,))
            thread.start()
            self.__table_worker_threads.append(thread)

    def load_question_template_in_queue(self, doc: AnswerDocument):
        '''

        :param question_templates: List of Questiontemplates that should be answered by Question Answering
        :return: None
        '''
        self._docs_in_pipeline.append(doc)
        self.__table_pipeline.put(doc)
        self.__text_pipeline.put(doc)

    def stop_question_worker(self):
        # Send stopsignal to the worker Trheads
        for _ in range(self.__number_of_workers):
            self.__text_pipeline.put((-1))
            self.__table_pipeline.put((-1))

        # Waits for the threads to be finished
        for thread in self.__text_worker_threads:
            thread.join()
        for thread in self.__table_worker_threads:
            thread.join()
        torch.cuda.empty_cache()
        print("Alle Beendet")

    def wait_until_question_answering_finishes(self, seconds_to_wait: int = 900):
        counter: int = 0
        counter_between_questiontemplates: int = 0
        # Conditions for the loop
        time_period_exceeded: bool = True
        empty_pipelines: bool = True
        while time_period_exceeded and empty_pipelines:
            answered_question_templates = [_ for _ in self._docs_in_pipeline if _.has_answer()]
            if len(answered_question_templates) == 0:
                time.sleep(1)
                counter += 1
                counter_between_questiontemplates += 1
            else:
                goal_answere_docs = [_ for _ in answered_question_templates if _.type == "GOAL"]
                if len(goal_answere_docs) > 0:
                    [answered_question_templates.remove(_) for _ in goal_answere_docs]
                    self._remove_question_templates_from_pipeline(goal_answere_docs)
                    self.send_question_template_to_scheduler(goal_answere_docs)

                self._remove_question_templates_from_pipeline(answered_question_templates)
                self.send_question_template_to_decision_maker(answered_question_templates)
                counter = 0
                counter_between_questiontemplates = 0

            # Update conditions
            time_period_exceeded = counter <= seconds_to_wait
            empty_pipelines = (self._docs_in_pipeline != [] or counter_between_questiontemplates > 5)

        self.reject_question_templates(self._docs_in_pipeline)

    def _remove_question_templates_from_pipeline(self, questionTemplates: List[QuestionTemplate]):
        self._docs_in_pipeline = [_ for _ in self._docs_in_pipeline if _ not in questionTemplates]

    def send_question_template_to_decision_maker(self, questionTemplates: List[QuestionTemplate]):
        self.infrastructure.interpret_decision(
            [('to_decision_maker', questionTemplate) for questionTemplate in questionTemplates])

    def send_question_template_to_scheduler(self, questionTemplates: List[QuestionTemplate]):
        self.infrastructure.interpret_decision(
            [('variables', questionTemplate) for questionTemplate in questionTemplates])

    def reject_question_templates(self, questionTemplates: List[QuestionTemplate]):
        self.infrastructure.interpret_decision(
            [('rejected', questionTemplate) for questionTemplate in questionTemplates])
