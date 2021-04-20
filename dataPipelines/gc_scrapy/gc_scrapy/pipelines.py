# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from datetime import datetime
import os
from scrapy.exceptions import DropItem
from jsonschema.exceptions import ValidationError

from .validators import DefaultOutputSchemaValidator, SchemaValidator
from . import OUTPUT_FOLDER_NAME

from dataPipelines.gc_crawler.utils import dict_to_sha256_hex_digest, get_fqdn_from_web_url


class AdditionalFieldsPipeline:
    def process_item(self, item, spider):

        item['crawler_used'] = spider.name

        source_page_url = item.get('source_page_url')
        if source_page_url is None:
            source_page_url = spider.start_urls[0]
            item['source_page_url'] = source_page_url

        if item.get('source_fqdn') is None:
            item['source_fqdn'] = get_fqdn_from_web_url(source_page_url)

        if item.get('version_hash') is None:
            item['version_hash'] = dict_to_sha256_hex_digest(
                item.get('version_hash_raw_data'))

        if item.get('access_timestamp') is None:
            item['access_timestamp'] = datetime.now().strftime(
                '%Y-%m-%d %H:%M:%S.%f')

        if item.get('publication_date') is None:
            item['publication_date'] = "N/A"

        if item.get('cac_login_required') is None:
            item['cac_login_required'] = spider.cac_login_required

        if item.get('doc_type') is None:
            item['doc_type'] = spider.doc_type

        return item


class ValidateJsonPipeline:
    """Validates json as Scrapy passes each item to be validated to self.process_item
    :param validator: output validator"""

    def __init__(self, validator: SchemaValidator = DefaultOutputSchemaValidator()):

        if not isinstance(validator, SchemaValidator):
            raise TypeError("arg: validator must be of type SchemaValidator")

        self.validator = validator

    def process_item(self, item, spider):
        item_dict = ItemAdapter(item).asdict()
        name = item_dict.get('doc_name', str(item_dict))

        try:
            self.validator.validate_dict(item_dict)
            return item
        except ValidationError as ve:
            raise DropItem(f'Dropped Item: {name} failed validation: {ve}')


class JsonWriterPipeline(object):
    def open_spider(self, spider):
        if not os.path.exists(OUTPUT_FOLDER_NAME):
            os.makedirs(OUTPUT_FOLDER_NAME)
        json_name = './' + OUTPUT_FOLDER_NAME + '/' + spider.name + '.json'

        self.file = open(json_name, 'w')
        # Your scraped items will be saved in the file 'scraped_items.json'.
        # You can change the filename to whatever you want.

    def close_spider(self, spider):
        self.file.close()

    def process_item(self, item, spider):
        doc = item['document']

        validator = DefaultOutputSchemaValidator()
        validator.validate(doc)
        self.file.write(doc + '\n')
        return doc
