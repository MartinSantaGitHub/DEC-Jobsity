import os

import uvicorn
from fastapi.params import File
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

db_conn = DatabaseConnection(DB_DRIVER, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME)
database_dml = DatabaseDML(db_conn, DB_SCHEMA)
process_manager = ProcessManager(database_dml=database_dml, files_folder=FILES_FOLDER,
                                 percent_update_rate=PERCENT_UPDATE_RATE)
router = APIRouter()

router.mount("/static", StaticFiles(directory="static"), name="static")
router.mount("/scripts", StaticFiles(directory="scripts"), name="scripts")

templates = Jinja2Templates(directory="templates")

current_file = None
percent = 0
new_data = False
is_finished = False


def update_status(filename, n):
    global current_file
    global percent
    global new_data

    current_file = filename
    percent = n
    new_data = True


def update_is_finished(finished):
    global is_finished

    is_finished = finished


async def status_event_generator(request):
    global new_data

    process_manager.add_subscribers_for_status_update_event(update_status)
    process_manager.add_subscribers_for_is_finished_update_event(update_is_finished)

    while True:
        if await request.is_disconnected():
            break

        if new_data:
            yield {
                "event": "update",
                "data": {'filename': current_file, 'percent': percent}
            }

        new_data = False

        if is_finished:
            process_manager.remove_subscribers_for_status_update_event(update_status)
            process_manager.remove_subscribers_for_is_finished_update_event(update_is_finished)

            break


@router.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.post("/uploadfiles")
async def upload_files(files: list[UploadFile] = File(None)):
    return process_manager.start(files)


@router.get('/status')
async def run_status(request: Request):
    event_generator = status_event_generator(request)

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
