from labelpandas import Client as lpClient
from tqdm import tqdm
from labelpandas import connector
import pandas

def load_local_files(client:lpClient, table:pandas.core.frame.DataFrame, file_path_column: str, verbose=False):
    """ Creates temporary URLs that can be used to create Labelbox data rows
    Args:
        client            :     Required (labelpandas.client.Client) - LabelPandas Client object
        table             :     Required (pandas.core.frame.DataFrame) - Pandas DataFrame
        file_path_column  :     Required (str) - Column with local file paths as strings
        verbose             :   Required (bool) - If True, prints details about code execution; if False, prints minimal information
    Returns:
        table with new `row_data` column which has urls to-be-used as row data in creating Labelbox data rows
    """
    existing_cols = connector.get_columns_function(table=table, extra_client=None)
    if "row_data" in existing_cols:
        print(f"Warning - column with name `row_data` already exists - renaming this column to `old_row_data` and creating a new `row_data` column with URL values to-be-used in creating Labelbox data rows")
        table = table.rename(columns={"row_data":"old_row_data"})
    url_column = []
    if verbose:
        table_length = connector.get_table_length_function(table=table, extra_client=None)
        print(f"Creating URLs for {table_length} local files...")
        for file_path in tqdm(table[file_path_column]):
            url_column.append(client.lb_client.upload_file(file_path))
        print(f"Success - {table_length} URLs created in `row_data` column")
    else:
        for file_path in table[file_path_column]:
            url_column.append(client.lb_client.upload_file(file_path))            
    table["row_data"] = url_column
    return table
