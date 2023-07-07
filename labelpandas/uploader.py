"""
uploader.py holds the function create_upload_dict() -- which creates the following style dictionary:
{
    global_key : {
        "data_row" : {}, -- This is your data row upload as a dictionary
        "dataset_id" : "" -- This is the dataset a global_key should go to (or belongs to)
        "project_id" : "", -- This batches data rows to projects, if applicable
        "annotations" : [], -- List of annotations for a given data row, if applicable
        "model_run_id" : "", -- This adds data rows to model runs, if applicable
        "predictions" : [] -- List of predictions for a given data row, if applicable
    },
    global_key : {
        "data_row" : {}, -- This is your data row upload as a dictionary
        "dataset_id" : "" -- This is the dataset a global_key should go to (or belongs to)
        "project_id" : "", -- This batches data rows to projects, if applicable
        "annotations" : [], -- List of annotations for a given data row, if applicable
        "model_run_id" : "", -- This adds data rows to model runs, if applicable
        "predictions" : [] -- List of predictions for a given data row, if applicable
    }    
}

This uniforms input formats so that they can leverage labelbase - Labelbox base code for best practices
"""

import pandas
from labelbox import Client as labelboxClient
from labelpandas.connector import get_table_length, get_unique_values
from labelbase.metadata import get_metadata_schema_to_name_key, process_metadata_value
from labelbase.ontology import get_ontology_schema_to_name_path
from labelbase.models import create_model_run_with_name
from labelbase.annotate import create_ndjsons
from concurrent.futures import ThreadPoolExecutor, as_completed

