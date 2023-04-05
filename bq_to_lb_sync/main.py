"""
A sample Hello World server.
"""
import os

from flask import Flask, render_template

# pylint: disable=C0103
app = Flask(__name__)


@app.route('/')
def labelbox():
    from google.cloud import bigquery
    from google.oauth2 import service_account
    import labelpandas as lp

    # Path to service account key file
    service_account_path = 'saleseng-3823e66acbe5.json'

    # Create credentials object from service account key file
    credentials = service_account.Credentials.from_service_account_file(
        service_account_path
    )

    # Create a BigQuery client object
    client = bigquery.Client(credentials=credentials)

    # Perform a query
    query = 'SELECT * FROM `saleseng.cloud_run_demo.cloud_run_demo` LIMIT 10'

    # copy the results to a dataframe
    df = client.query(query).to_dataframe()
    print(df)

    df = df.drop(columns={'global_key'})
    df['global_key'] = 'clg0xtns207ay07zj4nczdxyk' + df['external_id']
    print(df)

    # read API Key from environment variable - MUST be set in the docker container, or as a google cloud run secret
    #api_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiJjbGFqdThrMzcyNG5tMDgxbGcybjljZzVjIiwib3JnYW5pemF0aW9uSWQiOiJja3E4bXd6YnIxZnd0MHk0NmJ3enIxYWdmIiwiYXBpS2V5SWQiOiJjbGZtbXp5cGMxNXV3MDcwdWVhcjNjZGw3Iiwic2VjcmV0IjoiZTlhNzZhM2Y4Mzg0OWM0ZTkxMTVmYTg0ZDc3MTM0NWIiLCJpYXQiOjE2Nzk2NjgwNjYsImV4cCI6MjMxMDgyMDA2Nn0.xQwHmbjzyF4YGWMQ69jtluOGmaxt-Dk7nhYfIcF4dGY'
    api_key = os.environ.get("tm_lb_api_key")
    client = lp.Client(lb_api_key=api_key)
    dataset_id = client.lb_client.get_dataset('clg0xtns207ay07zj4nczdxyk')
    df = df.rename(columns={'metadata___string___LabelPandas_String': 'metadata///string///LabelPandas-String',
                            'metadata___number___LabelPandas_Number': 'metadata///number///LabelPandas-Number',
                            'metadata___enum___LabelPandas_Enum': 'metadata///enum///LabelPandas-Enum',
                            'metadata___datetime___LabelPandas_Datetime': 'metadata///datetime///LabelPandas-Datetime'
                            }
                   )
    print(df)
    import labelpandas as lp
    results = client.create_data_rows_from_table(
        table=df,
        dataset_id=dataset_id.uid,  # remove .uid if you've created a new dataset
        skip_duplicates=True,  # If True, will skip data rows where a global key is already in use,
        verbose=True,  # If True, prints information about code execution
    )
    print(results)

    return "ok"

if __name__ == '__main__':
    server_port = os.environ.get('PORT', '8080')
    app.run(debug=False, port=server_port, host='0.0.0.0')