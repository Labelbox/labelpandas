def create_data_rows(
    local_files, 
    lb_client, 
    row, 
    row_data_col, 
    global_key_col, 
    external_id_col, 
    metadata_index, 
    metadata_name_key_to_schema, 
    metadata_schema_to_name_key,    
    divider):
    """ Function to-be-multithreaded to create data row dictionaries from a Pandas table
    Args:
        local_files                 :   Required (bool) - If True, will create urls for local files / If False, treats the values in `row_data_col` as urls
        lb_client                   :   Required (labelbox.client.Client) - Labelbox Client object
        row                         :   Required (pandas.core.series.Series) - Pandas row object
        row_data_col                :   Required (str) - Column name where the data row row data URL is located
        global_key_col              :   Required (str) - Column name where the data row global key is located - defaults to the row_data column
        external_id_col             :   Required (str) - Column name where the data row external ID is located - defaults to the row_data column
        metadata_index              :   Required (dict) - Dictionary where {key=column_name : value=metadata_type} - metadata_type must be one of "enum", "string", "datetime" or "number"
        metadata_name_key_to_schema :   Required (dict) - Dictionary where {key=metadata_field_name_key : value=metadata_schema_id}
        metadata_schema_to_name_key :   Required (dict) - Inverse of metadata_name_key_to_schema
        divider                     :   Optional (str) - String delimiter to separate metadata field names from their metadata answer options in your metadata_name_key_to_schema dictionary
    Returns:
        Two items - the global_key, and a dictionary with "row_data", "global_key", "external_id" and "metadata_fields" keys
    """
    row_data = lb_client.upload_file(str(row[row_data_col])) if local_files else str(row[row_data_col])
    data_row_dict = {"row_data" : row_data, "global_key" : str(row[global_key_col]), "external_id" : row[external_id_col], "metadata_fields" : [{"schema_id" : metadata_name_key_to_schema['lb_integration_source', "value" : "Pandas"]}]}
    if metadata_index:
        for metadata_field_name in metadata_index.keys():
            name_key = f"{metadata_field_name}{divider}{row[metadata_field_name]}"
            value = row[metadata_field_name] if name_key not in metadata_name_key_to_schema.keys() else metadata_name_key_to_schema[name_key]
            data_row_dict['metadata_fields'].append({"schema_id" : metadata_schema_to_name_key[metadata_field_name], "value" : value})
    return data_row_dict

def get_columns_function(table):
    return [col for col in table.columns]

def get_unique_values_function(table, column_name:str):
    return list(table[column_name].unique())

def add_column_function(table, column_name:str):
    table[column_name] = ""
    return table
