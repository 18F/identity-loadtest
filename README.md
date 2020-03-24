# `identity-loadtest`

Load testing scripts and tooling for the Login.gov IdP application, currently using [`locust`](http://locust.io).

### Dependencies

- Ruby 2.6
- Python 2.8
- Docker
- Local clone of [the `identity-idp` repo](https://www.github.com/18F/identity-idp/)

### Docker Container Build

In `identity-idp`:

```
# if docker is not installed
brew install docker docker-machine
brew cask install docker

# in identity-idp repo
bin/docker_build
docker-compose build
make docker_setup
docker-compose up

# run all tests
docker-compose run app bundle exec rspec
# run one test
docker-compose run app bundle exec rspec spec/file.rb
# run test on already-running cluster
docker-compose exec app bundle exec rspec spec/file.rb
```

For the `locust` container:

```
docker build -f load-test.Dockerfile -t idp-locust .
docker run --rm -p 8089:8089 idp-locust
```

Access the Locust console at `http://127.0.0.1:8089` in a browser. Run tests against `http://app:3000`.

#### Legacy Load Testing Process

We provide some [Locust.io] Python scripts you can run to test how the
app responds to load. You'll need to have Python and `pyenv-virtualenvwrapper`
installed on your machine. If you're on a Mac, the easiest way to set up Python
and `pyenv-virtualenvwrapper` is to run the [laptop script].

Next, you'll need to set the following values in your local `application.yml`:

```
disable_email_sending: 'true'
enable_load_testing_mode: 'true'
telephony_disabled: 'true'
```

Then, run the app with `make run`, and in a new Terminal tab or window, run:
```
make load_test type=create_account
```
This will simulate 3 concurrent users going through the entire account creation
flow and then signing out. To change the number of concurrent users, number of
requests, and the rate at which users are created, modify the `-c`,
`-n`, and `-r` Locust parameters in `bin/load_test`. Run `locust --help` for
more details.

By default, the test will target the host running at `http://localhost:3000`.
To change the target host, set the `TARGET_HOST` environment variable.
For example:

```
TARGET_HOST=https://awesome.loadtesting.com make load_test type=create_account
```

[Locust.io]: http://locust.io/
[laptop script]: https://github.com/18F/laptop
