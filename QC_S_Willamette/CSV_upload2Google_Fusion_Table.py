"""
Upload data from a csv file to a Fusion tables
using the Google Fushion Tables API

"""
# To generate values for the variables below:
# 1. Go to https://console.developers.google.com/apis
# 2. Enable the Fusion Tables API (use search field)
# 3. Accept the terms
# 4. Click "Credentials" in left-hend nav
# 5. Under Create credentials: choose "OAuth client ID..."
# 6. Select "Other"
# 7. Name it whatever
# 8. Use 'http://localhost:8080' for Authorized JavaScript origins and Authorized redirect uri)
# 9. Save, and download the JSON file.

from __future__ import print_function
import json
import os

# set the working directory
#os.chdir(r"C:\WorkSpace\Quantifying_Conservation_2014\SouthernWillamette\Mapping_Web")
os.chdir(r"/Users/rmichie/Desktop")

api_file = "api_file.json"
credentials_file = 'credentials.json'
client_secret_file = 'client_secret_other.json'
login_file = 'login_file.json'

isExportable= "false"
name="Test Table"
attribution="Me myself and I" 
attributionLink=None
description="this is a test"

# These are columns names
col_list = [{"name": "ColName1",
             "columnId": 0,
             "type": "STRING"},
            {"name": "ColName2",
             "columnId": 1,
             "type": "NUMBER"},
            {"name": "LAT",
             "columnId": 2,
             "type": "LOCATION"}]

table_data = {"columns": col_list,
              "isExportable": isExportable,
              "name": name,
              "attribution": attribution,
              "attributionLink": attributionLink,
              "description": description
            }

# ----

#import requests

#payload = {"key": api_key}
#r = requests.get(url = "https://www.googleapis.com/fusiontables/v2/tables", params= payload)
#r = requests.post("https://www.googleapis.com/fusiontables/v2/tables",
#                  params = payload,
#                  data = table_data)
#print(r.status_code, r.reason)


import httplib2

from apiclient.discovery import build
from apiclient.http import MediaFileUpload
from oauth2client.file import Storage
from oauth2client import client
from oauth2client import tools
import argparse
import csv


with open(login_file) as f:    
    login_data = json.load(f)
    
with open(api_file) as f:
    api_key = json.load(f)["api_key"]

def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    credential_dir = os.path.join(os.getcwd(), '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir, credentials_file)

    locker = Storage(credential_path)
    credentials = locker.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(client_secret_file,
                                              scope='https://www.googleapis.com/auth/fusiontables',
                                              login_hint=login_data['email'])
        flow.user_agent = "Fushion Tables Python Script"
        credentials = tools.run_flow(flow, store, flags)

    return credentials

def insert_new_table():
    
    # make a table request
    request = service.table()
    
    # List the existing tables to check it if already exists
    response = request.list().execute()
    
    for f_table in response['items']:
        if f_table['name'] == table_data['name']:
            # table exists
            return f_table['tableId']
        else:
            # Create table and get table ID
            response = request.insert(body = table_data).execute()
            return response['tableId']    
    
def insert_new_rows():
    
    # upload metadata
    request = service.table()
    
    csv_data = MediaFileUpload(csvFileName,mimetype='application/octet-stream')
    request =  service.table().importRows(tableId=table_id, media_body=csv_data,
                                          startLine=1, encoding='auto-detect')
    response = request.execute()    
    
    response = request.importRows(table_id, uploadType='resumable').execute()
    

flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()

credentials = get_credentials()
http = credentials.authorize(httplib2.Http())

service = build(serviceName='fusiontables', version='v2', http=http)
 #               developerKey= api_key)

table_id = insert_new_table()



print(response)


