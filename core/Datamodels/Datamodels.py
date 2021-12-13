from __future__ import annotations
from core.Datamodels import IO_Models
from typing import List, Optional, Tuple
import re
from pandas import DataFrame


########################################################################################################################
########################################################################################################################
########################################################################################################################

class Text:

    def __init__(self):
        self._chapters: List[Chapter] = []
        self._knowledgeObjects: List[KnowledgeObject] = []
        self.__knowledgeObject_references: List[int] = []

    def update_sentences(self) -> None:
        ''' Creates textual sentences for each sentence'''
        for chapter in self._chapters:
            chapter.update_sentences()


    @classmethod
    def read_from_api(cls, data: List[IO_Models.InputChapter]):
        data_chapters: List[Chapter] = []
        data_knowledgeObject_references: List[int] = []

        for chapter in data:
            data_chapters.append(Chapter.read_from_api(chapter))

        data_knowledgeObject_references = []
        for chapter in data:
            data_knowledgeObject_references.extend(chapter.knowledgeObject_references)

        text_object: Text = cls()
        text_object._chapters = data_chapters
        text_object.__knowledgeObject_references = data_knowledgeObject_references

        return text_object


    @property
    def chapters(self) -> List[Chapter]:
        return self._chapters

    @chapters.setter
    def chapters(self, value: List[Chapter]):
        self._chapters = value

    @property
    def knowledgeObjects(self) -> List[KnowledgeObject]:
        return self._knowledgeObjects

    @knowledgeObjects.setter
    def knowledgeObjects(self, value: List[KnowledgeObject]):
        kObjs: List[KnowledgeObject] = []
        for kObj in value:
            if kObj.id in self.__knowledgeObject_references:
                kObjs.append(kObj)

        self._knowledgeObjects = kObjs

        for chapter in self._chapters:
            chapter.set_knowledgeObjects(self.knowledgeObjects)

class Abstract:
    def __init__(self):

        self._paragraphs: List[Paragraph] = []
        self._knowledgeObjects: List[KnowledgeObject] = []
        self.__knowledgeObject_references: List[int] = []

    def update_sentences(self) -> None:
        ''' Creates textual sentences for each sentence'''
        for paragraph in self._paragraphs:
            for sentence in paragraph.get_sentences():
                sentence.update_sentence_form()


    @classmethod
    def read_from_api(cls, data: IO_Models.InputChapter):
        data_paragraphs: List[Paragraph] = []
        data_knowledgeObject_references: List[int] = []

        data_paragraphs = data.paragraphs
        data_knowledgeObject_references = data.knowledgeObject_references

        chapter_object: Abstract = cls()
        chapter_object._paragraphs = [Paragraph.read_from_api(data) for data in data_paragraphs]
        chapter_object.__knowledgeObject_references = data_knowledgeObject_references

        return chapter_object



    def get_paragraphs(self) -> List[Paragraph]:
        return self._paragraphs



    @property
    def knowledgeObjects(self) -> List[KnowledgeObject]:
        return self._knowledgeObjects


    def set_knowledgeObjects(self, value: List[KnowledgeObject]):
        kObjs: List[KnowledgeObject] = []
        for kObj in value:
            if kObj.id in self.__knowledgeObject_references:
                kObjs.append(kObj)

        self._knowledgeObjects = kObjs

        for paragraph in self._paragraphs:
            try:
                paragraph.set_knowledgeObjects(kObjs)
            except AttributeError:
                print("ok")

class Chapter:
    def __init__(self):
        self._paragraphs: List[Paragraph] = []
        self._knowledgeObjects: List[KnowledgeObject] = []
        self.__knowledgeObject_references: List[int] = []

    def update_sentences(self):
        for paragraph in self.get_paragraphs():
            for sentence in paragraph.get_sentences():
                sentence.update_sentence_form()

    @classmethod
    def read_from_api(cls, data: IO_Models.InputChapter):
        data_paragraphs: List[Paragraph] = []
        data_knowledgeObject_references: List[int] = []

        data_paragraphs = data.paragraphs
        data_knowledgeObject_references = data.knowledgeObject_references

        chapter_object: Chapter = cls()
        chapter_object._paragraphs = [Paragraph.read_from_api(data) for data in data_paragraphs]
        chapter_object.__knowledgeObject_references = data_knowledgeObject_references

        return chapter_object


    def get_paragraphs(self) -> List[Paragraph]:
        return self._paragraphs


    def set_paragraphs(self, value: List[Paragraph]):
        self._paragraphs = value

    @property
    def knowledgeObjects(self) -> List[KnowledgeObject]:
        return self._knowledgeObjects


    def set_knowledgeObjects(self, value: List[KnowledgeObject]):
        kObjs: List[KnowledgeObject] = []
        for kObj in value:
            if kObj.id in self.__knowledgeObject_references:
                kObjs.append(kObj)

        self._knowledgeObjects = kObjs

        for paragraph in self._paragraphs:
            paragraph.set_knowledgeObjects(kObjs)

