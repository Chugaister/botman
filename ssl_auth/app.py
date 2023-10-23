from flask import Flask, send_file
from os import path
from socket import gethostname, gethostbyname
from re import match


class ArgsError(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class CustomFlask(Flask):

    def __init__(self, file_path: str, endpoint_path: str, host: str, port: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__file_path = None
        self.__file_name = None
        self.__endpoint_path = None
        self.__host = None
        self.__port = None

        self.file_path = file_path
        self.endpoint_path = endpoint_path
        self.host = host
        self.port = port

        self.create_endpoint()

    @property
    def file_path(self):
        return self.__file_path

    @property
    def file_name(self):
        return self.__file_name

    @file_path.setter
    def file_path(self, value: str):
        if path.isfile(value):
            self.__file_path = value
            self.__file_name = path.split(value)[-1]
        else:
            raise ArgsError(f"Cannot find file {value}")

    @property
    def endpoint_path(self):
        return self.__endpoint_path

    @endpoint_path.setter
    def endpoint_path(self, value: str):
        self.__endpoint_path = value

    @property
    def host(self):
        return self.__host

    @host.setter
    def host(self, value: str):
        ip_pattern = r'^(25[0-5]|2[0-4]\d|1\d{2}|\d{1,2})(\.(25[0-5]|2[0-4]\d|1\d{2}|\d{1,2})){3}$'
        if match(ip_pattern, value) is None:
            raise ArgsError(f"Provided host {value} is not valid")
        self.__host = value

    @property
    def port(self):
        return self.__port

    @port.setter
    def port(self, value: str | int):
        if isinstance(value, str) and value.isdigit():
            value = int(value)
        elif isinstance(value, int):
            pass
        else:
            raise ArgsError(f"Provided port {value} is not valid")
        if 0 > int(value) or int(value) > 65535:
            raise ArgsError(f"Provided port {value} is not valid")
        self.__port = int(value)

    def create_endpoint(self):
        @self.route(f"{self.endpoint_path}/{self.file_name}")
        def get_file():
            return send_file(self.file_path)

    def get_url(self):
        return f"http://{self.host}:{self.port}{self.endpoint_path}/{self.file_name}"

    @staticmethod
    def get_external_ip():
        hostname = gethostname()
        external_ip = gethostbyname(hostname)
        return external_ip
