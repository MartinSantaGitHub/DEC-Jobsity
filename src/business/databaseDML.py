import pandas as pd
from business.baseDB import BaseDB


class DatabaseDML(BaseDB):

    def __init__(self, db_conn, schema: str = 'public'):
        super().__init__(db_conn, schema)

    def __insert_new_data(self, data_new_df: pd.DataFrame, data_base_df: pd.DataFrame, table_name: str) -> pd.DataFrame:
        data_new_df.query('_merge == "left_only"', inplace=True)
        data_new_df.drop('_merge', axis=1, inplace=True)

        static_all_df = data_base_df

        if not data_new_df.empty:
            data_new_df.reset_index(drop=True, inplace=True)

            next_id = data_base_df['id'].max() + 1 if len(data_base_df.index) else 1
            data_new_df['id'] = data_new_df.index + next_id
            static_all_df = pd.concat([data_base_df, data_new_df])

            static_all_df.reset_index(drop=True, inplace=True)

            self.db_conn.import_data_frame_to_database(data=data_new_df,
                                                       table_name=table_name,
                                                       if_exists='append',
                                                       schema=self.schema)

        return static_all_df

    def __get_static_data_from_source(self, source_df: pd.DataFrame, table_name: str, data_source_field_name: str = None) -> pd.DataFrame:
        field_name = table_name if data_source_field_name is None else data_source_field_name
        source_copy_df = source_df.copy()
        source_copy_df = source_copy_df[source_copy_df[field_name].notna()]
        source_copy_df['description'] = source_copy_df[field_name].apply(lambda x: x.strip())

        source_copy_df.drop_duplicates(subset=['description'], inplace=True, ignore_index=True)

        return source_copy_df[['description']]

    def __insert_into_static_table(self, source_df: pd.DataFrame, table_name: str, data_source_field_name: str = None) -> pd.DataFrame:
        static_query = f'''SELECT id, description
                           FROM {self.schema}.{table_name}'''
        static_base_df = self.db_conn.export_data_to_data_frame(sql_query=static_query)[0]
        source_copy_df = self.__get_static_data_from_source(source_df, table_name, data_source_field_name)

        source_copy_df.reset_index(drop=True, inplace=True)

        source_copy_df['id'] = source_copy_df.index + 1
        static_new_df = pd.merge(source_copy_df['description'],
                                 static_base_df['description'],
                                 how='outer',
                                 indicator=True)

        return self.__insert_new_data(data_new_df=static_new_df, data_base_df=static_base_df, table_name=table_name)

    def __insert_into_coord_table(self, source_df: pd.DataFrame, table_name: str) -> pd.DataFrame:
        static_query = f'''SELECT id, x, y
                           FROM {self.schema}.{table_name}'''
        static_base_df = self.db_conn.export_data_to_data_frame(sql_query=static_query)[0]
        origin_df = source_df[['origin_x', 'origin_y']]
        destination_df = source_df[['destination_x', 'destination_y']]

        origin_df.set_axis(['x', 'y'], axis=1, inplace=True)
        destination_df.set_axis(['x', 'y'], axis=1, inplace=True)

        coord_df = pd.concat([origin_df, destination_df])

        coord_df.drop_duplicates(subset=['x', 'y'], inplace=True, ignore_index=True)

        coord_df.reset_index(drop=True, inplace=True)

        coord_df['id'] = coord_df.index + 1
        static_new_df = pd.merge(coord_df[['x', 'y']],
                                 static_base_df[['x', 'y']],
                                 how='outer',
                                 indicator=True)

        return self.__insert_new_data(data_new_df=static_new_df, data_base_df=static_base_df, table_name=table_name)

    def __insert_into_coord_time_table(self, source_df: pd.DataFrame, table_name: str):
        coord_df = self.__insert_into_coord_table(source_df=source_df, table_name='coord')
        source_df['origin_coord_id'] = source_df.apply(lambda row: coord_df[(row['origin_x'] == coord_df['x']) & (row['origin_y'] == coord_df['y'])]['id'].values[0], axis=1)
        source_df['dest_coord_id'] = source_df.apply(lambda row: coord_df[(row['destination_x'] == coord_df['x']) & (row['destination_y'] == coord_df['y'])]['id'].values[0], axis=1)
        coord_time_df = source_df[['origin_coord_id', 'dest_coord_id', 'time_range_id']]

        static_query = f'''SELECT id, origin_coord_id, dest_coord_id, time_range_id
                           FROM {self.schema}.coord_time'''
        static_base_df = self.db_conn.export_data_to_data_frame(sql_query=static_query)[0]

        coord_time_df.reset_index(drop=True, inplace=True)

        coord_time_df['id'] = coord_time_df.index + 1
        static_new_df = pd.merge(coord_time_df[['origin_coord_id', 'dest_coord_id', 'time_range_id']],
                                 static_base_df[['origin_coord_id', 'dest_coord_id', 'time_range_id']],
                                 how='outer',
                                 indicator=True)

        return self.__insert_new_data(data_new_df=static_new_df, data_base_df=static_base_df, table_name=table_name)

    def get_time_range_dataframe(self):
        time_range_query = f'''SELECT id, range, time_from, time_to
                               FROM {self.schema}.time_range'''
        time_range_df = self.db_conn.export_data_to_data_frame(sql_query=time_range_query)[0]

        return time_range_df

    def insert_into_trip(self, source_df: pd.DataFrame) -> None:
        region_df = self.__insert_into_static_table(source_df=source_df, table_name='region')
        datasource_df = self.__insert_into_static_table(source_df=source_df, table_name='datasource')
        coord_time_df = self.__insert_into_coord_time_table(source_df=source_df, table_name='coord_time')

        trip_df = pd.merge(source_df, region_df,
                           left_on='region',
                           right_on='description',
                           how="left",
                           suffixes=('_main_df', '_region_df'))

        trip_df = pd.merge(trip_df, datasource_df,
                           left_on='datasource',
                           right_on='description',
                           how="left",
                           suffixes=('_region_df', '_datasource_df'))

        trip_df = pd.merge(trip_df, coord_time_df,
                           left_on=['origin_coord_id', 'dest_coord_id', 'time_range_id'],
                           right_on=['origin_coord_id', 'dest_coord_id', 'time_range_id'],
                           how="left",
                           suffixes=('_datasource_df', '_coord_time_df'))

        trip_df.rename(columns={'id_region_df': 'region_id',
                                'id_datasource_df': 'datasource_id',
                                'id': 'coord_time_id'}, inplace=True)

        trip_df = trip_df[['region_id', 'coord_time_id', 'datasource_id', 'date']]

        self.db_conn.import_data_frame_to_database(data=trip_df,
                                                   table_name='trip',
                                                   if_exists='append',
                                                   schema=self.schema)

    def get_weekly_avg_of_trips_by_region(self):
        sql_query = f'''WITH week_cte AS (
                            SELECT region_id,
                                   date,
                                   DATE_PART('week', date) AS week
                            FROM {self.schema}.trip
                        ),
                        week_count_cte AS (
                            SELECT region_id,
                                   week,
                                   COUNT(region_id) AS num_trips
                            FROM week_cte
                            GROUP BY region_id, week
                        )
                        SELECT r.description AS region,
                               AVG(num_trips) AS weekly_avg_trips
                        FROM week_count_cte wc
                        INNER JOIN {self.schema}.region r ON wc.region_id = r.id
                        GROUP BY r.description
                        ORDER BY weekly_avg_trips;'''

        return self.db_conn.export_data_to_data_frame(sql_query=sql_query)

    def get_weekly_average_trips_by_bounding_box(self, x_a: float, y_a: float, x_b: float, y_b: float):

        x_min = min(x_a, x_b)
        x_max = max(x_a, x_b)
        y_min = min(y_a, y_b)
        y_max = max(y_a, y_b)

        sql_query = f'''WITH coords_cte AS (
                        SELECT ct.id, c.x, c.y
                        FROM {self.schema}.coord_time ct
                        INNER JOIN {self.schema}.coord c ON c.id = ct.origin_coord_id
                        UNION
                        SELECT ct.id, c.x, c.y
                        FROM {self.schema}.coord_time ct
                        INNER JOIN {self.schema}.coord c ON c.id = ct.dest_coord_id
                        ),
                        trips_bounding_box_cte AS (
                            SELECT COUNT(*) AS num_trips
                            FROM {self.schema}.trip t
                            INNER JOIN coords_cte c ON t.coord_time_id = c.id
                            WHERE x BETWEEN :x_min AND :x_max
                            AND y BETWEEN :y_min AND :y_max
                            GROUP BY DATE_PART('week', t.date)
                        )
                        SELECT AVG(num_trips) AS weekly_avg_trips_bb
                        FROM trips_bounding_box_cte;'''

        return self.db_conn.export_data_to_data_frame(sql_query=sql_query, params={'x_min': x_min,
                                                                                   'x_max': x_max,
                                                                                   'y_min': y_min,
                                                                                   'y_max': y_max})
