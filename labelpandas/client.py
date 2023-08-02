from labelbox import Client as labelboxClient
from labelpandas import uploader, connector
from labelbase.downloader import *
from labelbase.uploader import *
from labelbase.connector import *
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
        # Create a list of dictionaries where { key=column_name : value=row_value } using labelbase.downloader.export_and_flatten_labels
        flattened_labels_dict = export_and_flatten_labels(
            client=self.lb_client, project=project, include_metadata=include_metadata, 
            include_performance=include_performance, include_agreement=include_agreement,
            mask_method=mask_method, verbose=verbose, divider=divider
        )
        # Convert to a Pandas DataFrame
        table = pd.DataFrame.from_dict(flattened_labels_dict)
        if verbose:
            print(f"Success: DataFrame generated")
        return table 

    def create_data_rows_from_table(
        self, table:pd.core.frame.DataFrame, dataset_id:str="", project_id:str="", model_id:str="", model_run_id:str="", priority:int=5, 
        upload_method:str="", skip_duplicates:bool=False, mask_method:str="png", verbose:bool=False, divider="///"):
        """ Performs the following actions if proper information is provided:
                - creates data rows with metadata and attachments *
                - batches data rows to projects * **
                - uploads annotations as pre-labels or submitted labels * **
                - sends submitted labels to model runs as ground truth labels * ** ***
                - uploads predictions to a model run * ***
            * Requires a row_data AND dataset_id OR dataset_id_col
            ** Requires project_id OR project_id_col
            *** Requires model_id OR model_id_col OR model_run_id OR model_run_id_col
        Args:
            table               :   Required (pandas.core.frame.DataFrame) - Pandas DataFrame    
            dataset_id          :   Required (str) - Labelbox dataset ID to add data rows to - only necessary if no "dataset_id" column exists            
            project_id          :   Required (str) - Labelbox project ID to add data rows (and predictions) to - only necessary if no "project_id" column exists
            model_id            :   Required (str) - Labelbox model ID to add data rows, annotations and/or predictions to - will create a model run
            model_run_id        :   Required (str) - Labelbox model run ID to add data rows, annotations and/or predictions to - will use an existing model run
            priority            :   Optional (int) - Between 1 and 5, what priority to give to data row batches sent to projects                             
            upload_method       :   Optional (str) - Must be one of the following:
                                            "mal" - Project pre-labels (requires project ID)
                                            "import" - Project submitted labels (requires project ID)
                                            "ground-truth" - Project submitted labels AND ground truth submitted labels (requires project ID AND model / model run ID)
            skip_duplicates     :   Optional (bool) - Determines how to handle if a global key to-be-uploaded is already in use
                                        If True, will skip duplicate global_keys and not upload them
                                        If False, will generate a unique global_key with a suffix {divider} + "1", "2" and so on
            mask_method         :   Optional (str) - Specifies your input mask data format
                                        - "url" means your mask is an accessible URL (must provide color)
                                        - "array" means your mask is a numpy array (must provide color)
                                        - "png" means your mask value is a png-string                                           
            verbose             :   Optional (bool) - If True, prints details about code execution; if False, prints minimal information               
            divider             :   Optional (str) - String delimiter for schema name keys and suffix added to duplocate global keys
        Returns:
            Results from all performed actions in a dictionary - if an expected action has no results, it was not performed
        """
        # Confirm the existience of specific columns and construct reference indexes for different kinds of data to-be-uploaded using labelbase.connector.validate_columns
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
        x = validate_columns(
            client=self.lb_client, table=table,
            get_columns_function=connector.get_col_names,
            get_unique_values_function=connector.get_unique_values,
            divider=divider, verbose=verbose, extra_client=None
        )
        
        # Determine the actions we're taking in this run using labelbase.connector.determine_actions
        actions = determine_actions(
            row_data_col=x["row_data_col"], dataset_id=dataset_id, dataset_id_col=x["dataset_id_col"], project_id=project_id, 
            project_id_col=x["project_id_col"], model_id=model_id, model_id_col=x["model_id_col"], model_run_id=model_run_id, 
            model_run_id_col=x["model_run_id_col"], upload_method=upload_method, metadata_index=x["metadata_index"], 
            attachment_index=x["attachment_index"], annotation_index=x["annotation_index"], prediction_index=x["prediction_index"]
        )
        
        # Since this function's primary function is to create data rows, we raise an error if the create_action wasn't triggered
        if not actions["create"]:
            raise ValueError(f"No `dataset_id` argument or `dataset_id` column was provided in table to create data rows")
        
        # Iterating over your pandas DataFrame is faster once converted to a list of dictionaries where {keys=column_names : value=row_column_values}
        table_dict = table.to_dict('records')

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
        upload_dict = uploader.create_upload_dict( # Using labelpandas.uploader.create_upload_dict
            client=self.lb_client, table=table, table_dict=table_dict, 
            row_data_col=x["row_data_col"], global_key_col=x["global_key_col"], external_id_col=x["external_id_col"], 
            dataset_id_col=x["dataset_id_col"], dataset_id=dataset_id, 
            project_id_col=x["project_id_col"], project_id=project_id,
            model_id_col=x["model_id_col"], model_id=model_id, 
            model_run_id_col=x["model_run_id_col"], model_run_id=model_run_id,
            metadata_index=x["metadata_index"], attachment_index=x["attachment_index"], 
            annotation_index=x["annotation_index"], prediction_index=x["prediction_index"], batch_action=actions['batch'],
            create_action=actions["create"], annotate_action=actions["annotate"], prediction_action=actions["predictions"],
            upload_method=upload_method, mask_method=mask_method, divider=divider, verbose=verbose
        )
                
        # Upload your data rows to Labelbox, updating upload_dict if global keys are modified during upload using labelbase.uploader.batch_create_data_rows
        data_row_upload_results, upload_dict = batch_create_data_rows(
            client=self.lb_client, upload_dict=upload_dict, 
            skip_duplicates=skip_duplicates, divider=divider, verbose=verbose
        )
        
        # Bath to project attempt using labelbase.uploader.batch_rows_to_project
        if actions["batch"]:         
            batch_to_project_results = batch_rows_to_project(
                client=self.lb_client, upload_dict=upload_dict, 
                priority=priority, verbose=verbose
            )                
        else:
            batch_to_project_results = []
            
        # If performing actions that require data row IDs, we pull them here using labelbase.uploader.create_global_key_to_data_row_id_dict
        if actions["annotate"] or actions["predictions"]:
            global_key_to_data_row_id = create_global_key_to_data_row_id_dict(
                client=self.lb_client, global_keys=list(upload_dict.keys())
            )            
        
        # Annotation upload attempt using labelbase.uploader.batch_upload_annotations
        if actions["annotate"]:
            annotation_upload_results = batch_upload_annotations(
                client=self.lb_client, upload_dict=upload_dict, 
                global_key_to_data_row_id=global_key_to_data_row_id,
                how=actions["annotate"], verbose=verbose
            )
        else:
            annotation_upload_results = []

        # If model run upload attempt labelbase.uploader.batch_add_ground_truth_to_model_run
        if actions["annotate"] == "ground-truth":
            ground_truth_upload_results = batch_add_ground_truth_to_model_run(
                client=self.lb_client, upload_dict=upload_dict
            )
        else:
            ground_truth_upload_results = []
            
        # Prediction upload attempt using labelbase.uploader.batch_upload_predictions
        if actions["predictions"]:
            # If data rows aren't in the model run yet, add them with labelbase.uploader.batch_add_data_rows_to_model_run
            if not ground_truth_upload_results:
                data_row_to_model_run_results = batch_add_data_rows_to_model_run(
                    client=self.lb_client, upload_dict=upload_dict
                )
            prediction_upload_results = batch_upload_predictions(
                client=self.lb_client, upload_dict=upload_dict,
                global_key_to_data_row_id=global_key_to_data_row_id
            )
        else:
            data_row_to_model_run_results = []
            prediction_upload_results = []              

        return_payload = {
            "data_row_upload_results" : data_row_upload_results, 
            "batch_to_project_results" : batch_to_project_results,
            "annotation_upload_results" : annotation_upload_results,
            "ground_truth_upload_results" : ground_truth_upload_results,
            "data_row_to_model_run_results" : data_row_to_model_run_results,
            "prediction_upload_results" : prediction_upload_results
        }             

        return_payload = {k: v for k, v in return_payload.items() if v}
            
        return return_payload
    
    ## to do - add support for upserting metadata and upserting attachments
    # def upsert_data_rows_from_table(batch_data_rows:bool=False, anootation_method:str="", upsert_metadata:bool=False, upsert_attachments:bool=False):
    #     """
    #     Args:
    #         batch_data_rows     :   Optional (bool) - If True, will batch data rows to projects if not already in projects
    #         anootation_method   :   Optional (bool) -  Must be one of the following annotation import methods:
    #                                         "" - Does nothing with annotations
    #                                         "mal" - Uploaded to project as pre-labels
    #                                         "import" - Uploaded to project assubmitted labels
    #                                         "ground-truth" - Project submitted labels AND/OR ground truth submitted labels (will check existing project labels first)
    #         upsert_metadata     :   True if upserting metadata, False if not
    #         upsert_attachments  :   True if upserting attachments, False if not
    #     Returns:
    #         Results from all performed actions in a dictionary - if an expected action has no results, it was not performed
    #     """    
    def upsert_data_rows_from_table(self, table:pd.core.frame.DataFrame, dataset_id:str="", project_id:str="", model_id:str="", upload_method:str="", mask_method:str="png", priority:int=5, model_run_id:str="", batch_data_rows:bool=False, verbose:bool=False, divider:str="///"):
        """ Performs the following actions if proper information is provided:
                - batches data rows to projects (if batch_data_rows == True) * **
                - uploads annotations as pre-labels or submitted labels * **
                - sends submitted labels to model runs as ground truth labels * ** ***
                - uploads predictions to a model run * ***
            * Requires a global_key AND dataset_id OR dataset_id_col
            ** Requires project_id OR project_id_col
            *** Requires model_id OR model_id_col OR model_run_id OR model_run_id_col      
        Args:
            batch_data_rows     :   Optional (bool) - If True, will batch data rows to projects if not already in projects
            anootation_method   :   Optional (bool) -  Must be one of the following annotation import methods:
                                            "" - Does nothing with annotations
                                            "mal" - Uploaded to project as pre-labels
                                            "import" - Uploaded to project assubmitted labels
                                            "ground-truth" - Project submitted labels AND/OR ground truth submitted labels (will check existing project labels first)
            upsert_metadata     :   True if upserting metadata, False if not
            upsert_attachments  :   True if upserting attachments, False if not
        Returns:
            Results from all performed actions in a dictionary - if an expected action has no results, it was not performed
        """
        # Confirm the existience of specific columns and construct reference indexes for different kinds of data to-be-uploaded using labelbase.connector.validate_columns
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
        x = validate_columns(
            client=self.lb_client, table=table,
            get_columns_function=connector.get_col_names,
            get_unique_values_function=connector.get_unique_values,
            divider=divider, verbose=verbose, extra_client=None
        )
        
        # Determine the actions we're taking in this run using labelbase.connector.determine_actions
        actions = determine_actions(
            row_data_col=x["row_data_col"], dataset_id=dataset_id, dataset_id_col=x["dataset_id_col"], project_id=project_id, 
            project_id_col=x["project_id_col"], model_id=model_id, model_id_col=x["model_id_col"], model_run_id=model_run_id, 
            model_run_id_col=x["model_run_id_col"], upload_method=upload_method, metadata_index=x["metadata_index"], 
            attachment_index=x["attachment_index"], annotation_index=x["annotation_index"], prediction_index=x["prediction_index"]
        )

        # Iterating over your pandas DataFrame is faster once converted to a list of dictionaries where {keys=column_names : value=row_column_values}
        table_dict = table.to_dict('records')                
        
        # Create an upload dictionary where:
        # {
            # global_key : {
                # "project_id" : "", -- This batches data rows to projects, if applicable
                # "annotations" : [], -- List of annotations for a given data row, if applicable
                # "model_run_id" : "", -- This adds data rows to model runs, if applicable
                # "predictions" : [] -- List of predictions for a given data row, if applicable
            # }
        # }
        # This uniforms the upload to use labelbase - Labelbox base code for best practices
        upload_dict = uploader.create_upload_dict( # Using labelpandas.uploader.create_upload_dict
            client=self.lb_client, table=table, table_dict=table_dict, 
            row_data_col=x["row_data_col"], global_key_col=x["global_key_col"], external_id_col=x["external_id_col"], 
            dataset_id_col=x["dataset_id_col"], dataset_id=dataset_id, 
            project_id_col=x["project_id_col"], project_id=project_id,
            model_id_col=x["model_id_col"], model_id=model_id, 
            model_run_id_col=x["model_run_id_col"], model_run_id=model_run_id,
            metadata_index=x["metadata_index"], attachment_index=x["attachment_index"], 
            annotation_index=x["annotation_index"], prediction_index=x["prediction_index"], 
            create_action=actions["create"], annotate_action=actions["annotate"], prediction_action=actions["predictions"], batch_action=actions["batch"],
            upload_method=upload_method, mask_method=mask_method, divider=divider, verbose=verbose
        )

        # Bath to project attempt using labelbase.uploader.batch_rows_to_project
        if actions["batch"] and batch_data_rows:         
            batch_to_project_results = batch_rows_to_project(
                client=self.lb_client, upload_dict=upload_dict, priority=priority, verbose=verbose
            )                
        else:
            batch_to_project_results = []

        # Annotation upload attempt using labelbase.uploader.batch_upload_annotations
        if actions["annotate"]:
            annotation_upload_results = batch_upload_annotations(
                client=self.lb_client, upload_dict=upload_dict, how=actions["annotate"], verbose=verbose
            )
        else:
            annotation_upload_results = []

        # If model run upload attempt labelbase.uploader.batch_add_ground_truth_to_model_run
        if actions["annotate"] == "ground-truth":
            ground_truth_upload_results = batch_add_ground_truth_to_model_run(
                client=self.lb_client, upload_dict=upload_dict
            )
        else:
            ground_truth_upload_results = []
            
        # Prediction upload attempt using labelbase.uploader.batch_upload_predictions
        if actions["predictions"]:
            # If data rows aren't in the model run yet, add them with labelbase.uploader.batch_add_data_rows_to_model_run
            if not ground_truth_upload_results:
                data_row_to_model_run_results = batch_add_data_rows_to_model_run(
                    client=self.lb_client, upload_dict=upload_dict                    
                )
            prediction_upload_results = batch_upload_predictions(
                client=self.lb_client, upload_dict=upload_dict
            )
        else:
            data_row_to_model_run_results = []
            prediction_upload_results = []  

        return_payload = {
            "batch_to_project_results" : batch_to_project_results,
            "annotation_upload_results" : annotation_upload_results,
            "ground_truth_upload_results" : ground_truth_upload_results,
            "data_row_to_model_run_results" : data_row_to_model_run_results,
            "prediction_upload_results" : prediction_upload_results
        }             

        return_payload = {k: v for k, v in return_payload.items() if v}
            
        return return_payload        
    
