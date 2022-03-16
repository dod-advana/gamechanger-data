import sqlalchemy as sa


class SnapshotEntrySchema:
    """Columns for document snapshot"""
    doc_id = sa.Column(sa.Integer, primary_key=True)
    pub_id = sa.Column(sa.Integer, nullable=False)
    pub_name = sa.Column(sa.String(512), nullable=False)
    pub_title = sa.Column(sa.String(512), nullable=False)
    pub_type = sa.Column(sa.String(512), nullable=False)
    pub_number = sa.Column(sa.String(512), nullable=False)
    pub_is_revoked = sa.Boolean(sa.Boolean)
    doc_filename = sa.Column(sa.String(512), nullable=True)
    doc_s3_location = sa.Column(sa.String(512), nullable=True)
    json_metadata = sa.Column(sa.JSON, nullable=True)
    upload_date = sa.Column(sa.TIMESTAMP, nullable=True)
    publication_date = sa.Column(sa.TIMESTAMP, nullable=True)


class DAFACharterMapSchema:
    """Schema for dafa_charter_map"""
    org_abbreviation = sa.Column(sa.String(512), primary_key=True, unique=True)
    org_name = sa.Column(sa.String(512), primary_key=True, unique=True)
    pub_id = sa.Column(sa.Integer, unique=True, nullable=True)


class DAFACharterMapFlattenedSchema:
    """Schema for flatted dafa_charter_map view"""
    org_abbreviation = sa.Column(sa.String(512), primary_key=True)
    org_name = sa.Column(sa.String(512), primary_key=True, unique=True)
    charter_pub_id = sa.Column(sa.Integer, nullable=True)
    pub_name = sa.Column(sa.String(512), nullable=True)
    pub_type = sa.Column(sa.String(512), nullable=True)
    pub_title = sa.Column(sa.String(512), nullable=True)
    publication_date = sa.Column(sa.TIMESTAMP, nullable=True)
