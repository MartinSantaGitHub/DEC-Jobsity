import os
from datetime import datetime
from fastapi import UploadFile
from utils.file_process_base import FileProcessBase


class FileProcessUpload(FileProcessBase):
    def __init__(self, files: list[UploadFile], files_folder_path: str):
        super().__init__()
        self.files = files
        self.files_folder_path = files_folder_path

    def set_file_path_and_name(self, i: int):
        uploaded_file = self.files[i]
        file = uploaded_file.file
        self.file_name = uploaded_file.filename
        self.file_path = f'{self.files_folder_path}/{datetime.now().timestamp()}_{self.file_name}'
        bytes_data = file.read()

        with open(f'{self.file_path}', "wb") as f:
            f.write(bytes_data)

    def delete_file(self):
        if os.path.exists(f'{self.file_path}'):
            os.remove(f'{self.file_path}')
