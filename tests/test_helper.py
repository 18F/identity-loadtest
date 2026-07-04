from unittest.mock import MagicMock

import os

FIXDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures"))


def mock_response(fixture_name):
    """
    Accepts the name of a file in the fixtures directory
    Returns a mocked response object
    """

    f = open(os.path.abspath(os.path.join(FIXDIR, fixture_name)), "r")
    fixture_content = f.read()

    response = MagicMock()
    response.content = fixture_content

    return response


def mock_context():
    context = MagicMock()
    response = context.client.get.return_value.__enter__.return_value
    response.status_code = 500
    response.reason = "Internal Server Error"
    response.url = "http://example.test/example"
    response.request.method = "GET"

    return context
