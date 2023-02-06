""" 
labels.py holds the function create_annotation_upload_dict() -- which creates the following style dictionary:
{
    project_id : 
        [
            annotation_ndjson,
            annotation_ndjson,
            annotation_ndjson     
        ],
    project_id : 
        [
            annotation_ndjson,
            annotation_ndjson,
            annotation_ndjson
        ]      
}
This is the format that labelbase.uploader.batch_upload_annotations() expects
"""
import pandas
import labelbase
from labelbox import Client as labelboxClient
from tqdm.autonotebook import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

def create_annotation_upload_dict(client:labelboxClient, table:pandas.core.frame.DataFrame, table_dict:dict,
                                  row_data_col:str, global_key_col:str, project_id_col:str, 
                                  project_id:str, annotation_index:dict, global_key_to_data_row_id:dict,
                                  divider:str="///", verbose:bool=False):
    """
    Args:
        client                      :   Required (labelbox.client.Client) - Labelbox Client object        
        table                       :   Required (pandas.core.frame.DataFrame) - Pandas DataFrame                
        table_dict                  :   Required (dict) - Pandas DataFrame as dict with df.to_dict("records")    
        row_data_col                :   Required (str) - Column containing asset URL or raw text
        global_key_col              :   Required (str) - Column name containing the data row global key - defaults to row data
        project_id_col              :   Required (str) - Column name containing the project ID to batch a given row to
        project_id                  :   Required (str) - Labelbox project ID to add data rows to - only necessary if no "project_id" column exists
        annotation_index            :   Required (dict) - Dictonary where {key=column_name : value=top_level_feature_name}
        global_key_to_data_row_id   :   Required (dict) - Dictionary where {key=global_key : value=data_row_id}
    Returns:
        
    """
    project_id_to_upload_dict = {project_id : [] for project_id in get_unique_values_function(table, project_id_col)}
    project_id_to_ontology = {}
    for project_id in project_id_to_upload_dict:
        ontology = client.get_project(project_id).ontology()
        project_id_to_ontology[project_id] = {
            "ontology_index" : labelbase.ontology.get_ontology_schema_to_name_path(ontology, divider=divider, invert=True, detailed=True),
            "schema_to_name_path" : labelbase.ontology.get_ontology_schema_to_name_path(ontology, divider=divider, invert=False, detailed=False)
        }
    if verbose:
        for row_dict in tqdm(table_dict):
            for column_name in annotation_index.keys():
                ndjsons = create_ndjsons(
                    data_row_id = global_key_to_data_row_id[global_key_col],
                    top_level_name=annotation_index[column_name],
                    annotation_values=row_dict[column_name],
                    ontology_index=project_id_to_ontology_index[row[project_id_col]],
                    divider=divider
                )
                for ndjson in ndjsons:
                    project_id_to_upload_dict[row[project_id_col]].append(ndjson)    
        for row_dict in table_dict:
            for column_name in annotation_index.keys():
                ndjsons = create_ndjsons(
                    data_row_id = global_key_to_data_row_id[global_key_col],
                    top_level_name=annotation_index[column_name],
                    annotation_values=row_dict[column_name],
                    ontology_index=project_id_to_ontology_index[row[project_id_col]],
                    divider=divider
                )
                for ndjson in ndjsons:
                    project_id_to_upload_dict[row[project_id_col]].append(ndjson)                              
    return project_id_to_upload_dict
