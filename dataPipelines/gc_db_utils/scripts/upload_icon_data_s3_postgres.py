import pandas as pd
from dataPipelines.gc_ingest.tools.db.utils import CoreDBManager, DBType
import os
import subprocess

"""
    The purpose of this file is to upload icon data 
    related to each crawler from a specific excel spreadshet `excel_file_path`, and `image_folder_path` into:
    1. the s3 bucket folder `s3_prefix` (image)
    2. the postgres table `table_name` (metadata - s3 link, description)
"""

excel_file_path = 'source data collection.xslx'
image_folder_path = 'icon_data/'
table_name = "crawler_info"
s3_prefix = "s3://advana-data-zone/bronze/gamechanger/crawler_images/"

db_type = DBType('orch')
db_manager = CoreDBManager("", "")
db_engine = db_manager.get_db_engine(db_type=db_type)

update_table_sql_statement = f"""
    ALTER TABLE {table_name}
    ADD blerb TEXT;
"""

try:
    with db_engine.connect() as connection:
        connection.execute(update_table_sql_statement)
except Exception as e:
    print(f"Error updating table {table_name}: {str(e)}")

df = pd.read_excel(excel_file_path)

required_columns = [
    'CRAWLER_NAME',
    'DISPLAY_NAME',
    'ICON',
    'BLERB',
]

missing_columns = [col for col in required_columns if col not in df.columns]

if missing_columns:
    print(f"Missing columns: {', '.join(missing_columns)}")
else:    
    for index, row in df.iterrows():
        crawler_name = row['CRAWLER_NAME']
        display_name = row['DISPLAY_NAME']
        icon_fname = row['ICON']
        blerb = row['BLERB']

        if len(icon_fname) > 0:

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

            insert_sql_statement = f"""
                UPDATE {table_name}
                SET image_link = {s3_image_link}, blerb = {blerb}
                WHERE crawler = {crawler_name};
            """

            try:
                with db_engine.connect() as connection:
                    connection.execute(table_name)
            except Exception as e:
                print(f"Error inserting data into {table_name}: {str(e)}")

            
            