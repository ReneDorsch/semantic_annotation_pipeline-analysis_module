from __future__ import annotations
from typing import List, Dict, Tuple, Iterator
from queue import Queue

import torch
from transformers import pipeline, TapasTokenizer, TapasForQuestionAnswering

from core import config
from core.Datamodels.Datamodels import TableContext, TableAnswer, TextContext, TextAnswer, Question
from core.Datamodels.Answer_Document import AnswerDocument
import pandas as pd



def text_question_worker(queue: Queue):
    print("bin in text Question Worker")

    pip = initializeTextPipeline()
    print("Pipelines initialisiert")
    while True:

        answerList = []
        doc: AnswerDocument = queue.get()

        if doc == -1:
            print("Feierabend")
            break


        questionsContext: List[Tuple[Question, TextContext]] = doc.get_text_tuples()

        result = askQuestions(pip, questionsContext)


        for question, context, answer in result:
            _has_relevant_answer: bool = "answer" in answer and "start" in answer \
                                       and "end" in answer and "score" in answer
            if not _has_relevant_answer: print("Relevant answer: ", _has_relevant_answer)
            if _has_relevant_answer:
                answerList.append(TextAnswer(answer['answer'], answer['start'], answer['end'], question, context,
                                 answer['score']))


        doc._answers_in_text = answerList

        doc._answered_by_text = True

     #   print(f"Questions Answerd in Text {questionTemplate.questionCategory}")
        queue.task_done()


def askQuestions(searchEngine: pipeline, questionsContexts, batchSize: int = 8) -> Iterator[Tuple[
    Question, Context, Answer]]:
    questions = [_[0].get_question() for _ in questionsContexts]
    contexts = [_[1].text for _ in questionsContexts]

    try:
        answers: Dict = searchEngine(question=questions,
                                     context=contexts,  # List of Contexts used for the questions
                                     handle_impossible_answer=True,  # Checks if
                                     max_answer_len=30  # Length of Answer can be til 30 (sub)words
                                     )

    except ValueError:
        print("ValueError QA Pipeline 217")
        return []
    return zip([_[0] for _ in questionsContexts], [_[1] for _ in questionsContexts], answers)


    pass

########################################################################################################################
########################################################################################################################
########################################################################################################################


def prepare_inputs(tables: List['Table'], questions, tokenizer):
    """
      Convert dictionary into data frame and tokenize inputs given queries.
    """
    # Prepare inputs
    # Make the tables distinct
    question_context_dict = {}
    distinct_tables = []
    for num, table in enumerate(tables):
        try:
            table_df = table.as_pandas_df()
        except ValueError:
            table.as_pandas_df()
            continue
        if distinct_tables == []:
            distinct_tables.append(table_df)
            question_context_dict[num] = [table]
        else:
            if all(not table_df.equals(table_2) for table_2 in distinct_tables):
                distinct_tables.append(table_df)
                question_context_dict[num] = [table]

    queries = []
    for question in questions:
        if question not in queries:
            queries.append(question)

    questions_context_tuple = []
    for key in question_context_dict.values():

        questions_context_tuple.extend([(_,__) for _,__ in zip(key * len(queries), queries)])

    table_input_tuple = []
    for table in distinct_tables:
        with pd.option_context('display.max_rows', None, 'display.max_columns', None):
            print(table)
        inputs = tokenizer(table=table, queries=queries, padding='max_length', return_tensors="pt")
        table_input_tuple.append((table, inputs))

    # Return things
    return table_input_tuple, questions_context_tuple





def generate_predictions(inputs, model, tokenizer):
    """
      Generate predictions for some tokenized input.
    """
    # Generate model results
    res = []
    for table, input in inputs:
        outputs = model(**input)

        # Convert logit outputs into predictions for table cells and aggregation operators
        predicted_table_cell_coords, predicted_aggregation_operators = tokenizer.convert_logits_to_predictions(
            input,
            outputs.logits.detach(),
            outputs.logits_aggregation.detach()
        )
        res.append((predicted_table_cell_coords, predicted_aggregation_operators))

    # Return values
    return res


def postprocess_predictions(predictions, tables):
    """
      Compute the predicted operation and nicely structure the answers.
    """
    class Cell:
        def __init__(self, row, column):
            self.row: int = row
            self.column: int = column
    # Process predicted table cell coordinates
    answers = []
    for prediction, table in zip(predictions, tables):
        predicted_table_cell_coords, predicted_aggregation_operators = prediction
        table, _ = table


        for coordinates in predicted_table_cell_coords:
            if len(coordinates) == 1:
                # 1 cell
                answers.append(Cell(*coordinates[0]))
            else:
                # > 1 cell
                cell_values = []
                for coordinate in coordinates:
                    cell_values.append(Cell(*coordinate))
                answers.append(cell_values)

    # Return values
    return answers


def table_question_worker(queue: Queue):
    print("bin in table Question Worker")

    pip = initializeTablePipeline()
    print("Pipelines initialisiert")
    while True:

        answerList = []
        doc: AnswerDocument = queue.get()

        if doc == -1:
            print("Feierabend")
            break
        questionsContext: List[Tuple[Question, Context]] = doc.get_table_tuples()
        if len(questionsContext) > 0:
            result = ask_table_questions(pip[0], pip[1], questionsContext)

            for question, context, answer in result:
                # If there is only one answer for the question
                if not isinstance(answer, list):
                    answerList.append(TableAnswer(answer, question, context))
                # If there are serveral answers
                else:

                    for single_answer in answer:
                        answerList.append(TableAnswer(single_answer, question, context))
                        # If we have more as one possible answer, we handle every context as a new one

                        context = TableContext.copy(context)

            doc._answers_in_tables = answerList

        doc._answered_by_table = True

      #  print(f"Questions Answerd In Table: {questionTemplate.questionCategory}")
        queue.task_done()



def ask_table_questions(model, tokenizer, questionsContexts) -> Iterator[Tuple[
    Question, Context, Answer]]:
    questions = [_[0].get_question() for _ in questionsContexts]
    contexts = [_[1] for _ in questionsContexts]

    prepared_input, questions_context_tuple = prepare_inputs(contexts, questions, tokenizer)
    predictions = generate_predictions(prepared_input, model, tokenizer)
    answers = postprocess_predictions(predictions, prepared_input)
    return [_ for _ in zip([_[1] for _ in questions_context_tuple], [_[0] for _ in questions_context_tuple], answers)]


def initializeTablePipeline() -> pipeline:


    # Load pretrained tokenizer: TAPAS finetuned on WikiTable Questions
    tokenizer = TapasTokenizer.from_pretrained(config.T_QA_TOKENIZER, local_files_only=True)

    # Load pretrained model: TAPAS finetuned on WikiTable Questions
    model = TapasForQuestionAnswering.from_pretrained(config.T_QA_MODELL, local_files_only=True)


    return model, tokenizer


def initializeTextPipeline() -> pipeline:
    device: int = -1
    if torch.cuda.is_available():
        device = torch.cuda.current_device()
    else:
        torch.cuda.set_device(device)
    return pipeline(
        task="question-answering",                      # Type of Task
        model=config.QA_MODEL,          # Model used for QA
        tokenizer=config.QA_TOKENIZER,  # Tokenizer used to transform the words in a vector
        device=device                                   # device>0 -> GPU, device<0 CPU
    )