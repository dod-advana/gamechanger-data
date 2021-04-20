import sqlalchemy as sa
from sqlalchemy.ext.declarative import declared_attr


class PublicationSchema:
    """Schema for publications"""

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(512), nullable=False, unique=True)
    title = sa.Column(sa.String(512), nullable=False)
    type = sa.Column(sa.String(512), nullable=False)
    number = sa.Column(sa.String(512), nullable=True)
    is_ignored = sa.Column(sa.Boolean, default=False, nullable=False)
    is_revoked = sa.Column(sa.Boolean, default=False, nullable=False)


class VersionedDocSchema:
    """Schema for versioned_docs"""

    id = sa.Column(sa.Integer, primary_key=True)

    @declared_attr
    def pub_id(cls):
        return sa.Column(sa.Integer, sa.ForeignKey('publications.id'), nullable=False)

    name = sa.Column(sa.String(512), nullable=False)
    type = sa.Column(sa.String(512), nullable=False)
    number = sa.Column(sa.String(512), nullable=False)
    filename = sa.Column(sa.String(512), nullable=False)
    doc_location = sa.Column(sa.String(512), nullable=True)
    batch_timestamp = sa.Column(sa.DateTime, nullable=False)
    publication_date = sa.Column(sa.DateTime, nullable=True)
    json_metadata = sa.Column(sa.JSON, nullable=True)
    version_hash = sa.Column(sa.String(512))
    md5_hash = sa.Column(sa.String(512), nullable=True)
    is_ignored = sa.Column(sa.Boolean, default=False, nullable=False)


class PipelineJobSchema:
    "Schema for pipeline_jobs"

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(512))
    started_ts = sa.Column(sa.DateTime, nullable=False)
    finished_ts = sa.Column(sa.DateTime, nullable=True)
    sigkill_sent_ts = sa.Column(sa.DateTime, nullable=True)
    pid = sa.Column(sa.Integer, nullable=False)


class CrawlerStatusSchema:
    "Schema for pipeline_jobs"

    id = sa.Column(sa.Integer, primary_key=True)
    crawler_name = sa.Column(sa.String(512))
    status = sa.Column(sa.String(512))
    datetime = sa.Column(sa.DateTime, nullable=False)