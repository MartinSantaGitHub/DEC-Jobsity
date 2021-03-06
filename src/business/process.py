import re
import pandas as pd
import glob
import asyncio
from datetime import datetime
from dask import dataframe as dd
from tqdm import tqdm
from fastapi import UploadFile
from utils.event import Event
from utils.file_process_local import FileProcessLocal
from utils.file_process_upload import FileProcessUpload
from business.databaseDML import DatabaseDML


class ProcessManager:
    def __init__(self, database_dml: DatabaseDML, files_folder: str, percent_update_rate: int = 2):
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

    async def start(self, files: list[UploadFile], user_id: float) -> pd.DataFrame:
        file_process = None

        if not files:
            files = glob.glob(f'{self.files_folder_path}/*.csv')

            files.sort()

            file_process = FileProcessLocal(files=files)
        else:
            if not all([re.search(r'.*\.csv', f.filename) for f in files]):
                return 'The files must be .csv files'

            file_process = FileProcessUpload(files=files, files_folder_path=self.files_folder_path)

        self.on_is_finished_update(False, user_id)

        files_len = len(files)
        time_range_df = self.database_dml.get_time_range_dataframe()

        for i in range(files_len):
            file_process.set_file_path_and_name(i)
            filepath = file_process.get_file_path()
            filename = file_process.get_file_name()

            df = dd.read_csv(f'{filepath}', blocksize=64000000)
            partitions = df.npartitions
            partitions_perc = 100 // partitions
            top = partitions - 1

            # This line lets the thread be released so that it could handle the
            # 'status_event_generator' function in the 'services' module. Otherwise, it must be waited
            # to finish this process until the 'status_event_generator' function can be executed.
            # This happens because of the GIL.
            await asyncio.sleep(0.001)
            self.on_status_update(filename, 0, user_id)

            # For testing the progress bar, uncomment the next lines and comment
            # the next 'for loop' with its code inside.

            # partitions = 16
            # partitions_perc = 100 // partitions
            # top = partitions - 1

            # for i in range(partitions):
            #     await asyncio.sleep(1)
            #
            #     perc_completed = i * partitions_perc
            #
            #     if perc_completed % 2 == 0 or i == top:
            #         current_perc = perc_completed if i != top else 100
            #         self.on_status_update(filename, current_perc, user_id)

            for n in tqdm(range(partitions), desc=f'Processing file ({filename}) n?? {i + 1} of {files_len}'):
                source_df = df.get_partition(n).compute()

                source_df['datetime'] = source_df['datetime'].apply(lambda x: datetime.strptime(x, '%Y-%m-%d %H:%M:%S'))
                source_df['time'] = source_df['datetime'].apply(
                    lambda x: int(str(x.time().hour) + str(x.time().minute).zfill(2)))

                # source_df['date'] = source_df['datetime'].apply(lambda x: x.date())

                source_df['time_range_id'] = source_df['time'].apply(lambda x: time_range_df[
                    (x >= time_range_df['time_from']) & (x <= time_range_df['time_to'])]['id'].values[0])

                source_df.drop(['time'], axis=1, inplace=True)

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

                if perc_completed % self.percent_update_rate == 0 or n == top:
                    current_perc = perc_completed if n != top else 100

                    # This line lets the thread be released so that it could handle the
                    # 'status_event_generator' function in the 'services' module. Otherwise, it must be waited
                    # to finish this process until the 'status_event_generator' function can be executed.
                    # This happens because of the GIL.
                    await asyncio.sleep(0.001)
                    self.on_status_update(filename, current_perc, user_id)

            file_process.delete_file()

        self.on_is_finished_update(True, user_id)

        return 'All files were processed successfully'
