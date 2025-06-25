..
  Copyright (c) Ansible Project
  GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
  SPDX-License-Identifier: GPL-3.0-or-later

.. _ansible_collections.community.dns.docsite.hetzner_guide:

Hetzner DNS Guide
=================

.. contents:: Contents
   :local:
   :depth: 2

The :anscollection:`community.dns collection <community.dns>` offers several modules for working with the `Hetzner DNS service <https://docs.hetzner.com/dns-console/dns/>`_.
The modules use the `JSON REST based API <https://dns.hetzner.com/api-docs/>`_.

The collection provides six modules for working with Hetzner DNS:

- :ansplugin:`community.dns.hetzner_dns_record#module`: create/update/delete single DNS records
- :ansplugin:`community.dns.hetzner_dns_record_info#module`: retrieve information on DNS records
- :ansplugin:`community.dns.hetzner_dns_record_set#module`: create/update/delete DNS record sets
- :ansplugin:`community.dns.hetzner_dns_record_set_info#module`: retrieve information on DNS record sets
- :ansplugin:`community.dns.hetzner_dns_record_sets#module`: bulk synchronize DNS record sets
- :ansplugin:`community.dns.hetzner_dns_zone_info#module`: retrieve zone information

If you are interested in migrating from the `markuman.hetzner_dns collection <https://galaxy.ansible.com/ui/repo/published/markuman/hetzner_dns/>`_, please see :ref:`ansible_collections.community.dns.docsite.hetzner_guide.migration_markuman_hetzner_dns`.

It also provides an inventory plugin:

- :ansplugin:`community.dns.hetzner_dns_records#inventory`: create inventory from DNS records

To find out which record types are supported and how to use them, look at :ref:`ansible_collections.community.dns.docsite.hetzner_guide.records`.

Authentication
--------------

To use Hetzner's API, you need to create an API token. You can manage API tokens in the "API tokens" menu entry in your user menu in the `DNS Console <https://dns.hetzner.com/>`_. You must provide the token to the :ansopt:`hetzner_token` option of the modules, its alias :ansopt:`api_token`, or pass it on in the :envvar:`HETZNER_DNS_TOKEN` environment variable:

.. code-block:: yaml+jinja

  - community.dns.hetzner_dns_record:
      hetzner_token: '{{ token }}'
      # ...

In the examples in this guide, we will leave the authentication options away. Please note that you can set them globally with ``module_defaults`` (see :ref:`module_defaults`) or with an environment variable for the user and machine where the modules are run on.

Using the ``community.dns.hetzner`` module defaults group
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To avoid having to specify common parameters for all Hetzner DNS modules in every task, you can use the ``community.dns.hetzner`` module defaults group:

.. code-block:: yaml+jinja

    ---
    - name: Hetzner DNS
      hosts: localhost
      gather_facts: false
      module_defaults:
        group/community.dns.hetzner:
          hetzner_token: '{{ token }}'
      tasks:
        - name: Query zone information
          community.dns.hetzner_dns_zone_info:
            zone_name: example.com
          register: result

        - name: Set A records for www.example.com
          community.dns.hetzner_dns_record_set:
            state: present
            zone_name: example.com
            type: A
            prefix: www
            value:
              - 192.168.0.1

Here all two tasks will use the options set for the module defaults group.

Working with DNS zones
----------------------

The :ansplugin:`community.dns.hetzner_dns_zone_info module <community.dns.hetzner_dns_zone_info#module>` allows to query information on a zone. The zone can be identified both by its name and by its ID (which is an integer):

.. code-block:: yaml+jinja

    - name: Query zone information by name
      community.dns.hetzner_dns_zone_info:
        zone_name: example.com
      register: result

    - name: Query zone information by ID
      community.dns.hetzner_dns_zone_info:
        zone_id: aBcDeFgHiJlMnOpQrStUvW
      register: result

The module returns both the zone name and zone ID, so this module can be used to convert from zone ID to zone name and vice versa:

.. code-block:: yaml+jinja

    - ansible.builtin.debug:
        msg: |
            The zone ID: {{ result.zone_id }}
            The zone name: {{ result.zone_name }}

Working with DNS records
------------------------

