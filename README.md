# The Official Open-Source Labelbox <> Pandas Python Integration

[Labelbox](https://labelbox.com/) enables teams to maximize the value of their unstructured data with its enterprise-grade training data platform. For ML use cases, Labelbox has tools to deploy labelers to annotate data at massive scale, diagnose model performance to prioritize labeling, and plug in existing ML models to speed up labeling. For non-ML use cases, Labelbox has a powerful catalog with auto-computed similarity scores that users can use add metadata tags to large amounts of data with a couple clicks.

[Pandas](https://pandas.pydata.org/) stands as the premier open-source Python library for handling CSV and tabluar data and as one of the most widely used Python libraries in the world.

This GitHub repo stands as an open-source Python library, moderated by the Labelbox Solutions team, in facilitating Labelbox users in uploading data to Labelbox and retreiving data from Labelbox in tabular / CSV format using Pandas. 

We strongly encourage collaboration - please free to fork this repo and tweak the code base to work for you own data, and make pull requests if you have suggestions on how to enhance the overall experience, add new features, or improve general performance. 

Please report any issues/bugs via [Github Issues](https://github.com/Labelbox/labelpandas/issues).

## Table of Contents

* [Requirements](#requirements)
* [Setup](#setup)
* [Example Notebooks](#example-notebooks)

## Requirements

* [Labelbox account](http://app.labelbox.com/)
* [Generate a Labelbox API key](https://docs.labelbox.com/reference/create-api-key)

## Setup

Set up LabelPandas with the following lines of code:

```
!pip install labelpandas -q
import labelpandas as lp

api_key = "" # Insert your Labelbox API key here
client = lp.Client(api_key)
```

Once set up, you can run the following core functions:

- `client.create_data_rows_from_table()` :   Creates Labelbox data rows (and metadata) given a Pandas table

- `client.export_to_table()` :  Exports labels (and metadata) from a given Labelbox project and creates a Pandas DataFrame

## Example Notebooks

### Importing Data from a CSV

|            Notebook            |  Github  |    Google Colab   |
| ------------------------------ | -------- | ----------------- |
| Basics: Data Rows from URLs            | [![Github](https://img.shields.io/badge/GitHub-100000?logo=github&logoColor=white)](https://github.com/Labelbox/labelpandas/blob/main/notebooks/urls.ipynb)  | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1bxaWWPYGZnvGfFbHyYAX-pgn6kVMHP7q) |
| Data Rows from Raw Text*        | [![Github](https://img.shields.io/badge/GitHub-100000?logo=github&logoColor=white)](https://github.com/Labelbox/labelpandas/blob/main/notebooks/raw-text.ipynb)  | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1Xg-kn6BaYRLl-F4bMJVVopLmgEyQRTTk) |
| Data Rows from Local Files     | [![Github](https://img.shields.io/badge/GitHub-100000?logo=github&logoColor=white)](https://github.com/Labelbox/labelpandas/blob/main/notebooks/local-files.ipynb)  | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1oMEenCfGl19MtRfHdCNdsjGxwDqlo085) |
| Data Rows with Metadata        | [![Github](https://img.shields.io/badge/GitHub-100000?logo=github&logoColor=white)](https://github.com/Labelbox/labelpandas/blob/main/notebooks/metadata.ipynb)  | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1XSaiJlER0cC0yiekCg1eb9CuQw7lPOTL) |
| Data Rows with Attachments     | [![Github](https://img.shields.io/badge/GitHub-100000?logo=github&logoColor=white)](https://github.com/Labelbox/labelpandas/blob/main/notebooks/attachments.ipynb)  | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1JuT867kb7ZwbaYYJYSRVQYf58-0GjSzf) |
| Data Rows with Annotations     | [![Github](https://img.shields.io/badge/GitHub-100000?logo=github&logoColor=white)](https://github.com/Labelbox/labelpandas/blob/main/notebooks/annotations.ipynb)  | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/14NMlKInqaI0sP9MqlPaCN1we5pRnWmX3) |
| Putting it all Together        | [![Github](https://img.shields.io/badge/GitHub-100000?logo=github&logoColor=white)](https://github.com/Labelbox/labelpandas/blob/main/notebooks/full-import.ipynb)  | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1MTLXL32JFGgXV1btgq-1VkGuu7U9Un_n) |
------

### Exporting Data to a CSV

|            Notebook            |  Github  |    Google Colab   |
| ------------------------------ | -------- | ----------------- |
| Exporting Data to a CSV            | [![Github](https://img.shields.io/badge/GitHub-100000?logo=github&logoColor=white)](https://github.com/Labelbox/labelpandas/blob/main/notebooks/export.ipynb)  | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/135zZ3ardJKzZq4nD_ynpwdgwGtpARhht) |
------

* = Coming soon