class Paragraph:

    def __init__(self):
        self._sentences: List[Sentence] = []
        self._knowledgeObjects: List[KnowledgeObject] = []
        self.__knowledgeObject_references: List[int] = []

    @classmethod
    def read_from_api(cls, data: IO_Models.InputParagraph):
        data_sentences: List[Sentence] = []
        data_knowledgeObject_references: List[int] = []

        data_sentences = data.sentences
        data_knowledgeObject_references = data.knowledgeObject_references

        paragraph_object: Paragraph = cls()

        prevSentence: Sentence = None
        for data in data_sentences:
            prevSentence = Sentence.read_from_api(data, prevSentence)
            paragraph_object._sentences.append(prevSentence)

        paragraph_object.__knowledgeObject_references = data_knowledgeObject_references

        return paragraph_object


    def get_sentences(self) -> List[Sentence]:
        return self._sentences


    def set_sentences(self, value: List[Sentence]):
        self._sentences = value

    @property
    def knowledgeObjects(self) -> List[KnowledgeObject]:
        return self._knowledgeObjects

    def set_knowledgeObjects(self, value: List[KnowledgeObject]):
        kObjs: List[KnowledgeObject] = []
        for kObj in value:
            if kObj.id in self.__knowledgeObject_references:
                kObjs.append(kObj)

        self._knowledgeObjects = kObjs

        for sentence in self._sentences:
            sentence.set_knowledgeObjects(kObjs)

