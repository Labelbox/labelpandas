from labelbox import Client
import pandas

def create_upload_dict(df:pandas.core.frame.DataFrame, local_files:bool, lb_client:Client, row:pandas.core.series.Series, 
                       row_data_col:str, global_key_col:str="", external_id_col:str="", metadata_index:dict={}, divider:str="///"):
    """ Multithreads over a Pandas DataFrame, calling create_data_rows() on each row to return an upload dictionary
    Args:
        df              :   Required (pandas.core.frame.DataFrame) - Pandas DataFrame    
        local_files     :   Required (bool) - If True, will create urls for local files / If False, treats the values in `row_data_col` as urls
        lb_client       :   Required (labelbox.client.Client) - Labelbox Client object
        row             :   Required (pandas.core.series.Series) - Pandas row object
        row_data_col    :   Required (str) - Column name where the data row row data URL is located
        global_key_col  :   Optional (str) - Column name where the data row global key is located - defaults to the row_data_col
        external_id_col :   Optional (str) - Column name where the data row external ID is located - defaults to the global_key_col
        metadata_index  :   Optional (dict) - Dictionary where {key=column_name : value=metadata_type} - metadata_type must be one of "enum", "string", "datetime" or "number"
        divider         :   Optional (str) - String delimiter to separate metadata field names from their metadata answer options in your metadata_name_key_to_schema dictionary
    Returns:
        Two items - the global_key, and a dictionary with "row_data", "global_key", "external_id" and "metadata_fields" keys
    """    
    global_key_col = global_key_col if global_key_col else row_data_col
    external_id_col = external_id_col if external_id_col else global_key_col       
    metadata_schema_to_name_key = get_metadata_schema_to_name_key(lb_mdo=False, divider=divider, invert=False)
    metadata_name_key_to_schema = get_metadata_schema_to_name_key(lb_mdo=False, divider=divider, invert=True) 
    global_key_to_upload_dict = {}
    futures = []
    with ThreadPoolExecutor() as exc:
        for index, row in df.iterrows():
            futures.append(
                exc.submit(
                    create_data_rows, local_files, lb_client, row, row_data_col, 
                    global_key_col, external_id_col, metadata_index, metadata_name_key_to_schema,
                    metadata_schema_to_name_key, divider
                )
            )
        for f in as_completed(futures):
            res = f.result()
            global_key_to_upload_dict[str(res["global_key"])] = res    
    return global_key_to_upload_dict

def create_data_rows(local_files:bool, lb_client:Client, row:pandas.core.series.Series, row_data_col:str, global_key_col:str="", external_id_col:str="", 
                     metadata_index:dict={}, metadata_name_key_to_schema:dict, metadata_schema_to_name_key:dict, divider:str="///"):
    """ Function to-be-multithreaded to create data row dictionaries from a Pandas table
    Args:
        local_files                 :   Required (bool) - If True, will create urls for local files / If False, treats the values in `row_data_col` as urls
        lb_client                   :   Required (labelbox.client.Client) - Labelbox Client object
        row                         :   Required (pandas.core.series.Series) - Pandas row object
        row_data_col                :   Required (str) - Column name where the data row row data URL is located
        global_key_col              :   Optional (str) - Column name where the data row global key is located - defaults to the row_data_col
        external_id_col             :   Optional (str) - Column name where the data row external ID is located - defaults to the global_key_col
        metadata_index              :   Required (dict) - Dictionary where {key=column_name : value=metadata_type} - metadata_type must be one of "enum", "string", "datetime" or "number"
        metadata_name_key_to_schema :   Required (dict) - Dictionary where {key=metadata_field_name_key : value=metadata_schema_id}
        metadata_schema_to_name_key :   Required (dict) - Inverse of metadata_name_key_to_schema
        divider                     :   Optional (str) - String delimiter to separate metadata field names from their metadata answer options in your metadata_name_key_to_schema dictionary
    Returns:
        Two items - the global_key, and a dictionary with "row_data", "global_key", "external_id" and "metadata_fields" keys
    """
    row_data = lb_client.upload_file(str(row[row_data_col])) if local_files else str(row[row_data_col])
    data_row_dict = {
        "row_data" : row_data, "global_key" : str(row[global_key_col]), "external_id" : row[external_id_col], 
        "metadata_fields" : [{"schema_id" : metadata_name_key_to_schema['lb_integration_source', "value" : "Pandas"]}]
    }
    if metadata_index:
        for metadata_field_name in metadata_index.keys():
            name_key = f"{metadata_field_name}{divider}{row[metadata_field_name]}"
            value = row[metadata_field_name] if name_key not in metadata_name_key_to_schema.keys() else metadata_name_key_to_schema[name_key]
            data_row_dict['metadata_fields'].append({"schema_id" : metadata_schema_to_name_key[metadata_field_name], "value" : value})
    return data_row_dict

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
