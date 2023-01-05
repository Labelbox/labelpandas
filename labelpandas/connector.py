from labelbase import Client as baseClient
from labelbox import Client
import pandas
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import math

def create_upload_dict(df:pandas.core.frame.DataFrame, lb_client:Client, base_client:baseClient, row_data_col:str, 
                       global_key_col:str="", external_id_col:str="", metadata_index:dict={}, local_files:bool=False, divider:str="///", verbose=False):
    """ Multithreads over a Pandas DataFrame, calling create_data_rows() on each row to return an upload dictionary
    Args:
        df              :   Required (pandas.core.frame.DataFrame) - Pandas DataFrame    
        lb_client       :   Required (labelbox.client.Client) - Labelbox Client object
        base_client     :   Required (labelbase.client.Client) - Labelbase Client object
        row_data_col    :   Required (str) - Column containing asset URL or file path
        global_key_col  :   Optional (str) - Column name containing the data row global key - defaults to row data
        external_id_col :   Optional (str) - Column name containing the data row external ID - defaults to global key
        metadata_index  :   Optional (dict) - Dictionary where {key=column_name : value=metadata_type} - metadata_type = "enum", "string", "datetime" or "number"
        local_files     :   Optional (bool) - If True, will create urls for local files; if False, uploads `row_data_col` as urls
        divider         :   Optional (str) - String delimiter for all name keys generated
        verbose         :   Optional (bool) - If True, prints information about code execution
    Returns:
        Two values - a success value, and a dictinoary where {key=global_key : value = {"row_data", "global_key", "external_id", "metadata_fields"}}
    """    
    if verbose:
        print(f'Creating upload list - {len(df)} rows in Pandas DataFrame')
    global_key_col = global_key_col if global_key_col else row_data_col
    external_id_col = external_id_col if external_id_col else global_key_col       
    metadata_schema_to_name_key = base_client.get_metadata_schema_to_name_key(lb_mdo=False, divider=divider, invert=False)
    metadata_name_key_to_schema = base_client.get_metadata_schema_to_name_key(lb_mdo=False, divider=divider, invert=True) 
    global_key_to_upload_dict = {}
    try:
        with ThreadPoolExecutor() as exc:
            futures = []
            x = 0
            dupe_print = 0
            if verbose:
                print(f'Submitting data rows...')
            for index, row in df.iterrows():
                futures.append(exc.submit(create_data_rows, lb_client, base_client, row, metadata_name_key_to_schema, metadata_schema_to_name_key, row_data_col, global_key_col, external_id_col, metadata_index, local_files, divider))
            if verbose:
                print(f'Processing data rows...')        
            for f in as_completed(futures):
                res = f.result()
                global_key_to_upload_dict[str(res["global_key"])] = res    
                if verbose:
                    x += 1
                    percent_complete = math.ceil((x / len(df)*100))
                    if percent_complete%1 == 0 and (percent_complete!=dupe_print):
                        print(f'{str(percent_complete)}% complete')          
                        dupe_print = percent_complete
        if verbose:
            print(f'Generated upload list - {len(global_key_to_upload_dict)} data rows to upload')
        return True, global_key_to_upload_dict  
    except Exception as e:
        print(e)
        if res:
            return False, res
        else:
            return False, False
  
def create_data_rows(lb_client:Client, base_client:baseClient, row:pandas.core.series.Series,
                     metadata_name_key_to_schema:dict, metadata_schema_to_name_key:dict, row_data_col:str,
                     global_key_col:str="", external_id_col:str="", metadata_index:dict={}, local_files=False, divider:str="///"):
    """ Function to-be-multithreaded to create data row dictionaries from a Pandas DataFrame
    Args:
        lb_client                   :   Required (labelbox.client.Client) - Labelbox Client object
        base_client                 :   Required (labelbase.client.Client) - Labelbase Client object
        row                         :   Required (pandas.core.series.Series) - Pandas Series object, corresponds to one row in a df.iterrow()
        metadata_name_key_to_schema :   Required (dict) - Dictionary where {key=metadata_field_name_key : value=metadata_schema_id}
        metadata_schema_to_name_key :   Required (dict) - Inverse of metadata_name_key_to_schema        
        row_data_col                :   Required (str) - Column containing asset URL or file path        
        global_key_col              :   Optional (str) - Column name containing the data row global key - defaults to row data
        external_id_col             :   Optional (str) - Column name containing the data row external ID - defaults to global key
        metadata_index              :   Optional (dict) - Dictionary where {key=column_name : value=metadata_type} - metadata_type = "enum", "string", "datetime" or "number"
        local_files                 :   Optional (bool) - If True, will create urls for local files; if False, uploads `row_data_col` as urls                
        divider                     :   Optional (str) - String delimiter for all name keys generated
    Returns:
        Two items - the global_key, and a dictionary with "row_data", "global_key", "external_id" and "metadata_fields" keys
    """
    row_data = lb_client.upload_file(str(row[row_data_col])) if local_files else str(row[row_data_col])
#     row_data = base_client.upload_local_file(file_path=str(row[row_data_col])) if local_files else str(row[row_data_col])
    metadata_fields = [{"schema_id" : metadata_name_key_to_schema['lb_integration_source'], "value" : "Pandas"}]
    if metadata_index:
        for metadata_field_name in metadata_index.keys():
            input_metadata = base_client.process_metadata_value(
                metadata_value=row[metadata_field_name],
                metadata_type=metadata_index[metadata_field_name], 
                parent_name=metadata_field_name,
                metadata_name_key_to_schema=metadata_name_key_to_schema, 
                divider=divider
            )
            if input_metadata:
                metadata_fields.append({"schema_id" : metadata_name_key_to_schema[metadata_field_name], "value" : input_metadata})
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
        Your Pandas DataFrame with a new column   
    """
    df[column_name] = default_value
    return df
