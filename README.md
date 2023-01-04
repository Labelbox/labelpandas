# Labelbox Connector for Pandas

Access the Labelbox Connector for Pandas, an open-source Python API that handles CSVs and Dataframes very well
- `labelpandas.client.create_data_rows_from_table` :   Creates Labelbox data rows (and metadata) given a Pandas table ([example notebook](https://github.com/Labelbox/labelpandas/blob/main/notebooks/create_data_rows_example.ipynb))
- `labelpandas.client.create_table_from_dataset`   :   Creates a Pandas table given a Labelbox dataset (coming soon)
- `labelpandas.client.upsert_table_metadata`       :   Updates Pandas table metadata columns given a Labelbox dataset (coming soon)
- `labelpandas.client.upsert_labelbox_metadata`    :   Updates Labelbox metadata given a Pandas table (coming soon)

The Demo code supplied in this Github is designed to run in a Google Colab, but the code can be adapted to any notebook environment.

Labelbox is the enterprise-grade training data solution with fast AI enabled labeling tools, labeling automation, human workforce, data management, a powerful API for integration & SDK for extensibility. Visit [Labelbox](http://labelbox.com/) for more information.

This library is currently in beta. It may contain errors or inaccuracies and may not function as well as commercially released software. Please report any issues/bugs via [Github Issues](https://github.com/Labelbox/labelpandas/issues).


## Table of Contents

* [Requirements](#requirements)
* [Configuration](#configuration)
* [Use](#Use)

## Requirements

* [Labelbox account](http://app.labelbox.com/)
* [Generate a Labelbox API key](https://labelbox.com/docs/api/getting-started#create_api_key)

## Configuration

Install labelpandas to your Python environment. The installation will also add the Labelbox SDK.

```
pip install labelpandas
import labelpandas
```

## Use

The `client` class requires the following arguments:
- `lb_api_key` = Labelbox API Key
