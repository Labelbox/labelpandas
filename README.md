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
* [Example Notebooks](#example-notebooks)

## Requirements

* [Labelbox account](http://app.labelbox.com/)
* [Generate a Labelbox API key](https://labelbox.com/docs/api/getting-started#create_api_key)

## Example Notebooks

### Importing Data from a CSV

|            Notebook            |  Github  |    Google Colab   |
| ------------------------------ | -------- | ----------------- |
| Basics: Data Rows from URLs            | [![Github](https://img.shields.io/badge/GitHub-100000?logo=github&logoColor=white)](notebooks/urls.ipynb)  | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1bxaWWPYGZnvGfFbHyYAX-pgn6kVMHP7q) |
| Data Rows from Raw Text (coming soon)        | [![Github](https://img.shields.io/badge/GitHub-100000?logo=github&logoColor=white)](notebooks/raw-text.ipynb)  | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1Xg-kn6BaYRLl-F4bMJVVopLmgEyQRTTk) |
| Data Rows from Local Files     | [![Github](https://img.shields.io/badge/GitHub-100000?logo=github&logoColor=white)](notebooks/local-files.ipynb)  | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1oMEenCfGl19MtRfHdCNdsjGxwDqlo085) |
| Data Rows with Metadata        | [![Github](https://img.shields.io/badge/GitHub-100000?logo=github&logoColor=white)](notebooks/metadata.ipynb)  | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1XSaiJlER0cC0yiekCg1eb9CuQw7lPOTL) |
| Data Rows with Attachments     | [![Github](https://img.shields.io/badge/GitHub-100000?logo=github&logoColor=white)](notebooks/attachments.ipynb)  | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1JuT867kb7ZwbaYYJYSRVQYf58-0GjSzf) |
| Data Rows with Annotations (coming soon)     | [![Github](https://img.shields.io/badge/GitHub-100000?logo=github&logoColor=white)](notebooks/annotations.ipynb)  | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1Xg-kn6BaYRLl-F4bMJVVopLmgEyQRTTk) |
| Putting it all Together (coming soon)        | [![Github](https://img.shields.io/badge/GitHub-100000?logo=github&logoColor=white)](notebooks/full-import.ipynb)  | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1Xg-kn6BaYRLl-F4bMJVVopLmgEyQRTTk) |
------
