from labelbox import Client as labelboxClient
from labelbox.schema.dataset import Dataset as labelboxDataset
from labelbase.metadata import sync_metadata_fields
from labelbase import uploader
import pandas as pd
from labelpandas import connector

class Client():
    """
    Args:
        lb_api_key                  :   Required: labelbox.client.Client()
    Attributes:
        lb_client                   :   labelbox.Client object
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
           
    # def create_table_from_dataset(): 
    #     return table 

    def create_data_rows_from_table(
        self, table:pd.core.frame.DataFrame, lb_dataset:labelboxDataset, row_data_col:str, global_key_col=None, external_id_col=None,
        project_id_col:str="", priority=5, metadata_index:dict={}, attachment_index:dict={}, annotation_index:dict={}, upload_method:str="",
        local_files:bool=False, skip_duplicates:bool=False, verbose:bool=False, divider="___"):
        """ Creates Labelbox data rows given a Pandas table and a Labelbox Dataset
        Args:
            table               :   Required (pandas.core.frame.DataFrame) - Pandas DataFrame    
            lb_dataset          :   Required (labelbox.schema.dataset.Dataset) - Labelbox dataset to add data rows to            
            row_data_col        :   Required (str) - Column containing asset URL or file path
            local_files         :   Required (bool) - Determines how to handle row_data_col values
                                        If True, treats row_data_col values as file paths uploads the local files to Labelbox
                                        If False, treats row_data_col values as urls (assuming delegated access is set up)
            global_key_col      :   Optional (str) - Column name containing the data row global key - defaults to row_data_col
            external_id_col     :   Optional (str) - Column name containing the data row external ID - defaults to global_key_col
            project_id_col      :   Optional (str) - If provided, batches data rows to project ID in question
            priority            :   Optinoal (int) - Between 1 and 5, what priority to give to data row batches sent to projects
            metadata_index      :   Required (dict) - Dictionary where {key=column_name : value=metadata_type}
                                        metadata_type must be either "enum", "string", "datetime" or "number"
            attachment_index    :   Optional (dict) - Dictionary where {key=column_name : value=attachment_type}
                                        attachment_type must be one of "IMAGE", "VIDEO", "RAW_TEXT", "HTML", "TEXT_URL"
            annotation_index    :   Optional (dict) - Dictionary where {key=column_name : value=annotation_type} -- requires a project_id_col and an upload_method
                                        annotation_type must be one of the following - the format of the cell value must align with annotation type
                                                bbox    :   [[name_paths], [top, left, height, width], [name_paths], [top, left, height, width]]
                                                polygon :   [[name_paths], [(x, y), (x, y),...(x, y)], [name_paths], [(x, y), (x, y),...(x, y)]]
                                                point   :   [[name_paths], [x, y], [name_paths], [x, y]]
                                                mask    :   [[name_paths], URL], [name_paths], URL] OR [[name_paths], 2D_ARRAY], [name_paths], 2D_ARRAY]
                                                                - URL must be a publicly accessible string
                                                                - 2D_ARRAY must be a numpy array where mask values are the color (0,0)
                                                line    :   [[name_paths], [(x, y), (x, y),...(x, y)], [name_paths], [(x, y), (x, y),...(x, y)]]
                                                ner     :   [[name_paths], [start, end], [name_paths], [start, end]]
                                                radio   :   [name_paths]
                                                check   :   [name_paths]
                                                text    :   name_path, [text value]
                                        name_paths is parent///child///parent///child - you can specify the delimiter with the `divider` argument
                                        name_paths is passed as a list per annotation, since you can have multiple nested classifications in any given annotation
                                        for tools, you can have multiple annotations of the same class in a given data row, so your input is a list of name_paths and annotation values
            upload_method       :   Optional (str) - Either "mal" or "import" - required if an annotation_index is provided                                               
            skip_duplicates     :   Optional (bool) - Determines how to handle if a global key to-be-uploaded is already in use
                                        If True, will skip duplicate global_keys and not upload them
                                        If False, will generate a unique global_key with a suffix {divider} + "1", "2" and so on
            verbose             :   Required (bool) - If True, prints details about code execution; if False, prints minimal information
            divider             :   Optional (str) - String delimiter for schema name keys and suffix added to duplocate global keys
        Returns:
            A dictionary with "upload_results" and "conversion_errors" keys
            - "upload_results" key pertains to the results of the data row upload itself
            - "conversion_errors" key pertains to any errors related to data row conversion
        """    
        
        # Ensure all your metadata_index keys are metadata fields in Labelbox and that your Pandas DataFrame has all the right columns
        table = sync_metadata_fields(
            client=self.lb_client, table=table, get_columns_function=connector.get_columns_function, add_column_function=connector.add_column_function, 
            get_unique_values_function=connector.get_unique_values_function, metadata_index=metadata_index, verbose=verbose
        )
        
        # If df returns False, the sync failed - terminate the upload
        if type(table) == bool:
            return {
                "data_row_upload_results" : [], "data_row_conversion_errors" : [], 
                "batch_to_project_errors" : [], "annotation_upload_results" : [], "annotation_conversion_errors" : []
            }
        
        # Create a dictionary where {key=global_key : value=data_row_upload_dict} - this is unique to Pandas
        global_key_to_upload_dict, data_row_conversion_errors = connector.create_data_row_upload_dict(
            client=self.lb_client, table=table, row_data_col=row_data_col,
            global_key_col=global_key_col, external_id_col=external_id_col, metadata_index=metadata_index,
            attachment_index=attachment_index, local_files=local_files, divider=divider, verbose=verbose
        )
        
        # If there are conversion errors, let the user know; if there are no successful conversions, terminate the upload
        if data_row_conversion_errors:
            print(f'There were {len(data_row_conversion_errors)} errors in creating your upload list - see result["data_row_conversion_errors"] for more information')
            if global_key_to_upload_dict:
                print(f'Data row upload will continue')
            else:
                print(f'Data row upload will not continue')  
                    return {
                        "data_row_upload_results" : [], "data_row_conversion_errors" : data_row_conversion_errors, 
                        "batch_to_project_errors" : [], "annotation_upload_results" : [], "annotation_conversion_errors" : []
                    }
                
        # Upload your data rows to Labelbox
        data_row_upload_results = uploader.batch_create_data_rows(
            client=self.lb_client, dataset=lb_dataset, global_key_to_upload_dict=global_key_to_upload_dict, 
            skip_duplicates=skip_duplicates, divider=divider, verbose=verbose
        )
        
        # Default global_key_col if row_data_col not provided
        global_key_col = global_key_col if global_key_col else row_data_col
        
        # Create a dictionary where {key=global_key : value=data_row_id}
        global_key_to_data_row_id = uploader.create_global_key_to_data_row_dict(
            client=self.lb_client, global_keys=connector.get_unique_values_function(table, global_key_col)
        )
        
        # Create a dictionary where {key=project_id : value=list_of_data_row_ids}, if applicable
        project_id_to_batch_dict, batch_to_project_errors = connector.create_batches(
            client=self.lb_client, table=table, global_key_col=global_key_col, 
            project_id_col=project_id_col, global_key_to_data_row_id=global_key_to_data_row_id
        )
        
        # Batch data rows to projects, if applicable
        if not batch_to_project_errors:
            batch_to_project_errors = uploader.batch_rows_to_project(
                client=self.lb_client, project_id_to_batch_dict, priority=priority
            )
            
        # Create a dictionary where {key=project_id : value=annotation_upload_list}, if applicable
        project_id_to_upload_dict, annotation_conversion_errors = connector.create_annotation_upload_dict(
            client=self.lb_client, table=table, row_data_col=row_data_col, global_key_col=global_key_col, 
            project_id_col=project_id_col, annotation_index=annotation_index, divider=divider, verbose=verbose
        )
        
        # Upload your annotations to Labelbox, if applicable
        annotation_upload_results = uploader.batch_upload_annotations(
            client=self.lb_client, project_id_to_upload_dict=project_id_to_upload_dict, how=upload_method, verbose=verbose
        )
        
        return {
            "data_row_upload_results" : data_row_upload_results, 
            "data_row_conversion_errors" : data_row_conversion_errors,
            "batch_to_project_errors" : batch_to_project_errors,
            "annotation_upload_results" : annotation_upload_results,
            "annotation_conversion_errors" : annotation_conversion_errors
        }
    
    # def upsert_table_metadata():
    #     return table

    # def upsert_labelbox_metadata():
    #     return upload_results
