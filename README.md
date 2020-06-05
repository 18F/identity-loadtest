# `identity-loadtest`

Load testing scripts and tooling for the Login.gov, currently using [`locust`](http://locust.io).

## Local setup

### Python and Locust

Install python3 and dependencies

```sh
brew install python
pip3 install -r requirements.txt
```

### Login.gov IdP

Login IdP must be running with these settings in `application.yml`

```yml
telephony_adapter: 'test'
disable_email_sending: 'true'
enable_load_testing_mode: 'true'
enable_rate_limiting: 'false'
otp_delivery_blocklist_maxretry: 1000000
```

## Running Locust

You can only run one locustfile at a time, there are many to choose from that end in `.locustfile.py`.

- `clients` is the total number of concurrent Locust users.
- `hatch-rate` is the number of users to spawn per second, starting from zero.

### Common `locust` cmd line arguments

```sh
--host http://localhost:3000 --clients 1 --hatch-rate 1 --run-time 15m --no-web
```

Or omit `--no-web` and open <http://localhost:8089> for a UI.

Add `--csv=<base-name>` to generate CSV output

## Adding new tests

Add new `*.loucstfile.py` files to the project for new test scenarios.

### Sign-Up load test

- This will create lots of users in your database

```sh
locust --locustfile load_testing/sign_up.locustfile.py --host http://localhost:3000 --clients 1 --hatch-rate 1 --run-time 15m --no-web
```

### Sign-In load test

- You must run a rake task in the IdP before using this test, something like: `rake dev:random_users NUM_USERS=100 SCRYPT_COST='800$8$1$'` [(source)](https://github.com/18F/identity-idp/blob/master/lib/tasks/dev.rake)
- You also must pass in a matching `NUM_USERS=100` to the locust call.

```sh
NUM_USERS=100 locust --locustfile load_testing/sign_in.locustfile.py --host http://localhost:3000 --clients 1 --hatch-rate 1 --run-time 15m --no-web
```

### Sign-In remembered device load test

Tests sign ins simulating a very high (90%) ratio of users who are signing back
in using a remembered browser (device).

- You must run a rake task in the IdP before using this test, something like: `rake dev:random_users NUM_USERS=100 SCRYPT_COST='800$8$1$'` [(source)](https://github.com/18F/identity-idp/blob/master/lib/tasks/dev.rake)
- You also must pass in a matching `NUM_USERS=100` to the locust call.

```sh
NUM_USERS=100 locust --locustfile load_testing/sign_in_remember_me.locustfile.py --host http://localhost:3000 --clients 1 --hatch-rate 1 --run-time 15m --no-web
```

### Sign up + Sign-In load test

- This test mixes Sign-up and Sign-in together
- You must run the same rake task as above in the IdP before using this test
- You also must pass in a matching `NUM_USERS=100` to the locust call.

```sh
NUM_USERS=100 locust --locustfile load_testing/sign_up_sign_in.locustfile.py --host http://localhost:3000 --clients 1 --hatch-rate 1 --run-time 15m --no-web
```

### IAL2 load tests

- Same rules as above, but use `ial2_sign_*` filenames.
- Uses "desktop proofing" experience, not mobile.
- Requires `mont-front.jpeg` and `mont-back.jpeg` drivers license images

```sh
NUM_USERS=100 locust --locustfile load_testing/ial2_sign_in.locustfile.py --host http://localhost:3000 --clients 1 --hatch-rate 1 --run-time 15m --no-web
```

```sh
NUM_USERS=100 locust --locustfile load_testing/ial2_sign_up.locustfile.py --host http://localhost:3000 --clients 1 --hatch-rate 1 --run-time 15m --no-web
```

### SP Sign in load test

- This requires that [`identity-oidc-sinatra`](https://github.com/18F/identity-oidc-sinatra) be running as an SP
- This requires the `NUM_USERS` env varible
- This requires the `SP_HOST` env varible, something like `SP_HOST=http://localhost:9292`

```sh
NUM_USERS=100 SP_HOST=http://localhost:9292 locust --locustfile load_testing/sp_sign_in.locustfile.py --host http://localhost:3000 --clients 1 --hatch-rate 1 --run-time 15m --no-web
```


### Production Simulator load test

This is a hybrid test with the test mix roughly matching Login.gov's
workload.  (Subject to change.   See test source for details.)

The ratio of remembered devices for sign ins can be adjusted with
the __REMEMBERED_PERCENT__ variable.  (Default: 60)

For uniformity and simple calculation, test ratios should add up to
10000 (1 == 0.01%) and can be adjusted by setting a corresponding
environment variable.  The following are available, and defaults
can be found at the top of `load_testing/production_simulator.locustfile.py`:

* __RATIO_SIGN_IN__: Sign in test using REMEMBERED_PERCENT remember me
                      ratio.
* __RATIO_SIGN_UP__: Sign up test ratio.
* __RATIO_SIGN_IN_AND_PROOF__: Sign in followed by IAL2 proofing ratio.
* __RATIO_SIGN_UP_AND_PROOF__: Sign up followed by IAL2 proofing ratio.
* __RATIO_SIGN_IN_USER_NOT_FOUND__: Failed sign in with nonexistent user.
* __RATIO_SIGN_IN_INCORRECT_PASSWORD__: Failed sign in with bad password.
* __RATIO_SIGN_IN_INCORRECT_SMS_OTP__: Failed sign in with bad SMS OTP.
 
Test requirements:
- Requires prepopulated users (See [Sign-In load test](#sign-in-load-test))
- Requires `mont-front.jpeg` and `mont-back.jpeg` drivers license images (See [IAL2 load tests](#ial2-load-tests))
- You also must pass in a matching `NUM_USERS=100` to the locust call.

Example (including overrides of the sign in and sign up tests)
```sh
NUM_USERS=100 RATIO_SIGN_IN=5000 RATIO_SIGN_UP=1010 locust --locustfile load_testing/production_simulator.locustfile.py --host http://localhost:3000 --clients 1 --hatch-rate 1 --run-time 15m --no-web
```

## Running the test suite

There are tests for these load tests, find them in the `tests` folder.

```sh
# Run the tests
pytest

# Run the tests and show coverage
coverage run -m pytest
coverage report
```

If you install the [CircleCI CLI](https://circleci.com/docs/2.0/local-cli) you can test a CircleCI run in a local Docker container with `circleci local execute`.

## Debugging Locust scripts

The HTTP Library is called Requests: <https://requests.readthedocs.io/en/master/>

The python debugger _should_ just work. [Here are some commands](https://docs.python.org/3/library/pdb.html#debugger-commands) The following will drop you into a debugger:

```py
import pdb; pdb.set_trace()
```
