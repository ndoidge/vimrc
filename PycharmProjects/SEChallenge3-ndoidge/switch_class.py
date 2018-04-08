"""
switch_class.py - by Nick Doidge (ndoidge@cisco.com)
----------------
A basic class definition for a switch (or device). Allows you to connect to a switch using the NXAPI and 'sessions',
this maintains session information such as cookies, so you do not have to parse this info yourself. At present these
scripts assume you are using JSON to format message bodies etc. I will write extensions for XML when I can be bothered :-D

To create a switch object, first define a dictionary in the following format:
    <dict_name> = {
        'protocol': 'http',
        'ip': '127.0.0.1',
        'port': '10180',
        'username': '<username>',
        'password': '<password>'
    }

Note: square brackets indicate variable names - you can choose what you like as long as they conform to Python variable naming standards

Then call the switch class, specifying the dictionary you just created, the username and password)
    <switch_name> = switch(<dict_name>)

You can then perform a AAA login
    <switch_name>.aaaLogin()

Now you can perform GET and POST requests with the functions:
    <switch_name>.get(<url>)
    <switch_name.post(<url>, <body>)

Note in both cases the URL is the API path, not including the hostname/ IP/ port etc... i.e. '/api/mo/sys.json?rsp-subtree=children'
The <body> argument to the POST method should be a dictionary

Once you are finished you can logout of the switch with
    <switch_name>.aaaLogout()

As a final clean up, delete the created class
    del <switch_name>

"""

import requests
import json

class credentials():

    def __init__(self, ip, username, password, *args, **kwargs):
        port = kwargs.get('port', '80')
        protocol = kwargs.get('protocol', 'http')

        self.url = '{0}://{1}:{2}'.format(protocol, ip, port)
        self.username = username
        self.password = password
        self.headers = kwargs.get('headers', '')




#def myfunc(a, b, *args, **kwargs):
#    c = kwargs.get('c', None)
#    d = kwargs.get('d', None)
    # etc
#myfunc(a, b, c='nick', d='dog', ...)


class switch():

    def __init__(self, device):
        self.device = device

        #Take in the host details to produce the URL for REST requests
        self.url = '{0}://{1}:{2}'.format(device['protocol'], device['ip'], device['port'])

        #create the session object which allows each switch class a single session for all API calls
        self.session = requests.session()

    def aaaLogin(self):
        body = {
            "aaaUser": {
                "attributes": {
                    "name": self.device['username'],
                    "pwd": self.device['password']
                }
            }
        }

        # append the aaaLogin.json portion to create the full URL
        full_url = self.url + '/api/aaaLogin.json'

        #call the post, catch any connection errors
        try:
            response = self.session.post(full_url, json=body)
        except requests.exceptions.ConnectionError:
            print 'Unable to establish connectivity to the device: ' + self.device['ip']
            return 0

        if response.status_code != requests.codes.ok:
            return 0
        else:
            return 1


    def aaaLogout(self):

        body = {
		    'aaaUser' : {
			    'attributes' : {
				    'name' : self.device['username']
			    }
		    }
	    }

        #append the aaaLogout.json portion to create the full URL
        full_url = self.url + '/api/aaaLogout.json'

        #logout of the switch
        try:
            response = self.session.post(full_url, json=body)
        except requests.exceptions.ConnectionError:
            print 'Unable to establish connectivity to the device: ' + self.device['ip']
            return False

        if response.status_code != requests.codes.ok:
            return False
        else:
            return True


    def get(self, url):
        return self.session.get(self.url + url)


    def post(self, url, body, headers=''):
        return self.session.post(self.url + url, json=body, headers=headers)


    def is_feature_enabled(self, feature):
        url = '/api/mo/sys/fm.json?rsp-subtree=full&rsp-prop-include=config-only'
        rx_json = self.get(url)
        rx_json = json.loads(rx_json.text)

        feature_enabled = False
        # loop through each child element of the output, looking to match the feature name, if successful, check its enabled
        for i in range(len(rx_json['imdata'][0]['fmEntity']['children'])):
            if feature in rx_json['imdata'][0]['fmEntity']['children'][i].keys():
                if rx_json['imdata'][0]['fmEntity']['children'][i][feature]['attributes']['adminSt'] == 'enabled':
                    feature_enabled = True
                    print 'Feature \'' + feature + '\' is enabled'
                    break
        return feature_enabled


    def enable_feature(self, feature):
        url = '/ins'

        print 'Feature ' + feature + ' is not enabled... having to use CLI-based API to enable it... you might have to wait a while!'

        myheaders = {'content-type': 'application/json-rpc'}

        payload = [
            {
                "jsonrpc": "2.0",
                "method": "cli",
                "params": {
                    "cmd": "conf t",
                    "version": 1
                },
                "id": 1
            },
            {
                "jsonrpc": "2.0",
                "method": "cli",
                "params": {
                    "cmd": "feature interface-vlan",
                    "version": 1
                },
                "id": 2
            }
        ]

        response = requests.post(self.url + url, json=payload, headers=myheaders, auth=(self.device['username'], self.device['password']))
        if response.status_code == requests.codes.ok:
            print 'Feature ' + feature + ' is now enabled'
            return 1
        else:
            return 0


    def create_vlan(self, vlan, description):

        url = '/api/mo/sys/bd.json'

        payload = {
            "bdEntity": {
                "children": [{
                    "l2BD": {
                        "attributes": {
                            "fabEncap": "vlan-" + str(vlan),
                            "name": description
                        }
                    }
                }]
            }
        }

        #create the vlan and if the HTTP response is good then return 1, else return 0 to show the vlan couldnt be created
        if self.post(url, payload).status_code == requests.codes.ok:
            return 1
        else:
            return 0

