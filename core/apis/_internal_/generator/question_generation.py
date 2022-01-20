

class QuestionGenerator:
    """ A class that generates questions and with their contexts. """


    def search_for_contexts(self) -> List[Context]:
        """ Finds contexts for a set of parameters. """

        pass

    def generate_questions(self, contexts: List[Context], questionTemplate: QuestionTemplate) -> List[Question]:
        """ Generates questions. """
        pass



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