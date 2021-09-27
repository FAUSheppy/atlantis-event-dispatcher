# HTTP->Telegram Gateway Notification Service
Simplistic server to listing for HTTP queries, specifically from Icinga or Grafana and send out Signal-Messages.

# Signal Setup
- Setup signal cli
- add the target number(s) (one per line) to signal\_targets.txt

# Server Setup

	usage: interface.py [-h] [--interface INTERFACE] 
				 [--port PORT]
				 [--signal-cli-bin SIGNAL_CLI_BIN]
	
	optional arguments:
	  -h, --help            show this help message and exit
	  --interface INTERFACE
	                        Interface on which to listen (default: localhost)
	  --port PORT           Port on which to listen (default: 5000)
	  --signal-cli-bin SIGNAL_CLI_BIN
	                        Path to signal-cli binary if no in $PATH (default: None)

# HTTP Request
The HTTP request must be a *POST*-request, with *Content-Type: application/json* and a json-field containing the key *"message"* with the value being the message you want to send.

The following locations are supported:

    /send-all   	# send a message to all subscribed clients
    /send-all-icinga 	# send a message based on icinga-noficiation format

# Example (curl)

    curl -X POST -H "Content-Type: application/json" --data '{"message":"hallo world"}' localhost:5000/send-all


