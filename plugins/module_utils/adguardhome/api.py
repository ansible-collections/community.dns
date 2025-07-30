from __future__ import absolute_import, division, print_function
__metaclass__ = type

import ansible.module_utils.six.moves.urllib.error as urllib_error
from ansible.module_utils.urls import Request
import json


class AdGuardHomeAPIHandler:
    def __init__(self, params, fail_json):
        host = params.get('host')
        self.url = host + "/control/rewrite"

        self.validate_certs = params.get('validate_certs')
        self.fail_json = fail_json
        self.r = Request(
            validate_certs=params.get('validate_certs'),
            url_username=params.get('username'),
            url_password=params.get('password'),
            force_basic_auth=True,
            headers={"Content-Type": "application/json"}
        )

    def list(self):
        try:
            response = self.r.open(
                'GET',
                self.url + "/list"
            )

            return json.loads(response.read().decode('utf-8'))

        except urllib_error.HTTPError as e:
            self.fail_json(msg=e.read())

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

        data = json.dumps({
            "domain": domain,
            "answer": answer_value
        }).encode('utf-8')
        try:
            response = self.r.open(
                'POST',
                self.url + "/" + method,
                data=data,
            )
            return True

        except urllib_error.HTTPError as e:
            self.fail_json(msg=e.read())

    def update(self, domain, answer, target):
        data = json.dumps({
            "target": target,
            "update": {
                "domain": domain,
                "answer": answer
            }
        }).encode('utf-8')
        try:
            response = self.r.open(
                "PUT",
                self.url + "/update",
                data=data,
            )
            return True

        except urllib_error.HTTPError as e:
            self.fail_json(msg=e.read())
