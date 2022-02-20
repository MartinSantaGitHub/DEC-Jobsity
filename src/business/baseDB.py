class BaseDB:
    def __init__(self, db_conn, schema: str):
        self.schema = schema
        self.db_conn = db_conn