class Sentence:
    ID_Counter = 1
    def __init__(self):
        self._id: int = Sentence.ID_Counter
        self._words: List[Word] = []
        self._knowledgeObjects: List[KnowledgeObject] = []
        self.__knowledgeObject_references: List[int] = []
        self._prev_sentence: Sentence = None
        self._next_sentence: Sentence = None
        self._text: str = ''
        self._extended: str = ''
        self._enriched: str = ''
        self._extended_and_enriched: str = ''
        Sentence.ID_Counter += 1

    def get_position_of_sentence(self) -> int:
        return self._id

    def update_sentence_form(self) -> None:
        self._text = self._get_form('normal')
        self._extended = self._get_form('extended')
        self._enriched = self._get_form('enriched')
        self._extended_and_enriched = self._get_form('extended_and_enriched')


    def get_words_at(self, start, end, format) -> List[Word]:
        words: List[Word] = []

        start_word: int = 0
        end_word: int = 0

        for word in self._words:
            if format == 'normal':
                textual_representation_of_word = word.normal_form
            elif format == 'extended':
                textual_representation_of_word = word.long_form
            elif format == 'enriched':
                if word.knowledgeObject is not None:
                    textual_representation_of_word = word.normal_form + f" ({word.knowledgeObject.category})"
                else:
                    textual_representation_of_word = word.normal_form
            elif format == 'extended_and_enriched':
                if word.knowledgeObject is not None:
                    textual_representation_of_word = word.long_form + f" ({word.knowledgeObject.category})"
                else:
                    textual_representation_of_word = word.long_form

            if word.has_whitespace_after():
                end_word = start_word + len(textual_representation_of_word) + 1
            else:
                end_word = start_word + len(textual_representation_of_word)

            if start <= start_word < end or start < end_word <= end:
                words.append(word)

            start_word = end_word

        return words

    def get_knowledgeObjects_at(self, start, end, format) -> List[KnowledgeObject]:
        kObjs: List[KnowledgeObject] = []

        start_word: int = 0
        end_word: int = 0


        for word in self._words:
            if format == 'normal':
                textual_representation_of_word = word.normal_form
            elif format == 'extended':
                textual_representation_of_word = word.long_form
            elif format == 'enriched':
                if word.knowledgeObject is not None:
                    textual_representation_of_word = word.normal_form + f" ({word.knowledgeObject.category})"
                else:
                    textual_representation_of_word = word.normal_form
            elif format == 'extended_and_enriched':
                if word.knowledgeObject is not None:
                    textual_representation_of_word = word.long_form + f" ({word.knowledgeObject.category})"
                else:
                    textual_representation_of_word = word.long_form

            if word.has_whitespace_after():
                end_word = start_word + len(textual_representation_of_word) + 1
            else:
                end_word = start_word + len(textual_representation_of_word)

            if start <= start_word < end or start < end_word <= end:
                if word.knowledgeObject is not None:
                    kObjs.append(word.knowledgeObject)

            start_word = end_word

        return kObjs

    def find_textual_representation(self, kObj: KnowledgeObject) -> str:
        representation: str = ''
        if kObj not in self._knowledgeObjects:
            return representation

        sentence = self.get_form('normal')
        for label in kObj.labels:
            if label in sentence:
                representation = label
        return representation


    @classmethod
    def read_from_text(cls, text, knowledgeObjects_ids):
        sentence = cls()
        sentence.__knowledgeObject_references = knowledgeObjects_ids
        sentence._text = text
        sentence._extended = text
        sentence._enriched = text
        sentence._enriched_and_extended = text
        sentence._words = Word.read_from_tables(text)
        return sentence

    @classmethod
    def read_from_api(cls, data: IO_Models.InputSentence, prev_sentence: Sentence = None):
        data_words: List[Word] = []
        data_knowledgeObject_references: List[int] = []

        data_words = data.words
        data_knowledgeObject_references = data.knowledgeObject_references

        sentence_object: Sentence = cls()
        sentence_object._words = []
        for data in data_words:
            sentence_object._words.append(Word.read_from_api(data, sentence_object._words))
        sentence_object.__knowledgeObject_references = data_knowledgeObject_references


        if prev_sentence is not None:
            sentence_object._prev_sentence = prev_sentence
            prev_sentence._next_sentence = sentence_object

        return sentence_object


    def get_framing_sentences(self, frame_size: int):
        sentences = [self]
        prev_sentence: Sentence = self._prev_sentence
        next_sentence: Sentence = self._next_sentence
        for n in range(frame_size):
            if prev_sentence is not None:
                sentences = [prev_sentence] + sentences
                prev_sentence = prev_sentence._prev_sentence
            if next_sentence is not None:
                sentences = sentences + [next_sentence]
                next_sentence = next_sentence._next_sentence
        return sentences

    def get_form(self, format='normal'):
        if format == 'normal':
            return self._text
        elif format == 'extended':
            return self._extended
        elif format == 'enriched':
            return self._enriched
        elif format == 'extended_and_enriched':
            return self._extended_and_enriched
        else:
            return self._text

    def _get_form(self, format='normal'):
        textual_representation: str = ''

        for word in self._words:
            textual_representation_of_word = ''
            if format == 'normal':
                textual_representation_of_word = word.normal_form
            elif format == 'extended':
                textual_representation_of_word = word.long_form
            elif format == 'enriched':
                if word.knowledgeObject is not None:
                    textual_representation_of_word = word.normal_form + f" ({word.knowledgeObject.category})"
                else:
                    textual_representation_of_word = word.normal_form
            elif format == 'extended_and_enriched':
                if word.knowledgeObject is not None:
                    textual_representation_of_word = word.long_form + f" ({word.knowledgeObject.category})"
                else:
                    textual_representation_of_word = word.long_form

            if word.has_whitespace_after():
                textual_representation += textual_representation_of_word + ' '
            else:
                textual_representation += textual_representation_of_word
        return textual_representation





    @property
    def words(self) -> List[Word]:
        return self._words

    @words.setter
    def words(self, value: List[Word]):
        self._words = value

    @property
    def knowledgeObjects(self) -> List[KnowledgeObject]:
        return self._knowledgeObjects


    def set_knowledgeObjects(self, value: List[KnowledgeObject]):
        kObjs: List[KnowledgeObject] = []
        for kObj in value:
            if kObj.id in self.__knowledgeObject_references:
                kObjs.append(kObj)

        self._knowledgeObjects = kObjs

        for word in self._words:
            word.set_knowledgeObject(kObjs)