def create_upload_dict(client:labelboxClient, table: pandas.core.frame.DataFrame, table_dict:dict, 
                       row_data_col:str, global_key_col:str, external_id_col:str, 
                       dataset_id_col:str, dataset_id:str, project_id_col:str, project_id:str,
                       model_id_col:str, model_id:str, model_run_id_col:str, model_run_id:str,
                       metadata_index:dict, attachment_index:dict, annotation_index:dict, prediction_index:dict,
                       create_action, annotate_action, prediction_action, batch_action,
                       upload_method:str, mask_method:str, divider:str, verbose:bool, extra_client:bool=None):
    """
    Args:
        client                      :   Required (labelbox.client.Client) - Labelbox Client object        
        table                       :   Required (pandas.core.frame.DataFrame) - Pandas DataFrame                
        table_dict                  :   Required (dict) - Pandas DataFrame as dict with df.to_dict("records")
        row_data_col                :   Required (str) - Column containing asset URL or raw text
        global_key_col              :   Required (str) - Column name containing the data row global key - defaults to row data
        external_id_col             :   Required (str) - Column name containing the data row external ID - defaults to global key
        dataset_id_col              :   Required (str) - Column name containing the dataset ID to add data rows to
        dataset_id                  :   Required (str) - Labelbox dataset ID to add data rows to - only necessary if no "dataset_id" column exists            
        project_id_col              :   Required (str) - Column name containing the project ID to batch a given row to        
        project_id                  :   Required (str) - Labelbox project ID to add data rows to - only necessary if no "project_id" column exists
        model_id_col                :   Required (str) - Column name containing the model ID to add ground truth / predictions to (will create model runs)
        model_id                    :   Required (str) - Labelbox model ID to add ground truth / predictions to (will create a model run)
        model_run_id_col            :   Required (str) - Column name containing the model run ID to add ground truth / predictions to
        model_run_id                :   Required (str) - Labelbox model run ID to add ground truth / predictions to
        metadata_index              :   Required (dict) - Dictonary where {key=metadata_field_name : value=metadata_type}
        attachment_index            :   Required (dict) - Dictonary where {key=column_name : value=attachment_type}
        annotation_index            :   Required (dict) - Dictonary where {key=column_name : value=top_level_feature_name}
        prediction_index            :   Required (dict) - Dictonary where {key=column_name : value=top_level_feature_name}
        create_action               :   Required (bool) - If True, creates "data_row" key in upload_dict
        annotate_action             :   Required (str) - If any value, creates "annotations" key in the upload_dict
        prediction_action           :   Required (bool) - If True, creates "predictions" key in the upload_dict
        mask_method                 :   Optional (str) - Specifies your input mask data format
                                            - "url" means your mask is an accessible URL (must provide color)
                                            - "array" means your mask is a numpy array (must provide color)
                                            - "png" means your mask value is a png-string                 
        divider                     :   Required (str) - String delimiter for all name keys generated
        verbose                     :   Required (bool) - If True, prints details about code execution; if False, prints minimal information
        extra_client                :   Ignore this value - necessary for other labelbase integrations                
    Returns:
        - global_key_to_upload_dict - Dictionary in the above format
    """    
    # Check that global key column is entirely unique values
    table_length = get_table_length(table=table, extra_client=extra_client)
    if verbose:
        print(f'Creating upload list - {table_length} rows in Pandas DataFrame')
    # Get your global keys
    global_keys = get_unique_values(table=table, col=global_key_col, extra_client=extra_client)    
    if table_length != len(global_keys):
        print(f"Warning: Your global key column is not unique - upload will resume, only uploading 1 data row per unique global key")  
    # Get dictionaries where {key=metadata_name_key : value=metadata_schema_id}
    metadata_name_key_to_schema = get_metadata_schema_to_name_key(client=client, lb_mdo=False, divider=divider, invert=True) 
    # Get a list of project_ids
    if project_id != "":
        project_ids = [project_id]
    elif project_id_col != "":
        project_ids = get_unique_values(table=table, col=project_id_col, extra_client=extra_client)
    else:
        project_ids = []
    # Get dictionary where {key=project_id : value=ontology_index} 
    project_id_to_ontology_index = {}
    if annotate_action:
        for projectId in project_ids:
            ontology_index = get_ontology_schema_to_name_path(
                ontology=client.get_project(projectId).ontology(), 
                divider=divider, invert=True, detailed=True
            )
            ontology_index['project_type'] = str(client.get_project(projectId).media_type)
            project_id_to_ontology_index[projectId] = ontology_index
    # Get dictionary where {key=model_run_id : value=ontology_index}
    model_run_id_to_ontology_index = {}      
    # Get a dictionary where { key=model_id : value=model_run_id }    
    model_id_to_model_run_id = {}
    if prediction_action:
        if model_run_id != "": # If given a model_run_id, use it
            model_id = client.get_model_run(model_run_id).model_id
            model_id_to_model_run_id[model_id] = model_run_id
        elif model_run_id_col != "": # Else, use a model_run_id column if there is one
            model_run_ids = get_unique_values(table=table, col=model_run_id_col, extra_client=extra_client)
            for model_run_id in model_run_ids:
                model_id = client.get_model_run(model_run_id).model_id
                model_id_to_model_run_id[model_id] = model_run_id
        elif model_id != "": # Else, use a model_id keyword argument if there is one
            model = client.get_model(model_id)
            model_run = create_model_run_with_name(model=model)
            if verbose:
                print(f"Created model_run with name '{model_run.name}' for Labelbox Model with name {model.name}")
            model_id_to_model_run_id[model.uid] = model_run.uid
        elif model_id_col != "": # Else, use a model_id column if there is one
            model_ids = get_unique_values(table=table, col=model_id_col, extra_client=extra_client)
            for model_id in model_ids:
                model = client.get_model(model_id)
                model_run = create_model_run_with_name(model=model)
                if verbose:
                    print(f"Created model_run with name '{model_run.name}' for Labelbox Model with name {model.name}")                
                model_id_to_model_run_id[model.uid] = model_run.uid
        else:
            model_id_to_model_run_id = {}                                               
        for model_id in model_id_to_model_run_id.keys():
            model_run_id = model_id_to_model_run_id[model_id]
            ontology_index = get_ontology_schema_to_name_path(
                ontology=client.get_model(model_id).ontology(), divider=divider, invert=True, detailed=True
            )
            model_run_id_to_ontology_index[model_run_id] = ontology_index     
    # Multithread creating upload_dict global_key dictionaries
    upload_dict = {}
    with ThreadPoolExecutor(max_workers=8) as exc:
        futures = []
        for row_dict in table_dict:
            futures.append(exc.submit(
                create_upload, row_dict, row_data_col, global_key_col, external_id_col, 
                dataset_id_col, dataset_id, project_id_col, project_id, 
                model_id_col, model_id, model_run_id_col, model_run_id,
                metadata_index, attachment_index, annotation_index, prediction_index,
                project_id_to_ontology_index, model_run_id_to_ontology_index, model_id_to_model_run_id,
                create_action, annotate_action, prediction_action, batch_action,
                metadata_name_key_to_schema, upload_method, mask_method, divider, verbose 
            ))
        for f in as_completed(futures):
            res = f.result()
            global_key = str(res["data_row"]["global_key"])
            upload_dict[global_key] = {
                "data_row" : res["data_row"],
                "dataset_id" : res["dataset_id"],
                "project_id" : res["project_id"],
                "annotations" : res["annotations"],
                "model_run_id" : res["model_run_id"],
                "predictions" : res["predictions"]
            }
    if verbose:
        print(f'Upload generated')  
    return upload_dict

