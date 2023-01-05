# The Official Open-Source Labelbox <> Pandas Python Integration

[Labelbox](https://labelbox.com/) enables teams to maximize the value of their unstructured data with its enterprise-grade training data platform. For ML use cases, Labelbox has tools to deploy labelers to annotate data at massive scale, diagnose model performance to prioritize labeling, and plug in existing ML models to speed up labeling. For non-ML use cases, Labelbox has a powerful catalog with auto-computed similarity scores that users can use add metadata tags to large amounts of data with a couple clicks.

[Pandas](https://pandas.pydata.org/) stands as the premier open-source Python library for handling CSV and tabluar data and as one of the most widely used Python libraries in the world.

This GitHub repo stands as an open-source Python library, moderated by the Labelbox Solutions team, in facilitating Labelbox users in uploading data to Labelbox and retreiving data from Labelbox in tabular / CSV format using Pandas. 

We strongly encourage collaboration - please free to fork this repo and tweak the code base to work for you own data, and make pull requests if you have suggestions on how to enhance the overall experience, add new features, or improve general performance. 

All core functions come out of `labelpandas.Client()` which currently has the following functions:

- `labelpandas.client.create_data_rows_from_table` :   Creates Labelbox data rows (and metadata) given a Pandas table ([example notebook](https://github.com/Labelbox/labelpandas/blob/main/notebooks/create_data_rows_example.ipynb))

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
