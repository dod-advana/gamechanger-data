import sqlalchemy as sa
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from typing import Optional, Dict, Any
import datetime as dt
from sqlalchemy.orm import Session
import json
from sqlalchemy.ext.declarative import DeferredReflection
from dataPipelines.gc_db_utils.web.schemas import SnapshotEntrySchema
from common.utils.mixins import AutoRepr
from common.utils.parsers import parse_timestamp
from .schemas import PublicationSchema, VersionedDocSchema, PipelineJobSchema, CrawlerStatusSchema


OrchReflectedBase = declarative_base()


class DeferredOrchReflectedBase(DeferredReflection, OrchReflectedBase):
    __abstract__ = True


class Publication(AutoRepr, PublicationSchema, DeferredOrchReflectedBase):
    __tablename__ = 'publications'

    versioned_docs = relationship("VersionedDoc", back_populates="publication")

    # __table_args__ = (
    #     sa.UniqueConstraint(type, number),
    # {})

    # TODO: Need to use ProcessedDoc instead of Doc for md5 and other things
    @staticmethod
    def create_from_document(doc: Dict[str, Any]) -> 'Publication':
        """Generate Publication from Document dict obj."""
        return Publication(
            name=doc['doc_name'],
            title=doc['doc_title'][:100],
            type=doc['doc_type'],
            number=doc['doc_num'],
            is_ignored=False,
            is_revoked=False
        )

    @staticmethod
    def get_existing_from_doc(doc: Dict[str, Any], session: Session) -> Optional['Publication']:
        existing_pub = session.query(Publication).filter_by(name=doc['doc_name']).one_or_none()
        return existing_pub


    @staticmethod
    def get_or_create_from_document(doc: Dict[str, Any], session: Session) -> 'Publication':
        existing_pub = Publication.get_existing_from_doc(doc=doc, session=session)
        return existing_pub or Publication.create_from_document(doc)


class VersionedDoc(AutoRepr, VersionedDocSchema, DeferredOrchReflectedBase):
    __tablename__ = 'versioned_docs'

    publication = relationship("Publication", back_populates="versioned_docs")

    # TODO: Need to use ProcessedDoc instead of Doc for md5 and other things
    @staticmethod
    def create_from_document(
            doc: Dict[str, Any],
            doc_location: str,
            filename: str,
            batch_timestamp: dt.datetime,
            pub: Publication) -> 'VersionedDoc':
        """Generate VersionedDoc from Document obj. and associated Publication"""
        return VersionedDoc(
            publication=pub,
            name=doc['doc_name'],
            type=doc['doc_type'],
            number=doc['doc_num'],
            # TODO: Pass actual filename using ProcessedDoc instead of Doc
            # TODO: Tweak for clones?
            filename=filename,
            doc_location=doc_location,
            batch_timestamp=batch_timestamp,
            publication_date=parse_timestamp(doc['publication_date']),
            json_metadata=doc,
            version_hash=doc['version_hash'],
            md5_hash="",
            is_ignored=False
        )

    @staticmethod
    def get_existing_from_doc(doc: Dict[str, Any], session: Session) -> Optional['VersionedDoc']:
        # return (
        #     session.query(VersionedDoc)
        #         .filter(and_(
        #             VersionedDoc.name == doc['doc_name'],
        #             VersionedDoc.version_hash == doc['version_hash']
        #         )).one_or_none()
        # )
        # TODO: see if there's better logic here since we can have multiple docs for same pub_name = doc_name
        #       mind the fake metadata created for manually created pubs, it may not make sense to use versioned_hash there
        return None


    @staticmethod
    def get_or_create_from_document(
            doc: Dict[str, Any],
            pub: Publication,
            filename: str,
            doc_location: str,
            batch_timestamp: dt.datetime,
            session: Session) -> 'VersionedDoc':
        existing_vdoc = VersionedDoc.get_existing_from_doc(doc=doc, session=session)
        return (
                existing_vdoc or
                VersionedDoc.create_from_document(
                    doc=doc,
                    pub=pub,
                    doc_location=doc_location,
                    filename=filename,
                    batch_timestamp=batch_timestamp
                )
        )


class PipelineJob(AutoRepr, PipelineJobSchema, DeferredOrchReflectedBase):
    __tablename__ = 'pipeline_jobs'


class SnapshotViewEntry(AutoRepr, SnapshotEntrySchema, DeferredOrchReflectedBase):
    __tablename__ = 'gc_document_corpus_snapshot_vw'

class CrawlerStatusEntry(AutoRepr, CrawlerStatusSchema, DeferredOrchReflectedBase):
    __tablename__ = 'crawler_status'

    def create(status: str, crawler_name: str, datetime=dt.datetime) -> 'CrawlerStatusEntry':
        """Generate Publication from Document obj."""
        return CrawlerStatusEntry(
            status=status,
            crawler_name=crawler_name,
            datetime=datetime
        )
