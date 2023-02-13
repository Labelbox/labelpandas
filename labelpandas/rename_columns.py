import pandas
from labelpandas import connector

def rename_columns(table: pandas.core.frame.DataFrame, rename_dict:dict):
    """ Renames columns into the Labelpandas format    
    Args:
        table                       :   Required (pandas.core.frame.DataFrame) - Pandas DataFrame                    
        rename_dict                 :   Required (dict) - Dictionary where { key = old_column_name : value = new_column_name }
    """
    existing_cols = connector.get_columns_function(table, extra_client=False)
    for old_name in rename_dict.keys():
        validate_column(old_col_name=old_name, new_col_name=rename_dict[old_name], existing_col_names=existing_cols)
    table = table.rename(columns=rename_dict)
    return table

def validate_column(old_col_name:str, new_col_name:str, existing_col_names:list):
    """ Validates that the rename aligns with LabelPandas column name specifications
    Args:
        old_col_name                :   Required (str) - Original column name
        new_col_name                :   Required (str) - Desired new name
        existing_col_names          :   Required (list) - List of existing column names
    Returns:
        Nothing - 
        - Will raise an error if the old column name isn't in the passed in DataFrame
        - Will also raise an error if the new column name isn't what LabelPandas is expecting
    """ 
    if old_col_name not in existing_col_names:
        raise ValueError(f"Argument `rename_dict` requires a dictionary where:\n            \n        `old_column_name` : `new_column_name`,\n        `old_column_name` : `new_column_name`\n    \nReceived key `{old_col_name}` which is not an existing column name")    
    if new_col_name in ["row_data", "external_id", "global_key"]:
        valid_column = True
    elif new_col_name.startswith("metadata"):
        valid_column = True
    elif new_col_name.startswith("attachment"):
        valid_column = True
    elif new_col_name.startswith("annotation"):
        valid_column = True   
    else:
        valid_column = False
    if not valid_column:
        raise ValueError(f"New name assignment invalid for LabelPandas - colmn name must be one of `row_data`, `external_id` or `global_key` or start with `metadata`, `attachment` or `annotation` -- received new column name `{new_col_name}`")
        
