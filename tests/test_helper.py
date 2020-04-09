from unittest.mock import MagicMock

def mock_response(fixture_name):

  """
  Accepts the name of a file in the fixtures directory
  Returns a mocked response object
  """

  f = open("tests/fixtures/" + fixture_name, "r")
  fixture_content = f.read()

  response = MagicMock()
  response.content = fixture_content

  return response