# HTTP -> Notification Service
Simplistic server to listing for HTTP queries, specifically from Icinga or Grafana and send out Alert-Messages.

# HTTP Request
The HTTP request must be a *POST*-request, with *Content-Type: application/json* and a json-field containing the key *"message"* with the value being the message you want to send.

The following locations are supported:

    /send-all   	# send a message to all subscribed clients
    /send-all-icinga 	# send a message based on icinga-noficiation format

# Example (curl)

    curl -u nobody:API_PASS -X POST -H "Content-Type: application/json" --data '{"message":"hello world"}' localhost:5000/send-all

# Additional Packages Required

The following additional packages might be requried (on Debian) to successfully install the `python-ldap`-requirement:

    apt install libsasl2-dev python-dev libldap2-dev libssl-dev

