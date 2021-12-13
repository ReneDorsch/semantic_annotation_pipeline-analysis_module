from __future__ import annotations

import json
from typing import List
from core.Datamodels import IO_Models
from core.Datamodels.Topological_Map import TopologicalMap
from core.Datamodels.Question_Template import QuestionTemplate
from core.apis._internal_.scheduler_api import Scheduler
from core.apis._internal_.decision_maker_api import DecisionMaker
from core.Datamodels.hypothesis_modell import HypothesisSpace
from core.apis._internal_.QA_Pipeline.QA_Fabric import QuestionFabric
from core.apis._internal_.template_creation_api import TemplateEngine
from core.Datamodels.coordinating_model import Infrastructure
from core import config


class ContextAnalyzer:

    def __init__(self):
        self._decisionmaker: DecisionMaker = DecisionMaker()
        self._hypothesisSpace: HypothesisSpace = HypothesisSpace()
        self._qa_pipeline: QuestionFabric = QuestionFabric()
        self._template_engine: TemplateEngine = TemplateEngine()
        self._topological_map: TopologicalMap = None
        self._scheduler: Scheduler = Scheduler(self._template_engine, self._hypothesisSpace)
        self._infrastructure: Infrastructure = Infrastructure(self._decisionmaker, self._scheduler, self._qa_pipeline)

    def _parse_questionTemplates(self):
        res = []
        with open(config.QUESTIONTEMPLATE_PATH, 'r') as file:
            questionTemplates = json.load(file)

        res = QuestionTemplate.read_from_json(questionTemplates)
        return res

    def parse_data_from_api(self, data: IO_Models.InputData):
        self._topological_map = TopologicalMap.read_from_api(data)

    def preprocess(self) -> bool:
        questionTemplates: List[QuestionTemplate] = self._parse_questionTemplates()
        self._template_engine.set_templates(questionTemplates)
        self._template_engine.set_topological_map(self._topological_map)
        self._infrastructure.set_topological_map(self._topological_map)
        self._qa_pipeline.initalize_question_answering()
        self._scheduler.set_questionTemplate(questionTemplates)

    def postprocess(self):
        self._qa_pipeline.stop_question_worker()
        del self._qa_pipeline
        del self._topological_map
        del self._scheduler
        del self._decisionmaker
        del self._hypothesisSpace
        del self._infrastructure

    def process(self):
        print("Find Variables")
        self._scheduler.get_variables()
        print("Find variational Parametres")
        self._scheduler.set_variations()
        print("Find Static Parametres")
        self._scheduler.set_static_parameters()
        print("Find Output Parametres")
        self._scheduler.set_output_parameters()

    def save_data(self) -> dict:
        res = self._hypothesisSpace.save_hypothesis_as_json(),
        return res

    def to_io(self):
        return self._hypothesisSpace.to_io()
