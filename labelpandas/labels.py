""" 
labels.py holds the function create_annotation_upload_dict() -- which creates the following style dictionary:
{
    project_id : 
        [
            annotation_ndjson,
            annotation_ndjson,
            annotation_ndjson,            
        ],
    project_id : 
        [
            annotation_ndjson,
            annotation_ndjson,
            annotation_ndjson,            
        ],              
}
This is the format that labelbase.uploader.batch_upload_annotations() expects
"""
import pandas
from labelbox import Client as labelboxClient

def create_annotation_upload_dict(client:labelboxClient, table:pandas.core.frame.DataFrame, row_data_col:str, global_key_col:str,
                                  project_id_col:str, annotation_index:dict, divider:str="///", verbose:bool=False):
    if not annotation_index:
        project_id_to_upload_dict = {}        
        errors = f"No annotation index provided - no annotations uploaded"
    else:
        try:
            project_id_to_upload_dict = {project_id : [] for project_id in get_unique_values_function(table, project_id_col)}
            for project_id in project_id_to_upload_dict:
                project_id_to_upload_dict[project_id] = []
                project_id_to_ontology_index[project_id] = get_ontology_schema_to_name_path(
                    ontology=client.get_project(project_id).ontology(), divider=divider, invert=True
                )
            if verbose:
                for index, row in tqdm(table.iterrows()):
                    for column_name in annotation_index.keys():
                        ndjsons = create_ndjsons(
                            annotation_values=row[column_name], 
                            annotation_type=annotation_index[column_name],
                            ontology_index=project_id_to_ontology_index[row[project_id_col]],
                            divide=divider
                        )
                        for ndjson in ndjsons:
                            project_id_to_upload_dict[row[project_id_col]].append(ndjson)    
                for index, row in table.iterrows():
                    for column_name in annotation_index.keys():
                        ndjsons = create_ndjsons(
                            annotation_values=row[column_name], 
                            annotation_type=annotation_index[column_name],
                            ontology_index=project_id_to_ontology_index[row[project_id_col]],
                            divide=divider
                        )
                        for ndjson in ndjsons:
                            project_id_to_upload_dict[row[project_id_col]].append(ndjson)                              
        except Exception as e:
            errors = e
    return project_id_to_upload_dict, errors
