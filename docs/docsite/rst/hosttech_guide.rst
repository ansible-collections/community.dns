.. _ansible_collections.community.dns.docsite.hosttech_guide:

HostTech DNS Guide
==================

The :ref:`community.dns collection <plugins_in_community.dns>` offers several modules for working with the `HostTech DNS service <https://www.hosttech.ch/>`_.
The modules support both the old `WSDL-based API <https://ns1.hosttech.eu/public/api?wsdl>`_ and the new `JSON REST based API <https://api.ns1.hosttech.eu/api/documentation/>`_.

The collection provides four modules for working with HostTech DNS:

- ``community.dns.hosttech_dns_record``: create/update/delete DNS records
- ``community.dns.hosttech_dns_record_info``: retrieve information on DNS records
- ``community.dns.hosttech_dns_records``: bulk synchronize DNS records
- ``community.dns.hosttech_dns_zone_info``: retrieve zone information

Authentication, Requirements and APIs
-------------------------------------

HostTech currently has two APIs for working with DNS records: the old WSDL-based API, and the new JSON-based REST API. We recommend using the new REST API if possible.

JSON REST API
~~~~~~~~~~~~~

To use the JSON REST API, you need to create a API token. You can manage API tokens in the "DNS Editor" in the "API" section. You must provide the token to the ``hosttech_token`` option of the modules:

.. code-block:: yaml+jinja

  - community.dns.hosttech_dns_record:
      hosttech_token: '{{ token }}'
      ...

In the examples in this guide, we will leave the authentication options away. Please note that you can set them globally with ``module_defaults`` (see :ref:`module_defaults`).

WSDL API
~~~~~~~~

To use the WSDL API, you need to set API credentials. These can be found and changed in the "Servercenter" and there in the "Solutions" section under settings for the "DNS Tool". The username is fixed, but the password can be changed. The credentials must be provided to the ``hosttech_username`` and ``hosttech_password`` options of the modules.

You also need to install the `lxml Python module <https://pypi.org/project/lxml/>`_ to work with the WSDL API. This can be done before using the modules:

.. code-block:: yaml+jinja

  - name: Make sure lxml is installed
    pip:
      name: lxml

  - community.dns.hosttech_dns_record:
      hosttech_username: '{{ username }}'
      hosttech_password: '{{ password }}'
      ...

In the examples in this guide, we will leave the authentication options away. Please note that you can set them globally with ``module_defaults`` (see :ref:`module_defaults`).

Working with DNS zones
----------------------

The ``community.dns.hosttech_dns_zone_info`` module allows to query information on a zone. The zone can be identified both by its name and by its ID (which is an integer):

.. code-block:: yaml+jinja

    - name: Query zone information by name
      community.dns.hosttech_dns_zone_info:
        zone: example.com
      register: result

    - name: Query zone information by name
      community.dns.hosttech_dns_zone_info:
        zone_id: 42
      register: result

The module returns both the zone name and zone ID, so this module can be used to convert from zone ID to zone name and vice versa:

.. code-block:: yaml+jinja

    - ansible.builtin.debug:
        msg: |
            The zone ID: {{ result.zone_id }}
            The zone name: {{ result.zone_name }}

Working with DNS records
------------------------

Querying DNS records
~~~~~~~~~~~~~~~~~~~~

...

Creating and updating DNS records
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

...

Bulk synchronization of DNS records
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

...