class Word:
    COUNTER = 999999999
    def __init__(self):
        self.__id: int = -9999
        self._word: str = ''
        self._normalized_word: str = ''
        self._longform_word: str = ''
        self._start_pos: int = -9999
        self._end_pos: int = -9999
        self.__whitespace_after_word: int = True
        self.__prev_word: Optional[Word] = None
        self._knowledgeObject: Optional[KnowledgeObject] = None
        self.__knowledgeObject_reference: Optional[int] = -9999

    def has_whitespace_after(self) -> bool:
        return self.__whitespace_after_word

    @classmethod
    def read_from_tables(cls, text: str):
        res = []
        end_pos: int = 0
        for match in re.finditer(" ", text):
            start_pos = end_pos
            end_pos = match.start()
            word = cls()
            word._word = text[start_pos: end_pos]
            word._word = text[start_pos: end_pos].lower()
            word._longform_word = text[start_pos: end_pos]
            word._start_pos = start_pos
            word._end_pos = end_pos
            word.__id = Word.COUNTER
            Word.COUNTER -= 1
            res.append(word)

        start_pos = end_pos
        end_pos = len(text)
        word = cls()
        word._word = text[start_pos: end_pos]
        word._word = text[start_pos: end_pos].lower()
        word._longform_word = text[start_pos: end_pos]
        word._start_pos = start_pos
        word._end_pos = end_pos
        word.__id = Word.COUNTER
        Word.COUNTER -= 1
        res.append(word)
        return res




    @classmethod
    def read_from_api(cls, data: IO_Models.InputWord, prevWords: List[Word] = []):
        data_id: int = data.id
        data_knowledgeObject_reference: int = data.knowledgeObject_reference
        data_word: str = data.word
        data_normalized_word: str = data.normalized_word
        data_longform_word: str = data.longform_word
        data_start_pos: int = data.start_pos
        data_end_pos: int = data.end_pos
        data_prev_word: Optional[Word] = None
        data_whitespace_after_word: bool = bool(data.whitespace_after_word)
        data_knowledgeObject_reference: Optional[int] = -9999

        if hasattr(data, 'prev_word'):
            for word in prevWords:
                if word.id == data.prev_word:
                    data_prev_word = word
                    break

        if hasattr(data, 'knowledgeObject_reference'):
            data_knowledgeObject_reference = data.knowledgeObject_reference

        word_object: Word = cls()
        word_object.__id = data_id
        word_object._word = data_word
        word_object._normalized_word = data_normalized_word
        word_object._longform_word = data_longform_word
        word_object._start_pos = data_start_pos
        word_object._end_pos = data_end_pos
        word_object.__prev_word = data_prev_word
        word_object.__whitespace_after_word = data_whitespace_after_word
        word_object.__knowledgeObject_reference = data_knowledgeObject_reference

        return word_object


    @property
    def id(self) -> int:
        return self.__id

    @property
    def normal_form(self) -> str:
        return self._word

    @property
    def normalized_form(self) -> str:
        return self._normalized_word

    @property
    def long_form(self) -> str:
        return self._longform_word



    @property
    def knowledgeObject(self) -> KnowledgeObject:
        return self._knowledgeObject



    def set_knowledgeObject(self, value: List[KnowledgeObject]):
        # Get the first apperance of the KnowledgeObject
        for kObj in value:
            if kObj.id == self.__knowledgeObject_reference:
                self._knowledgeObject = kObj
                return



########################################################################################################################
########################################################################################################################
########################################################################################################################

class Table:

    def __init__(self):
        self._header: Header = None
        self._table_header: Line = None
        self._data: List[Line] = []
        self._units: Line = None
        self._textual_representation: List[Sentence] = []
        self.__knowledgeObject_references: List[int] = []
        self._knowledgeObjects: List[KnowledgeObject] = []
        self._table_name: str = ''
        self.description: List[Sentence] = []
        self.table_data = []

    def table_as_list(self) -> List:

        data_lines = [[_._text for _ in line.cells] for line in self._data]
        res = DataFrame(data_lines, index=[_._text for _ in self._table_header.cells]).T

        return res

    def get_knowledgeObjects(self) -> List[KnowledgeObject]:
        return self._knowledgeObjects


    def get_cell_at(self, cell_coordinates) -> Cell:
        # If the first row was selected it is the labels
        #if row == 0:
        #    return self._table_header.get_cell_at(column)
        # Else it is the data
        #else:

        return self._data[cell_coordinates.column].get_cell_at(cell_coordinates.row)


    def get_textual_representation(self):
        return self._textual_representation

    def get_table_name(self) -> str:
        return self._table_name

    def _set_table_name(self):
        if self._header is not None:
            description = self._header._description
            regex = '(fig\.|figure|table|tab\.) *\d+'
            res = re.search(regex, description.get_form('normal').lower())
            if res is not None:
                self._table_name = res.group()

    def as_pandas_df(self) -> DataFrame:
        table = self.table_as_list()
        return table


    def set_knowledgeObjects(self, value: List[KnowledgeObject]):
        kObjs: List[KnowledgeObject] = []
        for kObj in value:
            if kObj.id in self.__knowledgeObject_references:
                kObjs.append(kObj)

        self._knowledgeObjects = kObjs

        for line in self._data:
            line.set_knowledgeObjects(self._knowledgeObjects)

        for sentence in self._textual_representation:
            sentence.set_knowledgeObjects(self._knowledgeObjects)

    @classmethod
    def read_from_api(cls, data: IO_Models.InputTable):
        data_header = None
        if data.description is not None:
            data_header = Header.read_from_api(data.description)

        _data = [Line.read_from_api(line) for line in data.data]
        _table_header = Line.read_from_api(data.table_header)
        _units = data.units

        textual_representations = []
        for line in _data:
            for cell, table_cell,  unit in zip(line.cells, _table_header.cells, _units):
                text: str = f"The {table_cell._text} has a value of {cell._text}{' in ' + unit if unit != '' else ''}."
                text = re.sub(" +", " ", text)
                textual_representations.append(Sentence.read_from_text(text, data.knowledgeObject_references))

        table: Table = cls()
        table.__knowledgeObject_references = data.knowledgeObject_references
        table._table_header = _table_header
        table._data = _data
        table._units = _units
        table._textual_representation = textual_representations
        table._header = data_header

        table._set_units()
        table._set_table_name()
        table.table_data = table.get_table_name()

        return table

    def _set_units(self):
        for line in self._data:
            for cell, unit in zip(line.cells, self._units):
                if unit not in cell._text:
                    cell._text_with_unit = re.sub(' +', ' ', cell._text + " " + unit)
                    print(cell._text_with_unit)

