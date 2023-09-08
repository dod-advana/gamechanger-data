import pandas as pd
from dataPipelines.gc_ingest.tools.db.utils import CoreDBManager, DBType
from sqlalchemy import update, MetaData, Table, Column, TEXT, VARCHAR
import os
import subprocess

"""
    The purpose of this file is to upload icon data 
    related to each crawler from a specific excel spreadshet `excel_file_path`, and `image_folder_path` into:
    1. the s3 bucket folder `s3_prefix` (image)
    2. the postgres table `table_name` (metadata - s3 link, description)
"""

excel_file_path = '/home/gamechanger/de_test_scripts/icon_test_data/source_data_collection.xlsx'
image_folder_path = '/home/gamechanger/de_test_scripts/icon_test_data/'
table_name = "crawler_info"
s3_prefix = "s3://advana-data-zone/bronze/gamechanger/crawler_images/"

db_type = DBType('orch')
db_manager = CoreDBManager("", "")
db_engine = db_manager.get_db_engine(db_type=db_type)

# update_table_sql_statement = f"""
#     ALTER TABLE {table_name}
#     ADD blerb TEXT;
# """

# try:
#     with db_engine.connect() as connection:
#         connection.execute(update_table_sql_statement)
# except Exception as e:
#     print(f"Error updating table {table_name}: {str(e)}")

df = pd.read_excel(excel_file_path, engine='openpyxl')

required_columns = [
    'CRAWLER NAME',
    'DISPLAY NAME',
    'ICON',
    'BLERB',
]

missing_columns = [col for col in required_columns if col not in df.columns]

if missing_columns:
    print(f"Missing columns: {', '.join(missing_columns)}")
else:    
    for index, row in df.iterrows():
        crawler_name = row['CRAWLER NAME']
        display_name = row['DISPLAY NAME']
        icon_fname = str(row['ICON'])
        blerb = row['BLERB']

        if icon_fname != 'nan' and icon_fname.endswith('.png'):

            s3_image_link = s3_prefix + icon_fname

            icon_fname_local_file_path = os.path.join(image_folder_path, icon_fname)
            if os.path.exists(icon_fname_local_file_path):
                try:
                    list_files = subprocess.run([
                        "aws",
                        "s3",
                        "cp",
                        icon_fname_local_file_path,
                        s3_image_link,
                    ])
                except subprocess.CalledProcessError as e:
                    print(f"aws upload of the image icon {icon_fname} failed")
                except Exception as e:
                    print(f"An error occurred: {str(e)}")

            metadata_obj = MetaData()
            crawler_info_table = Table(
                table_name,
                metadata_obj,
                Column("image_link", TEXT),
                Column("blerb", TEXT),
                Column("crawler", VARCHAR(512))
            )
            
            insert_sql_statement = (
                update(crawler_info_table)
                .values(image_link=s3_image_link, blerb=blerb)
                .where(crawler_info_table.c.crawler == crawler_name)
            )
            
            # (f"""
            #     UPDATE {table_name}
            #     SET image_link = {s3_image_link}, blerb = {blerb}
            #     WHERE crawler = {crawler_name};
            # """)

            try:
                with db_engine.connect() as connection:
                    connection.execute(insert_sql_statement)
            except Exception as e:
                print(f"Error inserting data into {table_name}: {str(e)}")          
            