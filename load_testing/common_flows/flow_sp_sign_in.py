from .flow_helper import (
    authenticity_token,
    do_request,
    get_env,
    otp_code,
    querystring_value,
    random_cred,
    sp_signin_link,
    sp_signout_link,
    url_without_querystring,
)
"""
*** Service Provider Sign In Flow ***

Using this flow requires that a Service Provider be running and configured to work with HOST
"""

def do_sp_sign_in(context):

  sp_root_url = get_env("SP_HOST")

  # GET the SP root, which should contain a login link, give it a friendly name for output
  resp = do_request(
      context, "get", sp_root_url, sp_root_url, {}, {}, sp_root_url
  )
  signin_link = sp_signin_link(resp)

  # GET the signin link we found
  resp = do_request(
      context,
      "get",
      signin_link,
      "/?request_id=",
      {},
      {},
      url_without_querystring(signin_link),
  )
  auth_token = authenticity_token(resp)
  request_id = querystring_value(resp.url, "request_id")

  # POST username and password
  credentials = random_cred(context.num_users)
  resp = do_request(
      context,
      "post",
      "/",
      "/login/two_factor/sms",
      {
          "user[email]": credentials["email"],
          "user[password]": credentials["password"],
          "user[request_id]": request_id,
          "authenticity_token": auth_token,
      },
  )
  auth_token = authenticity_token(resp)
  code = otp_code(resp)

  # POST to 2FA
  # If first time for user, this redirects to "completed", otherwise to the SP root.
  resp = do_request(
      context,
      "post",
      "/login/two_factor/sms",
      None,
      {"code": code, "authenticity_token": auth_token,},
  )

  if "/sign_up/completed" in resp.url:
      # POST to completed, should go back to the SP
      auth_token = authenticity_token(resp)
      resp = do_request(
          context,
          "post",
          "/sign_up/completed",
          sp_root_url,
          {"authenticity_token": auth_token,},
      )

  # We should now be at the SP root, with a "logout" link.
  # The test SP goes back to the root, so we'll test that for now
  logout_link = sp_signout_link(resp)
  do_request(
      context,
      "get",
      logout_link,
      sp_root_url,
      {},
      {},
      url_without_querystring(logout_link),
  )
