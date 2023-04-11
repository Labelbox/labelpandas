"""
connector.py holds the following helper functions specific to pandas DataFrames:

- get_col_names(table)                                    : Gets all column names
- get_unique_values(table, col)                           : Gets all unique values in a given column
- add_col(table, col, default)                            : Creates a column where all values equal the default value
- get_table_length(table)                                 : Gets the length of a DataFrame
- rename_col(table, col, to)                              : Renames a given column

"""
import pandas   
  
def get_col_names(table:pandas.core.frame.DataFrame, extra_client=None):
    """Grabs all column names from a Pandas DataFrame
    Args:
        table           :   Required (pandas.core.frame.DataFrame) - Pandas DataFrame
        extra_client    :   Ignore this value - necessary for other labelbase integrations
    Returns:
        List of strings corresponding to all column names
    """
    return [c for c in table.columns]

def get_unique_values(table:pandas.core.frame.DataFrame, col:str, extra_client=None):
    """Grabs all unique values from a column in a Pandas DataFrame
    Args:
        table           :   Required (pandas.core.frame.DataFrame) - Pandas DataFrame
        col             :   Required (str) - Column name
        extra_client    :   Ignore this value - necessary for other labelbase integrations
        
    Returns:
        List of strings corresponding to all unique values in a column
    """    
    return list(table[col].unique())

def add_col(table:pandas.core.frame.DataFrame, col:str, default="", extra_client=None):
    """ Adds a column of empty values to an existing Pandas DataFrame
    Args:
        table           :   Required (pandas.core.frame.DataFrame) - Pandas DataFrame
        col             :   Required (str) - Column name
        default         :   Optional - Value to insert for every row in the newly created column
        extra_client    :   Ignore this value - necessary for other labelbase integrations        
    Returns:
        Your table with a new column given the column name and default value
    """
    table[col] = default_value
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
