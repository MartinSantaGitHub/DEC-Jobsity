import pandas as pd
import sqlalchemy
import psycopg2
from sqlalchemy import create_engine
from sqlalchemy.engine import CursorResult
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from typing import Union


class DatabaseConnection:

    def __init__(self, driver: str, username: str, password: str, host: str, port: Union[int, str], name: str):
        self.driver = driver
        self.username = username
        self.password = password
        self.host = host
        self.port = port
        self.name = name
        self.db_path = self.__set_database()
        self.engine = self.__set_engine()

    def __set_database(self):
        return '{}://{}:{}@{}:{}/{}'.format(self.driver, self.username, self.password, self.host, self.port, self.name)

    def __set_engine(self):
        return create_engine(self.db_path, pool_size=20, max_overflow=0)

    def execute(self, sql_query: str, params: dict = None) -> CursorResult:
        sql_query = text(sql_query)

        with self.engine.connect() as conn:
            with Session(bind=conn) as session:
                result = session.execute(statement=sql_query, params=params)

                session.commit()

        return result

    def import_data_frame_to_database(self, data: pd.DataFrame, table_name: str,
                                      if_exists: str = 'fail', schema: str = 'public') -> None:
        if not data.empty:
            data.to_sql(name=table_name, con=self.engine, index=False, if_exists=if_exists, schema=schema)

    def export_data_to_data_frame(self, sql_query: str, params: dict = None) -> tuple:
        """
        :param sql_query: The sql query must refer to the schema of the database prior to the name of the tables
        :param params: These are the params that are sent when we build a sql parameterized query.
        """

        ret_code = 0
        message = None
        df = None

        try:
            sql_query = text(sql_query)
            df = pd.read_sql(sql_query, con=self.engine, params=params)

        except sqlalchemy.exc.ProgrammingError as ex:

            if type(ex.orig) == psycopg2.errors.InsufficientPrivilege:
                message = f'Permission denied.'
                ret_code = -1

        return df, ret_code, message
