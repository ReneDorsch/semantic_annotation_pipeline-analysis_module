from __future__ import annotations
from core.Datamodels import IO_Models
from core.Datamodels.Datamodels import KnowledgeObject, Text, Table, Abstract, Sentence
from typing import List
import re
from functools import lru_cache
class TopologicalMap:

    def __init__(self):
        self._text: Text = None
        self._knowledgeObjects: List[KnowledgeObject] = []
        self._abstract: Abstract = None
        self._tables: List[Table] = []
        self._sentences: List[Sentence] = []

    def _get_tables_representation(self):
        tables = {}
        for table in self._tables:
            if table.description == []:
                describing_sentences = []
                sentences = self._get_sentences()
                for sentence in sentences:
                    if re.search(table.get_table_name().lower(), sentence.get_form('normal').lower()):
                        describing_sentences.append(sentence)
                table.description = list(set(describing_sentences))
            sentences = table.description
            sentences.extend(table.get_textual_representation())

            tables[table] = sentences


        return tables

    @lru_cache(maxsize=1000)
    def get_tables_for_regex(self, regex: str) -> List[Table]:
        tables = self._get_tables_representation()
        res: List[Sentence] = []

        for table, sentences in tables.items():
            for sentence in sentences:
                if re.search(regex.lower(), sentence.get_form('normal').lower()):
                    res.append(table)
                    break

        return res

    @lru_cache(maxsize=1000)
    def get_tables_for_category(self, category: str) -> List[Table]:
        tables: List[Table] = self._tables
        res: List[Sentence] = []


        for table in tables:
            table_categories = set([_.category for _ in table.get_knowledgeObjects()])
            if category in table_categories:
                res.append(table)
                continue

        deprecated = """
        for table, sentences in tables.items():
            for sentence in sentences:
                categories_of_kObjs = [kObj.category for kObj in sentence.knowledgeObjects]
                if category in categories_of_kObjs:
                    res.append(table)
                    break
        """
        return res


    def _get_sentences(self):
        if self._sentences == []:
            for chapter in self._text.chapters:
                for paragraph in chapter.get_paragraphs():
                    self._sentences.extend(paragraph.get_sentences())
            if self._abstract is not None:
                for paragraph in self._abstract.get_paragraphs():
                    self._sentences.extend(paragraph.get_sentences())

        return self._sentences

    @lru_cache(maxsize=1000)
    def get_sentences_for_regex(self, regex: str) -> List[Sentence]:
        sentences = self._get_sentences()
        res: List[Sentence] = []
        for sentence in sentences:
            if re.search(regex.lower(), sentence.get_form('normal').lower()):
                res.append(sentence)
        return res

    @lru_cache(maxsize=1000)
    def get_sentences_for_category(self, category: str) -> List[Sentence]:
        sentences = self._get_sentences()
        res: List[Sentence] = []
        for sentence in sentences:
            categories_of_kObjs = [kObj.category for kObj in sentence.knowledgeObjects]
            if category in categories_of_kObjs:
                res.append(sentence)
        return res


    def get_kObjs_in_abstract(self):
        kObjs = []
        if self._abstract is not None:
            kObjs = self._abstract.knowledgeObjects
        return kObjs

    def get_kObjs_in_summary(self):
        kObjs = []
        if self._text is not None:
            if self._text.chapters != []:
                for chapter in self._text.chapters[-2:]:
                    kObjs.extend(chapter.knowledgeObjects)
        return kObjs

    def getTopNknowledgeObjects(self, n: int):
        kObjs = {}
        for sentence in self._sentences:
            for kObj in sentence.knowledgeObjects:
                if kObj not in kObjs:
                    kObjs[kObj] = 1
                else:
                    kObjs[kObj] += 1
        kObjList = [(kObj, frequency) for kObj, frequency in kObjs.items()]
        kObjList.sort(key=lambda x: x[1], reverse=True)
        return [kObj for kObj, _ in kObjList[:n]]

    def get_kObjs_in_goal_description(self):
        kObjs = []
        if self._text is not None:
            if self._text.chapters != []:
                intoduction_chapter = self._text.chapters[1]
                if intoduction_chapter.get_paragraphs() != []:
                    for paragraph in intoduction_chapter.get_paragraphs()[-3:]:
                        kObjs.extend(paragraph.knowledgeObjects)
        return kObjs

    @property
    def text(self) -> Text:
        return self._text

    @text.setter
    def text(self, value: Text):
        self._text = value

    @property
    def knowledgeObjects(self) -> KnowledgeObject:
        return self._knowledgeObjects

    @text.setter
    def knowledgeObjects(self, value: List[KnowledgeObject]):
        self._knowledgeObjects = value

    @property
    def abstract(self) -> Abstract:
        return self._abstract

    @text.setter
    def abstract(self, value: Abstract):
        self._abstract = value

    @property
    def tables(self) -> List[Table]:
        return self._tables

    @text.setter
    def tables(self, value: List[Table]):
        self._tables = value


    @classmethod
    def read_from_api(cls, data: IO_Models.InputData) -> TopologicalMap:
        # Transform the Input Data in to Objects
        text_data: Text = None
        knowledgeObjects: List[KnowledgeObject] = []
        abstract_data: Abstract = None
        tables: List[Table] = []

        knowledgeObjects: List[KnowledgeObject] = [KnowledgeObject.read_from_api(kObj) for kObj in data.knowledgeObjects]
        text_data: Text = Text.read_from_api(data.chapters)
        text_data.knowledgeObjects = knowledgeObjects

        text_data.update_sentences()

        if data.abstract is not None:
            abstract_data: Abstract = Abstract.read_from_api(data.abstract)
            abstract_data.set_knowledgeObjects(knowledgeObjects)
            abstract_data.update_sentences()
        if data.tables is not None:
            tables: List[Table] = [Table.read_from_api(table) for table in data.tables]
            [table.set_knowledgeObjects(knowledgeObjects) for table in tables]



        # Create the Topological Map
        topological_map = cls()

        # Update the Topological Map with the data from the api
        topological_map.text = text_data
        topological_map.knowledgeObjects = knowledgeObjects
        topological_map.abstract = abstract_data
        topological_map.tables = tables

        return topological_map



