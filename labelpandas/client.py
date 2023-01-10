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
        create_data_rows_from_table :   Creates Labelbox data rows (and metadata) given a Pandas DataFrame an an existing Labelbox Dataset
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
        self, table:pd.core.frame.DataFrame, lb_dataset:labelboxDataset, row_data_col:str, global_key_col=None, external_id_col=None,
        metadata_index:dict={}, local_files:bool=False, skip_duplicates:bool=False, verbose:bool=False, divider="___"):
        """ Creates Labelbox data rows given a Pandas table and a Labelbox Dataset
        Args:
            table           :   Required (pandas.core.frame.DataFrame) - Pandas DataFrame    
            lb_dataset      :   Required (labelbox.schema.dataset.Dataset) - Labelbox dataset to add data rows to            
            row_data_col    :   Required (str) - Column containing asset URL or file path
            local_files     :   Required (bool) - Determines how to handle row_data_col values
                                    If True, treats row_data_col values as file paths uploads the local files to Labelbox
                                    If False, treats row_data_col values as urls (assuming delegated access is set up)
            global_key_col  :   Optional (str) - Column name containing the data row global key - defaults to row_data_col
            external_id_col :   Optional (str) - Column name containing the data row external ID - defaults to global_key_col
            metadata_index  :   Required (dict) - Dictionary where {key=column_name : value=metadata_type}
                                    metadata_type must be either "enum", "string", "datetime" or "number"
            skip_duplicates :   Optional (bool) - Determines how to handle if a global key to-be-uploaded is already in use
                                    If True, will skip duplicate global_keys and not upload them
                                    If False, will generate a unique global_key with a suffix "_1", "_2" and so on
            verbose         :   Required (bool) - If True, prints details about code execution; if False, prints minimal information
            divider         :   Optional (str) - String delimiter for all name keys generated for parent/child schemas
        Returns:
            A dictionary with "upload_results" and "conversion_errors" keys
            - "upload_results" key pertains to the results of the data row upload itself
            - "conversion_errors" key pertains to any errors related to data row conversion
        """    
        
        # Ensure all your metadata_index keys are metadata fields in Labelbox and that your Pandas DataFrame has all the right columns
        table = self.base_client.sync_metadata_fields(
            table=table, get_columns_function=connector.get_columns_function, add_column_function=connector.add_column_function, 
            get_unique_values_function=connector.get_unique_values_function, metadata_index=metadata_index, verbose=verbose
        )
        
        # If df returns False, the sync failed - terminate the upload
        if type(table) == bool:
            return {"upload_results" : [], "conversion_errors" : []}
        
        # Create a dictionary where {key=global_key : value=labelbox_upload_dictionary} - this is unique to Pandas
        global_key_to_upload_dict, conversion_errors = connector.create_upload_dict(
            table=table, lb_client=self.lb_client, base_client=self.base_client,
            row_data_col=row_data_col, global_key_col=global_key_col, external_id_col=external_id_col, 
            metadata_index=metadata_index, local_files=local_files, divider=divider, verbose=verbose
        )
        
        # If there are conversion errors, let the user know; if there are no successful conversions, terminate the upload
        if conversion_errors:
            print(f'There were {len(conversion_errors)} errors in creating your upload list - see result["conversion_errors"] for more information')
            if global_key_to_upload_dict:
                print(f'Data row upload will continue')
            else:
                print(f'Data row upload will not continue')  
                return {"upload_results" : [], "conversion_errors" : errors}
                
        # Upload your data rows to Labelbox
        upload_results = self.base_client.batch_create_data_rows(
            dataset=lb_dataset, global_key_to_upload_dict=global_key_to_upload_dict, 
            skip_duplicates=skip_duplicates, divider=divider, verbose=verbose
        )
        
        return {"upload_results" : upload_results, "conversion_errors" : conversion_errors}
    
    # def upsert_table_metadata():
    #     return table

    # def upsert_labelbox_metadata():
    #     return upload_results
