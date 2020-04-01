import os
import sys
from locust import HttpLocust, TaskSet, task, between
from locust_helpers import do_request, authenticity_token, otp_code 
from common_flows import do_sign_in
from faker import Faker

class IAL2SignInLoad(TaskSet):
    def on_start(self):
        print("*** Starting IAL2 Sign-In load tests with " + os.environ.get('NUM_USERS') + " users ***")

    def on_stop(self):
        print("*** Ending IAL2 Sign-In load tests ***")

    """ @task(<weight>) : value=3 executes 3x as often as value=1 """
    """ Things inside task are synchronous. Tasks are async """
    @task(1)
    def sign_in_and_verify_path(self):

      """
      Here's the flow:
      1.  Login flow
      2.  GET  /verify
      3.  POST /verify/doc_auth/welcome
      4.  POST /verify/doc_auth/upload?type=desktop
      5.  POST /verify/doc_auth/front_image
      6.  POST /verify/doc_auth/back_image
      7.  POST /verify/doc_auth/ssn
      8.  POST /verify/doc_auth/verify
      9.  POST /verify/doc_auth/doc_success
      10. POST /verify/doc_auth/phone
      11. POST /verify/otp_delivery_method
      12. POST /verify/phone_confirmation
      13. POST /verify/review
      14. POST /verify/confirmations
      15. GET  /verify (redirects -> /verify/activated)
      """

      #  Sign in
      do_sign_in(self)

      #  Get /account page
      do_request(self, 'get', '/account', '/account')

      # Request IAL2 Verification
      resp = do_request(self, 'get', '/verify', '/verify/doc_auth')
      auth_token = authenticity_token(resp)
      
      # Post consent to Welcome
      resp = do_request(self, 'post',
        '/verify/doc_auth/welcome',
        '/verify/doc_auth/upload',
        { '_method': 'put',
          'ial2_consent_given': 'true',
          'authenticity_token': auth_token,
        })
      auth_token = authenticity_token(resp)

      # Choose Desktop flow
      resp = do_request(self, 'post',
        '/verify/doc_auth/upload?type=desktop',
        '/verify/doc_auth/front_image',
        { '_method': 'put',
          'authenticity_token': auth_token,
        })
      auth_token = authenticity_token(resp)

      # Post the Front Image of the license
      front_path = sys.path[0] + "/load_testing/mont-front.jpeg"
      image = open(front_path, 'rb')
      resp = do_request(self, 'post',
        '/verify/doc_auth/front_image',
        '/verify/doc_auth/back_image',
        { '_method': 'put',
          'authenticity_token': auth_token,
        },
        { 'doc_auth[image]': image
        })
      auth_token = authenticity_token(resp)

      # Post the Back Image of the license
      back_path = sys.path[0] + "/load_testing/mont-back.jpeg"
      image = open(back_path, 'rb')
      resp = do_request(self, 'post',
        '/verify/doc_auth/back_image',
        '/verify/doc_auth/ssn',
        { '_method': 'put',
          'authenticity_token': auth_token,
        },
        { 'doc_auth[image]': image
        })
      auth_token = authenticity_token(resp)

      # SSN - use faker to get unique SSNs
      fake = Faker()
      ssn = fake.ssn()
      # print("*** Using ssn: " + ssn)
      resp = do_request(self, 'post',
        '/verify/doc_auth/ssn',
        '/verify/doc_auth/verify',
        { '_method': 'put',
          'authenticity_token': auth_token,
          'doc_auth[ssn]': ssn,
        })
      # There are three auth tokens on the response, get the second
      auth_token = authenticity_token(resp, 1)

      # You can debug by issuing a GET and checking the expected path
      # resp = get_request(self, "/verify", "/verify/doc_auth/verify")
      # auth_token = authenticity_token(resp)
 
      # Verify
      resp = do_request(self, 'post',
        '/verify/doc_auth/verify',
        '/verify/doc_auth/doc_success',
        { '_method': 'put',
          'authenticity_token': auth_token,
        })
      auth_token = authenticity_token(resp)

      # Continue after doc success
      resp = do_request(self, 'post',
        '/verify/doc_auth/doc_success',
        '/verify/phone',
        { '_method': 'put',
          'authenticity_token': auth_token,
        })
      auth_token = authenticity_token(resp)

      # Enter Phone
      resp = do_request(self, 'post',
        '/verify/phone',
        '/verify/otp_delivery_method',
        { '_method': 'put',
          'authenticity_token': auth_token,
          'idv_phone_form[phone]': '8888888888',
        })
      auth_token = authenticity_token(resp)

       # Select SMS Delivery
      resp = do_request(self, 'post',
        '/verify/otp_delivery_method',
        '/verify/phone_confirmation',
        { '_method': 'put',
          'authenticity_token': auth_token,
          'otp_delivery_preference': 'sms',
        })
      auth_token = authenticity_token(resp)
      try:
          code = otp_code(resp)
      except Exception:
          resp.failure(
              "Could not find pre-filled OTP code, is IDP telephony_disabled: true ?")

      # Verify SMS Delivery
      resp = do_request(self, 'post',
        '/verify/phone_confirmation',
        '/verify/review',
        { '_method': 'put',
          'authenticity_token': auth_token,
          'code': code,
        })
      auth_token = authenticity_token(resp)

      # Re-enter password
      resp = do_request(self, 'post',
        '/verify/review',
        '/verify/confirmations',
        { '_method': 'put',
          'authenticity_token': auth_token,
          'user[password]': 'salty pickles',
        })
      auth_token = authenticity_token(resp)

      # Confirmations
      do_request(self, 'post'
        '/verify/confirmations',
        '/account',
        { 'authenticity_token': auth_token,
        })
        
      # Re-Check verification activated
      do_request(self, 'get', '/verify', '/verify/activated')

      # Now log out
      do_request(self, 'get', '/logout', '/')


class WebsiteUser(HttpLocust):
    task_set = IAL2SignInLoad
    wait_time = between(5, 9)