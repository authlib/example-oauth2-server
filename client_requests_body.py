import os
import sys
import logging

# Enable logging
log = logging.getLogger('requests_oauthlib')
log.addHandler(logging.StreamHandler(sys.stdout))
log.setLevel(logging.DEBUG)

from oauthlib.oauth2.rfc6749.clients import BackendApplicationClient

from requests_oauthlib import OAuth2Session


os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

TOKEN_URL = 'http://127.0.0.1:5000/oauth/token'

cid = os.environ.get('CLIENT_ID', '')
csecret = os.environ.get('CLIENT_SECRET', '')
if not cid or not csecret:
    print 'Please set CLIENT_ID and CLIENT_SECRET env variables'
    sys.exit(1)

client = BackendApplicationClient(client_id=cid, scope='email', state='authtoken')

o = OAuth2Session(client=client)

o.fetch_token(TOKEN_URL, client_id=cid, client_secret=csecret)
