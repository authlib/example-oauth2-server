import os
import sys
import logging
import requests

import httplib
httplib.HTTPConnection.debuglevel = 1

logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger('requests.packages.urllib3')
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

TOKEN_URL = 'http://127.0.0.1:5000/oauth/token'

cid = os.environ.get('CLIENT_ID', '')
csecret = os.environ.get('CLIENT_SECRET', '')
if not cid or not csecret:
    print 'Please set CLIENT_ID and CLIENT_SECRET env variables'
    sys.exit(1)

data = {'grant_type': 'client_credentials'}
result = requests.post(TOKEN_URL, data=data, auth=(cid, csecret))
print(result.content)
