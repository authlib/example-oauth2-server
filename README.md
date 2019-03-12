# How to create an OAuth 2.0 Provider

This is an example of OAuth 2.0 server in [Authlib](https://authlib.org/).
If you are looking for old Flask-OAuthlib implementation, check the
`flask-oauthlib` branch.

- Documentation: <https://docs.authlib.org/en/latest/flask/oauth2.html>
- Authlib Repo: <https://github.com/lepture/authlib>

## Sponsors

<table>
  <tr>
    <td><img align="middle" width="48" src="https://user-images.githubusercontent.com/290496/39297078-89d00928-497d-11e8-8119-0c53afe14cd0.png"></td>
    <td>If you want to quickly add secure token-based authentication to Python projects, feel free to check Auth0's Python SDK and free plan at <a href="https://auth0.com/overview?utm_source=GHsponsor&utm_medium=GHsponsor&utm_campaign=example-oauth2-server">auth0.com/overview</a>.</td>
  </tr>
</table>

## Take a quick look

This is a ready to run example, let's take a quick experience at first. To
run the example, we need to install all the dependencies:

    $ pip install -r requirements.txt

Set Flask and Authlib environment variables:

    # disable check https (DO NOT SET THIS IN PRODUCTION)
    $ export AUTHLIB_INSECURE_TRANSPORT=1

Create Database and run the development server:

    $ flask initdb
    $ flask run

Now, you can open your browser with `http://127.0.0.1:5000/`, login with any
name you want.

Before testing, we need to create a client:

![create a client](https://user-images.githubusercontent.com/290496/38811988-081814d4-41c6-11e8-88e1-cb6c25a6f82e.png)

Get your `client_id` and `client_secret` for testing. In this example, we
have enabled `password` grant types, let's try:

    $ curl -u ${client_id}:${client_secret} -XPOST http://127.0.0.1:5000/oauth/token -F grant_type=password -F username=${username} -F password=valid -F scope=profile

Because this is an example, every user's password is `valid`. For now, you
can read the source in example or follow the long boring tutorial below.

**IMPORTANT**: To test implicit grant, you need to `token_endpoint_auth_method` to `none`.

## Preparation

Assume this example doesn't exist at all. Let's write an OAuth 2.0 server
from scratch step by step.

### Create folder structure

Here is our Flask website structure:

```
app.py         --- FLASK_APP
website/
  app.py       --- Flask App Factory
  models.py    --- SQLAlchemy Models
  oauth2.py    --- OAuth 2.0 Provider Configuration
  routes.py    --- Routes views
  templates/
```

### Installation

Create a virtualenv and install all the requirements. You can also put the
dependencies into `requirements.txt`:

```
Flask
Flask-SQLAlchemy
Authlib
```

### Hello World!

Create a home route view to say "Hello World!". It is used to test if things
working well.


```python
# website/routes.py
from Flask import Blueprint
bp = Blueprint(__name__, 'home')

@bp.route('/')
def home():
    return 'Hello World!'
```

```python
# website/app.py
from flask import Flask

def create_app(config=None):
    app = Flask(__name__)
    # load app sepcified configuration
    if config is not None:
        if isinstance(config, dict):
            app.config.update(config)
        elif config.endswith('.py'):
            app.config.from_pyfile(config)
    return app
    
def setup_app(app):
    app.register_blueprint(bp, url_prefix='')
```

```python
# app.py
from website.app import create_app

app = create_app({
    'SECRET_KEY': 'secret',
})
```


The "Hello World!" example should run properly:

    $ FLASK_APP=app.py flask run

## Define Models

We will use SQLAlchemy and SQLite for our models. You can also use other
databases and other ORM engines. Authlib has some built-in SQLAlchemy mixins
which will make it easier for creating models.

Let's create the models in `website/models.py`. We need four models, which are

- User: you need a user to test and create your application
- OAuth2Client: the oauth client model
- OAuth2AuthorizationCode: for `grant_type=code` flow
- OAuth2Token: save the `access_token` in this model.

Check how to define these models in `website/models.py`.

## Implement Grants

The source code is in `website/oauth2.py`. There are four standard grant types:

- Authorization Code Grant
- Implicit Grant
- Client Credentials Grant
- Resource Owner Password Credentials Grant

And Refresh Token is implemented as a Grant in Authlib. You don't have to do
any thing on Implicit and Client Credentials grants, but there are missing
methods to be implemented in other grants, checkout the source code in
`website/oauth2.py`.


## `@require_oauth`

Authlib has provided a `ResourceProtector` for you to create the decorator
`@require_oauth`, which can be easily implemented:

```py
from authlib.flask.oauth2 import ResourceProtector

require_oauth = ResourceProtector()
```

For now, only Bearer Token is supported. Let's add bearer token validator to
this ResourceProtector:

```py
from authlib.flask.oauth2.sqla import create_bearer_token_validator

# helper function: create_bearer_token_validator
bearer_cls = create_bearer_token_validator(db.session, OAuth2Token)
require_oauth.register_token_validator(bearer_cls())
```

Check the full implementation in `website/oauth2.py`.


## OAuth Routes

For OAuth server itself, we only need to implement routes for authentication,
and issuing tokens. Since we have added token revocation feature, we need a
route for revoking too.

Checkout these routes in `website/routes.py`. Their path begin with `/oauth/`.


## Other Routes

But that is not enough. In this demo, you will need to have some web pages to
create and manage your OAuth clients. Check that `/create_client` route.

And we have an API route for testing. Check the code of `/api/me`.

## Finish

Now, init everything in `website/app.py`. And here you go. You've got an OAuth
2.0 server.

Read more information on <https://docs.authlib.org/>.

## License

Same license with [Authlib](https://authlib.org/plans).
