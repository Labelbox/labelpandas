from labelbox import Client as labelboxClient
from labelbase import Client as labelbaseClient
from labelbox.schema.dataset import Dataset as labelboxDataset
import pandas as pd
from labelpandas import connector

class Client():
    """
    Args:
        lb_api_key                  :   Required: labelbox.client.Client()
    Attributes:
        lb_client                   :   labelbox.Client object
        base_client                 :   labelbase.Client object
    Key Functions:
        create_data_rows_from_table :   Creates Labelbox data rows (and metadata) given a Pandas DataFrame
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
        self, df:pd.core.frame.DataFrame, lb_dataset:labelboxDataset, row_data_col:str, global_key_col=None, external_id_col=None,
        metadata_index:dict={}, local_files:bool=False, skip_duplicates:bool=False, verbose:bool=False, divider="___"):
        """ Creates Labelbox data rows given a Pandas table and a Labelbox Dataset
        Args:
            df              :   Required (pandas.core.frame.DataFrame) - Pandas DataFrame    
            lb_dataset      :   Required (labelbox.schema.dataset.Dataset) - Labelbox dataset to add data rows to            
            row_data_col    :   Required (str) - Column containing asset URL or file path
            local_files     :   Required (bool) - If True, will create urls for local files; if False, uploads `row_data_col` as urls
            global_key_col  :   Optional (str) - Column name containing the data row global key - defaults to row data
            external_id_col :   Optional (str) - Column name containing the data row external ID - defaults to global key
            metadata_index  :   Required (dict) - Dictionary where {key=column_name : value=metadata_type} - metadata_type = "enum", "string", "datetime" or "number"
            skip_duplicates :   Optional (bool) - If True, will skip duplicate global_keys, otherwise will generate a unique global_key with a suffix "_1", "_2" and so on
            verbose         :   Required (bool) - If True, prints information about code execution
            divider         :   Optional (str) - String delimiter for all name keys generated                    
        Returns:
            List of errors from data row upload - if successful, is an empty list
        """    
        
        # Ensure all your metadata_index keys are metadata fields in Labelbox and that your Pandas DataFrame has all the right columns
        df = self.base_client.sync_metadata_fields(
            table=df, get_columns_function=connector.get_columns_function, add_column_function=connector.add_column_function, 
            get_unique_values_function=connector.get_unique_values_function, metadata_index=metadata_index, verbose=verbose
        )
        
        # If df returns False, the sync failed
        if type(df) == bool:
            return None   
        
        # Create a dictionary where {key=global_key : value=labelbox_upload_dictionary} - this is unique to Pandas
        global_key_to_upload_dict = connector.create_upload_dict(
            df=df, lb_client=self.lb_client, base_client=self.base_client,
            row_data_col=row_data_col, global_key_col=global_key_col, external_id_col=external_id_col, 
            metadata_index=metadata_index, local_files=local_files, divider=divider, verbose=verbose
        )
                
        # Upload your data rows to Labelbox
        upload_results = self.base_client.batch_create_data_rows(
            dataset=lb_dataset, global_key_to_upload_dict=global_key_to_upload_dict, 
            skip_duplicates=skip_duplicates, divider=divider, verbose=verbose
        )

        return upload_results
    
    # def upsert_table_metadata():
    #     return table

    # def upsert_labelbox_metadata():
    #     return upload_results
