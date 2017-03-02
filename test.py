import os, json, logging, sys
import random, time
import requests
from urlparse import urlparse, parse_qs

###############################################################################
# turn on debug spew for requests library
###############################################################################
try:
    import http.client as http_client
except ImportError:
    # Python 2
    import httplib as http_client
http_client.HTTPConnection.debuglevel = 1

# You must initialize logging, otherwise you'll not see debug output.
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True


def dbg(v):
    print(''.join(['=']*80) + "\n" + v + "\n" + ''.join(['=']*80) + "\n")

###############################################################################
# basic config
###############################################################################
oauthsrv_prefix = 'http://0.0.0.0:5000/'
authorize_url = oauthsrv_prefix + 'oauth/authorize'
token_url = oauthsrv_prefix + 'oauth/token'
client_url = 'http://127.0.0.1:8000'


###############################################################################
# tests begin
###############################################################################

test_id = 'test' + str(int(time.time()))

dbg('Setting up user: ' + test_id)
r = requests.post(oauthsrv_prefix, data = { 'username': test_id } )
assert r.status_code == 200


# get the user session, and store for subsequent requests
test_session = r.cookies['session']
assert test_session != '' and test_session is not None
dbg('Obtained session: ' + test_session)

cookies = {'session': test_session}

# get the client ID and secret
r = requests.get(oauthsrv_prefix + 'client', cookies=cookies)
client_data = json.loads(r.text)
assert 'client_id' in client_data and 'client_secret' in client_data
dbg('Client secrets: ' + client_data['client_id'])



# build the authorization request URL
auth_code_url = authorize_url + '?response_type=code' + '&client_id=' + client_data['client_id'] + '&redirect_uri='+ client_url + '/authorized&scope=email'
dbg(auth_code_url)

r = requests.post(authorize_url,
        data = {
        'client_id': client_data['client_id'],
        'scope':'email',
        'response_type':'code',
        'redirect_uri': client_url + '/authorized',
        'confirm':'yes' # NOTE 'no' to test disallow
    },
    cookies = {'session': test_session},
    allow_redirects=False # we don't have a participating web service, don't auto-redirect
)
authorized_url = r.headers['Location']

# if all went well, we should now have an authorization code
assert 'code=' in authorized_url
o = urlparse(authorized_url)
auth_code = parse_qs(o.query)['code'][0]
print(auth_code)



# we have enough data now to request the access token
request_access_token_url = token_url + '?client_id=' + client_data['client_id'] + '&client_secret=' + client_data['client_secret'] + '&grant_type=authorization_code&code=' + auth_code + '&redirect_uri=' + client_url + '/authorized'
dbg(request_access_token_url)

r = requests.get(request_access_token_url,
    cookies = {'session': test_session},
    allow_redirects=False
)
oauth_access_data = json.loads(r.text)
assert 'access_token' in oauth_access_data
assert oauth_access_data['token_type'] == 'Bearer'



#### now, we should have access to the resource data
r = requests.get(oauthsrv_prefix + 'api/me',
    headers = {
        'Authorization': 'Bearer ' + oauth_access_data['access_token']
    },
    cookies = {'session': test_session},
    allow_redirects=False
)
user_data = json.loads(r.text)
assert 'username' in user_data and 'test' in user_data['username']
dbg('User data from Oauth server: ' + r.text)