class Line:

    def __init__(self):
        self.cells: List[Cell] = []
        self.__knowledgeObject_references = []

    def get_cell_at(self, position: int) -> Cell:
        return self.cells[position]

    def as_list(self) -> List[str]:
        return [_.get_text() for _ in self.cells]

    def get_knowledgeObjects_references(self) -> List[int]:
        return self.__knowledgeObject_references

    @classmethod
    def read_from_api(cls, data):
        line: Line = cls()
        line.cells = [Cell.read_from_api(cell) for cell in data.cells]

        references = []
        for cell in line.cells:
            if cell.has_references():
                references.extend(cell.get_references())
        line.__knowledgeObject_references = references
        return line

    def set_knowledgeObjects(self, value: List[KnowledgeObject]):
        kObjs: List[KnowledgeObject] = []
        for kObj in value:
            if kObj.id in self.__knowledgeObject_references:
                kObjs.append(kObj)

        self._knowledgeObjects = kObjs

        for cell in self.cells:
            cell.set_knowledgeObjects(kObjs)

class Cell:

    def __init__(self):
        self._text = ''
        self._text_with_unit = ''
        self._words: List[Word] = []
        self.__knowledgeObject_references: List[int] = []
        self._knowledgeObjects: List[KnowledgeObject] = []
        self._category: str = ''

    def has_references(self) -> bool:
        return self.__knowledgeObject_references != []

    def get_references(self) -> List[int]:
        return self.__knowledgeObject_references

    def get_text(self) -> str:
        return self._text

    def get_knowledgeObjects(self) -> List[KnowledgeObject]:
        return self._knowledgeObjects

    def set_knowledgeObjects(self, value: List[KnowledgeObject]):
        kObjs: List[KnowledgeObject] = []
        for kObj in value:
            for _reference_kObj in self.__knowledgeObject_references:
                if kObj.id == _reference_kObj:
                    kObjs.append(kObj)

        self._knowledgeObjects = kObjs



    @classmethod
    def read_from_api(cls, data: IO_Models.InputCell):
        data_knowledgeObject_reference = []
        if data.knowledgeObject_references is not None:
            data_knowledgeObject_reference = data.knowledgeObject_references

        cell: Cell = cls()
        cell.__knowledgeObject_references = data_knowledgeObject_reference
        cell._text = data.text
        cell._category = data.category

        return cell

class Header:

    def __init__(self):
        self._description: Sentence = None

    @classmethod
    def read_from_api(cls, data) -> Header:
        header = cls()
        header._description = Sentence.read_from_text(data, [])
        return header



########################################################################################################################
########################################################################################################################
########################################################################################################################

class KnowledgeObject:

    def __init__(self):
        self.__id = -999
        self._category: str = ''
        self._labels: List[str] = []

    def save_for_api(self) -> dict:
        res = {}
        res['id'] = self.__id
        res['category'] = self._category
        res['labels'] = self._labels
        return res

    @classmethod
    def read_from_api(cls, data: IO_Models.KnowledgeObject):
        kObj: KnowledgeObject = cls()

        kObj.__id = data.id
        kObj._category = data.category
        kObj._labels = data.labels

        return kObj

    @property
    def id(self) -> int:
        return self.__id

    @property
    def category(self) -> int:
        return self._category

    @property
    def labels(self) -> int:
        return self._labels


########################################################################################################################
########################################################################################################################
########################################################################################################################

