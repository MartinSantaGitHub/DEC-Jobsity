from sqlalchemy import Table, inspect, Column, Integer, MetaData, String, Float, DateTime
from sqlalchemy.sql.ddl import CreateSchema
from business.baseDB import BaseDB


class DatabaseDDL(BaseDB):
    def __init__(self, db_conn, schema: str = 'public'):
        super().__init__(db_conn, schema)
        self.__create_schema()

    def __create_schema(self):
        engine = self.db_conn.engine

        if not engine.dialect.has_schema(engine, self.schema):
            engine.execute(CreateSchema(self.schema))

    def __create_table(self, table: Table) -> tuple:
        insp = inspect(self.db_conn.engine)
        table_name = table.name

        if not insp.has_table(table_name, schema=self.schema):
            table.metadata.create_all(self.db_conn.engine)
        else:
            return False, f'Table {table_name} already exists.'

        return True, f'Table {table_name} was created successfully.'

    def create_region_table(self) -> tuple:
        region_table = Table(
            'region', MetaData(schema=self.schema),
            Column('id', Integer, primary_key=True),
            Column('description', String)
        )

        return self.__create_table(table=region_table)

    def create_datasource_table(self) -> tuple:
        datasource_table = Table(
            'datasource', MetaData(schema=self.schema),
            Column('id', Integer, primary_key=True),
            Column('description', String)
        )

        return self.__create_table(table=datasource_table)

    def create_coord_table(self) -> tuple:
        coord_table = Table(
            'coord', MetaData(schema=self.schema),
            Column('id', Integer, primary_key=True),
            Column('x', Float),
            Column('y', Float)
        )

        return self.__create_table(table=coord_table)

    def create_time_range_table(self) -> tuple:
        time_range_table = Table(
            'time_range', MetaData(schema=self.schema),
            Column('id', Integer, primary_key=True),
            Column('range', String),
            Column('time_from', Integer),
            Column('time_to', Integer)
        )

        return self.__create_table(table=time_range_table)

    def create_coord_time_table(self) -> tuple:
        coord_time_table = Table(
            'coord_time', MetaData(schema=self.schema),
            Column('id', Integer, primary_key=True),
            Column('origin_coord_id', Integer),
            Column('dest_coord_id', Integer),
            Column('time_range_id', Integer)
        )

        return self.__create_table(table=coord_time_table)

    def create_trip_table(self) -> tuple:
        trip_table = Table(
            'trip', MetaData(schema=self.schema),
            Column('region_id', Integer),
            Column('coord_time_id', Integer),
            Column('datasource_id', Integer),
            Column('datetime', DateTime)
        )

        return self.__create_table(table=trip_table)
