import botocore.client
import boto3
import elasticsearch
import sqlalchemy
import neo4j
from sqlalchemy.orm import Session
import redis
import requests
import typing as t
from configuration.providers import DefaultConfigProvider
from urllib.parse import urljoin
from enum import Enum
from contextlib import contextmanager
from common.utils.serializers import FlexibleUTF8Serializer
from dataPipelines.gc_db_utils.orch.utils import init_db_bindings as init_orch_db_bindings, create_tables_and_views as create_orch_db_schema, drop_tables_and_views as drop_orch_schema
from dataPipelines.gc_db_utils.web.utils import init_db_bindings as init_web_db_bindings, create_tables_and_views as create_web_db_schema, drop_tables_and_views as drop_web_schema
from common.utils.timeout_utils import raise_on_timeout, ContextTimeout
import os

class ApiSession(requests.Session):
    def __init__(self, __api_base_url=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__api_base_url = None

    def request(self, method, url, *args, **kwargs) -> requests.Response:
        url = urljoin(self.__api_base_url, url)
        return super().request(method, url, *args, **kwargs)


class DBSessionScopeMode(Enum):
    READ_WRITE = 'rw'
    READ_ONLY = 'ro'


class ConnectionHelper:
    DEFAULT_TIMEOUT_SECS=5
    def __init__(self, conf_dict: t.Dict[str, t.Any]):
        self.conf = conf_dict

    @classmethod
    def from_config(cls, *config_provider_args, **config_provider_kwargs) -> 'ConnectionHelper':
        return cls(DefaultConfigProvider().get_config(*config_provider_args, **config_provider_kwargs))  # type: ignore

    @property
    def s3_resource(self) -> 'boto3.resources.factory.s3.ServiceResource':

        base_kwargs = dict(
            region_name=self.conf['aws']['default_region']
        )

        key_kwargs = dict(
            aws_access_key_id=self.conf['aws']['access_key'],
            aws_secret_access_key=self.conf['aws']['secret_key'],
        ) if self.conf['aws']['auth_type'] == 'key' else {}

        endpoint_kwargs = dict(
            endpoint_url=self.conf['aws']['endpoint_url'],
            config=botocore.client.Config(
                signature_version=self.conf['aws']['endpoint_s3_signature_version']
            )
        ) if self.conf['aws']['endpoint_type'] != 'aws' else {}

        boto_resource_kwargs = dict(
            **base_kwargs,
            **key_kwargs,
            **endpoint_kwargs
        )

        return boto3.resource('s3', **boto_resource_kwargs)

    @property
    def s3_client(self) -> 'botocore.client.S3':
        return self.s3_resource.meta.client

    @property
    def data_api_requests_session(self) -> requests.Session:
        api_base_url = self.conf['data_api']['api_base_url']
        return ApiSession(__api_base_url=api_base_url)

    @property
    def ml_api_requests_session(self) -> requests.Session:
        api_base_url = "http://{host}:{port}".format(
            host=self.conf['ml_api']['flask_host'],
            port=self.conf['ml_api']['flask_port']
        )
        return ApiSession(__api_base_url=api_base_url)

    @property
    def ml_api_redis_client(self) -> redis.client.Redis:
        return redis.Redis(
            self.conf['ml_api']['redis_host'],
            self.conf['ml_api']['redis_port']
        )

    @property
    def orch_db_engine(self) -> sqlalchemy.engine.Engine:
        if hasattr(self, '_orch_db_engine'):
            # this avoids same engine handle being reused in multiprocessing code, causing errors and deadlocks
            self._orch_db_engine.dispose()
            return self._orch_db_engine

        db_conn_string = "postgresql://{user}:{passw}@{host}:{port}/{db}".format(
            user=self.conf['orch_db']['username'],
            passw=self.conf['orch_db']['password'],
            host=self.conf['orch_db']['host'],
            port=self.conf['orch_db']['port'],
            db=self.conf['orch_db']['database']
        )
        self._orch_db_engine: sqlalchemy.engine.Engine = sqlalchemy.create_engine(db_conn_string, connect_args={'connect_timeout': self.DEFAULT_TIMEOUT_SECS})
        return self._orch_db_engine

    def init_orch_db(self, create_schema: bool = False, drop_existing_schema: bool = False) -> None:
        engine = self.orch_db_engine
        if drop_existing_schema:
            drop_orch_schema(engine=engine)

        if create_schema:
            create_orch_db_schema(engine=engine)
        init_orch_db_bindings(engine=engine)

    @property
    def web_db_engine(self) -> sqlalchemy.engine.Engine:
        if hasattr(self, '_web_db_engine'):
            # this avoids same engine handle being reused in multiprocessing code, causing errors and deadlocks
            self._web_db_engine.dispose()
            return self._web_db_engine

        db_conn_string = "postgresql://{user}:{passw}@{host}:{port}/{db}".format(
            user=self.conf['web_db']['username'],
            passw=self.conf['web_db']['password'],
            host=self.conf['web_db']['host'],
            port=self.conf['web_db']['port'],
            db=self.conf['web_db']['database']
        )
        self._web_db_engine: sqlalchemy.engine.Engine = sqlalchemy.create_engine(db_conn_string, connect_args={'connect_timeout': self.DEFAULT_TIMEOUT_SECS})
        return self._web_db_engine

    def init_web_db(self, create_schema: bool = False, drop_existing_schema: bool = False) -> None:
        engine = self.web_db_engine
        if drop_existing_schema:
            drop_web_schema(engine=engine)

        if create_schema:
            create_web_db_schema(engine=engine)

        init_web_db_bindings(engine=engine)

    def init_dbs(self, create_schema: bool = False, drop_existing_schema: bool = False) -> None:
        self.init_orch_db(create_schema=create_schema, drop_existing_schema=drop_existing_schema)
        self.init_web_db(create_schema=create_schema, drop_existing_schema=drop_existing_schema)

    @property
    def es_client(self) -> elasticsearch.Elasticsearch:
        if hasattr(self, '_es_args'):
            return elasticsearch.Elasticsearch(**self._es_args)

        host_args = dict(
            hosts=[{
                'host': self.conf['es']['host'],
                'port': self.conf['es']['port'],
                'http_compress': True,
                'timeout': 60 * 5
            }]
        )

        auth_args = dict(
            http_auth=(
                self.conf['es']['username'],
                self.conf['es']['password']
            )
        ) if self.conf['es']['basic_auth'] else {}

        ssl_args = dict(
            use_ssl=self.conf['es']['ssl']
        )

        misc_args = dict(
            serializer=FlexibleUTF8Serializer()
        )

        # TODO: temporary workaround to check ES client with lower timeout
        #       need to look into custom connection classes or pools to set
        #       lower timeout for initial connection
        def ping_es() -> bool:
            test_host_args = dict(
                hosts=[{
                    'host': self.conf['es']['host'],
                    'port': self.conf['es']['port'],
                    'http_compress': True,
                    'timeout': self.DEFAULT_TIMEOUT_SECS
                }]
            )

            test_es_args = dict(
                **test_host_args,
                **auth_args,
                **ssl_args,
                **misc_args
            )
            return elasticsearch.Elasticsearch(**test_es_args).ping()

        if not ping_es():
            raise RuntimeError("Could not connect to ES cluster.")

        es_args = dict(
            **host_args,
            **auth_args,
            **ssl_args,
            **misc_args
        )

        self._es_args: t.Dict[str, t.Any] = es_args
        return elasticsearch.Elasticsearch(**self._es_args)

    @contextmanager  # type: ignore
    def db_session_scope(self,
                         engine: sqlalchemy.engine.Engine,
                         session_mode: t.Union[DBSessionScopeMode, str] = "rw") -> t.ContextManager[Session]:
        """Provide a transactional scope around a series of operations."""
        is_ro = DBSessionScopeMode(session_mode) == DBSessionScopeMode.READ_ONLY
        session = Session(bind=engine, autoflush=False, autocommit=False)

        def nonce(*args, **kwargs):
            return None

        if is_ro:
            session.flush = nonce
            session._flush = nonce

        try:
            yield session
            if not is_ro:
                session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def web_db_session_scope(self, session_mode: t.Union[DBSessionScopeMode, str]) -> t.ContextManager[Session]:
        return self.db_session_scope(engine=self.web_db_engine, session_mode=session_mode)

    def orch_db_session_scope(self, session_mode: t.Union[DBSessionScopeMode, str]) -> t.ContextManager[Session]:
        return self.db_session_scope(engine=self.orch_db_engine, session_mode=session_mode)

    @property
    def neo4j_driver(self) -> neo4j.Driver:
        if hasattr(self, '_neo4j_driver_settings'):
            return neo4j.GraphDatabase.driver(**self._neo4j_driver_settings)

        host = self.conf['neo4j']['host']
        port = self.conf['neo4j']['port']
        user = self.conf['neo4j']['username']
        password = self.conf['neo4j']['password']
        connection_protocol = self.conf['neo4j']['connection_protocol']
        uri = f"{connection_protocol}://{host}:{port}"

        self._neo4j_driver_settings: t.Dict[str, t.Any] = dict(uri=uri, auth=(user, password))

        try:
            with raise_on_timeout(5):
                return neo4j.GraphDatabase.driver(uri, auth=(user, password))
        except ContextTimeout:
            raise TimeoutError("Timed out trying to connect to neo4j")

    @contextmanager  # type: ignore
    def neo4j_session_scope(self) -> t.ContextManager[neo4j.Session]:
        """Ctx manager for a neo4j session"""
        session = self.neo4j_driver.session()
        try:
            yield session
        finally:
            session.close()
