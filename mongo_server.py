# coding: utf-8

from datetime import datetime, timedelta
from flask import Flask
from flask import session, request
from flask import render_template, redirect, jsonify
from flask_mongoengine import MongoEngine
from werkzeug.security import gen_salt
from flask_oauthlib.provider import OAuth2Provider


app = Flask(__name__, template_folder='templates')
app.debug = True
app.secret_key = 'secret'

app.config.update({
    'MONGODB_SETTINGS': {'DB': 'OAuth2'}
})
db = MongoEngine(app)
oauth = OAuth2Provider(app)


class User(db.Document):
    username = db.StringField()


class Client(db.Document):
    client_id = db.StringField()
    client_secret = db.StringField()

    user = db.ReferenceField(User)

    _redirect_uris = db.StringField()
    _default_scopes = db.StringField()

    @property
    def client_type(self):
        return 'public'

    @property
    def redirect_uris(self):
        if self._redirect_uris:
            return self._redirect_uris.split()
        return []

    @property
    def default_redirect_uri(self):
        return self.redirect_uris[0]

    @property
    def default_scopes(self):
        if self._default_scopes:
            return self._default_scopes.split()
        return []


class Grant(db.Document):
    user = db.ReferenceField(User)

    client_id = db.StringField()
    client = db.ReferenceField(Client)

    code = db.StringField()

    redirect_uri = db.StringField()
    expires = db.DateTimeField()

    _scopes = db.StringField()


    @property
    def scopes(self):
        if self._scopes:
            return self._scopes.split()
        return []


class Token(db.Document):
    client_id = db.StringField()
    client = db.ReferenceField(Client)

    user = db.ReferenceField(User)

    # currently only bearer is supported
    token_type = db.StringField()

    access_token = db.StringField()
    refresh_token = db.StringField()
    expires = db.DateTimeField()
    _scopes = db.StringField()

    @property
    def scopes(self):
        if self._scopes:
            return self._scopes.split()
        return []


def current_user():
    if 'username' in session:
        username = session['username']
        return User.objects.get(username=username)
    return None


@app.route('/', methods=('GET', 'POST'))
def home():
    if request.method == 'POST':
        username = request.form.get('username')
        user = User.objects(username=username).first()
        if not user:
            user = User(username=username)
            user.save()
        session['username'] = user.username
        return redirect('/')
    user = current_user()
    return render_template('home.html', user=user)


@app.route('/client')
def client():
    user = current_user()
    if not user:
        return redirect('/')
    item = Client(
        client_id=gen_salt(40),
        client_secret=gen_salt(50),
        _redirect_uris=' '.join([
            'http://localhost:8000/authorized',
            'http://localhost:8000/authorized',
            'http://localhost:8000/authorized',
            'http://localhost:8000/authorized',
            ]),
        _default_scopes='email',
        user=user
    )

    item.save()
    return jsonify(
        client_id=item.client_id,
        client_secret=item.client_secret,
    )


@oauth.clientgetter
def load_client(client_id):
    return Client.objects(client_id=client_id).first()


@oauth.grantgetter
def load_grant(client_id, code):
    return Grant.objects(client_id=client_id, code=code).first()


@oauth.grantsetter
def save_grant(client_id, code, request, *args, **kwargs):
    # decide the expires time yourself
    expires = datetime.utcnow() + timedelta(seconds=100)
    grant = Grant(
        client_id=client_id,
        code=code['code'],
        redirect_uri=request.redirect_uri,
        _scopes=' '.join(request.scopes),
        user=current_user(),
        expires=expires
    )

    grant.save()
    return grant


@oauth.tokengetter
def load_token(access_token=None, refresh_token=None):
    if access_token:
        return Token.objects(access_token=access_token).first()
    elif refresh_token:
        return Token.objects(refresh_token=refresh_token).first()


@oauth.tokensetter
def save_token(token, request, *args, **kwargs):
    toks = Token.objects(
        client_id=request.client.client_id,
        user = request.user
    )
    # make sure that every client has only one token connected to a user
    for t in toks:
        t.delete()

    expires_in = token.pop('expires_in')
    expires = datetime.utcnow() + timedelta(seconds=expires_in)

    tok = Token(
        access_token=token['access_token'],
        refresh_token=token['refresh_token'],
        token_type=token['token_type'],
        _scopes=token['scope'],
        expires=expires,
        client_id=request.client.client_id,
        user=request.user
    )
    tok.save()
    return tok


@app.route('/oauth/token', methods=['GET', 'POST'])
@oauth.token_handler
def access_token():
    return None


@app.route('/oauth/authorize', methods=['GET', 'POST'])
@oauth.authorize_handler
def authorize(*args, **kwargs):
    user = current_user()
    if not user:
        return redirect('/')
    if request.method == 'GET':
        client_id = kwargs.get('client_id')
        client = Client.objects(client_id=client_id).first()
        kwargs['client'] = client
        kwargs['user'] = user
        return render_template('authorize.html', **kwargs)

    confirm = request.form.get('confirm', 'no')
    return confirm == 'yes'


@app.route('/api/me')
@oauth.require_oauth()
def me():
    user = request.oauth.user
    return jsonify(username=user.username)


if __name__ == '__main__':
    app.run(host='0.0.0.0')
