import os
import uvicorn
from datetime import datetime
from threading import Semaphore
from fastapi.params import File, Query
from sse_starlette.sse import EventSourceResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from fastapi import APIRouter, Response, status, UploadFile, Request
from utils.connection import DatabaseConnection
from business.databaseDML import DatabaseDML
from business.process import ProcessManager

load_dotenv()

DB_DRIVER = os.environ["DB_DRIVER"]
DB_NAME = os.environ["DB_NAME"]
DB_USER = os.environ["DB_USER"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_HOST = os.environ["DB_HOST"]
DB_PORT = os.environ["DB_PORT"]
DB_SCHEMA = os.environ["DB_SCHEMA"]
FILES_FOLDER = os.environ["FILES_FOLDER"]
PERCENT_UPDATE_RATE = int(os.environ["PERCENT_UPDATE_RATE"])


def update_status(filename, n, user_id: float):
    current_user = router.users[user_id]

    current_user['current_file'] = filename
    current_user['percent'] = n
    current_user['new_data'] = True


def update_is_finished(is_finished, user_id: float):
    router.users[user_id]['is_finished'] = is_finished


db_conn = DatabaseConnection(DB_DRIVER, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME)
database_dml = DatabaseDML(db_conn, DB_SCHEMA)
process_manager = ProcessManager(database_dml=database_dml, files_folder=FILES_FOLDER,
                                 percent_update_rate=PERCENT_UPDATE_RATE)

process_manager.add_subscribers_for_status_update_event(update_status)
process_manager.add_subscribers_for_is_finished_update_event(update_is_finished)

semaphore = Semaphore(value=1)
router = APIRouter()

router.mount("/static", StaticFiles(directory="static"), name="static")
router.mount("/scripts", StaticFiles(directory="scripts"), name="scripts")

templates = Jinja2Templates(directory="templates")
router.users = {}


async def status_event_generator(request, user_id: float):
    current_user = router.users[user_id]

    while True:
        if await request.is_disconnected():
            del current_user
            break

        if current_user['new_data']:
            current_user['new_data'] = False

            yield {
                "event": "update",
                "data": {'filename': current_user['current_file'], 'percent': current_user['percent']}
            }

        if current_user['is_finished']:
            del current_user
            break


def get_id():
    with semaphore:
        user_id = datetime.now().timestamp()
        router.users[user_id] = {
            'current_file': None,
            'router.percent': 0,
            'router.new_data': False,
            'router.is_finished': False
        }

        return user_id


@router.get("/")
async def home(request: Request):
    user_id = get_id()

    return templates.TemplateResponse("index.html", {"request": request, "user_id": user_id})


@router.post("/uploadfiles/")
async def upload_files(files: list[UploadFile] = File(None), user_id: float = Query(...)):
    return await process_manager.start(files, user_id)


@router.get('/status/')
async def run_status(request: Request, user_id: float = Query(...)):
    event_generator = status_event_generator(request, user_id)

    return EventSourceResponse(event_generator)


@router.get("/weekly_average_trips_by_region")
async def get_weekly_average_trips_by_region(response: Response):
    result = database_dml.get_weekly_avg_of_trips_by_region()
    json_result = None

    if result[1] == 0:
        result_list = []
        df = result[0]

        df.apply(lambda row: result_list.append({'region': row['region'], 'weekly_avg_trips': row['weekly_avg_trips']}),
                 axis=1)

        json_result = {"message": "", "data": result_list}
    else:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        json_result = {"message": "There was an error obtaining the results"}

    return json_result


@router.post("/get_weekly_average_trips_by_bounding_box")
async def get_weekly_average_trips_by_bounding_box(request: Request, response: Response):
    params = await request.json()
    result = database_dml.get_weekly_average_trips_by_bounding_box(params['x_a'], params['y_a'], params['x_b'],
                                                                   params['y_b'])
    json_result = None

    if result[1] == 0:
        df = result[0]
        # I had to cast the result to String because of a strange error when the result was return
        # to the client (Exception in ASGI application - 'numpy.int64' object is not iterable)
        json_result = {"message": "", "data": str(df['weekly_avg_trips_bb'][0])}
    else:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        json_result = {"message": "There was an error obtaining the results"}

    return json_result


# This is only for debbuging purposes
if __name__ == "__main__":
    uvicorn.run("services:router", host="0.0.0.0", port=8000)
