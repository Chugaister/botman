from sqlite3 import connect
from sqlite3 import IntegrityError
import aiopg
from . import DIR, exists, join, makedirs
from .exceptions import *
from . import autocreation
import logging
import os
import argparse

from configs import args_parse
from web_config.config import DB_URI

args = args_parse.args
# parser = argparse.ArgumentParser()
# parser.add_argument('--local', action='store_true', help='Run in local mode')
# parser.add_argument('--token', action='store', help='Bot token to run on')
# parser.add_argument('--port', action='store', help='Select the port to run on')
# parser.add_argument('--source', action='store', help='Database folder path')
# parser.add_argument('--logs', action='store', help='Logs folder path')
# args = parser.parse_args()

source_folder = "source" if not args.source else args.source
tables_with_media = ["captchas", "greetings", "mails", "admin_mails"]
tables_with_dual_foreign_keys = ["msgs", "users"]
tables_tg_id = ["admins", "users", "bots", "msgs"]


# create dirs if not exists and create tables if not exists
# gets source folder name
# returns None
async def create_db(source):
    path = join(DIR, source)
    if not exists(path):
        makedirs(path)
        makedirs(join(path, "media"))
    async with aiopg.create_pool(DB_URI) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                for query in autocreation.queries:
                    await cur.execute(query)


# create connection to db
# gets None
# returns None
async def create_conn() -> aiopg.Connection:
    pool = await aiopg.create_pool(DB_URI)
    return await pool.acquire()


class Database:

    def __init__(self, table_name: str, DB_URI: str, datatype):
        self.table_name = table_name
        self.DB_URI = DB_URI
        self.datatype = datatype

    async def add(self, object):
        def form_query(object):
            into = "("
            for column in object.columns:
                into += f"\"{column}\", "
            into = into[:-2]
            into = into + ")"
            return into

        query = f"INSERT INTO {self.table_name} {form_query(object)} VALUES ({('%s, ' * len(object.columns))[:-2]})"
        async with aiopg.create_pool(DB_URI) as pool:
            async with pool.acquire() as conn:
                async with conn.cursor() as cur:
                    try:
                        await cur.execute(query, object.get_tuple())
                    except IntegrityError:
                        raise RecordAlreadyExists(object)
                    object.id = cur.lastrowid if self.table_name not in tables_tg_id else object.id

    async def get(self, _id: int):
        query = f"SELECT * FROM {self.table_name} WHERE id=%s"
        async with aiopg.create_pool(DB_URI) as pool:
            async with pool.acquire() as conn:
                async with conn.cursor() as cur:
                    cur = await cur.execute(query, (_id,))
                    data = await cur.fetchone()
        if data is None:
            raise RecordIsMissing(_id)
        return self.datatype(*data)

    async def update(self, object):
        data_tuple = object.get_tuple()
        if self.table_name in tables_with_dual_foreign_keys:
            query = f"UPDATE {self.table_name} SET {', '.join([f'{cl_name}=%s' for cl_name, value in zip(object.columns, data_tuple)])} WHERE id={object.id} AND bot={object.bot}"
        else:
            query = f"UPDATE {self.table_name} SET {', '.join([f'{cl_name}=%s' for cl_name, value in zip(object.columns, data_tuple)])} WHERE id={object.id}"
        async with aiopg.create_pool(DB_URI) as pool:
            async with pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(query, data_tuple)

    async def delete(self, _id: int):
        async with aiopg.create_pool(DB_URI) as pool:
            async with pool.acquire() as conn:
                if self.table_name in tables_with_media:
                    query = f"SELECT photo, video, gif FROM {self.table_name} WHERE {_id}"
                    async with conn.cursor() as cur:
                        await cur.execute(query)
                        records = await cur.fetchall()
                    for record in records[0]:
                        if record is not None:
                            os.remove(join(DIR, source_folder, "media", record))
                query = f"DELETE FROM {self.table_name} WHERE id={_id}"
                async with conn.cursor() as cur:
                    await cur.execute(query)

    async def get_by(self, **kwargs):
        items = list(kwargs.items())
        query = f"SELECT * FROM {self.table_name} WHERE {' AND '.join([f'{key}=%s' for key, value in items])}"
        async with aiopg.create_pool(DB_URI) as pool:
            async with pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(query, [value for key, value in items])
                    records = await cur.fetchall()
        return [self.datatype(*record) for record in records]

    async def get_all(self):
        query = f"SELECT * FROM {self.table_name}"
        async with aiopg.create_pool(DB_URI) as pool:
            async with pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(query)
                    records = await cur.fetchall()
        return [self.datatype(*record) for record in records]
