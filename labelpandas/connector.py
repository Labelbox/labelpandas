from labelbase.metadata import get_metadata_schema_to_name_key, process_metadata_value
from labelbase.ontology import get_ontology_schema_to_name_path
from labelbox import labelboxClient
import pandas
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm.autonotebook import tqdm
import math

def create_batches(table=pandas.core.frame.DataFrame, global_key_col:str, project_id_col:str, global_key_to_data_row_id:dict):
    """ From a Pandas DataFrame, creates a dictionary where {key=project_id : value=list_of_data_row_ids}
    Args:
        table                       :   Required (pandas.core.frame.DataFrame) - Pandas DataFrame        
        global_key_col              :   Required (str) - Column name containing the data row global key - defaults to row data
        project_id_col              :   Required (str) - Column name containing the project ID to batch a given row to
        global_key_to_data_row_id   :   Required (dict) - Dictionary where {key=global_key : value=data_row_id}
    Returns:
        Dictionary where {key=project_id : value=list_of_data_row_ids}
    """
    project_id_to_batch_dict = {}
    errors = []
    if not project_id_col:
        errors = f"No project_id_col provided - please provide a column indicating what project to batch data rows to"
    else:
        try:
            column_names = get_columns_function(table)
            if project_id_col not in column_names:
                raise ValueError(f"Provided value for project_id_col `{project_id_col}` not in provided table column names")
            for index, row in table.iterrows():
                project_id = row[project_id_col]
                data_row_id = global_key_to_data_row_id[row[global_key_col]]
                if project_id not in project_id_to_batch_dict.keys():
                    project_id_to_batch_dict[project_id] = []
                project_id_to_batch_dict[project_id].append(data_row_id)
        except Exception as e:
            errors = e
    return project_id_to_batch_dict, errors
  
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

def create_data_row_upload_dict(client:labelboxClient, table:pandas.core.frame.DataFrame, row_data_col:str, 
                                global_key_col:str="", external_id_col:str="", metadata_index:dict={}, attachment_index:dict=attachment_index
                                local_files:bool=False, divider:str="///", verbose=False):
    """ Multithreads over a Pandas DataFrame, calling create_data_rows() on each row to return an upload dictionary
    Args:
        table           :   Required (pandas.core.frame.DataFrame) - Pandas DataFrame    
        client          :   Required (labelbox.client.Client) - Labelbox Client object
        row_data_col    :   Required (str) - Column containing asset URL or file path
        global_key_col  :   Optional (str) - Column name containing the data row global key - defaults to row data
        external_id_col :   Optional (str) - Column name containing the data row external ID - defaults to global key
        metadata_index  :   Optional (dict) - Dictionary where {key=column_name : value=metadata_type}
                                metadata_type must be either "enum", "string", "datetime" or "number"
        local_files     :   Optional (bool) - Determines how to handle row_data_col values
                                If True, treats row_data_col values as file paths uploads the local files to Labelbox
                                If False, treats row_data_col values as urls (assuming delegated access is set up)
        divider         :   Optional (str) - String delimiter for all name keys generated for parent/child schemas
        verbose         :   Optional (bool) - If True, prints details about code execution; if False, prints minimal information
    Returns:
        Two values:
        - global_key_to_upload_dict - Dictionary where {key=global_key : value=data row dictionary in upload format}
        - errors - List of dictionaries containing conversion error information; see connector.create_data_rows() for more information
    """    
    global_key_col = global_key_col if global_key_col else row_data_col
    external_id_col = external_id_col if external_id_col else global_key_col     
    if verbose:
        print(f'Creating upload list - {get_table_length_function(table)} rows in Pandas DataFrame')
    if get_table_length_function(table=table) != get_unique_values_function(table=table, column_name=global_key_col):
        print(f"Warning: Your global key column is not unique - upload will resume, only uploading 1 data row for duplicate global keys")     
    metadata_schema_to_name_key = get_metadata_schema_to_name_key(client=lb_client, lb_mdo=False, divider=divider, invert=False)
    metadata_name_key_to_schema = get_metadata_schema_to_name_key(client=lb_client, lb_mdo=False, divider=divider, invert=True) 
    with ThreadPoolExecutor(max_workers=8) as exc:
        global_key_to_upload_dict = {}
        errors = []
        futures = []
        if verbose:
            print(f'Submitting data rows...')
            for index, row in tqdm(table.iterrows()):
                futures.append(exc.submit(
                    create_data_rows, client, row, metadata_name_key_to_schema, metadata_schema_to_name_key, 
                    row_data_col, global_key_col, external_id_col, metadata_index, attachment_index, local_files, divider
                ))           
        else:
            for index, row in table.iterrows():
                futures.append(exc.submit(
                    create_data_rows, client, row, metadata_name_key_to_schema, metadata_schema_to_name_key, 
                    row_data_col, global_key_col, external_id_col, metadata_index, attachment_index, local_files, divider
                ))
        if verbose:
            print(f'Processing data rows...')
            for f in tqdm(as_completed(futures)):
                res = f.result()
                if res['error']:
                    errors.append(res)
                else:
                    global_key_to_upload_dict[str(res['data_row']["global_key"])] = res['data_row']  
        else:
            for f in as_completed(futures):
                res = f.result()
                if res['error']:
                    errors.append(res)
                else:
                    global_key_to_upload_dict[str(res['data_row']["global_key"])] = res['data_row']
    if verbose:
        print(f'Generated upload list - {len(global_key_to_upload_dict)} data rows to upload')
    return global_key_to_upload_dict, errors
  
