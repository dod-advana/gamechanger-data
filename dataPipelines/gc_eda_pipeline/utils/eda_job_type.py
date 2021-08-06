from enum import Enum


class EDAJobType(Enum):
    """
    :param NORMAL: Process New All Documents. If document as already been processed it will skip
    :param REINDEX: Generate the metadata and pull down the docparsed json, combines them
            and insert into Elasticsearch, if record has not been index, it will SKIP the entire process
    :parm REPROCESS: Reprocess, reprocess all stages
    """
    NORMAL = 'normal'
    REINDEX = 'reindex'
    REPROCESS = 'reprocess'