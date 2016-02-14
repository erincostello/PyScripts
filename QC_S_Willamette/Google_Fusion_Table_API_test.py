

import os
import json
import webbrowser

import httplib2

from apiclient import discovery
from oauth2client import client
from oauth2client.file import Storage

# set the working directory
os.chdir(r"C:\WorkSpace\Quantifying_Conservation_2014\SouthernWillamette\Mapping_Web")
credentials_file = r"credentials"

api_key = read_secret_file


def table_insert(self, t_columns, isExportable, name, attribution=None, attributionLink=None, description=None):
    print "Create a new table, returns table id"
    data_raw = {"columns": t_columns,
            "isExportable": isExportable,
            "name": name,
            "attribution": attribution,
            "attributionLink": attributionLink,
            "description": description
            }
    
    data_json = json.dumps(data_raw, separators=(',', ': '))
    response = self.runRequest(
        "POST",
        "/fusiontables/v2/tables?fields=tableId&key={0}".format(api_key),
        data_json)
    json_response = simplejson.loads(response)
    return json_response["tableId"]




flow = client.flow_from_clientsecrets(
    'client_secrets.json',
    scope='https://www.googleapis.com/auth/fusiontables',
    redirect_uri='urn:ietf:wg:oauth:2.0:oob')

auth_uri = flow.step1_get_authorize_url()
webbrowser.open(auth_uri)

auth_code = raw_input('Enter the auth code: ')

credentials = flow.step2_exchange(auth_code)
http_auth = credentials.authorize(httplib2.Http())

storage = Storage(credentials_file)
storage.put(credentials)        

drive_service = discovery.build('fusiontables', 'v2', http_auth)
files = drive_service.files().list().execute()

code = raw_input("Enter code (parameter of URL): ")


api_test = Google_FushionTable_API()
api_test.main()

col_list = [{"name": "ColName1",
             "columnId": 0,
             "type": "STRING"},
            {"name": "ColName2",
             "columnId": 1,
             "type": "NUMBER"},
            {"name": "LAT",
             "columnId": 2,
             "type": "LOCATION"}]

#col_json = json.dumps(col_list, sort_keys=True, separators=(',', ': '))

table_id = api_test.table_insert(t_columns=col_list,
                                 isExportable=False,
                                 name="Test Table",
                                 attribution="Me myself and I", 
                                 attributionLink=None, 
                                 description="this is a test")