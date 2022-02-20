import os
from dotenv import load_dotenv
from fastapi import FastAPI, Response, status
from utils.connection import DatabaseConnection
from business.databaseDML import DatabaseDML

app = FastAPI()

load_dotenv()

DB_DRIVER = os.environ["DB_DRIVER"]
DB_NAME = os.environ["DB_NAME"]
DB_USER = os.environ["DB_USER"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_HOST = os.environ["DB_HOST"]
DB_PORT = os.environ["DB_PORT"]
DB_SCHEMA = os.environ["DB_SCHEMA"]

db_conn = DatabaseConnection(DB_DRIVER, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME)
database_dml = DatabaseDML(db_conn, DB_SCHEMA)


@app.get("/weekly_average_trips")
async def get_weekly_average_of_trips(response: Response):
    result = database_dml.get_weekly_number_of_trips()
    json_result = None

    if result[1] == 0:
        result_list = []
        df = result[0]

        df.apply(lambda row: result_list.append({'Region': row['region'], 'weekly_avg_trips': row['weekly_avg_trips']}), axis=1)

        json_result = result_list
    else:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        json_result = {"message": "There was an error obtaining the results"}

    return json_result
