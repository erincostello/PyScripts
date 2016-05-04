"""
Upload data from a csv file to a Fusion table
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
import csv

import httplib2

from apiclient.discovery import build
from apiclient.http import MediaFileUpload
from oauth2client.file import Storage
from oauth2client import client
from oauth2client import tools
import argparse


# set the working directory
os.chdir(r"C:\WorkSpace\Quantifying_Conservation_2014\SouthernWillamette\Mapping_Web")
#os.chdir(r"/Users/rmichie/Desktop")

api_file = "api_file.json"
credentials_file = 'credentials.json'
client_secret_file = 'client_secret_other.json'
login_file = 'login_file.json'
csv_file = 'outputs_model_nodes_v1.csv'

# Table metadata
isExportable= "false"
name="CWP Effective Shade v1"
attribution="Oregon DEQ, CWP" 
attributionLink=None
description="CWP Southern Willamette pilot project. Effective shade model results for current condition and site potential"

with open(login_file) as f:    
    login_data = json.load(f)
    
with open(api_file) as f:
    api_key = json.load(f)["api_key"]
    
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    credential_dir = os.getcwd()
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
        credentials = tools.run_flow(flow, locker, flags)

    return credentials

def format_columns():
    '''Reads'''
    
    with open(csv_file) as f:
        csvreader = csv.reader(f)
        cols = csvreader.next()
        data = csvreader.next()
        
        col_list = []
        for n, c in enumerate(cols):
            col_item = {"name":c}
            col_item['columnId'] = n
            
            if c.upper() in ['LOCATION']:
                col_item['type'] = 'LOCATION'
            elif is_number(data[n]):
                col_item['type'] = 'NUMBER'
            else:
                col_item['type'] = 'STRING'
                
            
            col_list.append(col_item)
            
    return col_list
               
def insert_new_table():
    
    table_data = {"columns": col_list,
                  "isExportable": isExportable,
                  "name": name,
                  "attribution": attribution,
                  "attributionLink": attributionLink,
                  "description": description
                  }     
    
    # make a table request
    request = service.table()
    
    # List the existing tables to check it if already exists
    response = request.list().execute()
    
    for f_table in response['items']:
        if f_table['name'] == table_data['name']:
            # table exists
            return f_table['tableId']

    # Create table and get table ID
    response = request.insert(body = table_data).execute()
    return response['tableId']    
    
def insert_new_rows():
    
    media_data = MediaFileUpload(csv_file, mimetype='application/octet-stream', resumable=True)
    request =  service.table().importRows(tableId=table_id, media_body=media_data,
                                          isStrict=True, startLine=1,
                                          encoding='auto-detect')
    response = request.execute()
    
    status = response.getStatus()
    
    return response['numRowsReceived']
    

def insert_style():
        
    style_body = {"name": "CWP_shade_diff",
                  "markerOptions": {
                      "iconStyler": {
                          "columnName": "SHADE_DIFF",
                          "kind": "fusiontables#buckets",
                           "buckets": [
                               {
                                   "min": 0.66,
                                   "icon": "small_red"},
                               {
                                   "min": 0.16,
                                   "max": 0.65, 
                                   "icon": "small_yellow"
                                },
                               {
                                   "max": 0.15,
                                   "icon": "small_green"
                               }
                               ]
                       }
                       }
               }    
    
    request = service.style().insert(tableId=table_id, body=style_body)
    response = request.execute() 
    
    return response['styleId']

flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()

credentials = get_credentials()
http = credentials.authorize(httplib2.Http())

service = build(serviceName='fusiontables', version='v2', http=http, 
                developerKey= api_key)

col_list = format_columns()
table_id = insert_new_table()
print("Insert Table Table ID {0}".format(table_id))
#numRowsReceived = insert_new_rows()
#print("Insert Rows status: {0}. Number of rows uploaded {1}".format(return_status, numRowsReceived))
#style_id = insert_style()
#print("Insert Style. Style_ID {1}".format(style_id))



print("done")


