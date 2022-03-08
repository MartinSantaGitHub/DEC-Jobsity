import os
from utils.file_process_base import FileProcessBase


class FileProcessLocal(FileProcessBase):
    def __init__(self, files: list[str]):
        super().__init__()
        self.files = files

    def set_file_path_and_name(self, i: int):
        self.file_path = self.files[i]
        self.file_name = os.path.basename(self.file_path)
