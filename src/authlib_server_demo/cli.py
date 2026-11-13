import os

from dotenv import load_dotenv

from authlib_server_demo import create_app


def run():
    """Run the Authlib server demo."""
    load_dotenv()
    app = create_app()
    host = os.environ.get("FLASK_RUN_HOST", "127.0.0.1")
    port = int(os.environ.get("FLASK_RUN_PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run()