class Answer:
    ID_Counter = 1
    def __init__(self, answer, question, context, knowledgeObjects):
        self._id = Answer.ID_Counter
        self._textual_representation: str = answer
        self._context: Context = context
        self._question: Question = question
        self._knowledgeObjects: List[KnowledgeObject] = knowledgeObjects if knowledgeObjects is not None else []
        Answer.ID_Counter += 1

    def save_for_api(self) -> dict:
        return {
            'id': self._id,
            'textual_representation': self._textual_representation,
            'question_id': self._question.get_id(),
            'knowledgeObject_ids': [_.id for _ in self._knowledgeObjects],
            'context_id': self._context.get_id()
        }

    def get_id(self) -> int:
        return self._id

    @staticmethod
    def get_distance(answer_1: Answer, answer_2: Answer) -> int:
        '''
            Calculates the absolute distance between two answers by measuring the distance between the sentences.
            answer_1:
            answer_2:
            :return
            absolute distance between two sentences, so the answer will be a positiv int-value
            between 0 and number of Sentences
        '''

        ###
        # If one of the answers is a table_answer use its mention in the text as the point
        # If there are serveral points use the one, where the distance is smaller
        min_distance: int = 99999
        if isinstance(answer_1, TableAnswer):
            table_answer_1: TableAnswer = answer_1
            table_1_sentences = table_answer_1.context._table.description
            table_1_sentence_positions = [_.get_position_of_sentence() for _ in table_1_sentences]
            if isinstance(answer_2, TableAnswer):
                table_answer_2: TableAnswer = answer_2
                table_2_sentences = table_answer_2.context._table.description
                table_2_sentence_positions = [_.get_position_of_sentence() for _ in table_2_sentences]


                for _position_1 in table_1_sentence_positions:
                    for _position_2 in table_2_sentence_positions:
                        if abs(_position_2 - _position_1) < min_distance:
                            min_distance = abs(_position_2 - _position_1)

            else:
                text_answer_2: TextAnswer = answer_2
                text_2_sentence = text_answer_2.get_sentence()
                text_answer_2_position = text_2_sentence.get_position_of_sentence()

                for _position_1 in table_1_sentence_positions:
                    if abs(text_answer_2_position - _position_1) < min_distance:
                        min_distance = abs(text_answer_2_position - _position_1)
        else:
            text_answer_1 = answer_1
            text_1_sentence = text_answer_1.get_sentence()
            text_answer_1_position = text_1_sentence.get_position_of_sentence()

            if isinstance(answer_2, TableAnswer):
                table_answer_2: TableAnswer = answer_2
                table_2_sentences = table_answer_2.context._table.description
                table_2_sentence_positions = [_.get_position_of_sentence() for _ in table_2_sentences]


                for _position_2 in table_2_sentence_positions:
                    if abs(_position_2 - text_answer_1_position) < min_distance:
                        min_distance = abs(_position_2 - text_answer_1_position)


            else:
                text_answer_2: TextAnswer = answer_2
                text_2_sentence = text_answer_2.get_sentence()
                text_answer_2_position = text_2_sentence.get_position_of_sentence()

                min_distance = abs(text_answer_2_position - text_answer_1_position)


        return min_distance


    @staticmethod
    def intersection(table_answers: List[TableAnswer], text_answers: List[TextAnswer]) -> List[Answer]:

        intersection_of_kObjs, dict_of_kObjs = Answer._intersection_between_kObjs(table_answers, text_answers)
        intersection_of_texts, dict_of_texts = Answer._intersection_between_textual_representations(table_answers, text_answers)

        if len(intersection_of_kObjs) > len(intersection_of_texts):
            return [dict_of_kObjs[_][0] for _ in intersection_of_kObjs]
        else:
            return [dict_of_texts[_][0] for _ in intersection_of_texts]


    @staticmethod
    def _intersection_between_kObjs(table_answers: List[TableAnswer], text_answers: List[TextAnswer]) -> List[Answer]:
        table_results_as_kObj = []
        dict_of_knowledgeObjects_to_answers = {}
        for _ in table_answers:
            table_results_as_kObj.extend(_.get_knowledgeObjects())

            # Make a Backup of the kObjs in the TableAnswers
            for kObj in _.get_knowledgeObjects():
                if kObj in dict_of_knowledgeObjects_to_answers:
                    dict_of_knowledgeObjects_to_answers[kObj].append(_)
                else:
                    dict_of_knowledgeObjects_to_answers[kObj] = [_]

        text_results_as_knowledgeObject = []
        for _ in text_answers:
            text_results_as_knowledgeObject.extend(_.get_knowledgeObjects())

            for kObj in _.get_knowledgeObjects():
                if kObj in dict_of_knowledgeObjects_to_answers:
                    dict_of_knowledgeObjects_to_answers[kObj].append(_)
                else:
                    dict_of_knowledgeObjects_to_answers[kObj] = [_]

        intersection_of_kObjs = set(text_results_as_knowledgeObject).intersection(set(table_results_as_kObj))
        return intersection_of_kObjs, dict_of_knowledgeObjects_to_answers


    @staticmethod
    def _intersection_between_textual_representations(table_answers: List[TableAnswer], text_answers: List[TextAnswer]) -> List[Answer]:
        table_results_as_text = []
        dict_of_textual_representations_to_answers = {}
        for _ in table_answers:
            table_results_as_text.append(_.textual_representation)

            # Make a Backup of the kObjs in the TableAnswers
            if _.textual_representation in dict_of_textual_representations_to_answers:
                dict_of_textual_representations_to_answers[_.textual_representation].append(_)
            else:
                dict_of_textual_representations_to_answers[_.textual_representation] = [_]

        text_results_as_text = []
        for _ in text_answers:
            text_results_as_text.append(_.textual_representation)
            if _.textual_representation in dict_of_textual_representations_to_answers:
                dict_of_textual_representations_to_answers[_.textual_representation].append(_)
            else:
                dict_of_textual_representations_to_answers[_.textual_representation] = [_]

        intersection_of_text = set(text_results_as_text).intersection(set(table_results_as_text))
        return intersection_of_text, dict_of_textual_representations_to_answers


    def get_categories_in_answer(self) -> List[str]:
        return [_._category for _ in self._knowledgeObjects]

    def _delete_following_zeros(self, words) -> str:
        '''
        Identifies Numbers in Answer-String and deletes following zeros
        E.g.
        0.80 GPa -> 0.8 GPa
        :param answer: String
        :return:
        '''

        regex = "0+$"
        regex_for_finding_following_zeros = "(\.|,)\d0+$"

        answerList = []
        for word in words:
            if re.search(regex_for_finding_following_zeros, word):
                answerList.append(re.sub(regex, "", word))
            else:
                answerList.append(word)
        return " ".join(answerList)


    def is_part_of(self, other_answer: Answer) -> bool:
        # If one Answer is part of the other answer it is the same answer
        try:
            if re.search(self._textual_representation.lower(), other_answer._textual_representation.lower()):
                return True
            elif re.search(other_answer._textual_representation.lower(), self._textual_representation.lower()):
                return True
        except re.error:
            if self._textual_representation.lower() == other_answer._textual_representation.lower():
                return True
        return False

    def get_knowledgeObjects(self) -> List[KnowledgeObject]:
        if self._knowledgeObjects is None:
            return []
        return self._knowledgeObjects

    @property
    def textual_representation(self) -> str:
        return self._textual_representation

    @textual_representation.setter
    def textual_representation(self, value: str):
        self._textual_representation = value


    @property
    def context(self) -> Context:
        return self._context

    @context.setter
    def chapters(self, value: Context):
        self._context = value

    @property
    def question(self) -> Question:
        return self._question

    @question.setter
    def question(self, value: Question):
        self._question = value

