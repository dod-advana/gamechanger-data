import psycopg2
from psycopg2.extras import RealDictCursor
from dataPipelines.gc_eda_pipeline.utils.eda_utils import read_extension_conf
import click


@click.command()
@click.option(
    '-s',
    '--staging-folder',
    help="A temp folder for which the eda data will be staged for processing.",
    required=False,
    type=str,
)
def run(staging_folder: str):
    print("Starting Gamechanger EDA Metrics Pipeline")
    # Load Extensions configuration files.
    data_conf_filter = read_extension_conf()


    sql_syn_old = "SELECT * FROM pds_parsed_validation.all_outgoing_counts_pdf_syn_xwalk_only"
    sql_syn_insert_new = "INSERT INTO pds_parsed_validation.all_outgoing_counts_pdf_syn_xwalk_only_new(pdf_filename, pdf_grouping, pdf_category, pdf_contract, pdf_ordernum, pdf_modification, syn_json_filename, syn_category, syn_contract, syn_ordernum, syn_modification, s3_loc, syn_xml_filename, syn_directory, syn_partition_path) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"

    sql_pds_old = "SELECT * FROM pds_parsed_validation.all_outgoing_counts_pdf_pds_xwalk_only"
    sql_pds_insert_new = "INSERT INTO pds_parsed_validation.all_outgoing_counts_pdf_pds_xwalk_only_new( pdf_filename, pdf_grouping, pdf_category, pdf_contract, pdf_ordernum, pdf_modification, pds_json_filename, pds_contract, pds_ordernum, pds_modification, s3_loc, pds_xml_filename, pds_directory, pds_partition_path) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
    

    conn = psycopg2.connect(host=data_conf_filter['eda']['database']['hostname'],
                            port=data_conf_filter['eda']['database']['port'],
                            user=data_conf_filter['eda']['database']['user'],
                            password=data_conf_filter['eda']['database']['password'],
                            dbname=data_conf_filter['eda']['database']['db'],
                            cursor_factory=psycopg2.extras.DictCursor)
    conn.autocommit = True
    cursor = conn.cursor()

    # cursor.execute(sql_syn_old)
    # syn_rows = cursor.fetchall()
    #
    # for syn_row in syn_rows:
    #     if syn_row['syn_filename']:
    #         pdf_filename = syn_row['pdf_filename']
    #         pdf_grouping = syn_row['pdf_grouping']
    #         pdf_category = syn_row['pdf_category']
    #         pdf_contract = syn_row['pdf_contract']
    #         pdf_ordernum = syn_row['pdf_ordernum']
    #         pdf_modification = syn_row['pdf_modification']
    #
    #         syn_json_filename = syn_row['syn_filename']
    #         syn_category = syn_row['syn_category']
    #         syn_contract = syn_row['syn_contract']
    #         syn_ordernum = syn_row['syn_ordernum']
    #         syn_modification = syn_row['syn_modification']
    #
    #         contact_metadata = syn_row['syn_contract']
    #         ordernum_metadata = syn_row['syn_ordernum']
    #
    #         prefix = ""
    #         if ordernum_metadata is not None and ordernum_metadata != "empty" and ordernum_metadata != "":
    #             prefix = contact_metadata + ordernum_metadata
    #         else:
    #             prefix = contact_metadata
    #
    #         s3_loc = "s3://advana-raw-zone/eda/syn/" + prefix + "/" + syn_json_filename
    #         print(s3_loc)
    #         syn_xml_filename = None
    #         syn_directory = None
    #         syn_partition_path = None
    #
    #         record_to_insert = (pdf_filename, pdf_grouping, pdf_category, pdf_contract, pdf_ordernum, pdf_modification, syn_json_filename, syn_category, syn_contract, syn_ordernum, syn_modification, s3_loc, syn_xml_filename, syn_directory, syn_partition_path)
    #
    #         cursor.execute(sql_syn_insert_new, record_to_insert)

    print("---------------------------")

    cursor.execute(sql_pds_old)
    pds_rows = cursor.fetchall()
    for pds_row in pds_rows:
        if pds_row['pds_filename']:
            pdf_filename = pds_row['pdf_filename']
            pdf_grouping = pds_row['pdf_grouping']
            pdf_category = pds_row['pdf_category']
            pdf_contract = pds_row['pdf_contract']
            pdf_ordernum = pds_row['pdf_ordernum']
            pdf_modification = pds_row['pdf_modification']

            pds_json_filename = pds_row['pds_filename']
            pds_contract = pds_row['pds_contract']
            pds_ordernum = pds_row['pds_ordernum']
            pds_modification = pds_row['pds_modification']

            contact_metadata = pds_row['pds_contract']
            ordernum_metadata = pds_row['pds_ordernum']

            prefix = ""
            if ordernum_metadata is not None and ordernum_metadata != "empty" and ordernum_metadata != "":
                prefix = contact_metadata + ordernum_metadata
            else:
                prefix = contact_metadata

            s3_loc = "s3://advana-raw-zone/eda/pds/" + prefix + "/" + pds_json_filename
            print(s3_loc)

            pds_xml_filename = None
            pds_directory = None
            pds_partition_path = None

            record_to_insert = (pdf_filename, pdf_grouping, pdf_category, pdf_contract, pdf_ordernum, pdf_modification, pds_json_filename, pds_contract, pds_ordernum, pds_modification, s3_loc, pds_xml_filename, pds_directory, pds_partition_path)

            cursor.execute(sql_pds_insert_new, record_to_insert)


    cursor.close()



    print("hello World")

if __name__ == '__main__':
    run()


