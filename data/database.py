import asyncio
import sqlite3
from sqlite3 import connect
from sqlite3 import IntegrityError
import aiosqlite
from . import DIR, exists, join, makedirs
from .exceptions import *
from . import autocreation
import logging


def create_db(source):
    path = join(DIR, source)
    if not exists(path):
        makedirs(path)
        conn = connect(join(path, "base.db"))
        cur = conn.cursor()
        for query in autocreation.queries:
            cur.execute(query)
        conn.commit()
        makedirs(join(path, "media"))


async def get_db(source) -> aiosqlite.Connection:
    return await aiosqlite.connect(join(DIR, source, "base.db"))



class Database:

    def __init__(self, table_name: str, conn: aiosqlite.Connection, datatype):
        self.table_name = table_name
        self.conn = conn
        self.datatype = datatype

    async def addToBD(self, object):
        query = f"INSERT INTO {self.table_name} {str(object.columns)} VALUES ({'?, '*(len(object.columns)-1)}?)"
        logging.debug(f"{query}, {object.get_tuple()}")
        try:
            cur = await self.conn.execute(query, object.get_tuple())
        except IntegrityError:
            raise RecordAlreadyExists(object)
        object.id = cur.lastrowid
        await self.conn.commit()

    async def getFromDB(self, _id: int):
        query = f"SELECT * FROM {self.table_name} WHERE id=?"
        # logging.debug(f"GET: {query}")
        cur = await self.conn.execute(query, (_id,))
        data = await cur.fetchone()
        if data is None:
            raise RecordIsMissing(_id)
        return self.datatype(*data)

    async def updateInDB(self, object):
        data_tuple = object.get_tuple()
        query = f"UPDATE {self.table_name} SET {', '.join([f'{cl_name}=?' for cl_name, value in zip(object.columns, data_tuple)])} WHERE id={object.id}"
        logging.debug(f"UPDATE: {query} {data_tuple}")
        await self.conn.execute(query, data_tuple)
        await self.conn.commit()

    async def deleteFromDB(self, _id: int):
        query = f"DELETE FROM {self.table_name} WHERE id={_id}"
        logging.debug(f"DELETE: {query}")
        await self.conn.execute(query)
        await self.conn.commit()

    async def get_by_fromDB(self, **kwargs):
        items = list(kwargs.items())
        query = f"SELECT * FROM {self.table_name} WHERE {' AND '.join([f'{key}=?' for key, value in items])}"
        # logging.debug(f"GETBY: {query}")
        cur = await self.conn.execute(query, [value for key, value in items])
        records = await cur.fetchall()
        return [self.datatype(*record) for record in records]

    async def get_all_fromDB(self):
        query = f"SELECT * FROM {self.table_name}"
        # logging.debug(f"GETALL: {query}")
        cur = await self.conn.execute(query)
        records = await cur.fetchall()
        return [self.datatype(*record) for record in records]
    