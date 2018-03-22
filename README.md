# Example for OAuth 2 Server

Example OAuth 2 server for [Authlib](https://authlib.org/). If you are
looking for old Flask-OAuthlib implementation, check the `flask-oauthlib`
branch.

## How to run

Install the required dependencies:

    $ pip install -r requirements.txt

Set Flask and Authlib environment variables:

    $ export FLASK_APP=app.py
    $ export FLASK_DEBUG=1
    # disable check https
    $ export AUTHLIB_INSECURE_TRANSPORT=1

Create Database:

    $ flask initdb

Start Flask development server:

    $ flask run

## How to test
