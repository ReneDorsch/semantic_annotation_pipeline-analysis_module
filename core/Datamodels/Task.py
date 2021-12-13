import os
from core.Datamodels import IO_Models


class Task:

    def __init__(self, path_to_document, path_to_log, data: IO_Models.InputData, task: str, requester, request_id):
        self.path = path_to_document
        self.data = data
        self.logging_path = path_to_log
        self.task = task
        self.requester = requester
        self.is_break_order: bool = False
        self.request_id: str = request_id

    def get_data(self) -> IO_Models.InputData:
        return self.data

    def get_task(self) -> str:
        return self.task

    def stop_worker(self) -> None:
        self.is_break_order = True

    def is_break(self) -> bool:
        return self.is_break_order

    def get_path(self) -> str:
        return self.path

    def get_logging_path(self) -> str:
        return self.logging_path

    def __del__(self):
        if os.path.exists(self.path):
            os.remove(self.path)


    def get_document_id(self) -> str:
        return self.request_id