.. note::

  By default, TXT record values returned and accepted by the modules and plugins in this collection are unquoted. This means that  you do not have to add double quotes (``"``), and escape double quotes (as ``\"``) and backslashes (as ``\\``). All modules and plugins which work with DNS records support the :ansopt:`community.dns.hetzner_dns_record_set#module:txt_transformation` option which allows to configure this behavior.

Querying DNS records and record sets
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :ansplugin:`community.dns.hetzner_dns_record_set_info module <community.dns.hetzner_dns_record_set_info#module>` allows to query DNS record sets from the API. It can be used to query a single record set:

.. code-block:: yaml+jinja

    - name: Query single record
      community.dns.hetzner_dns_record_set_info:
        zone_name: example.com
        type: A  # IPv4 addresses
        what: single_record  # default value
        # Either specify a record name:
        record: www.example.com
        # Or a record prefix ('' is the zone itself):
        prefix: www
      register: result

    - name: Show IPv4 addresses if record exists
      ansible.builtin.debug:
        msg: >
          IPv4s are {{ result.set.value | join(', ') }},
          TTL is {{ result.set.ttl }}
      when: result.set is truthy

    - name: Show that record is not set
      ansible.builtin.debug:
        msg: There is no A record for www.example.com
      when: result.set is falsy

In all examples in this section, you can replace :ansopt:`community.dns.hetzner_dns_record_set_info#module:zone_name=example.com` by :ansopt:`community.dns.hetzner_dns_record_set_info#module:zone_id=aBcDeFgHiJlMnOpQrStUvW` with the zone's ID string.

You can also query a list of all record sets for a record name or prefix:

.. code-block:: yaml+jinja

    - name: Query all records for www.example.com
      community.dns.hetzner_dns_record_set_info:
        zone_name: example.com
        what: all_types_for_record
        # Either specify a record name:
        record: www.example.com
        # Or a record prefix ('' is the zone itself):
        prefix: www
      register: result

    - name: Show all records for www.example.com
      ansible.builtin.debug:
        msg: >
          {{ item.type }} record with TTL {{ item.ttl }} has
          values {{ item.value | join(', ') }}
      loop: result.sets

Finally you can query all record sets for a zone:

.. code-block:: yaml+jinja

    - name: Query all records for a zone
      community.dns.hetzner_dns_record_set_info:
        zone_name: example.com
        what: all_records
      register: result

    - name: Show all records for the example.com zone
      ansible.builtin.debug:
        msg: >
          {{ item.type }} record for {{ item.record }} with
          TTL {{ item.ttl }} has values {{ item.value | join(', ') }}
      loop: result.sets

If you are interested in individual DNS records, and not record sets, you should use the :ansplugin:`community.dns.hetzner_dns_record_info module <community.dns.hetzner_dns_record_info#module>`. It supports the same limiting options as the :ansplugin:`community.dns.hetzner_dns_record_set_info module <community.dns.hetzner_dns_record_set_info#module>`.

Creating and updating DNS single records
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you do not want to add/remove values, but replace values, you will be interested in modifying a **record set** and not a single record. This is in particular important when working with ``CNAME`` and ``SOA`` records.

The :ansplugin:`community.dns.hetzner_dns_record module <community.dns.hetzner_dns_record#module>` allows to set, update and remove single DNS records. Setting and updating can be done as follows. Records will be matched by record name and type, and the TTL value will be updated if necessary:

.. code-block:: yaml+jinja

    - name: Add an A record with value 1.1.1.1 for www.example.com, resp. make sure the TTL is 300
      community.dns.hetzner_dns_record:
        state: present
        zone_name: example.com
        type: A  # IPv4 addresses
        # Either specify a record name:
        record: www.example.com
        # Or a record prefix ('' is the zone itself):
        prefix: www
        value: 1.1.1.1
        ttl: 300

To delete records, simply use :ansopt:`community.dns.hetzner_dns_record#module:state=absent`. Records will be matched by record name and type, and the TTL will be ignored:

.. code-block:: yaml+jinja

    - name: Remove A values for www.example.com
      community.dns.hetzner_dns_record:
        state: absent
        zone_name: example.com
        type: A  # IPv4 addresses
        record: www.example.com
        value: 1.1.1.1

Records of the same type for the same record name with other values are ignored.

Creating and updating DNS record sets
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :ansplugin:`community.dns.hetzner_dns_record_set module <community.dns.hetzner_dns_record_set#module>` allows to set, update and remove DNS record sets. Setting and updating can be done as follows:

.. code-block:: yaml+jinja

    - name: Make sure record is set to the given value
      community.dns.hetzner_dns_record_set:
        state: present
        zone_name: example.com
        type: A  # IPv4 addresses
        # Either specify a record name:
        record: www.example.com
        # Or a record prefix ('' is the zone itself):
        prefix: www
        value:
          - 1.1.1.1
          - 8.8.8.8

If you want to assert that a record has a certain value, set :ansopt:`community.dns.hetzner_dns_record_set#module:on_existing=keep`. Using :ansval:`keep_and_warn` instead will emit a warning if this happens, and :ansval:`keep_and_fail` will make the module fail.

To delete values, you can either overwrite the values with value :ansval:`[]`, or use :ansopt:`community.dns.hetzner_dns_record_set#module:state=absent`:

.. code-block:: yaml+jinja

    - name: Remove A values for www.example.com
      community.dns.hetzner_dns_record_set:
        state: present
        zone_name: example.com
        type: A  # IPv4 addresses
        record: www.example.com
        value: []

    - name: Remove TXT values for www.example.com
      community.dns.hetzner_dns_record_set:
        zone_name: example.com
        type: TXT
        prefix: www
        state: absent

    - name: Remove specific AAAA values for www.example.com
      community.dns.hetzner_dns_record_set:
        zone_name: example.com
        type: AAAA  # IPv6 addresses
        prefix: www
        state: absent
        on_existing: keep_and_fail
        ttl: 300
        value:
          - '::1'

In the third example, :ansopt:`community.dns.hetzner_dns_record_set#module:on_existing=keep_and_fail` is present and an explicit value and TTL are given. This makes the module remove the current value only if there's a AAAA record for ``www.example.com`` whose current value is ``::1`` and whose TTL is 300. If another value is set, the module will not make any change, but fail. This can be useful to not accidentally remove values you do not want to change. To issue a warning instead of failing, use :ansopt:`community.dns.hetzner_dns_record_set#module:on_existing=keep_and_warn`, and to simply not do a change without any indication of this situation, use :ansopt:`community.dns.hetzner_dns_record_set#module:on_existing=keep`.

Bulk synchronization of DNS record sets
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want to set/update multiple records at once, or even make sure that the precise set of records you are providing are present and nothing else, you can use the :ansplugin:`community.dns.hetzner_dns_record_sets module <community.dns.hetzner_dns_record_sets#module>`.

The following example shows up to set/update multiple records at once:

.. code-block:: yaml+jinja

    - name: Make sure that multiple records are present
      community.dns.hetzner_dns_record_sets:
        zone_name: example.com
        record_sets:
          - prefix: www
            type: A
            value:
              - 1.1.1.1
              - 8.8.8.8
          - prefix: www
            type: AAAA
            value:
              - '::1'

The next example shows how to make sure that only the given records are available and all other records are deleted. Note that for the :ansopt:`community.dns.hetzner_dns_record_sets#module:record_sets[].type=NS` record we used :ansopt:`community.dns.hetzner_dns_record_sets#module:record_sets[].ignore=true`, which allows us to skip the value. It tells the module that it should not touch the ``NS`` record for ``example.com``.

.. code-block:: yaml+jinja

    - name: Make sure that multiple records are present
      community.dns.hetzner_dns_record_sets:
        zone_name: example.com
        prune: true
        record_sets:
          - prefix: www
            type: A
            value:
              - 1.1.1.1
              - 8.8.8.8
          - prefix: www
            type: AAAA
            value:
              - '::1'
          - prefix: ''
            type: NS
            ignore: true

.. _ansible_collections.community.dns.docsite.hetzner_guide.migration_markuman_hetzner_dns:

Migrating from ``markuman.hetzner_dns``
---------------------------------------

This section describes how to migrate playbooks and roles from using the `markuman.hetzner_dns collection <https://galaxy.ansible.com/ui/repo/published/markuman/hetzner_dns/>`_ to the Hetzner modules and plugins in the ``community.dns`` collection.

There are three steps for migrating. Two of these steps must be done on migration, the third step can also be done later:

1. Replace the modules and plugins used by the new ones.
2. Adjust module and plugin options if necessary.
3. Avoid deprecated aliases which ease the transition.

The `markuman.hetzner_dns collection <https://galaxy.ansible.com/ui/repo/published/markuman/hetzner_dns/>`_ collection provides three modules and one inventory plugin.

.. note::

  When working with TXT records, please look at the :ansopt:`community.dns.hetzner_dns_record_set#module:txt_transformation` option. By default, the modules and plugins in this collection use **unquoted** values (you do not have to add double quotes and escape double quotes and backslashes), while the modules and plugins in ``markuman.hetzner_dns`` use partially quoted values. You can switch behavior of the ``community.dns`` modules by passing :ansopt:`community.dns.hetzner_dns_record_set#module:txt_transformation=api` or :ansopt:`community.dns.hetzner_dns_record_set#module:txt_transformation=quoted`.

The markuman.hetzner_dns.record module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``markuman.hetzner_dns.zone_info`` module can be replaced by the :ansplugin:`community.dns.hetzner_dns_record module <community.dns.hetzner_dns_record#module>` and the :ansplugin:`community.dns.hetzner_dns_record_set module <community.dns.hetzner_dns_record_set#module>`, depending on what it is used for.

When creating, updating or removing single records, the :ansplugin:`community.dns.hetzner_dns_record module <community.dns.hetzner_dns_record#module>` should be used. This is the case when :ansopt:`purge=false` is specified (the default value). Note that :ansopt:`replace`, :ansopt:`overwrite` and :ansopt:`solo` are aliases of :ansopt:`purge`.

.. code-block:: yaml+jinja

    # Creating and updating DNS records

    - name: Creating or updating a single DNS record with markuman.hetzner_dns
      markuman.hetzner_dns.record:
        zone_name: example.com
        name: localhost
        type: A
        value: 127.0.0.1
        ttl: 60
        # This means the module operates on single DNS entries. If not specified,
        # this is the default value:
        purge: false

    - name: Creating or updating a single DNS record with community.dns
      community.dns.hetzner_dns_record:
        zone_name: example.com
        # 'state' must always be specified:
        state: present
        # 'name' is a deprecated alias of 'prefix', so it can be
        # kept during a first migration step:
        name: localhost
        # 'type', 'value' and 'ttl' do not change:
        type: A
        value: 127.0.0.1
        ttl: 60
        # If type is TXT, you either have to adjust the value you pass,
        # or keep the following option:
        txt_transformation: api

When the ``markuman.hetzner_dns.record`` module is in replace mode, it should be replaced by the :ansplugin:`community.dns.hetzner_dns_record_set module <community.dns.hetzner_dns_record_set#module>`, since then it operates on the *record set* and not just on a single record:

.. code-block:: yaml+jinja

    # Creating and updating DNS record sets

    - name: Creating or updating a record set with markuman.hetzner_dns
      markuman.hetzner_dns.record:
        zone_name: example.com
        name: localhost
        type: A
        value: 127.0.0.1
        ttl: 60
        # This means the module operates on the record set:
        purge: true

    - name: Creating or updating a record set with community.dns
      community.dns.hetzner_dns_record_set:
        zone_name: example.com
        # 'state' must always be specified:
        state: present
        # 'name' is a deprecated alias of 'prefix', so it can be
        # kept during a first migration step:
        name: localhost
        # 'type' and 'ttl' do not change:
        type: A
        ttl: 60
        # 'value' is now a list:
        value:
          - 127.0.0.1
        # Ansible allows to specify lists as a comma-separated string.
        # So for records which do not contain a comma, you can also
        # keep the old syntax, in this case:
        #
        #     value: 127.0.0.1
        #
        # If type is TXT, you either have to adjust the value you pass,
        # or keep the following option:
        txt_transformation: api

When deleting a record, it depends on whether :ansopt:`value` is specified or not. If :ansopt:`value` is specified, the module is deleting a single DNS record, and the :ansplugin:`community.dns.hetzner_dns_record module <community.dns.hetzner_dns_record#module>` should be used:

.. code-block:: yaml+jinja

    # Deleting single DNS records

    - name: Deleting a single DNS record with markuman.hetzner_dns
      markuman.hetzner_dns.record:
        zone_name: example.com
        state: absent
        name: localhost
        type: A
        value: 127.0.0.1
        ttl: 60

    - name: Deleting a single DNS record with community.dns
      community.dns.hetzner_dns_record:
        zone_name: example.com
        state: absent
        # 'name' is a deprecated alias of 'prefix', so it can be
        # kept during a first migration step:
        name: localhost
        # 'type', 'value' and 'ttl' do not change:
        type: A
        value: 127.0.0.1
        ttl: 60
        # If type is TXT, you either have to adjust the value you pass,
        # or keep the following option:
        txt_transformation: api

When :ansopt:`value` is not specified, the ``markuman.hetzner_dns.record`` module will delete all records for this prefix and type. In that case, it operates on a record set and the :ansplugin:`community.dns.hetzner_dns_record_set module <community.dns.hetzner_dns_record_set#module>` should be used:

.. code-block:: yaml+jinja

    # Deleting multiple DNS records

    - name: Deleting multiple DNS records with markuman.hetzner_dns
      markuman.hetzner_dns.record:
        zone_name: example.com
        state: absent
        name: localhost
        type: A

    - name: Deleting a single DNS record with community.dns
      community.dns.hetzner_dns_record_set:
        zone_name: example.com
        state: absent
        # 'name' is a deprecated alias of 'prefix', so it can be
        # kept during a first migration step:
        name: localhost
        # 'type' does not change:
        type: A

A last step is replacing the removed alias ``name`` of :ansopt:`community.dns.hetzner_dns_record_set#module:prefix` by :ansopt:`community.dns.hetzner_dns_record_set#module:prefix`.

The markuman.hetzner_dns.record_info module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``markuman.hetzner_dns.record_info`` module can be replaced by the :ansplugin:`community.dns.hetzner_dns_record_info module <community.dns.hetzner_dns_record_info#module>`. The main difference is that instead of by the :ansopt:`filters` option, the output is controlled by the :ansopt:`community.dns.hetzner_dns_record_info#module:what` option (choices :ansval:`single_record`, :ansval:`all_types_for_record`, and :ansval:`all_records`), the :ansopt:`community.dns.hetzner_dns_record_info#module:type` option (needed when :ansopt:`community.dns.hetzner_dns_record_info#module:what=single_record`), and the :ansopt:`community.dns.hetzner_dns_record_info#module:record` and :ansopt:`community.dns.hetzner_dns_record_info#module:prefix` options (needed when :ansopt:`community.dns.hetzner_dns_record_info#module:what` is not :ansval:`all_records`).

The markuman.hetzner_dns.zone_info module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``markuman.hetzner_dns.zone_info`` module can be replaced by the :ansplugin:`community.dns.hetzner_dns_zone_info module <community.dns.hetzner_dns_zone_info#module>`. The main differences are:

1. The parameter :ansopt:`name` must be changed to :ansopt:`community.dns.hetzner_dns_zone_info#module:zone_name` or :ansopt:`community.dns.hetzner_dns_zone_info#module:zone`.
2. The return value :ansretval:`community.dns.hetzner_dns_zone_info#module:zone_info` no longer has the ``name`` and ``id`` entries. Use the return values :ansretval:`community.dns.hetzner_dns_zone_info#module:zone_name` and :ansretval:`community.dns.hetzner_dns_zone_info#module:zone_id` instead.

The markuman.hetzner_dns.inventory inventory plugin
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``markuman.hetzner_dns.inventory`` inventory plugin can be replaced by the :ansplugin:`community.dns.hetzner_dns_records inventory plugin <community.dns.hetzner_dns_records#inventory>`. Besides the plugin name, no change should be necessary.


.. _ansible_collections.community.dns.docsite.hetzner_guide.records:

Supported DNS records
---------------------

Here you can find a list of supported DNS records together with their syntax for the :ansopt:`value` field:

- **A** records: IPv4 address.

  Simply provide the IPv4 address as :ansopt:`value`, such as ``127.0.0.1``.
- **AAAA** records: IPv6 address.

  Simply provide the IPv6 address as :ansopt:`value`, such as ``3fff::1:2``.
- **CAA** records: Certification Authority Authorization

  The record's :ansopt:`value` is of the form ``<flags> <tag> <value>``,
  where ``<flags>`` is an unsigned integer between 0 and 255;
  ``<tag>`` is a ASCII string such as ``issue``, ``issuewild``, or ``iodef``;
  and ``<value>`` is the value enclosed in double quotes.
  An example entry is ``0 issue "letsencrypt.org"``.
  The exact syntax is explained in L(Section 4.1.1 of RFC 8659, https://datatracker.ietf.org/doc/html/rfc8659#name-syntax).
- **CNAME** records: Canonical Name.
- **DANE** records: DNS-based Authentication of Named Entities.
- **DS** records: Delegation Signer.
- **HINFO** records: Host Information.
- **MX** records: Mail Exchange.

  The record's :ansopt:`value` is of the form ``<priority> <hostname>``,
  where ``<priority>`` is an unsigned integer and ``<hostname>`` a DNS hostname.
- **NS** records: Name Server record.

  The record's :ansopt:`value` is the list of DNS names of the authoritative nameservers for this zone.
- **RP** records: Responsible Person.
- **SOA** records: Start Of Authority record.
- **SRV** records: Service locator.

  The record's :ansopt:`value` is of the form ``<priority> <weight> <port> <target>``.
- **TLSA** records: TLSA certificate association.

  This record is for DANE.
- **TXT** records: Text record.

  The value is simply a free form text. Its use depends on its context.
