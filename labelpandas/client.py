from labelbox import Client as labelboxClient
from labelbox.schema.dataset import Dataset as labelboxDataset
import labelpandas
import labelbase
import pandas as pd


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
        self, table:pd.core.frame.DataFrame, dataset_id:str="", project_id:str="", priority:int=5, 
        upload_method:str="", skip_duplicates:bool=False, verbose:bool=False, divider="///"):
        """ Creates Labelbox data rows given a Pandas table and a Labelbox Dataset
        Args:
            table               :   Required (pandas.core.frame.DataFrame) - Pandas DataFrame    
            dataset_id          :   Required (str) - Labelbox dataset ID to add data rows to - only necessary if no "dataset_id" column exists            
            project_id          :   Required (str) - Labelbox project ID to add data rows to - only necessary if no "project_id" column exists
            priority            :   Optinoal (int) - Between 1 and 5, what priority to give to data row batches sent to projects                             
            upload_method       :   Optional (str) - Either "mal" or "import" - required to upload annotations (otherwise leave as "")
            skip_duplicates     :   Optional (bool) - Determines how to handle if a global key to-be-uploaded is already in use
                                        If True, will skip duplicate global_keys and not upload them
                                        If False, will generate a unique global_key with a suffix {divider} + "1", "2" and so on
            verbose             :   Required (bool) - If True, prints details about code execution; if False, prints minimal information
            divider             :   Optional (str) - String delimiter for schema name keys and suffix added to duplocate global keys
        """
        # Create a metadata_index, attachment_index, and annotation_index
        # row_data_col      : column with name "row_data"
        # global_key_col    : column with name "global_key" - defaults to row_data_col
        # external_id_col   : column with name "external_id" - defaults to global_key_col
        # project_id_col    : column with name "project_id" - defaults to "" (requires project_id input argument if no "project_id" column exists)
        # dataset_id_col    : column with name "dataset_id" - defaults to "" (requires project_id input argument if no "dataset_id" column exists)        
        # external_id_col   : column with name "external_id" - defaults to global_key_col        
        # metadata_index    : Dictonary where {key=column_name : value=metadata_type}
        # attachment_index  : Dictonary where {key=column_name : value=attachment_type}
        # annotation_index  : Dictonary where {key=column_name : value=top_level_feature_name}
        row_data_col, global_key_col, external_id_col, project_id_col, dataset_id_col, metadata_index, attachment_index, annotation_index = labelbase.connector.validate_columns(
            client=self.lb_client,
            table=table,
            get_columns_function=labelpandas.connector.get_columns_function,
            get_unique_values_function=labelpandas.connector.get_unique_values_function,
            divider=divider,
            verbose=verbose,
            extra_client=None
        )
        
        # Iterating over your pandas DataFrame is faster once converted to a list of dictionaries where {key=column_name : value=row_value}
        table_dict = table.to_dict('records')
        
        if (dataset_id_col=="") and (dataset_id==""):
            raise ValueError(f"To create data rows, please provide either a `dataset_id` column or a Labelbox dataset id to argument `dataset_id`")
        
        if (upload_method!="") and (project_id_col=="") and (project_id=="") and (annotation_index!={}):
            raise ValueError(f"To upload annotations, please provide either a `project_id` column or a Lablebox project id to argument `project_id`")
        
        # Create a dictionary where {key=dataset_id : value={key=global_key : value=data_row_upload_dict}} - this is unique to Pandas
        dataset_to_global_key_to_upload_dict = labelpandas.data_rows.create_data_row_upload_dict(
            client=self.lb_client, table=table, table_dict=table_dict, 
            row_data_col=row_data_col, global_key_col=global_key_col, external_id_col=external_id_col, dataset_id_col=dataset_id_col,
            dataset_id=dataset_id, metadata_index=metadata_index, attachment_index=attachment_index, 
            divider=divider, verbose=verbose, extra_client=None
        )
                
        # Upload your data rows to Labelbox
        data_row_upload_results = labelbase.uploader.batch_create_data_rows(
            client=self.lb_client, dataset_to_global_key_to_upload_dict=dataset_to_global_key_to_upload_dict, 
            skip_duplicates=skip_duplicates, divider=divider, verbose=verbose
        )
        
        # If project ids are provided, we can batch data rows to projects
        if project_id or project_id_col:
            
            # Create a dictionary where {key=global_key : value=data_row_id}
            global_key_to_data_row_id = labelbase.uploader.create_global_key_to_data_row_dict(
                client=self.lb_client, global_keys=labelpandas.connector.get_unique_values_function(table, global_key_col)
            )            
            
            # Create a dictionary where {key=project_id : value=list_of_data_row_ids}, if applicable
            project_id_to_batch_dict = labelpandas.batches.create_batches_dict(
                client=self.lb_client, table=table, table_dict=table_dict,
                global_key_col=global_key_col, project_id_col=project_id_col, 
                global_key_to_data_row_id=global_key_to_data_row_id
            )
        
            # Batch data rows to projects, if applicable
            batch_to_project_results = labelbase.uploader.batch_rows_to_project(
                client=self.lb_client, project_id_to_batch_dict=project_id_to_batch_dict, priority=priority
            )
            
            if (upload_method in ["mal", "import"]) and (annotation_index!={}):
            
                # Create a dictionary where {key=project_id : value=annotation_upload_list}, if applicable
                project_id_to_upload_dict = labelpandas.labels.create_annotation_upload_dict(
                    client=self.lb_client, table=table, table_dict=table_dict,
                    row_data_col=row_data_col, global_key_col=global_key_col, project_id_col=project_id_col, 
                    project_id=project_id, annotation_index=annotation_index, global_key_to_data_row_id=global_key_to_data_row_id,
                    divider=divider, verbose=verbose
                )

                # Upload your annotations to Labelbox, if applicable
                annotation_upload_results = labelbase.uploader.batch_upload_annotations(
                    client=self.lb_client, project_id_to_upload_dict=project_id_to_upload_dict, how=upload_method, verbose=verbose
                )
                
            else: # If no proper upload_method is provided or annotation_index is generated, we don't upload annotations
                annotation_upload_results = []

        else: # If project ids are not provided, we don't batch data rows to projects or upload annotations
            batch_to_project_results = []
            annotation_upload_results = []
            
        return {
            "data_row_upload_results" : data_row_upload_results, 
            "batch_to_project_results" : batch_to_project_results,
            "annotation_upload_results" : annotation_upload_results
        }
    
    # def upsert_table_metadata():
    #     return table

    # def upsert_labelbox_metadata():
    #     return upload_results
