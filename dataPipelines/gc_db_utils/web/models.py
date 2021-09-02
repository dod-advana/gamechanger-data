from sqlalchemy.ext.declarative import declarative_base
from .schemas import SnapshotEntrySchema, DAFACharterMapFlattenedSchema, DAFACharterMapSchema, CloneMetaSchema
from common.utils.mixins import AutoRepr
from sqlalchemy.ext.declarative import DeferredReflection


WebReflectedBase = declarative_base()


class DeferredWebReflectedBase(DeferredReflection, WebReflectedBase):
    __abstract__ = True


class SnapshotEntry(AutoRepr, SnapshotEntrySchema, DeferredWebReflectedBase):
    __tablename__ = 'gc_document_corpus_snapshot'


class DAFACharterMap(AutoRepr, DAFACharterMapSchema, DeferredWebReflectedBase):
    __tablename__ = 'dafa_charter_map'


class DAFACharterMapFlattened(AutoRepr, DAFACharterMapFlattenedSchema, DeferredWebReflectedBase):
    __tablename__ = 'dafa_charter_map_flattened_vw'


class CloneMeta(AutoRepr, CloneMetaSchema, DeferredWebReflectedBase):
    __tablename__ = 'clone_meta'