class TableAnswer(Answer):

    def __init__(self, answer, question, context: TableContext):
        if answer == []:
            textual_answer = ''
            knowledgeObjects = []
            cell = None
        else:
            cell = context.get_cell_at(answer)
            knowledgeObjects = cell.get_knowledgeObjects()
            textual_answer = cell.get_text()
        question = Question(question)
        print('Answer:', textual_answer)
        print('Position:', answer)
        self._positon: Tuple[int, int] = answer
        self._cell: Cell = cell
        super().__init__(textual_answer, question, context, knowledgeObjects)

    def save_for_api(self):
        data = super().save_for_api()
        data['answer_source'] = 'TABLE-QA'
        return data

    def normalized_form(self):

        words = self._textual_representation.lower().split(' ')
        return re.sub("( +|-|\+|_)", "", self._delete_following_zeros(words))

class TextAnswer(Answer):

    def __init__(self, answer, start_pos, end_pos, question, context: TextContext, score):
        knowledgeObjects = context.get_knowledgeObjects_at(start_pos, end_pos)
        self.words: List[Word] = context.get_words_at(start_pos, end_pos)
        self._start_pos: int = start_pos
        self._end_pos: int = end_pos
        super().__init__(answer, question, context, knowledgeObjects)

    def get_sentence(self) -> int:
        return self._context.get_sentence_for_words(self.words)

    def normalized_form(self):

        if self.words is not None:
            words = [word.normalized_form for word in self.words]
            return re.sub("( +|-|\+|_)", "", self._delete_following_zeros(words))
        else:
            print("OK Error in normalized Form Datamodels  954. Evtl. re.escape")
            return 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'

    def save_for_api(self):
        data = super().save_for_api()
        data['answer_source'] = 'TEXT-QA'
        return data

