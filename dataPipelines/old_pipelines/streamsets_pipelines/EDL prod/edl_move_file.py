import os
from java.lang import Class
from java.sql import DriverManager, SQLException

for record in records:
    try:
        # source_filename = record.value['fname']
        # base_path = record.value['filepath'].replace('/opt/volumes/uploads', '')
        base_path = record.value['filepath'].replace('/opt/UA/volumes/uploads', '').replace('/opt/volumes/uploads', '')
        output_filename = os.path.basename(base_path)
        output_directory_name = os.path.dirname(base_path)

        ###This is the default input and output location
        default_output_path = '/data_zones/data_landing_zone/edl'
        default_input_path = '/apps/webapp/ExternalDataLoadUploads'
        system_name = str(record.value['system']).replace(' ', '_').replace(',', '').replace('-', '_').replace('(',
                                                                                                               '').replace(
            ')', '').lower()
        if (system_name == 'none'):
            record.value['hdfs_file_path'] = default_output_path + '/unsorted' + output_directory_name
            record.value['hdfs_file_system_dir'] = default_output_path + '/unsorted'
        else:
            record.value['hdfs_file_path'] = default_output_path + '/sorted/' + system_name + output_directory_name
            record.value['hdfs_file_system_dir'] = default_output_path + '/sorted/' + system_name
        record.value['input_file_path'] = default_input_path + output_directory_name
        #### COST system ####
        if (record.value['system'] == 'COST'):
            product_arr = record.value['product']
            if (',' in product_arr):
                product_info = product_arr.split(',')[0][1:-1]
            else:
                product_info = product_arr[2:-2]

            if (product_info == 'Cost Management - Enterprise'):
                record.value[
                    'hdfs_file_path'] = '/data_zones/raw_zone/CostManagement/DCMO_Cost_Raw_Ent/' + output_filename
                record.value['input_file_path'] = '/apps/webapp/ExternalDataLoadUploads' + base_path

            elif (product_info == 'Cost Management - IT'):
                record.value[
                    'hdfs_file_path'] = '/data_zones/raw_zone/CostManagement/DCMO_Cost_Raw_IT/' + output_filename
                record.value['input_file_path'] = '/apps/webapp/ExternalDataLoadUploads' + base_path

            elif (product_info == 'Cost Management - FM'):
                record.value[
                    'hdfs_file_path'] = '/data_zones/raw_zone/CostManagement/DCMO_Cost_Raw_FM/' + output_filename
                record.value['input_file_path'] = '/apps/webapp/ExternalDataLoadUploads' + base_path

            elif (product_info == 'Cost Management - Medical'):
                record.value[
                    'hdfs_file_path'] = '/data_zones/raw_zone/CostManagement/DCMO_Cost_Raw_Med/' + output_filename
                record.value['input_file_path'] = '/apps/webapp/ExternalDataLoadUploads' + base_path

            elif (product_info == 'Cost Management - Reference'):
                record.value[
                    'hdfs_file_path'] = '/data_zones/raw_zone/CostManagement/DCMO_Cost_Raw_REF/' + output_filename
                record.value['input_file_path'] = '/apps/webapp/ExternalDataLoadUploads' + base_path

            elif (product_info == 'Cost Management - Real Property'):
                record.value[
                    'hdfs_file_path'] = '/data_zones/raw_zone/CostManagement/DCMO_Cost_Raw_RP/' + output_filename
                record.value['input_file_path'] = '/apps/webapp/ExternalDataLoadUploads' + base_path
            elif (record.value['system'] == 'COST'):
                record.value[
                    'hdfs_file_path'] = '/data_zones/raw_zone/CostManagement/DCMO_Cost_Raw_Other/' + output_filename
                record.value['input_file_path'] = '/apps/webapp/ExternalDataLoadUploads' + base_path

        #### Budget Analytics product ####
        elif (record.value['system'] == 'OMB-MAX'):
            product_arr = record.value['product']
            if (',' in product_arr):
                product_info = product_arr.split(',')[0][1:-1]
            else:
                product_info = product_arr[2:-2]
            if (product_info == 'Budget Analytics' and record.value['filename'][0:12] == 'BA_132Daily_'):
                record.value[
                    'hdfs_file_path'] = '/data_zones/raw_zone/BudgetAnalytics/132_DailyFiles/' + output_filename
                record.value['input_file_path'] = '/apps/webapp/ExternalDataLoadUploads' + base_path

        ###### COVID Taskforce Daily uploaded datasets #####
        elif (record.value['system'] == 'COVID-taskforce'):
            ##### Carepoint data #####
            if ('_carepoint_mtfbedstatus.xlsx' in output_filename):
                record.value[
                    'hdfs_file_path'] = '/data_zones/raw_zone/carepoint/military_treatment_facility_bed_status_staging/' + output_filename
                record.value['input_file_path'] = '/apps/webapp/ExternalDataLoadUploads' + base_path
            ##### DoDCases data #####
            elif (output_filename.startswith('dodcases_')):
                record.value[
                    'hdfs_file_path'] = '/data_zones/raw_zone/covid_taskforce/dod_case_location_staging/' + output_filename
                record.value['input_file_path'] = '/apps/webapp/ExternalDataLoadUploads' + base_path
            ##### DMA data #####
            elif (output_filename.startswith('DOD_covid_JS_data_')):
                record.value[
                    'hdfs_file_path'] = '/data_zones/raw_zone/covid_taskforce/dod_casedata_dma_staging/' + output_filename
                record.value['input_file_path'] = '/apps/webapp/ExternalDataLoadUploads' + base_path
        ###### PBIS #####
        elif (record.value['system'] == 'PBIS'):
            ##### Allocation Table #####
            if ('PBIS_ALLOCATION_TABLE' in output_filename):
                record.value[
                    'hdfs_file_path'] = '/data_zones/raw_zone/PBIS/allocation_detail/allocation_table/latest/' + output_filename
                record.value['input_file_path'] = '/apps/webapp/ExternalDataLoadUploads' + base_path
            elif ('PBIS_WORKING_TABLE' in output_filename):
                record.value[
                    'hdfs_file_path'] = '/data_zones/raw_zone/PBIS/working_tables/pbis/latest/' + output_filename
                record.value['input_file_path'] = '/apps/webapp/ExternalDataLoadUploads' + base_path
            elif ('BOCS_WORKING_TABLE' in output_filename):
                record.value[
                    'hdfs_file_path'] = '/data_zones/raw_zone/PBIS/working_tables/bocs/latest/' + output_filename
                record.value['input_file_path'] = '/apps/webapp/ExternalDataLoadUploads' + base_path
            ##### Policy Analytics - Gamechanger clone files #####
        elif ((record.value['system'] in ["GAMECHANGER", "Policy Analytics"]) and (
                record.value['portfolio'].find('GAMECHANGER') > 0)):
            record.value['input_file_path'] = '/apps/webapp/ExternalDataLoadUploads' + base_path
            record.attributes['GAMECHANGER_CLONE'] = 'Yes'
        output.write(record)
    except Exception as e:
        # Send record to error
        error.write(record, str(e))