import sqlite3
from sqlite3 import connect
from sqlite3 import IntegrityError
from os.path import join

from . import DIR
from .exceptions import *


def get_db(source) -> sqlite3.Connection:
    return connect(join(DIR, source, "base.db"))


class Database:

    def __init__(self, table_name: str, conn: sqlite3.Connection, datatype):
        self.table_name = table_name
        self.conn = conn
        self.cur = conn.cursor()
        self.datatype = datatype

    def add(self, object):
        query = f"INSERT INTO {self.table_name} {str(object.columns)} VALUES ({'?, '*(len(object.columns)-1)}?)"
        print(query)
        print(object.get_tuple())
        try:
            self.cur.execute(query, object.get_tuple())
        except IntegrityError:
            raise RecordAlreadyExists(object)
        object.id = self.cur.lastrowid
        self.conn.commit()

    def get(self, _id: int):
        query = f"SELECT * FROM {self.table_name} WHERE id={_id}"
        print(query)
        self.cur.execute(query)
        data = self.cur.fetchone()
        if data is None:
            raise RecordIsMissing(_id)
        return self.datatype(*data)

    def update(self, object):
        data_tuple = object.get_tuple()
        query = f"UPDATE {self.table_name} SET {', '.join([f'{cl_name}=?' for cl_name, value in zip(object.columns, data_tuple)])} WHERE id={object.id}"
        print(query)
        self.cur.execute(query, data_tuple)
        self.conn.commit()

    def delete(self, _id: int):
        query = f"DELETE FROM {self.table_name} WHERE id={_id}"
        self.cur.execute(query)
        self.conn.commit()

    def get_by(self, **kwargs):
        items = list(kwargs.items())
        query = f"SELECT * FROM {self.table_name} WHERE {' AND '.join([f'{key}=?' for key, value in items])}"
        self.cur.execute(query, [value for key, value in items])
        records = self.cur.fetchall()
        return [self.datatype(*record) for record in records]