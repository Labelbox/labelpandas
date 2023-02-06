""" 
data_rows.py holds the function create_data_row_upload_dict() -- which multithreads over create_data_rows() to create the following style dictionary:

{
    dataset_id : 
        {
            global_key : data_row_upload_dict,
            global_key : data_row_upload_dict,
            global_key : data_row_upload_dict
        },
    dataset_id : 
        {
            global_key : data_row_upload_dict,
            global_key : data_row_upload_dict,
            global_key : data_row_upload_dict
        }                
}

This is the format that labelbase.uploader.batch_create_data_rows() expects
"""
import pandas
from labelbox import Client as labelboxClient
import labelbase
from labelpandas import connector
from tqdm.autonotebook import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

def create_data_row_upload_dict(client:labelboxClient, table: pandas.core.frame.DataFrame, table_dict:dict, 
                                row_data_col:str, global_key_col:str, external_id_col:str, dataset_id_col:str,
                                dataset_id:str, metadata_index:dict, attachment_index:dict,
                                divider:str, verbose:bool, extra_client:bool=None):
    """ Multithreads over a Pandas DataFrame, calling create_data_rows() on each row to return an upload dictionary
    Args:
        client                      :   Required (labelbox.client.Client) - Labelbox Client object        
        table                       :   Required (pandas.core.frame.DataFrame) - Pandas DataFrame                
        table_dict                  :   Required (dict) - Pandas DataFrame as dict with df.to_dict("records")
        row_data_col                :   Required (str) - Column containing asset URL or raw text
        global_key_col              :   Required (str) - Column name containing the data row global key - defaults to row data
        external_id_col             :   Required (str) - Column name containing the data row external ID - defaults to global key
        dataset_id_col              :   Required (str) - Column name containing the dataset ID to add data rows to
        dataset_id                  :   Required (str) - Labelbox dataset ID to add data rows to - only necessary if no "dataset_id" column exists            
        metadata_index              :   Required (dict) - Dictonary where {key=column_name : value=metadata_type}
        attachment_index            :   Required (dict) - Dictonary where {key=column_name : value=attachment_type}
        divider                     :   Required (str) - String delimiter for all name keys generated
        verbose                     :   Required (bool) - If True, prints details about code execution; if False, prints minimal information
        extra_client                :   Ignore this value - necessary for other labelbase integrations                
    Returns:
        Two values:
        - global_key_to_upload_dict - Dictionary where {key=global_key : value=data row dictionary in upload format}
        - errors - List of dictionaries containing conversion error information; see connector.create_data_rows() for more information
    """
    table_length = connector.get_table_length_function(table=table)
    if verbose:
        print(f'Creating upload list - {table_length} rows in Pandas DataFrame')
    unique_global_key_count = len(connector.get_unique_values_function(table=table, column_name=global_key_col))
    if table_length != unique_global_key_count:
        print(f"Warning: Your global key column is not unique - upload will resume, only uploading 1 data row per unique global key")     
    metadata_schema_to_name_key = labelbase.metadata.get_metadata_schema_to_name_key(client=client, lb_mdo=False, divider=divider, invert=False)
    metadata_name_key_to_schema = labelbase.metadata.get_metadata_schema_to_name_key(client=client, lb_mdo=False, divider=divider, invert=True) 
    if dataset_id:
        dataset_to_global_key_to_upload_dict = {dataset_id : {}}
    else:
        dataset_to_global_key_to_upload_dict = {id : {} for id in connector.get_unique_values_function(table=table, column_name=dataset_id_col)}
    with ThreadPoolExecutor(max_workers=8) as exc:
        errors = []
        futures = []
        if verbose:
            print(f'Submitting data rows...')
            for row_dict in tqdm(table_dict):
                futures.append(exc.submit(
                    create_data_rows, client, row_dict, metadata_name_key_to_schema, metadata_schema_to_name_key, 
                    row_data_col, global_key_col, external_id_col, dataset_id_col, 
                    dataset_id, metadata_index, attachment_index, divider
                ))           
            print(f'Processing data rows...')
            for f in tqdm(as_completed(futures)):
                res = f.result()
                id = str(list(res.keys()))[0]
                data_row_dict = res[id]
                global_key = str(data_row_dict["global_key"])
                dataset_to_global_key_to_upload_dict[id].update({global_key:data_row_dict})                
        else:
            for row_dict in tqdm(table_dict):
                futures.append(exc.submit(
                    create_data_rows, client, row_dict, metadata_name_key_to_schema, metadata_schema_to_name_key, 
                    row_data_col, global_key_col, external_id_col, dataset_id_col, 
                    dataset_id, metadata_index, attachment_index, divider
                ))
            for f in as_completed(futures):
                res = f.result()
                id = str(list(res.keys()))[0]
                data_row_dict = res[id]
                global_key = str(data_row_dict["global_key"])
                dataset_to_global_key_to_upload_dict[id].update({global_key:data_row_dict})
    if verbose:
        print(f'Generated upload list')
    return global_key_to_upload_dict
  
