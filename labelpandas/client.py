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
           
    def export_to_table(
        self, project, 
        include_metadata:bool=False, include_performance:bool=False, include_agreement:bool=False,
        verbose:bool=False, divider="///"):
        """ Creates a Pandas DataFrame given a Labelbox Projet ID
        Args:
            project                 :   Required (str / lablebox.Project) - Labelbox Project ID or lablebox.Project object to export labels from
            include_metadata        :   Optional (bool) - If included, exports metadata fields
            include_performance     :   Optional (bool) - If included, exports labeling performance
            include_agreement       :   Optional (bool) - If included, exports consensus scores       
            verbose                 :   Optional (bool) - If True, prints details about code execution; if False, prints minimal information
            divider                 :   Optional (str) - String delimiter for schema name keys and suffix added to duplocate global keys 
        """
        flattened_labels_dict = labelbase.downloader.export_and_flatten_labels(
            client=self.lb_client, project=project, 
            include_metadata=include_metadata, include_performance=include_performance, include_agreement=include_agreement,
            verbose=verbose, divider=divider
        )
        
        table = pd.DataFrame.from_dict(flattened_labels_dict)
        
        if verbose:
            print(f"Success: DataFrame generated")
        
        return table 

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
            verbose             :   Optional (bool) - If True, prints details about code execution; if False, prints minimal information
            divider             :   Optional (str) - String delimiter for schema name keys and suffix added to duplocate global keys
        """
        # Create a metadata_index, attachment_index, and annotation_index
        # row_data_col      : column with name "row_data"
        # global_key_col    : column with name "global_key" - defaults to row_data_col
        # external_id_col   : column with name "external_id" - defaults to global_key_col
        # project_id_col    : column with name "project_id" - defaults to "" (requires project_id input argument if no "project_id" column exists)
        # dataset_id_col    : column with name "dataset_id" - defaults to "" (requires project_id input argument if no "dataset_id" column exists)        
        # external_id_col   : column with name "external_id" - defaults to global_key_col        
        # metadata_index    : Dictonary where {key=metadata_field_name : value=metadata_type}
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
        
        # Create an upload dictionary where {
            # dataset_id : {
                # global_key : {
                    # "data_row" : {}, -- This is your data row upload as a dictionary
                    # "project_id" : "", -- This batches data rows to projects, if applicable
                    # "annotations" : [] -- List of annotations for a given data row, if applicable
                # }
            # }
        # }
        # This uniforms the upload to use labelbase - Labelbox base code for best practices
        
        upload_dict = labelpandas.uploader.create_upload_dict(
            client=self.lb_client, table=table, table_dict=table_dict, 
            row_data_col=row_data_col, global_key_col=global_key_col, external_id_col=external_id_col, 
            dataset_id_col=dataset_id_col, dataset_id=dataset_id, 
            project_id_col=project_id_col, project_id=project_id,
            metadata_index=metadata_index, attachment_index=attachment_index, annotation_index=annotation_index,
            upload_method=upload_method, divider=divider, verbose=verbose
        )      
        
        print(upload_dict)
                
        # Upload your data rows to Labelbox - update upload_dict if global keys are modified during upload
        data_row_upload_results, upload_dict = labelbase.uploader.batch_create_data_rows(
            client=self.lb_client, upload_dict=upload_dict, 
            skip_duplicates=skip_duplicates, divider=divider, verbose=verbose
        )
        
        # Bath to project attempt
        try:
            # If project ids are provided, we can batch data rows to projects
            if project_id or project_id_col:
                batch = True
                # Create a dictionary where {key=global_key : value=data_row_id}
                global_keys_list = []
                for dataset_id in upload_dict.keys():
                    for global_key in upload_dict[dataset_id].keys():
                        global_keys_list.append(global_key)
                global_key_to_data_row_id = labelbase.uploader.create_global_key_to_data_row_dict(
                    client=self.lb_client, global_keys=global_keys_list
                )          
                # Create a batch dictionary where {key=project_id : value=list_of_data_row_ids}      
                # Create an upload dictionary where {
                    # project_id : [list_of_data_row_ids]
                # }
                # This uniforms batches to use labelbase - Labelbox base code for best practices                
                project_id_to_batch_dict = {}                
                for dataset_id in upload_dict:
                    for global_key in upload_dict[dataset_id].keys():                    
                        project_id = upload_dict[dataset_id][global_key]["project_id"]
                        if project_id:
                            if project_id not in project_id_to_batch_dict.keys():
                                project_id_to_batch_dict[project_id] = []
                            data_row_id = global_key_to_data_row_id[global_key]                                
                            project_id_to_batch_dict[project_id].append(data_row_id)
                # Batch data rows to projects
                batch_to_project_results = labelbase.uploader.batch_rows_to_project(
                    client=self.lb_client, project_id_to_batch_dict=project_id_to_batch_dict, priority=priority, verbose=verbose
                )
            else:
                batch = "Data rows were not batched to any projects"                
                batch_to_project_results = []
        except Exception as e:
            batch = False
            batch_to_project_results = e
        
        # Annotation upload attempt
        try: # If we batched successfully and an upload_method was provided, upload annotations
            if (batch==True) and (upload_method in ["mal", "import"]) and (annotation_index!={}):
                # Create a dictionary where {
                    # project_id : [list_of_annotation_ndjsons]
                # }
                # This uniforms the upload to use labelbase - Labelbox base code for best practices                  
                project_id_to_upload_dict = {}
                for dataset_id in upload_dict.keys():
                    for global_key in upload_dict[dataset_id].keys():
                        project_id = upload_dict[dataset_id][global_key]["project_id"]
                        # Remember - the annotation list generated earlier doesn't have data row IDs, so here we add them in
                        annotations_no_data_row_id = upload_dict[dataset_id][global_key]["annotations"]
                        if project_id not in project_id_to_upload_dict.keys():
                            project_id_to_upload_dict[project_id] = []
                        if annotations_no_data_row_id: # For each annotation in the list, add the data row ID and add it to your annotation upload dict
                            for annotation in annotations_no_data_row_id:
                                annotation_data_row_id = annotation
                                annotation_data_row_id["dataRow"] = {"id" : global_key_to_data_row_id[global_key]}
                                project_id_to_upload_dict[project_id].append(annotation_data_row_id)
                # Upload your annotations to Labelbox
                annotation_upload_results = labelbase.uploader.batch_upload_annotations(
                    client=self.lb_client, project_id_to_upload_dict=project_id_to_upload_dict, how=upload_method, verbose=verbose
                )
            else:
                annotation_upload_results = "No annotation upload attempted"
        except Exception as e:
            annotation_upload_results = e
            
        return {
            "data_row_upload_results" : data_row_upload_results, 
            "batch_to_project_results" : batch_to_project_results,
            "annotation_upload_results" : annotation_upload_results
        }
    
    # def upsert_table_metadata():
    #     return table

    # def upsert_labelbox_metadata():
    #     return upload_results
