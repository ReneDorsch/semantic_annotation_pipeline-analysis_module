from __future__ import annotations

from collections import defaultdict
from typing import List, Dict, Tuple
from core.Datamodels.Answer_Document import _AnswerDocument

class AnswerDocumentArchive(dict):
    '''
    A AnswerDocumentArchive is a Archive to save the AnswerDocuments, found in every action step.
    Every Action Step is defined by the id the Answer Document has, combined with the type of ...
    '''
    def __init__(self):
        self.data = defaultdict(list)
        pass

    def get_answered_answerDocuments(self) -> List[_AnswerDocument]:
        return self.data

    def answerDoc_was_send(self, questionTemplate: QuestionTemplate) -> bool:
        for qt_list in self.data.values():
            for _, answerDoc in qt_list:
                try:
                    if answerDoc.questionTemplate is questionTemplate:
                        return True
                except:
                    print("ok")
        return False


    def save(self, data: Tuple[str, _AnswerDocument]):
        answerdocument = data[1]
        self.data[answerdocument.type].append(data)

    def save_as_json(self) -> dict:
        return {}