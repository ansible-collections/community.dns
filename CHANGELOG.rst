======================================
Community DNS Collection Release Notes
======================================

.. contents:: Topics


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
