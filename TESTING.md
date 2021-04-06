# Running tests

## HostTech DNS modules

The CI (based on GitHub Actions) does not run integration tests for the HostTech modules, because they need access to HostTech API credentials. If you have some, copy [`tests/integration/integration_config.yml.template`](https://github.com/ansible-collections/community.dns/blob/main/tests/integration/integration_config.yml.template) to `integration_config.yml` in the same directory, and insert username, key, a test zone (`domain.ch`) and test record (`foo.domain.ch`). Then run `ansible-test integration`. Please note that the test record will be deleted, (re-)created, and finally deleted, so do not use any record you actually need!
