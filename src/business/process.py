import glob
import re
import pandas as pd
from datetime import datetime
from dask import dataframe as dd
from tqdm import tqdm
from business.databaseDML import DatabaseDML


class ProcessManager:
    def __init__(self, database_dml: DatabaseDML, files_folder: str):
        self.files_folder_path = f'../{files_folder}'
        self.database_dml = database_dml

    def start(self) -> pd.DataFrame:
        all_files = glob.glob(f'./{self.files_folder_path}/*.csv')
        all_files_len = len(all_files)
        time_range_df = self.database_dml.get_time_range_dataframe()

        for i in range(all_files_len):
            filename = all_files[i]
            df = dd.read_csv(filename, blocksize=64000000)

            for n in tqdm(range(df.npartitions), desc=f'Processing file ({filename}) nº {i + 1} of {all_files_len}'):
                source_df = df.get_partition(n).compute()

                source_df['datetime'] = source_df['datetime'].apply(lambda x: datetime.strptime(x, '%Y-%m-%d %H:%M:%S'))
                source_df['time'] = source_df['datetime'].apply(lambda x: int(str(x.time().hour) + str(x.time().minute).zfill(2)))
                source_df['date'] = source_df['datetime'].apply(lambda x: x.date())
                source_df['time_range_id'] = source_df['time'].apply(lambda x: time_range_df[(x >= time_range_df['time_from']) & (x <= time_range_df['time_to'])]['id'].values[0])

                source_df.drop(['datetime', 'time'], axis=1, inplace=True)

                regex_rule = r'\d+\.\d+'

                source_df['origin_x'] = source_df['origin_coord'].apply(lambda x: (round(float(re.findall(regex_rule, x)[0]),2)))
                source_df['origin_y'] = source_df['origin_coord'].apply(lambda x: (round(float(re.findall(regex_rule, x)[1]),2)))
                source_df['destination_x'] = source_df['destination_coord'].apply(lambda x: (round(float(re.findall(regex_rule, x)[0]),2)))
                source_df['destination_y'] = source_df['destination_coord'].apply(lambda x: (round(float(re.findall(regex_rule, x)[1]),2)))

                self.database_dml.insert_into_trip(source_df=source_df)

        message = 'All files were processed successfully'

        return message
