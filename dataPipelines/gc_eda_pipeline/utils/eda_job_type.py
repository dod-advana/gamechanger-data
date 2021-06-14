from enum import Enum


class EDAJobType(Enum):
    """
    :param NORMAL: Process New All Documents. If document as already been processed it will skip
    :param UPDATE_METADATA: Generate the metadata and pull down the docparsed json, combines them
            and insert into Elasticsearch, if record has not been index will do the entire process
    :parm REPROCESS: Reprocess, reprocess all stages
    """
    NORMAL = 'normal'
    UPDATE_METADATA = 'update_metadata'
    UPDATE_METADATA_SKIP_NEW = 'update_metadata_skip_new'
    REPROCESS = 'reprocess'