from elasticsearch import Elasticsearch
import requests
import os
import logging
import typing as t
import base64
from urllib.parse import urljoin

logger = logging.getLogger("gamechanger")


class ESUtils:
    def __init__(
        self,
        host: str = os.environ.get("ES_HOST", "localhost"),
        port: str = os.environ.get("ES_PORT", 443),
        user: str = os.environ.get("ES_USER", ""),
        password: str = os.environ.get("ES_PASSWORD", ""),
        enable_ssl: bool = os.environ.get(
            "ES_ENABLE_SSL", "True").lower() == "true",
        enable_auth: bool = os.environ.get(
            "ES_ENABLE_AUTH", "False").lower() == "true",
        es_index: str = os.environ.get("ES_INDEX", "gamechanger"),
    ):

        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.enable_ssl = enable_ssl
        self.enable_auth = enable_auth
        self.es_index = es_index

        self.auth_token = base64.b64encode(
            f"{self.user}:{self.password}".encode()
        ).decode()

    @property
    def client(self) -> Elasticsearch:
        if hasattr(self, "_client"):
            return getattr(self, "_client")

        host_args = dict(
            hosts=[
                {
                    "host": self.host,
                    "port": self.port,
                    "http_compress": True,
                    "timeout": 60,
                }
            ]
        )
        auth_args = (
            dict(http_auth=(self.user, self.password)
                 ) if self.enable_auth else {}
        )
        ssl_args = dict(use_ssl=self.enable_ssl)

        es_args = dict(
            **host_args,
            **auth_args,
            **ssl_args,
        )

        self._es_client = Elasticsearch(**es_args)
        return self._es_client

    @property
    def auth_headers(self) -> t.Dict[str, str]:
        return {"Authorization": f"Basic {self.auth_token}"} if self.enable_auth else {}

    @property
    def content_headers(self) -> t.Dict[str, str]:
        return {"Content-Type": "application/json"}

    @property
    def default_headers(self) -> t.Dict[str, str]:
        if self.enable_auth:
            return dict(**self.auth_headers, **self.content_headers)
        else:
            return dict(**self.content_headers)

    @property
    def root_url(self) -> str:
        return ("https" if self.enable_ssl else "http") + f"://{self.host}:{self.port}/"

    def request(self, method: str, url: str, **request_opts) -> requests.Response:
        complete_url = urljoin(self.root_url, url.lstrip("/"))
        return requests.request(
            method=method,
            url=complete_url,
            headers=self.default_headers,
            **request_opts,
        )

    def post(self, url: str, **request_opts) -> requests.Response:
        return self.request(method="POST", url=url, **request_opts)

    def put(self, url: str, **request_opts) -> requests.Response:
        return self.request(method="PUT", url=url, **request_opts)

    def get(self, url: str, **request_opts) -> requests.Response:
        return self.request(method="GET", url=url, **request_opts)

    def delete(self, url: str, **request_opts) -> requests.Response:
        return self.request(method="DELETE", url=url, **request_opts)
