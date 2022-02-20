import os
import pandas as pd
from dotenv import load_dotenv
from utils.connection import DatabaseConnection
from business.databaseDDL import DatabaseDDL


def populate_bound_list(bound_list: list, initial_value: int = 0):
    bound_list.append(initial_value)

    for i in range(47):
        if i % 2 == 0:
            initial_value += 30
        else:
            initial_value += 70

        bound_list.append(initial_value)


load_dotenv()

DB_DRIVER = os.environ["DB_DRIVER"]
DB_NAME = os.environ["DB_NAME"]
DB_USER = os.environ["DB_USER"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_HOST = os.environ["DB_HOST"]
DB_PORT = os.environ["DB_PORT"]
DB_SCHEMA = os.environ["DB_SCHEMA"]
db_conn = DatabaseConnection(DB_DRIVER, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME)
database_ddl = DatabaseDDL(db_conn, DB_SCHEMA)

# Create tables
print(database_ddl.create_region_table()[1])
print(database_ddl.create_datasource_table()[1])
print(database_ddl.create_coord_table()[1])
print(database_ddl.create_coord_time_table()[1])
print(database_ddl.create_trip_table()[1])

# Create and populate 'time_range' table
time_range_result = database_ddl.create_time_range_table()

print(time_range_result[1])

if time_range_result[0]:
    from_list = []
    to_list = []

    populate_bound_list(from_list)
    populate_bound_list(to_list, initial_value=29)

    data = {'range': ['0000-0029', '0030-0059', '0100-0129', '0130-0159', '0200-0229', '0230-0259', '0300-0329',
                      '0330-0359', '0400-0429', '0430-0459', '0500-0529', '0530-0559', '0600-0629', '0630-0659',
                      '0700-0729', '0730-0759', '0800-0829', '0830-0859', '0900-0929', '0930-0959', '1000-1029',
                      '1030-1059', '1100-1129', '1130-1159', '1200-1229', '1230-1259', '1300-1329', '1330-1359',
                      '1400-1429', '1430-1459', '1500-1529', '1530-1559', '1600-1629', '1630-1659', '1700-1729',
                      '1730-1759', '1800-1829', '1830-1859', '1900-1929', '1930-1959', '2000-2029', '2030-2059',
                      '2100-2129', '2130-2159', '2200-2229', '2230-2259', '2300-2329', '2330-2359'],
            'time_from': from_list,
            'time_to': to_list}

    time_range_df = pd.DataFrame(data)

    db_conn.import_data_frame_to_database(data=time_range_df,
                                          table_name='time_range',
                                          if_exists='append',
                                          schema=DB_SCHEMA)

    print("The table 'time_range' has been populated")
