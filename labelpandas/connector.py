"""
connector.py holds the following helper functions specific to pandas DataFrames:

- get_col_names(table)                                    : Gets all column names
- get_unique_values(table, column_name)                   : Gets all unique values in a given column
- add_col(table, column_name, default_value)              : Creates a column where all values equal the default value
- get_table_length(table)                                 : Gets the length of a DataFrame
- rename_col(table, col, to)                              : Renames a given column

"""
import pandas   
from labelbase.connector import validate_column_name_change
  
def get_col_names(table:pandas.core.frame.DataFrame, extra_client=None):
    """Grabs all column names from a Pandas DataFrame
    Args:
        table           :   Required (pandas.core.frame.DataFrame) - Pandas DataFrame
        extra_client    :   Ignore this value - necessary for other labelbase integrations
    Returns:
        List of strings corresponding to all column names
    """
    return [col for col in table.columns]

def get_unique_values(table:pandas.core.frame.DataFrame, column_name:str, extra_client=None):
    """Grabs all unique values from a column in a Pandas DataFrame
    Args:
        table           :   Required (pandas.core.frame.DataFrame) - Pandas DataFrame
        column_name     :   Required (str) - Column name
        extra_client    :   Ignore this value - necessary for other labelbase integrations
        
    Returns:
        List of strings corresponding to all unique values in a column
    """    
    return list(table[column_name].unique())

def add_col(table:pandas.core.frame.DataFrame, column_name:str, default_value="", extra_client=None):
    """ Adds a column of empty values to an existing Pandas DataFrame
    Args:
        table           :   Required (pandas.core.frame.DataFrame) - Pandas DataFrame
        column_name     :   Required (str) - Column name
        default_value   :   Optional - Value to insert for every row in the newly created column
        extra_client    :   Ignore this value - necessary for other labelbase integrations        
    Returns:
        Your table with a new column given the column_name and default_value
    """
    table[column_name] = default_value
    return table

def get_table_length(table:pandas.core.frame.DataFrame, extra_client=None):
    """ Tells you the size of a Pandas DataFrame
    Args:
        table           :   Required (pandas.core.frame.DataFrame) - Pandas DataFrame
        extra_client    :   Ignore this value - necessary for other labelbase integrations        
    Returns:
        The length of your table as an integer
    """  
    return len(table)

def rename_col(table: pandas.core.frame.DataFrame, col:str, to:str):
    """ Renames columns into the Labelpandas format    
    Args:
        table           :   Required (pandas.core.frame.DataFrame) - Pandas DataFrame
        col             :   Required (str) - Existing column name to-be-changed
        to              :   Required (str) - What to rename the column as       
    Returns:
        Updated `table` object with renamed column
    """
    existing_cols = get_col_names(table, extra_client=False)
    validate_column_name_change(old_col_name=col, new_col_name=to, existing_col_names=existing_cols)
    table = table.rename(columns={col:to})
    return table  
