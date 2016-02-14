""" Demostrates use of the new Fusion Tables API

"""
# To generate values for the variables below:
# 1. Go to https://console.developers.google.com/apis
# 2. Enable the Fusion Tables API (use search field)
# 3. Accept the terms
# 4. Click "Credentials" in left-hend nav
# 5. Create New credential: "Create an OAuth client ID..." to get the client_id and client_secret
# 6. Select Web Application
# 7. Name it whatever
# 8. Use 'http://localhost' for Authorized redirect uri)
# 9. To run the code, from command line in the directory containing the file, type python infowindow_styling_demo.py

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

class Google_FushionTable_API:
    def __init__(self):
        self.access_token = ""
        self.params = ""

    def main(self):
        
        storage = Storage(credentials_file)
        credentials = storage.get()
        
        flow = client.flow_from_clientsecrets(
                'client_secrets_other.json',
                scope='https://www.googleapis.com/auth/fusiontables',
                redirect_uri='urn:ietf:wg:oauth:2.0:oob')
        
        auth_uri = flow.step1_get_authorize_url()
        webbrowser.open(auth_uri)
        
        auth_code = raw_input('Enter the auth code: ')
        
        credentials = flow.step2_exchange(auth_code)
        http_auth = credentials.authorize(httplib2.Http())
        
        storage.put(credentials)        
    
        drive_service = discovery.build('fusiontables', 'v2', http=http_auth)
        files = drive_service.files().list().execute()
             

        #serv_req = urllib2.Request(url="https://accounts.google.com/o/oauth2/token",
        #                           data=data)

        #serv_resp = urllib2.urlopen(serv_req)
        #response = serv_resp.read()
        #tokens = simplejson.loads(response)
        #access_token = tokens["access_token"]
        #self.access_token = access_token
        #self.params = "?key=%s&access_token=%s".format(api_key, self.access_token)
    
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

    def runRequest(self, method, url, data=None, headers=None):
        request = httplib.HTTPSConnection("www.googleapis.com", 443)

        if data and headers:
            request.request(method, url, data, headers)
        else:
            request.request(method, url)
        response = request.getresponse()
        print response.status, response.reason
        response = response.read()
        print response
        return response
    
if __name__ == "__main__":
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