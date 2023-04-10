from labelbox import Client as labelboxClient
from labelpandas.uploader import create_upload_dict
from labelpandas.connector import get_col_names, get_unique_values
from labelbase.connector import validate_columns, determine_actions
from labelbase.uploader import create_global_key_to_data_row_dict, batch_create_data_rows, batch_rows_to_project, batch_upload_annotations
from labelbase.downloader import export_and_flatten_labels
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
        verbose:bool=False, mask_method:str="png", divider="///"):
        """ Creates a Pandas DataFrame given a Labelbox Projet ID
        Args:
            project                 :   Required (str / lablebox.Project) - Labelbox Project ID or lablebox.Project object to export labels from
            include_metadata        :   Optional (bool) - If included, exports metadata fields
            include_performance     :   Optional (bool) - If included, exports labeling performance
            include_agreement       :   Optional (bool) - If included, exports consensus scores       
            verbose                 :   Optional (bool) - If True, prints details about code execution; if False, prints minimal information
            mask_method             :   Optional (str) - Specifies your desired mask data format
                                            - "url" leaves masks as-is
                                            - "array" converts URLs to numpy arrays
                                            - "png" converts URLs to png byte strings             
            divider                 :   Optional (str) - String delimiter for schema name keys and suffix added to duplocate global keys 
        """
        flattened_labels_dict = export_and_flatten_labels(
            client=self.lb_client, project=project, 
            include_metadata=include_metadata, include_performance=include_performance, include_agreement=include_agreement,
            mask_method=mask_method, verbose=verbose, divider=divider
        )
        
        table = pd.DataFrame.from_dict(flattened_labels_dict)
        
        if verbose:
            print(f"Success: DataFrame generated")
        
        return table 

    def create_data_rows_from_table(
        self, table:pd.core.frame.DataFrame, dataset_id:str="", project_id:str="", priority:int=5, 
        upload_method:str="", skip_duplicates:bool=False, mask_method:str="png", verbose:bool=False, divider="///"):
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
            mask_method         :   Optional (str) - Specifies your input mask data format
                                        - "url" means your mask is an accessible URL (must provide color)
                                        - "array" means your mask is a numpy array (must provide color)
                                        - "png" means your mask value is a png-string                                           
            verbose             :   Optional (bool) - If True, prints details about code execution; if False, prints minimal information               
            divider             :   Optional (str) - String delimiter for schema name keys and suffix added to duplocate global keys
        """
        # Create/identify the following values:
            # row_data_col                :   Column representing asset URL, raw text, or path to local asset file
            # global_key_col              :   Defaults to row_data_col
            # external_id_col             :   Defaults to global_key_col
            # project_id_col              :   Either `project_id` or "" - overridden by arg for project_id        
            # dataset_id_col              :   Either `dataset_id` or "" - overridden by arg for dataset_id
            # model_id_col                :   Either `model_id` or "" - overridden by arg for model_id and any args for model_run_id
            # model_run_id_col            :   Either `model_run_id` or "" - overridden by arg for model_run_id        
            # metadata_index              :   Dictonary where {key=metadata_field_name : value=metadata_type} or {} if not uploading metadata
            # attachment_index            :   Dictonary where {key=column_name : value=attachment_type} or {} if not uploading attachments
            # annotation_index            :   Dictonary where {key=column_name : value=top_level_class_name} or {} if not uploading annotations
            # prediction_index            :   Dictonary where {key=column_name : value=top_level_class_name} or {}  if not uploading predictions
        x = validate_uploader_columns(
            client=self.lb_client, table=table,
            get_columns_function=get_col_names,
            get_unique_values_function=get_unique_values,
            divider=divider, verbose=verbose, extra_client=None
        )
        
        # Iterating over your pandas DataFrame is faster once converted to a list of dictionaries where {keys=column_names : value=row_column_values}
        table_dict = table.to_dict('records')
       
        
        # Determine the actions we're taking in this run
        create_action, batch_action, annotate_action, prediction_action = determine_actions(
            dataset_id=dataset_id, dataset_id_col=x["dataset_id_col"], project_id=project_id, project_id_col=x["project_id_col"], 
            model_id=model_id, model_id_col=x["model_id_col"], model_run_id=model_run_id, model_run_id_col=x["model_run_id_col"],
            upload_method=upload_method, annotation_index=x["annotation_index"], prediction_index=x["prediction_index"]
        )
        
        if not create_action:
            raise ValueError(f"No `dataset_id` argument or `dataset_id` column was provided in table to create data rows")
        
        # Create an upload dictionary where:
        # {
            # global_key : {
                # "data_row" : {}, -- This is your data row upload as a dictionary
                # "dataset_id" : "", -- This is the dataset a global_key should go to (or belongs to)
                # "project_id" : "", -- This batches data rows to projects, if applicable
                # "annotations" : [], -- List of annotations for a given data row, if applicable
                # "model_run_id" : "", -- This adds data rows to model runs, if applicable
                # "predictions" : [] -- List of predictions for a given data row, if applicable
            # }
        # }
        # This uniforms the upload to use labelbase - Labelbox base code for best practices
        upload_dict = create_upload_dict(
            client=self.lb_client, table=table, table_dict=table_dict, 
            row_data_col=x["row_data_col"], global_key_col=x["global_key_col"], external_id_col=x["external_id_col"], 
            dataset_id_col=x["dataset_id_col"], dataset_id=dataset_id, project_id_col=x["project_id_col"], project_id=project_id,
            metadata_index=x["metadata_index"], attachment_index=x["attachment_index"], annotation_index=x["annotation_index"],
            create_action=create_action, annotate_action=annotate_action, prediction_action=prediction_action,
            upload_method=upload_method, mask_method=mask_method, divider=divider, verbose=verbose
        )      
                
        # Upload your data rows to Labelbox - update upload_dict if global keys are modified during upload
        data_row_upload_results, upload_dict = batch_create_data_rows(
            client=self.lb_client, upload_dict=upload_dict, 
            skip_duplicates=skip_duplicates, divider=divider, verbose=verbose
        )
        
        # Bath to project attempt
        if batch_action: 
            try:
                # Create a dictionary where {key=global_key : value=data_row_id}
                global_key_to_data_row_id = create_global_key_to_data_row_dict(
                    client=self.lb_client, global_keys=list(upload_dict.keys())
                )     
                # Create batch dictionary where {key=project_id : value=[data_row_ids]}   
                project_id_to_batch_dict = {}                
                for global_key in upload_dict.keys():                  
                    project_id = upload_dict[global_key]["project_id"]
                    if project_id:
                        if project_id not in project_id_to_batch_dict.keys():
                            project_id_to_batch_dict[project_id] = []
                        project_id_to_batch_dict[project_id].append(global_key_to_data_row_id[global_key])
                # Labelbase command to batch data rows to projects
                batch_to_project_results = batch_rows_to_project(
                    client=self.lb_client, project_id_to_batch_dict=project_id_to_batch_dict, 
                    priority=priority, verbose=verbose
                )
            except Exception as e:
                annotate_action = False
                batch_to_project_results = e
        else:
            batch_to_project_results = []                
        
        # Annotation upload attempt
        if annotate_action:
            try:               
                # Create batch dictionary where {key=project_id : value=[data_row_ids]}
                project_id_to_upload_dict = {}
                for global_key in upload_dict.keys():
                    project_id = upload_dict[global_key]["project_id"]
                    annotations_no_data_row_id = upload_dict[global_key]["annotations"]
                    if annotations_no_data_row_id: 
                        if project_id not in project_id_to_upload_dict.keys():
                            project_id_to_upload_dict[project_id] = []
                        # Add data row ID to your annotations to-be-uploaded
                        for annotation in annotations_no_data_row_id:
                            annotation_data_row_id = annotation
                            annotation_data_row_id["dataRow"] = {"id" : global_key_to_data_row_id[global_key]}
                            project_id_to_upload_dict[project_id].append(annotation_data_row_id)
                # Labelbase command to upload annotations to projects
                annotation_upload_results = batch_upload_annotations(
                    client=self.lb_client, project_id_to_upload_dict=project_id_to_upload_dict, how=upload_method, verbose=verbose
                )
            except Exception as e:
                annotation_upload_results = e
        else:
            annotation_upload_results = []         
            
        # Annotation upload attempt
        if prediction_action:
            try:               
                # Create batch dictionary where {key=project_id : value=[data_row_ids]}
                model_run_id_to_upload_dict = {}
                for global_key in upload_dict.keys():
                    model_run_id = upload_dict[global_key]["model_run_id"]
                    predictions_no_data_row_id = upload_dict[global_key]["predictions"]
                    if annotations_no_data_row_id:
                        if model_run_id not in model_run_id_to_upload_dict.keys():
                            model_run_id_to_upload_dict[model_run_id] = []
                        if annotate_action:
                            project_id_to_upload_dict[model_run_id].extend(annotations)
                        for preidction in predictions_no_data_row_id:
                            prediction_data_row_id = annotation
                            prediction_data_row_id["dataRow"] = {"id" : global_key_to_data_row_id[global_key]}
                            model_run_id_to_upload_dict[model_run_id].append(prediction_data_row_id)
                # Labelbase command to upload annotations to projects
                annotation_upload_results = batch_upload_predictions(
                    client=self.lb_client, model_run_id_to_upload_dict=model_run_id_to_upload_dict, how=upload_method, verbose=verbose
                )
            except Exception as e:
                prediction_upload_results = e
        else:
            prediction_upload_results = []               
            
        return {
            "data_row_upload_results" : data_row_upload_results, 
            "batch_to_project_results" : batch_to_project_results,
            "annotation_upload_results" : annotation_upload_results,
            "prediction_upload_results" : prediction_upload_results
        }
    
    # def upsert_table_metadata():
    #     return table

    # def upsert_labelbox_metadata():
    #     return upload_results