class Question:
    ID_COUNTER = 1
    def __init__(self, question: str):
        self._id: int = Question.ID_COUNTER
        self._question: str = question
        Question.ID_COUNTER += 1

    def save_for_api(self) -> dict:
        return {
            'id': self.get_id(),
            'question': self._question
        }

    def get_id(self) -> int:
        return self._id

    def get_question(self) -> str:
        return self._question





class Context:
    ID_Counter = 1
    def __init__(self):
        self.__id = Context.ID_Counter
        Context.ID_Counter += 1

    def _save_for_api(self) -> dict:
        return {
            'id': self.get_id()
        }


    def get_id(self) -> int:
        return self.__id



class TableContext(Context):

    def __init__(self, table: Table):
        super().__init__()
        self._table: Table = table
        self._textual_representation: str = " ".join([_.get_form('normal') for _ in table._textual_representation])
        self._knowledgeObjects: List[KnowledgeObject] = self.get_knowledgeObjects()

    def save_for_api(self) -> dict:
        res = super()._save_for_api()
        res['table'] = self._table.get_table_name()
        res['textual_representation'] = self._textual_representation
        res['knowledgeObject_ids'] =  [_.id for _ in self._knowledgeObjects]
        return res



    @classmethod
    def copy(cls, context: TableContext) -> TableContext:
        copy = cls(context._table)
        copy._textual_representation = context._textual_representation

        return copy
    def get_cell_at(self, cell_coordinates):
        return self._table.get_cell_at(cell_coordinates)

    def as_pandas_df(self):
        return self._table.as_pandas_df()

    @property
    def text(self) -> str:
        return self._textual_representation

    def get_knowledgeObjects(self) -> List[KnowledgeObject]:
        kObjs = self._table.get_knowledgeObjects()
        if kObjs is None:
            kObjs = []
        return kObjs

    def get_textual_representation(self, kObj: KnowledgeObject) -> str:
        for sentence in self._table._textual_representation:
            text: str = sentence.find_textual_representation(kObj)
            if text != '':
                return text
        return ''

class TextContext(Context):

    def __init__(self, sentences: List[Sentence], textual_representation: str, context_format='normal'):
        super().__init__()
        self._sentences: List[Sentence] = sentences
        self._textual_representation: str = textual_representation
        self._context_format: str = context_format
        self._knowledgeObjects: List[KnowledgeObject] = self.__set_knowledgeObjects()

    def save_for_api(self) -> dict:
        res = super()._save_for_api()
        res['textual_representation'] = self._textual_representation
        res['knowledgeObject_ids'] = [_.id for _ in self._knowledgeObjects]
        return res



    def get_knowledgeObjects(self) -> List[KnowledgeObject]:
        kObjs = self._knowledgeObjects
        if kObjs is None:
            kObjs = []
        return kObjs

    def __set_knowledgeObjects(self) -> List[KnowledgeObject]:
        kObjs: List[KnowledgeObject] = []
        for sentence in self._sentences:
            kObjs.extend(sentence.knowledgeObjects)
        return kObjs

    def get_sentence_for_words(self, words: List[Word]) -> Sentence:
        first_word_position = words[0].id
        for sentence in self._sentences:
            sentence_beginning: int = sentence.words[0].id
            sentence_ending: int = sentence.words[-1].id
            if sentence_beginning <= first_word_position <= sentence_ending:
                return sentence

    def get_knowledgeObjects_at(self, start_pos: int, end_pos: int):
        start_pos_sentence = 0
        end_pos_sentence = 0
        for sentence in self._sentences:
            end_pos_sentence = start_pos_sentence + len(sentence.get_form(self._context_format))
            if start_pos_sentence <= start_pos and end_pos <= end_pos_sentence:
                start = start_pos - start_pos_sentence
                end = end_pos - start_pos_sentence
                return sentence.get_knowledgeObjects_at(start, end, self._context_format)
            start_pos_sentence = end_pos_sentence + 1

    def get_words_at(self, start_pos: int, end_pos: int):
        start_pos_sentence = 0
        end_pos_sentence = 0
        for sentence in self._sentences:
            end_pos_sentence = start_pos_sentence + len(sentence.get_form(self._context_format))
            if start_pos_sentence <= start_pos and end_pos <= end_pos_sentence:
                start = start_pos - start_pos_sentence
                end = end_pos - start_pos_sentence
                return sentence.get_words_at(start, end, self._context_format)
            start_pos_sentence = end_pos_sentence + 1

    @property
    def text(self) -> str:
        return self._textual_representation

    def get_textual_representation(self, kObj: KnowledgeObject) -> str:
        for sentence in self._sentences:
            text: str = sentence.find_textual_representation(kObj)
            if text != '':
                return text
        return ''
