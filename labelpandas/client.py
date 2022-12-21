from labelbox import Client as labelboxClient
from labelbase import Client as labelbaseClient
from labelbox.schema.dataset import Dataset as labelboxDataset
import pandas as pd
from labelpandas import connector

class Client():
    """
    Args:
      pandas_dataframe    :   Required: pandas.core.frame.DataFrame() object
      lb_client           :   Required: labelbox.client.Client()
      lb_dataset          :   labelbox.schema.dataset.Dataset() object - if provided, will create data rows in this dataset
      row_data_col        :   Column name corresponding to file_path / URL
      external_id_col     :   Column name corresponding to external ID
      metadata_index      :   Creates metadata, dictionary where {key=metadata_field_name : value=metadata_type}, where metadata_type is one of "string", "number", "datetime", or "enum"
      attachment_index    :   Creates attachments, ictionary where {key=attachment_field_name : value=attachment_type}, where attachment_type is one of "image_row_data", "video_row_data", "text_row_data", "raw_text", or "html"
      verbose             :   If True, prints events

    Attributes:
        lb_client                   :   labelbox.Client object
        bq_client                   :   bigquery.Client object

    Key Functions:
        create_table_from_dataset   :   Creates a BigQuery table given a Labelbox dataset
        create_data_rows_from_table :   Creates Labelbox data rows (and metadata) given a BigQuery table
        upsert_table_metadata       :   Updates BigQuery table metadata columns given a Labelbox dataset
        upsert_labelbox_metadata    :   Updates Labelbox metadata given a BigQuery table
    """       
    def __init__(
        self,           
        lb_api_key:str=None,
        lb_endpoint='https://api.labelbox.com/graphql', 
        lb_enable_experimental=False, 
        lb_app_url="https://app.labelbox.com"):

        self.lb_client = labelboxClient(lb_api_key, endpoint=lb_endpoint, enable_experimental=lb_enable_experimental, app_url=lb_app_url)
        self.base_client = labelbaseClient(lb_api_key, lb_endpoint=lb_endpoint, lb_enable_experimental=lb_enable_experimental, lb_app_url=lb_app_url)
           
    # def create_table_from_dataset(): 
    #     return table 

    def create_data_rows_from_table(
        self,
        table:pd.core.frame.DataFrame,
        lb_dataset:labelboxDataset, 
        row_data_col:str, 
        local_files:bool=False,
        global_key_col:str="", 
        external_id_col:str="", 
        metadata_index:dict={}, 
        skip_duplicates:bool=False,
        divider="___",
        verbose:bool=False):
        """ Creates Labelbox data rows given a Pandas table and a Labelbox Dataset
        Args:
            table           :   Required (pandas.core.frame.DataFrame) - Pandas dataframe to-be-uploaded
            lb_dataset      :   Required (labelbox.schema.dataset.Dataset) - Labelbox dataset to add data rows to            
            row_data_col    :   Required (str) - Column name where the data row row data URL is located
            local_files     :   Required (bool) - If True, will create urls for local files / If False, treats the values in `row_data_col` as urls
            global_key_col  :   Optional (str) - Column name where the data row global key is located - defaults to the row_data column
            external_id_col :   Optional (str) - Column name where the data row external ID is located - defaults to the row_data column
            metadata_index  :   Optional (dict) - Dictionary where {key=column_name : value=metadata_type} - metadata_type must be one of "enum", "string", "datetime" or "number"
            skip_duplicates :   Optional (bool) - If True, will skip duplicate global_keys, otherwise will generate a unique global_key with a suffix "_1", "_2" and so on
            divider         :   Optional (str) - If skip_duplicates=False, uploader will auto-add a suffix to global keys to create unique ones, where new_global_key=old_global_key+divider+clone_counter
            verbose         :   Required (bool) - If True, prints information about code execution
        Returns:
            List of errors from data row upload - if successful, is an empty list
        """        
        check = self.base_client.enforce_metadata_index(metadata_index, verbose)
        if not check:
            return None
        table = self.base_client.sync_metadata_fields(table, get_columns_function, add_column_function, get_unique_values_function, metadata_index, verbose)
        if not table:
            return None
        global_key_col = global_key_col if global_key_col else row_data_col
        external_id_col = external_id_col if external_id_col else global_key_col

        metadata_schema_to_name_key = self.base_client.get_metadata_schema_to_name_key(lb_mdo=False, divider=divider, invert=False)
        metadata_name_key_to_schema = self.base_client.get_metadata_schema_to_name_key(lb_mdo=False, divider=divider, invert=True)

        global_key_to_upload_dict = {}
        futures = []
        with ThreadPoolExecutor() as exc:
            for index, row in table.iterrows():
                futures.append(exc.submit(connector.create_data_rows, local_files, self.lb_client, row, row_data_col, global_key_col, external_id_col, metadata_name_key_to_schema, metadata_index))
            for f in as_completed(futures):
                res = f.result()
                global_key_to_upload_dict[str(res[0])] = res[1]

        upload_results = self.base_client.batch_create_data_rows(lb_dataset, global_key_to_upload_dict, skip_duplicates, divider)

        return upload_results
    
    # def upsert_table_metadata():
    #     return table

    # def upsert_labelbox_metadata():
    #     return upload_results
