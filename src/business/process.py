import os
import re
import pandas as pd
from datetime import datetime
from dask import dataframe as dd
from tqdm import tqdm
from fastapi import UploadFile
from utils.event import Event
from business.databaseDML import DatabaseDML


class ProcessManager:
    def __init__(self, database_dml: DatabaseDML, files_folder: str, percent_update_rate: int = 5):
        self.files_folder_path = f'../{files_folder}'
        self.database_dml = database_dml
        self.on_status_update = Event()
        self.on_is_finished_update = Event()
        self.percent_update_rate = percent_update_rate

    def add_subscribers_for_status_update_event(self, method):
        self.on_status_update += method

    def remove_subscribers_for_status_update_event(self, method):
        self.on_status_update -= method

    def add_subscribers_for_is_finished_update_event(self, method):
        self.on_is_finished_update += method

    def remove_subscribers_for_is_finished_update_event(self, method):
        self.on_is_finished_update -= method

    def start(self, files: list[UploadFile]) -> pd.DataFrame:
        if files and not all([re.search(r'.*\.csv', f.filename) for f in files]):
            return 'The files must be .csv files'

        self.on_is_finished_update(False)

        files_len = len(files)
        time_range_df = self.database_dml.get_time_range_dataframe()

        for i in range(files_len):
            uploaded_file = files[i]
            file = uploaded_file.file
            filename = uploaded_file.filename
            filepath = f'{self.files_folder_path}/{filename}'
            bytes_data = file.read()

            with open(f'{filepath}', "wb") as f:
                f.write(bytes_data)

            df = dd.read_csv(f'{filepath}', blocksize=64000000)
            partitions = df.npartitions
            partitions_perc = 100 // partitions

            for n in tqdm(range(partitions), desc=f'Processing file ({filename}) nº {i + 1} of {files_len}'):
                source_df = df.get_partition(n).compute()

                source_df['datetime'] = source_df['datetime'].apply(lambda x: datetime.strptime(x, '%Y-%m-%d %H:%M:%S'))
                source_df['time'] = source_df['datetime'].apply(
                    lambda x: int(str(x.time().hour) + str(x.time().minute).zfill(2)))
                source_df['date'] = source_df['datetime'].apply(lambda x: x.date())
                source_df['time_range_id'] = source_df['time'].apply(lambda x: time_range_df[
                    (x >= time_range_df['time_from']) & (x <= time_range_df['time_to'])]['id'].values[0])

                source_df.drop(['datetime', 'time'], axis=1, inplace=True)

                regex_rule = r'\d+\.\d+'

                source_df['origin_x'] = source_df['origin_coord'].apply(
                    lambda x: (round(float(re.findall(regex_rule, x)[0]), 2)))
                source_df['origin_y'] = source_df['origin_coord'].apply(
                    lambda x: (round(float(re.findall(regex_rule, x)[1]), 2)))
                source_df['destination_x'] = source_df['destination_coord'].apply(
                    lambda x: (round(float(re.findall(regex_rule, x)[0]), 2)))
                source_df['destination_y'] = source_df['destination_coord'].apply(
                    lambda x: (round(float(re.findall(regex_rule, x)[1]), 2)))

                self.database_dml.insert_into_trip(source_df=source_df)

                perc_completed = n * partitions_perc

                if perc_completed % self.percent_update_rate == 0:
                    self.on_status_update(filename, perc_completed)

            if os.path.exists(f'{filepath}'):
                os.remove(f'{filepath}')

        self.on_is_finished_update(True)

        return 'All files were processed successfully'
