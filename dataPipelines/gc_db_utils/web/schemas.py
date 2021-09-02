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


class CloneMetaSchema:
    """Schema for clone_meta table"""
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    clone_name = sa.Column(sa.String(512), nullable=True)
    display_name = sa.Column(sa.String(512), nullable=True)
    is_live = sa.Boolean(sa.Boolean)
    url = sa.Column(sa.String(512), nullable=True)
    permissions_required = sa.Boolean(sa.Boolean)
    clone_to_advana = sa.Boolean(sa.Boolean)
    clone_to_gamechanger = sa.Boolean(sa.Boolean)
    clone_to_sipr = sa.Boolean(sa.Boolean)
    clone_to_jupiter = sa.Boolean(sa.Boolean)
    show_tutorial = sa.Boolean(sa.Boolean)
    show_graph = sa.Boolean(sa.Boolean)
    show_crowd_source = sa.Boolean(sa.Boolean)
    show_feedback = sa.Boolean(sa.Boolean)
    search_module = sa.Column(sa.String(512), nullable=True)
    export_module = sa.Column(sa.String(512), nullable=True)
    title_bar_module = sa.Column(sa.String(512), nullable=True)
    navigation_module = sa.Column(sa.String(512), nullable=True)
    card_module = sa.Column(sa.String(512), nullable=True)
    main_view_module = sa.Column(sa.String(512), nullable=True)
    graph_module = sa.Column(sa.String(512), nullable=True)
    search_bar_module = sa.Column(sa.String(512), nullable=True)
    s3_bucket = sa.Column(sa.String(512), nullable=True)
    data_source_name = sa.Column(sa.String(512), nullable=True)
    source_agency_name = sa.Column(sa.String(512), nullable=True)
    metadata_creation_group = sa.Column(sa.String(512), nullable=True)
    elasticsearch_index = sa.Column(sa.String(512), nullable=True)
    createdAt = sa.Column(sa.TIMESTAMP, nullable=True)
    updatedAt = sa.Column(sa.TIMESTAMP, nullable=True)
    needs_ingest = sa.Boolean(sa.Boolean)
    source_s3_prefix = sa.Column(sa.String(512), nullable=True)
    source_s3_bucket = sa.Column(sa.String(512), nullable=True)
