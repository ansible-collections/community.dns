from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.basic import missing_required_lib
import traceback

REQUESTS_IMP_ERR = None
try:
    import requests
    HAS_REQUESTS = True
except Exception:
    REQUESTS_IMP_ERR = traceback.format_exc()
    HAS_REQUESTS = False


class AdGuardHomeAPIHandler:
    def __init__(self, params, fail_json):
        if not HAS_REQUESTS:
            fail_json(
                msg=missing_required_lib("python-requests", url='https://requests.readthedocs.io/en/latest/'),
                exception=REQUESTS_IMP_ERR
            )

        username = params.get('username')
        password = params.get('password').encode("utf-8")
        self.auth = requests.auth.HTTPBasicAuth(username, password)

        host = params.get('host')
        self.url = f"{host}/control/rewrite"

        self.ssl_verify = params.get('ssl_verify')
        self.fail_json = fail_json

    def list(self):
        try:
            response = requests.get(
                self.url + "/list",
                auth=self.auth,
                verify=self.ssl_verify
            )

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            self.fail_json(msg=str(e), exception=type(e).__name__)

    def add_or_delete(self, domain, answer, method, target):
        """
        the delete api requires the matching answer value.
        but because we make the answer value optional, it's
        taken from previous `find_and_compare` function.
        """
        if method == "add":
            answer_value = answer
        else:
           answer_value = target["answer"] if answer is None else answer

        data = {
            "domain": domain,
            "answer": answer_value
        }
        try:
            response = requests.post(
                self.url + "/" + method,
                json=data,
                auth=self.auth,
                verify=self.ssl_verify
            )
            response.raise_for_status()
            return response.status_code

        except requests.exceptions.RequestException as e:
            self.fail_json(msg=str(e), exception=type(e).__name__)

    def update(self, domain, answer, target):
        data = {
            "target": target,
            "update": {
                "domain": domain,
                "answer": answer
            }
        }
        try:
            response = requests.put(
                self.url + "/update",
                json=data,
                auth=self.auth,
                verify=self.ssl_verify
            )
            response.raise_for_status()
            return response.status_code

        except requests.exceptions.RequestException as e:
            self.fail_json(msg=str(e), exception=type(e).__name__)
