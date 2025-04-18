from pydantic import BaseModel


class SQLQuery(BaseModel):
    sql: str
