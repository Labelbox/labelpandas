"""
uploader.py holds the function create_upload_dict() -- which creates the following style dictionary:
{
    dataset_id : {
        global_key : {
            "data_row" : {}, -- This is your data row upload as a dictionary
            "project_id" : "", -- This batches data rows to projects, if applicable
            "annotations" : [] -- List of annotations for a given data row, if applicable -- note this does not contain required data row ID information
        }
        global_key : {
            "data_row" : {},
            "project_id" : "",
            "annotations" : []
        }
    },
    dataset_id : {
        global_key : {
            "data_row" : {},
            "project_id" : "",
            "annotations" : []
        }
        global_key : {
            "data_row" : {},
            "project_id" : "",
            "annotations" : []
        }
    }
}

This uniforms input formats so that they can leverage labelbase - Labelbox base code for best practices
"""

import pandas
from labelbox import Client as labelboxClient
from labelpandas import connector
import labelbase
from concurrent.futures import ThreadPoolExecutor, as_completed

def create_upload_dict(client:labelboxClient, table: pandas.core.frame.DataFrame, table_dict:dict, 
                       row_data_col:str, global_key_col:str, external_id_col:str, 
                       dataset_id_col:str, dataset_id:str,
                       project_id_col:str, project_id:str,
                       metadata_index:dict, attachment_index:dict, annotation_index:dict,
                       upload_method:str, divider:str, verbose:bool, extra_client:bool=None):
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
        metadata_index              :   Required (dict) - Dictonary where {key=metadata_field_name : value=metadata_type}
        attachment_index            :   Required (dict) - Dictonary where {key=column_name : value=attachment_type}
        annotation_index            :   Required (dict) - Dictonary where {key=column_name : value=top_level_feature_name}
        upload_method               :   Required (str) - Either "mal" or "import" - required to upload annotations (otherwise leave as "")
        divider                     :   Required (str) - String delimiter for all name keys generated
        verbose                     :   Required (bool) - If True, prints details about code execution; if False, prints minimal information
        extra_client                :   Ignore this value - necessary for other labelbase integrations                
    Returns:
        Two values:
        - global_key_to_upload_dict - Dictionary where {key=global_key : value=data row dictionary in upload format}
        - errors - List of dictionaries containing conversion error information; see connector.create_data_rows() for more information
    """    
    # Check that global key column is entirely unique values
    table_length = connector.get_table_length_function(table=table, extra_client=extra_client)
    if verbose:
        print(f'Creating upload list - {table_length} rows in Pandas DataFrame')
    unique_global_key_count = len(connector.get_unique_values_function(table=table, column_name=global_key_col, extra_client=extra_client))
    if table_length != unique_global_key_count:
        print(f"Warning: Your global key column is not unique - upload will resume, only uploading 1 data row per unique global key")  
    # Get dictionaries where {key=metadata_name_key : value=metadata_schema_id}
    metadata_name_key_to_schema = labelbase.metadata.get_metadata_schema_to_name_key(client=client, lb_mdo=False, divider=divider, invert=True) 
    # Get dictionary where {key=project_id : value=ontology_index} -- index created by labelbase -- if project IDs are available
    if project_id != "":
        project_ids = [project_id]
    elif project_id_col != "":
        project_ids = connector.get_unique_values_function(table=table, column_name=project_id_col, extra_client=extra_client)
    else:
        project_ids = []
    project_id_to_ontology_index = {}
    if (project_ids!=[]) and (annotation_index!={}) and (upload_method in ["mal", "import"]): # If we're uploading annotations
        for projectId in project_ids:
            ontology_index = labelbase.ontology.get_ontology_schema_to_name_path(
                ontology=client.get_project(projectId).ontology(), 
                divider=divider, invert=True, detailed=True
            )
            project_id_to_ontology_index[projectId] = ontology_index
    print(project_id_to_ontology_index)
    # Initiate your upload dict, where they keys are all your dataset IDs
    if dataset_id:
        upload_dict = {dataset_id : {}}
    else:
        upload_dict = {id : {} for id in connector.get_unique_values_function(table=table, column_name=dataset_id_col)}    
    with ThreadPoolExecutor(max_workers=8) as exc:
        futures = []
        for row_dict in table_dict:
            futures.append(exc.submit(
                create_upload, row_dict, row_data_col, global_key_col, external_id_col, dataset_id_col, dataset_id,
                project_id_col, project_id, metadata_index, attachment_index, annotation_index, 
                project_id_to_ontology_index, metadata_name_key_to_schema, upload_method, divider, verbose 
            ))
        for f in as_completed(futures):
            res = f.result()
            dataRow = res["data_row"]
            global_key = str(dataRow["global_key"])
            upload_dict[res["dataset_id"]][global_key] = {
                "data_row" : dataRow,
                "project_id" : res["project_id"],
                "annotations" : res["annotations"]
            }
    return upload_dict

def create_upload(row_dict:dict, 
                  row_data_col:str, global_key_col:str, external_id_col:str, 
                  dataset_id_col:str, dataset_id:str,
                  project_id_col:str, project_id:str,
                  metadata_index:dict, attachment_index:dict, annotation_index:dict, 
                  project_id_to_ontology_index:dict, metadata_name_key_to_schema:dict,
                  upload_method:str, divider:str, verbose:bool):
    """ Takes a row as-a-dictinary and returns a dictionary where:
    {
        "data_row" : {
            "global_key" : "",
            "row_data" : "",
            "external_id" : "",
            "metadata_fields" : [],
            "attachments" : []
        }, -- This is your data row upload as a dictionary
        "dataset_id" : "" -- This is the dataset ID to upload this data row to
        "project_id" : "", -- This batches data rows to projects, if applicable
        "annotations" : [] -- List of annotations for a given data row, if applicable (note that data row ID is not included)
    }
    """
    # Determine project ID and dataset ID
    datasetId = dataset_id if dataset_id else row_dict[dataset_id_col]
    if project_id == project_id_col == "":
        projectId = ""
    else:
        projectId = project_id if project_id else row_dict[project_id_col]
    # Create a base data row dictionary
    data_row = {
        "row_data" : row_dict[row_data_col],
        "global_key" : row_dict[global_key_col],
        "external_id" : row_dict[external_id_col],
    }
    # Create a list of metadata for a data row    
    metadata_fields = [{"schema_id" : metadata_name_key_to_schema['lb_integration_source'], "value" : "LabelPandas"}]
    if metadata_index:
        for metadata_field_name in metadata_index.keys():
            metadata_type = metadata_index[metadata_field_name]
            column_name = f"metadata{divider}{metadata_type}{divider}{metadata_field_name}"
            input_metadata = labelbase.metadata.process_metadata_value(
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
    if (annotation_index!={}) and (project_id_to_ontology_index!={}) and (upload_method in ["mal", "import"]):
        ontology_index = project_id_to_ontology_index[projectId]
        for column_name in annotation_index.keys():
            annotations.extend(
                labelbase.annotate.create_ndjsons(
                    top_level_name=annotation_index[column_name],
                    annotation_inputs=row_dict[column_name],
                    ontology_index=ontology_index,
                    divider=divider
                )
            )
    return {
        "data_row" : data_row,
        "project_id" : projectId,
        "dataset_id" : datasetId,
        "annotations" : annotations
    }
    