def create_upload(row_dict:dict, row_data_col:str, global_key_col:str, external_id_col:str, 
                  dataset_id_col:str, dataset_id:str, project_id_col:str, project_id:str,
                  model_id_col:str, model_id:str, model_run_id_col:str, model_run_id:str,
                  metadata_index:dict, attachment_index:dict, annotation_index:dict, prediction_index:dict,
                  project_id_to_ontology_index:dict, model_run_id_to_ontology_index:dict, model_id_to_model_run_id:dict, 
                  create_action:bool, annotate_action:bool, prediction_action:bool, batch_action:bool,
                  metadata_name_key_to_schema:dict, upload_method:str, mask_method:str, 
                  divider:str, verbose:bool):
    """ Takes a single table row as-a-dictinary and returns a dictionary where:
    {
        "data_row" : {
            "global_key" : "",                    |
            "row_data" : "",                      |
            "external_id" : "",                   | ---- This is your data row upload as a dictionary
            "metadata_fields" : [],               |
            "attachments" : []                    |
        }, -- This is your data row upload as a dictionary
        "dataset_id" : "" -- This is the dataset ID to upload this data row to, if applicable
        "project_id" : "", -- This batches data rows to projects, if applicable
        "annotations" : [], -- List of annotations for a given data row, if applicable
        "model_run_id" : "", -- This adds data rows to model runs, if applicable
        "predictions" : [] -- List of predictions for a given data row, if applicable
    }
    """
    # Determine dataset ID
    if dataset_id:
        datasetId = dataset_id
    elif dataset_id_col:
        datasetId = row_dict[dataset_id_col]
    else:
        datasetId = ""                                                                                
    # Determine project ID
    if project_id:
        projectId = project_id
    elif project_id_col:
        projectId = row_dict[project_id_col]
    else:
        projectId = ""
    # Determine model run ID - check for model run first, model second  + keyword arguments first, columns second, 
    if model_run_id:
        modelRunId = model_run_id
    elif model_run_id_col: 
        modelRunId = row_dict[model_run_id_col]
    elif model_id:
        modelRunId = model_id_to_model_run_id[model_id]                                                                               
    elif model_id_col:
        model_id = row_dict[model_id_col]                                                                 
        modelRunId = model_id_to_model_run_id[model_id]
    else:
        modelRunId = ""   
    # Create a base data row dictionary     
    data_row = {}
    if create_action or batch_action:    
        data_row["row_data"] = row_dict[row_data_col]
        data_row["global_key"] = row_dict[global_key_col]
        data_row["external_id"] = row_dict[external_id_col]
        # Create a list of metadata for a data row    
        metadata_fields = [{"schema_id" : metadata_name_key_to_schema['lb_integration_source'], "value" : "LabelPandas"}]
        if metadata_index:
            for metadata_field_name in metadata_index.keys():
                metadata_type = metadata_index[metadata_field_name]
                column_name = f"metadata{divider}{metadata_type}{divider}{metadata_field_name}"
                input_metadata = process_metadata_value(
                    metadata_value=row_dict[column_name], metadata_type=metadata_type, 
                    parent_name=metadata_field_name, metadata_name_key_to_schema=metadata_name_key_to_schema, divider=divider
                )            
                if input_metadata:
                    metadata_fields.append({"schema_id" : metadata_name_key_to_schema[metadata_field_name], "value" : input_metadata})
                else:
                    continue        
        data_row["metadata_fields"] = metadata_fields  
        # Create a list of attachments for a data row
        if attachment_index:
            data_row["attachments"] = [{"type" : attachment_index[column_name], "value" : row_dict[column_name]} for column_name in attachment_index]
    # Create a list of annotation ndjsons for a data row (does not include data row ID since data row has not been created)
    annotations = []        
    if annotate_action:
        ontology_index = project_id_to_ontology_index[projectId]
        for column_name in annotation_index.keys():
            annotations.extend(
                create_ndjsons(
                    top_level_name=annotation_index[column_name],
                    annotation_inputs=row_dict[column_name],
                    ontology_index=ontology_index,
                    confidence=False,
                    mask_method=mask_method,
                    divider=divider
                )
            )
    # Create a list of predictoin ndjsons for a data row (does not include data row ID since data row has not been created)
    predictions = []        
    if prediction_action:
        ontology_index = model_run_id_to_ontology_index[modelRunId]
        for column_name in prediction_index.keys():
            predictions.extend(
                create_ndjsons(
                    top_level_name=prediction_index[column_name],
                    annotation_inputs=row_dict[column_name],
                    ontology_index=ontology_index,
                    confidence=True,
                    mask_method=mask_method,
                    divider=divider
                )
            )                                                                                
    return {
        "data_row" : data_row,
        "project_id" : projectId,
        "dataset_id" : datasetId,
        "annotations" : annotations,
        "model_run_id" : modelRunId,
        "predictions" : predictions
    }
    
