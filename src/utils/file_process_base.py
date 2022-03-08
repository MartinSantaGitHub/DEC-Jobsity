from abc import abstractmethod


class FileProcessBase:
    def __init__(self):
        self.file_path = None
        self.file_name = None

    @abstractmethod
    def set_file_path_and_name(self, i: int):
        pass

    @abstractmethod
    def delete_file(self):
        pass

    def get_file_path(self):
        return self.file_path

    def get_file_name(self):
        return self.file_name
