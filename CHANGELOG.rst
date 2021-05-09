======================================
Community DNS Collection Release Notes
======================================

.. contents:: Topics


v1.0.0
======

Release Summary
---------------

First stable release.

Bugfixes
--------

- Update Public Suffix List.

v0.3.0
======

Release Summary
---------------

Fixes bugs, adds rate limiting for Hosttech JSON API, and adds a new bulk synchronization module.

Minor Changes
-------------

- hosttech_dns_* - handle ``419 Too Many Requests`` with proper rate limiting for JSON API (https://github.com/ansible-collections/community.dns/pull/14).

Bugfixes
--------

- Avoid converting ASCII labels which contain underscores or other printable ASCII characters outside ``[a-zA-Z0-9-]`` to alabels during normalization (https://github.com/ansible-collections/community.dns/pull/13).
- Updated Public Suffix List.

New Modules
-----------

- community.dns.hosttech_dns_records - Bulk synchronize DNS records in Hosttech DNS service

v0.2.0
======

Release Summary
---------------

Major refactoring release, which adds a zone information module and supports HostTech's new REST API.

Major Changes
-------------

- hosttech_* modules - support the new JSON API at https://api.ns1.hosttech.eu/api/documentation/ (https://github.com/ansible-collections/community.dns/pull/4).

Minor Changes
-------------

- hosttech_dns_record* modules - allow to specify ``prefix`` instead of ``record`` (https://github.com/ansible-collections/community.dns/pull/8).
- hosttech_dns_record* modules - allow to specify zone by ID with the ``zone_id`` parameter, alternatively to the ``zone`` parameter (https://github.com/ansible-collections/community.dns/pull/7).
- hosttech_dns_record* modules - return ``zone_id`` on success (https://github.com/ansible-collections/community.dns/pull/7).
- hosttech_dns_record* modules - support IDN domain names and prefixes (https://github.com/ansible-collections/community.dns/pull/9).
- hosttech_dns_record_info - also return ``prefix`` for a record set (https://github.com/ansible-collections/community.dns/pull/8).
- hosttech_record - allow to delete records without querying their content first by specifying ``overwrite=true`` (https://github.com/ansible-collections/community.dns/pull/4).

Breaking Changes / Porting Guide
--------------------------------

- hosttech_* module_utils - completely rewrite and refactor to support new JSON API and allow to re-use provider-independent module logic (https://github.com/ansible-collections/community.dns/pull/4).

Bugfixes
--------

- Update Public Suffix List.
- hosttech_record - fix diff mode for ``state=absent`` (https://github.com/ansible-collections/community.dns/pull/4).
- hosttech_record_info - fix authentication error handling (https://github.com/ansible-collections/community.dns/pull/4).

New Modules
-----------

- community.dns.hosttech_dns_zone_info - Retrieve zone information in Hosttech DNS service

v0.1.0
======

Release Summary
---------------

Initial public release.

New Plugins
-----------

Filter
~~~~~~

- community.dns.get_public_suffix - Returns the public suffix of a DNS name
- community.dns.get_registrable_domain - Returns the registrable domain name of a DNS name
- community.dns.remove_public_suffix - Removes the public suffix from a DNS name
- community.dns.remove_registrable_domain - Removes the registrable domain name from a DNS name

New Modules
-----------

- community.dns.hosttech_dns_record - Add or delete entries in Hosttech DNS service
- community.dns.hosttech_dns_record_info - Retrieve entries in Hosttech DNS service
- community.dns.wait_for_txt - Wait for TXT entries to be available on all authoritative nameservers