def create_data_rows(client:labelboxClient, row_dict:dict,
                     metadata_name_key_to_schema:dict, metadata_schema_to_name_key:dict, 
                     row_data_col:str, global_key_col:str, external_id_col:str, dataset_id_col:str,
                     dataset_id:str, metadata_index:dict, attachment_index:dict, 
                     divider:str):
    """ Function to-be-multithreaded to create data row dictionaries from a Pandas DataFrame
    Args:
        client                      :   Required (labelbox.client.Client) - Labelbox Client object            
        row_dict                    :   Required (dict) - Dictionary where {key=column_name : value=row_value}
        metadata_name_key_to_schema :   Required (dict) - Dictionary where {key=metadata_field_name_key : value=metadata_schema_id}
        metadata_schema_to_name_key :   Required (dict) - Inverse of metadata_name_key_to_schema        
        row_data_col                :   Required (str) - Column containing asset URL or raw text
        global_key_col              :   Required (str) - Column name containing the data row global key
        external_id_col             :   Required (str) - Column name containing the data row external ID
        dataset_id_col              :   Required (str) - Column name containing the dataset ID to add data rows to
        dataset_id                  :   Required (str) - Default dataset if dataset_id_col == ""        
        metadata_index              :   Required (dict) - Dictonary where {key=column_name : value=metadata_type}
        attachment_index            :   Required (dict) - Dictonary where {key=column_name : value=attachment_type}                                       
        divider                     :   Required (str) - String delimiter for all name keys generated
    Returns:
        A dictionary with "error" and "data_row" keys:
        - "error" - If there's value in the "error" key, the script will scip it on upload and return the error at the end
        - "data_row" - Dictionary with "global_key" "external_id" "row_data" and "metadata_fields" keys in the proper format to-be-uploaded
    """
    id = dataset_id if dataset_id else row_dict["dataset_id_col"]
    return_value = {id : {}}
    return_value[id]["row_data"] = str(row_dict[row_data_col])
    return_value[id]["global_key"] = str(row_dict[global_key_col])
    return_value[id]["external_id"] = str(row_dict[external_id_col])
    metadata_fields = [{"schema_id" : metadata_name_key_to_schema['lb_integration_source'], "value" : "Pandas"}]
    if metadata_index:
        for metadata_field_name in metadata_index.keys():
            input_metadata = labelbase.metadata.process_metadata_value(
                client=client, metadata_value=row_dict[metadata_field_name], metadata_type=metadata_index[metadata_field_name], 
                parent_name=metadata_field_name, metadata_name_key_to_schema=metadata_name_key_to_schema, divider=divider
            )
            if input_metadata:
                metadata_fields.append({"schema_id" : metadata_name_key_to_schema[metadata_field_name], "value" : input_metadata})
            else:
                continue
    return_value[id]["metadata_fields"] = metadata_fields                    
    if attachment_index:
        return_value[id]["attachments"] = []
        for column_name in attachment_index:
            return_value[id]['attachments'].append({"type" : attachment_index[column_name], "value" : row_dict[column_name]})
    return return_value  
