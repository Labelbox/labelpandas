""" 
batches.py holds the function create_batches_dict() -- which creates the following style dictionary:
{
    project_id : 
        [
            data_row_id,
            data_row_id,
            data_row_id,            
        ],
    project_id : 
        [
            data_row_id,
            data_row_id,
            data_row_id,            
        ]
}
This is the format that labelbase.uploader.batch_rows_to_project() expects
"""
import pandas

def create_batches_dict(table: pandas.core.frame.DataFrame, table_dict:dict, 
                        global_key_col:str, project_id_col:str, 
                        project_id:str, global_key_to_data_row_id:dict):
    """ From a Pandas DataFrame, creates a dictionary where {key=project_id : value=list_of_data_row_ids}
    Args:
        table                       :   Required (pandas.core.frame.DataFrame) - Pandas DataFrame                
        table_dict                  :   Required (dict) - Pandas DataFrame as dict with df.to_dict("records")
        global_key_col              :   Required (str) - Column name containing the data row global key - defaults to row data
        project_id_col              :   Required (str) - Column name containing the project ID to batch a given row to
        project_id                  :   Required (str) - Labelbox project ID to add data rows to - only necessary if no "project_id" column exists
        global_key_to_data_row_id   :   Required (dict) - Dictionary where {key=global_key : value=data_row_id}
    Returns:
        Dictionary where {key=project_id : value=list_of_data_row_ids}
    """
    if project_id:
        project_id_to_batch_dict = {project_id : []}
    else:
        project_ids = labelpandas.connector.get_unique_values_function(table=table)
        project_id_to_batch_dict = {id : [] for id in project_ids}
    errors = []
    try:
        for row in table_dict:
            id = project_id if project_id else row[project_id_col]
            data_row_id = global_key_to_data_row_id[row[global_key_col]]
            project_id_to_batch_dict[id].append(data_row_id)
    except Exception as e:
        errors = e
    return project_id_to_batch_dict, errors
