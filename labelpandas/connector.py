from labelbox import Client
from labelbase import Client as baseClient
import pandas
from concurrent.futures import ThreadPoolExecutor, as_completed
from google.api_core import retry

def create_upload_dict(df:pandas.core.frame.DataFrame, local_files:bool, lb_client:Client, base_client:baseClient, row_data_col:str, 
                       global_key_col:str="", external_id_col:str="", metadata_index:dict={}, divider:str="///", verbose=False):
    """ Multithreads over a Pandas DataFrame, calling create_data_rows() on each row to return an upload dictionary
    Args:
        df              :   Required (pandas.core.frame.DataFrame) - Pandas DataFrame    
        local_files     :   Required (bool) - If True, will create urls for local files; if False, uploads `row_data_col` as urls
        lb_client       :   Required (labelbox.client.Client) - Labelbox Client object
        base_client     :   Required (labelbase.client.Client) - Labelbase Client object
        row_data_col    :   Required (str) - Column containing asset URL or file path
        global_key_col  :   Optional (str) - Column name containing the data row global key - defaults to row data
        external_id_col :   Optional (str) - Column name containing the data row external ID - defaults to global key
        metadata_index  :   Required (dict) - Dictionary where {key=column_name : value=metadata_type} - metadata_type = "enum", "string", "datetime" or "number"
        divider         :   Optional (str) - String delimiter for all name keys generated
        verbose         :   Required (bool) - If True, prints information about code execution
    Returns:
        Two items - the global_key, and a dictionary with "row_data", "global_key", "external_id" and "metadata_fields" keys
    """    
    if verbose:
        print(f'Creating upload list - {len(df)} rows in Pandas DataFrame')
    global_key_col = global_key_col if global_key_col else row_data_col
    external_id_col = external_id_col if external_id_col else global_key_col       
    metadata_schema_to_name_key = base_client.get_metadata_schema_to_name_key(lb_mdo=False, divider=divider, invert=False)
    metadata_name_key_to_schema = base_client.get_metadata_schema_to_name_key(lb_mdo=False, divider=divider, invert=True) 
    global_key_to_upload_dict = {}
    futures = []
    with ThreadPoolExecutor() as exc:
        for index, row in df.iterrows():
            futures.append(
                exc.submit(
                    create_data_rows, local_files, lb_client, base_client, row, 
                    metadata_name_key_to_schema, metadata_schema_to_name_key,
                    row_data_col, global_key_col, external_id_col, metadata_index, divider
                )
            )
        for f in as_completed(futures):
            res = f.result()
            print(res)
            global_key_to_upload_dict[str(res["global_key"])] = res  
    if verbose:
        print(f'Generated upload list - {len(global_key_to_upload_dict)} data rows to upload')
    return global_key_to_upload_dict

@retry.Retry(predicate=retry.if_exception_type(Exception), deadline=120.)
def create_file(lb_client, file_path:str):
    """ Wraps lb_client.upload_file() in retry logic
    Args:
        lb_client                   :   Required (labelbox.client.Client) - Labelbox Client object
        file_path                   :   Required (str) - String corresponding to the row data file path
    Returns: 
        Temporary URL to-be-uploaded to Labelbox
    """ 
    return lb_client.upload_file(file_path)    
  
def create_data_rows(local_files:bool, lb_client:Client, base_client:baseClient, row:pandas.core.series.Series, 
                     metadata_name_key_to_schema:dict, metadata_schema_to_name_key:dict,
                     row_data_col:str, global_key_col:str="", external_id_col:str="", metadata_index:dict={}, divider:str="///"):
    """ Function to-be-multithreaded to create data row dictionaries from a Pandas DataFrame
    Args:
        local_files                 :   Required (bool) - If True, will create urls for local files; if False, uploads `row_data_col` as urls
        lb_client                   :   Required (labelbox.client.Client) - Labelbox Client object
        base_client                 :   Required (labelbase.client.Client) - Labelbase Client object
        row_data_col                :   Required (str) - Column containing asset URL or file path
        global_key_col              :   Optional (str) - Column name containing the data row global key - defaults to row data
        external_id_col             :   Optional (str) - Column name containing the data row external ID - defaults to global key
        metadata_index              :   Required (dict) - Dictionary where {key=column_name : value=metadata_type} - metadata_type = "enum", "string", "datetime" or "number"
        metadata_name_key_to_schema :   Required (dict) - Dictionary where {key=metadata_field_name_key : value=metadata_schema_id}
        metadata_schema_to_name_key :   Required (dict) - Inverse of metadata_name_key_to_schema
        divider                     :   Optional (str) - String delimiter for all name keys generated
    Returns:
        Two items - the global_key, and a dictionary with "row_data", "global_key", "external_id" and "metadata_fields" keys
    """
    row_data = create_file(str(row[row_data_col])) if local_files else str(row[row_data_col])
    metadata_fields = [{"schema_id" : metadata_name_key_to_schema['lb_integration_source'], "value" : "Pandas"}]
    if metadata_index:
        for metadata_field_name in metadata_index.keys():
            metadata_value = base_client.process_metadata_value(
                metadata_value=row[metadata_field_name],
                metadata_type=metadata_index[metadata_field_name], 
                parent_name=metadata_field_name,
                metadata_name_key_to_schema=metadata_name_key_to_schema, 
                divider=divider
            )
            if metadata_value:
                metadata_fields.append({"schema_id" : metadata_name_key_to_schema[metadata_field_name], "value" : value})
            else:
                continue
    return {"row_data":row_data,"global_key":str(row[global_key_col]),"external_id":str(row[external_id_col]),"metadata_fields":metadata_fields}                
  
def get_columns_function(df):
    """Grabs all column names from a Pandas DataFrame
    Args:
        df              :   Required (pandas.core.frame.DataFrame) - Pandas DataFrame
    Returns:
        List of strings corresponding to all column names
    """
    return [col for col in df.columns]

def get_unique_values_function(df, column_name:str):
    """Grabs all unique values from a column in a Pandas DataFrame
    Args:
        df              :   Required (pandas.core.frame.DataFrame) - Pandas DataFrame
        column_name     :   Required (str) - Column name
    Returns:
        List of strings corresponding to all unique values in a column
    """    
    return list(df[column_name].unique())

def add_column_function(df, column_name:str, default_value=""):
    """ Adds a column of empty values to an existing Pandas DataFrame
    Args:
        df              :   Required (pandas.core.frame.DataFrame) - Pandas DataFrame
        column_name     :   Required (str) - Column name
        default_value   :   Optional - Value to insert into column
    Returns:
        You Pandas DataFrame with a new column   
    """
    df[column_name] = default_value
    return df
