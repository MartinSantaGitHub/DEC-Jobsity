import os
from dotenv import load_dotenv
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

db_conn = DatabaseConnection(DB_DRIVER, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME)
database_dml = DatabaseDML(db_conn, DB_SCHEMA)
process_manager = ProcessManager(database_dml=database_dml, files_folder=FILES_FOLDER)
result = process_manager.start()

print(result)
