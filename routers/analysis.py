from fastapi import Response, APIRouter, File, UploadFile, BackgroundTasks, Request, Form, HTTPException
from starlette.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_404_NOT_FOUND, HTTP_200_OK

from core.Datamodels.IO_Models import InputData
from core.task_api.tasks import TaskBuilder, TaskStatus
from core.schemas import LogFile, AnswerDocumentList, HypothesisList
router = APIRouter()


# The APIs necessary for the tasks

taskBuilderAPI: TaskBuilder = TaskBuilder()
finished_tasks_database = dict()


def get_state(document_id: str):
    """ Gets the state of the document. If the document is ready for the response to the Requester the state finished
    will be called."""
    if document_id in finished_tasks_database:
        return 'finished'
    else:
        return 'working'


def get_results(document_id: str):
    """ Returns the results of the document as the outputmodel (document). """
    data: LogFile = finished_tasks_database[document_id].data
    data.document_id = document_id
    return data



@router.get('/annotation/get_full_logs/', response_model=LogFile, status_code=HTTP_200_OK)
def get_task_extraction(document_id: str):
    """ An API to get the extraction of the task. """
    state: str = get_state(document_id)
    if state == 'finished':
        res: LogFile = get_results(document_id)
        return res
    else:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND,
                            detail="Document not ready or not found")

@router.get('/annotation/get_hypothesis/', response_model=HypothesisList, status_code=HTTP_200_OK)
def get_task_extraction(document_id: str):
    """ An API to get the extraction of the task. """
    state: str = get_state(document_id)
    if state == 'finished':
        log: LogFile = get_results(document_id)
        res: HypothesisList = HypothesisList(**log.dict())
        return res
    else:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND,
                            detail="Document not ready or not found")


@router.get('/annotation/answer_documents/', response_model=AnswerDocumentList, status_code=HTTP_200_OK)
def get_task_extraction(document_id: str):
    """ An API to get the extraction of the task. """
    state: str = get_state(document_id)
    if state == 'finished':
        log: LogFile = get_results(document_id)
        res: AnswerDocumentList = AnswerDocumentList(**log.dict())
        return res
    else:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND,
                            detail="Document not ready or not found")

@router.get('/analysis/has_results/')
def has_extraction(document_id: str, response: Response):
    """ An API to get the extraction of the task. """
    state = get_state(document_id)
    if state == 'finished':
        response.status_code = HTTP_201_CREATED
    else:
        response.status_code = HTTP_204_NO_CONTENT
    return {}


@router.post('/api/contextualize_data', response_model=TaskStatus, status_code=HTTP_201_CREATED)
def extract_annotations(request: Request,
                        background_tasks: BackgroundTasks,
                        document: InputData
                        ):
    """ An API that extracts Information from a single PDF-Document. """

    _job = dict(
        status='pending',
        document_id=document.document_id
    )
    background_tasks.add_task(asy_bg_annotate, request, document)
    return _job




async def asy_bg_annotate(request, document: InputData):
    task = await taskBuilderAPI.asy_create_task(task='annotate',
                                                client=request.client.host,
                                                document=document)

    taskBuilderAPI.perform_task(task)
    finished_tasks_database.update({
        document.document_id: task
    })


def bg_transform_pdf_to_data(request, document_id, file):
    task = taskBuilderAPI.create_task(task='annotate',
                                      client=request.client.host,
                                      document_id=document_id,
                                      file=file)

    taskBuilderAPI.perform_task(task)
    finished_tasks_database.update({
        document_id: task
    })