def create_data_rows(client:labelboxClient, row:pandas.core.series.Series,
                     metadata_name_key_to_schema:dict, metadata_schema_to_name_key:dict, row_data_col:str,
                     global_key_col:str, external_id_col:str, metadata_index:dict, attachment_index:dict, local_files:bool, divider:str):
    """ Function to-be-multithreaded to create data row dictionaries from a Pandas DataFrame
    Args:
        client.                     :   Required (labelbox.client.Client) - Labelbox Client object
        row                         :   Required (pandas.core.series.Series) - Pandas Series object, corresponds to one row in a df.iterrow()
        metadata_name_key_to_schema :   Required (dict) - Dictionary where {key=metadata_field_name_key : value=metadata_schema_id}
        metadata_schema_to_name_key :   Required (dict) - Inverse of metadata_name_key_to_schema        
        row_data_col                :   Required (str) - Column containing asset URL or file path        
        global_key_col              :   Required (str) - Column name containing the data row global key
        external_id_col             :   Required (str) - Column name containing the data row external ID
        metadata_index              :   Required (dict) - Dictionary where {key=column_name : value=metadata_type}
                                            metadata_type must be either "enum", "string", "datetime" or "number"
        attachment_index            :   Required (dict) - Dictionary where {key=column_name : value=attachment_type}
                                            attachment_type must be one of "IMAGE", "VIDEO", "RAW_TEXT", "HTML", "TEXT_URL"                                            
        local_files                 :   Required (bool) - Determines how to handle row_data_col values
                                            If True, treats row_data_col values as file paths uploads the local files to Labelbox
                                            If False, treats row_data_col values as urls (assuming delegated access is set up)
        divider                     :   Required (str) - String delimiter for all name keys generated for parent/child schemas
    Returns:
        A dictionary with "error" and "data_row" keys:
        - "error" - If there's value in the "error" key, the script will scip it on upload and return the error at the end
        - "data_row" - Dictionary with "global_key" "external_id" "row_data" and "metadata_fields" keys in the proper format to-be-uploaded
    """
    return_value = {"error" : None, "data_row" : {}}
    try:
        return_value["data_row"]["row_data"] = client.upload_file(str(row[row_data_col])) if local_files else str(row[row_data_col])
        return_value["data_row"]["global_key"] = str(row[global_key_col])
        return_value["data_row"]["external_id"] = str(row[external_id_col])
        metadata_fields = [{"schema_id" : metadata_name_key_to_schema['lb_integration_source'], "value" : "Pandas"}]
        if metadata_index:
            for metadata_field_name in metadata_index.keys():
                input_metadata = process_metadata_value(
                    client=client, metadata_value=row[metadata_field_name], metadata_type=metadata_index[metadata_field_name], 
                    parent_name=metadata_field_name, metadata_name_key_to_schema=metadata_name_key_to_schema, divider=divider
                )
                if input_metadata:
                    metadata_fields.append({"schema_id" : metadata_name_key_to_schema[metadata_field_name], "value" : input_metadata})
                else:
                    continue
        return_value["data_row"]["metadata_fields"] = metadata_fields                    
        if attachment_index:
            return_value['data_row']['attachments'] = []
            for column_name in attachment_index:
                return_value['data_row']['attachments'].append({"type" : attachment_index[column_name], "value" : row[column_name]})
    except Exception as e:
        return_value["error"] = e
        return_value["data_row"]["global_key"] = str(row[global_key_col])
    return return_value
  
def get_columns_function(table:pandas.core.frame.DataFrame):
    """Grabs all column names from a Pandas DataFrame
    Args:
        table           :   Required (pandas.core.frame.DataFrame) - Pandas DataFrame
    Returns:
        List of strings corresponding to all column names
    """
    return [col for col in table.columns]

def get_unique_values_function(table:pandas.core.frame.DataFrame, column_name:str):
    """Grabs all unique values from a column in a Pandas DataFrame
    Args:
        table           :   Required (pandas.core.frame.DataFrame) - Pandas DataFrame
        column_name     :   Required (str) - Column name
    Returns:
        List of strings corresponding to all unique values in a column
    """    
    return list(table[column_name].unique())

def add_column_function(table:pandas.core.frame.DataFrame, column_name:str, default_value=""):
    """ Adds a column of empty values to an existing Pandas DataFrame
    Args:
        table           :   Required (pandas.core.frame.DataFrame) - Pandas DataFrame
        column_name     :   Required (str) - Column name
        default_value   :   Optional - Value to insert for every row in the newly created column
    Returns:
        Your table with a new column given the column_name and default_value
    """
    table[column_name] = default_value
    return table

def get_table_length_function(table:pandas.core.frame.DataFrame):
    """ Tells you the size of a Pandas DataFrame
    Args:
        table           :   Required (pandas.core.frame.DataFrame) - Pandas DataFrame
    Returns:
        The length of your table as an integer
    """  
    return len(table)
