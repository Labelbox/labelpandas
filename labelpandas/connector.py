"""
connector.py holds the following helper functions specific to pandas DataFrames:

- get_columns_function(table)                             : Gets all column names
- get_unique_values_function(table, column_name)          : Gets all unique values in a given column
- add_column_function(table, column_name, default_value)  : Creates a column where all values equal the default value
- get_table_length_function(table)                        : Gets the length of a DataFrame

"""
import pandas   
  
def get_columns_function(table:pandas.core.frame.DataFrame, extra_client=None):
    """Grabs all column names from a Pandas DataFrame
    Args:
        table           :   Required (pandas.core.frame.DataFrame) - Pandas DataFrame
        extra_client    :   Ignore this value - necessary for other labelbase integrations
    Returns:
        List of strings corresponding to all column names
    """
    return [col for col in table.columns]

def get_unique_values_function(table:pandas.core.frame.DataFrame, column_name:str, extra_client=None):
    """Grabs all unique values from a column in a Pandas DataFrame
    Args:
        table           :   Required (pandas.core.frame.DataFrame) - Pandas DataFrame
        column_name     :   Required (str) - Column name
        extra_client    :   Ignore this value - necessary for other labelbase integrations
        
    Returns:
        List of strings corresponding to all unique values in a column
    """    
    return list(table[column_name].unique())

def add_column_function(table:pandas.core.frame.DataFrame, column_name:str, default_value="", extra_client=None):
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

def get_table_length_function(table:pandas.core.frame.DataFrame, extra_client=None):
    """ Tells you the size of a Pandas DataFrame
    Args:
        table           :   Required (pandas.core.frame.DataFrame) - Pandas DataFrame
        extra_client    :   Ignore this value - necessary for other labelbase integrations        
    Returns:
        The length of your table as an integer
    """  
    return len(table)
