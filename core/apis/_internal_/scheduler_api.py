from __future__ import annotations
from typing import List, Set, Tuple
from core.Datamodels.Answer_Document import AnswerLog
from core.apis._internal_.generator.template_creation_api import TemplateEngine
from core.Datamodels.Archive.Answer_Document_Archive import AnswerDocumentArchive
from core.Datamodels.Question_Template import QuestionTemplate
from core.Datamodels.coordinating_model import Infrastructure
from core.Datamodels.hypothesis_modell import HypothesisSpace


class Scheduler:

    def __init__(self, template_engine, hypothesisspace, archive):
        self._template_engine: TemplateEngine = template_engine
        self._archive: AnswerDocumentArchive = archive
        self._question_templates: List[QuestionTemplate] = []
        self._variation_question_templates: List[QuestionTemplate] = []
        self._static_question_templates_without_dependencies: List[QuestionTemplate] = []
        self._static_question_templates_with_dependencies: List[QuestionTemplate] = []
        self._output_question_templates: List[QuestionTemplate] = []
        self.infracstructure: Infrastructure = None
        self.__variables: List[str] = []
        self._hypothesisSpace: HypothesisSpace = hypothesisspace
        self._goal_question_templates = []

    def save_variables_as_json(self):

        pass

    def get_previous_answers_of_same_type(self, answerDoc: AnswerLog) -> List[AnswerLog]:
        answers: List[AnswerLog] = self._hypothesisSpace.get_answers()

        searched_answer_type = answerDoc.questionTemplate.get_questionType()[1]
        answers_of_same_type: List[AnswerLog] = []
        for answer in answers:
            answer_type = answer.questionTemplate.get_questionType()[1]
            if searched_answer_type == answer_type:
                answers_of_same_type.append(answer)

        return answers_of_same_type

    def set_questionTemplate(self, questionTemplates: List[QuestionTemplate]) -> None:
        self._question_templates = questionTemplates

    def set_infrastructure(self, infracstructure: Infrastructure) -> None:
        self.infracstructure = infracstructure

    def get_variables(self):
        ### Do some stuff

        # goal_answer_docs = []
        # for questionTemplate in goal_templates:
        #     goal_answer_docs.append(self._template_engine.build_answer_log(questionTemplate))
        self.identify_variables_by_question_answering()

    def _get_variables(self, data: Set[AnswerLog]):
        variables_question_answering = data.get_knowledgeObjects_from_answers()
        self._hypothesisSpace.save_answerDoc(data)
        path_description_topological_map: List[str] = ['get_kObjs_in_abstract', 'get_kObjs_in_summary',
                                                       'get_kObjs_in_goal_description', 'get_top_5_kObjs']
        self.infracstructure.send_variation_decisions_to_decisionmaker(path_description_topological_map,
                                                                       variables_question_answering)

    def identify_variables_by_question_answering(self):
        answerDocuments = []
        for questionTemplate in self._question_templates:
            specific_questiontype = questionTemplate.get_questionType()[0]
            if specific_questiontype == 'GOAL':
                document: Tuple[str, AnswerLog] = (
                'to_qa', self._template_engine.build_answer_log(questionTemplate, doc_type='GOAL'))
                answerDocuments.append(document)
                self._goal_question_templates.append(questionTemplate)
                self._archive.save(document)

        self.infracstructure.interpret_decision(answerDocuments)

        # Check the waiting answers if these could be answered now

    def set_variables(self, variables):
        self.__variables = variables
        self._build_scheduling_plan(variables)

    def _build_scheduling_plan(self, variables: Set[str]):
        """ Creates a scheduling plan """
        # Get all Variational Question Templates
        for qTemplate in self._question_templates:
            for variable in variables:
                if qTemplate.has_dependency_to_category(variable):
                    self._variation_question_templates.append(qTemplate)

        for qTemplate in self._question_templates:
            in_variations: bool = qTemplate in self._variation_question_templates
            in_goal: bool = qTemplate in self._goal_question_templates
            if not in_variations and not in_goal:
                is_output_parameter: bool = qTemplate._broader_question_type == 'WEAR_BEHAVIOUR' and qTemplate.has_dependency_constraints() or \
                                            qTemplate._broader_question_type == 'FRICTION_BEHAVIOUR' and qTemplate.has_dependency_constraints()
                # Get all Output Question Template
                if is_output_parameter:
                    self._output_question_templates.append(qTemplate)
                else:
                    # Get all static Question Templates

                    # If questionTemplate has any dependency
                    # Save it separate
                    if qTemplate.has_dependency_constraints():
                        if qTemplate.has_dependency_to_hypothesis():
                            self._output_question_templates.append(qTemplate)
                        else:
                            self._static_question_templates_with_dependencies.append(qTemplate)
                    else:
                        self._static_question_templates_without_dependencies.append(qTemplate)


    def set_variations(self):
        variations: List[AnswerLog] = []
        for qTemplate in self._variation_question_templates:
            answerDocument = ('to_qa', self._template_engine.build_answer_log(qTemplate, doc_type='VARIATION'))
            variations.append(answerDocument)
            self._archive.save(answerDocument)

        self.infracstructure.interpret_decision(variations)

    def _check_waiting_answerDocs(self):
        self.infracstructure.send_waiting_data_to_decision_maker()

    def set_static_parameters(self):

        static_parameters: List[AnswerLog] = []
        for qTemplate in self._static_question_templates_without_dependencies:
            answerDocument = ('to_qa', self._template_engine.build_answer_log(qTemplate, doc_type='STATIC'))
            static_parameters.append(answerDocument)
            self._archive.save(answerDocument)
        self.infracstructure.interpret_decision(static_parameters)

        # Check the waiting answers if these could be answered now
        self._check_waiting_answerDocs()

    def _build_hypothesis(self) -> List[Hypothesis]:
        return self._hypothesisSpace._build_hypothesis()

    def set_output_parameters(self):
        # Build Hypothesis
        hypothesis = self._build_hypothesis()
        # For each Hypothesis build a answerDocument

        variations: List[AnswerLog] = []
        for hypo in hypothesis:
            for qTemplate in self._output_question_templates:
                # ToDo: Expenisive operation maybe look for some things to imporve the performance
                answerDocument = ('to_qa', self._template_engine.build_answer_log(qTemplate,
                                                                                  doc_type='OUTPUT',
                                                                                  hypothesis=hypo))
                variations.append(answerDocument)
                self._archive.save(answerDocument)

        self.infracstructure.interpret_decision(variations)

        # Check the waiting answers if these could be answered now

    def accepted_answer(self, answerDoc: AnswerLog):
        # If the question is not a Variation. Check if the question has any not answered dependency
        # If so: send them after saving the answer to the qa_pipeline
        self._hypothesisSpace.save_answerDoc(answerDoc)
        new_answerDocuments = []
        if answerDoc.type != 'VARIATION':
            for questionTemplate in self._static_question_templates_with_dependencies:

                if questionTemplate.has_dependency_to_questionTemplate(answerDoc.questionTemplate):
                    if not self._archive.answerDoc_was_send(questionTemplate):
                        self._template_engine.update_hypothesisSpace(self._hypothesisSpace)
                        new_answerDocuments.append(self._template_engine.build_answer_log(task='normal',
                                                                                          mode=1,
                                                                                          template=questionTemplate,
                                                                                          doc_type='STATIC',
                                                                                          hypothesis=None))

        datas = []
        for answerDocument in new_answerDocuments:
            data = ('to_qa', answerDocument)

            self._archive.save(data)
            datas.append(data)

        self.infracstructure.interpret_decision(datas)

    def rejected_answer(self, answerDoc: AnswerLog):
        # Whats with the case if a questionTemplate has more as one strong dependency?
        # I haven't done it yet, but it should restrict the questionTemplate

        # For every qTemplate that has only a strong dependency to this answer
        # Reject them to, and this recursively
        self._hypothesisSpace.save_answerDoc(answerDoc)
        _not_answerable_questionTemplates = [answerDoc.questionTemplate]
        while _not_answerable_questionTemplates != []:
            zwerg_not_answerable_questionTemplates = []

            for questionTemplate in self._question_templates:
                for not_answerable_questionTemplate in _not_answerable_questionTemplates:
                    if questionTemplate.has_strong_dependency_to(not_answerable_questionTemplate):
                        zwerg_not_answerable_questionTemplates.append(questionTemplate)

            for questionTemplate in zwerg_not_answerable_questionTemplates:
                if questionTemplate in self._question_templates:
                    self._question_templates.remove(questionTemplate)
                if questionTemplate in self._static_question_templates_with_dependencies:
                    self._static_question_templates_with_dependencies.remove(questionTemplate)
                if questionTemplate in self._output_question_templates:
                    self._output_question_templates.remove(questionTemplate)
                if questionTemplate in self._variation_question_templates:
                    self._variation_question_templates.remove(questionTemplate)
                if questionTemplate in self._goal_question_templates:
                    self._goal_question_templates.remove(questionTemplate)
            # Update the loop
            _not_answerable_questionTemplates = zwerg_not_answerable_questionTemplates

    def update_answer_document(self, answerDoc: AnswerLog):
        answerDocument = None
        if answerDoc.get_mode() == 1:
            answerDocument = self._template_engine.build_answer_log(task='extended',
                                                                    mode=2,
                                                                    template=answerDoc.questionTemplate,
                                                                    doc_type=answerDoc.type,
                                                                    hypothesis=answerDoc.get_hypothesis())
        elif answerDoc.get_mode() == 2:
            answerDocument = self._template_engine.build_answer_log(task='enriched',
                                                                    mode=3,
                                                                    template=answerDoc.questionTemplate,
                                                                    doc_type=answerDoc.type,
                                                                    hypothesis=answerDoc.get_hypothesis())
        elif answerDoc.get_mode() == 3:
            answerDocument = self._template_engine.build_answer_log(task='extended_and_enriched',
                                                                    mode=4,
                                                                    template=answerDoc.questionTemplate,
                                                                    doc_type=answerDoc.type,
                                                                    hypothesis=answerDoc.get_hypothesis())
        else:
            self.rejected_answer(answerDoc)

        if answerDocument is not None:
            data = ('to_qa', answerDocument)

            self._archive.save(data)
            self.infracstructure.interpret_decision([data])
