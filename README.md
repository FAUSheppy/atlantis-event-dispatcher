# HTTP->Signal Gateway Notification Service
Simplistic server to listing for HTTP queries, specifically from Icinga or Grafana and send out Signal-Messages.

# Signal Cli Setup
You need `glibc>=2.29`, check this first with `ldd --version` (for Debian this means bullseye or later).
Clone the following repositories

	https://github.com/AsamK/signal-cli
	https://github.com/signalapp/libsignal-client/
	https://github.com/signalapp/zkgroup

Install the prerequisites (potentially non-exaustive list):

	apt install gradle
	https://www.rust-lang.org/tools/install (as current user)

Go to signal-cli project-root:

	./gradlew build
	./gradlew installDist

Go to libsignal-client project-root, change to java-directory and make sure to remove android from the build options, otherwise this will take ages:

	cd java
	sed -i "s/, ':android'//" settings.gradle 
	./build_jni.sh desktop

Go to zkgroup project-root and build it:

	make libzkgroup

You need to make the build libraries available for java, either copy them to the java-library path (make sure they are readable for all users) or add them to the *LD\_LIBRARY\_PATH* enviroment variable whenever you intend to use the signal-cli binary.

To get the default java-library-path execute:

	java -XshowSettings:properties 2>&1 | grep java.library

Usually on linux that's `/usr/java/packages/lib/`, though this directory might not exist yet, so:

	sudo mkdir -p /usr/java/packages/lib/
	sudo cp libsignal-client/target/release/libsignal_jni.so /usr/java/packages/lib/
	sudo cp zkgroup/target/release/libzkgroup.so /usr/java/packages/lib/
	sudo chmod a+rX /usr/java/packages/lib/

Or:

	LD_LIBRARY_PATH=LD_LIBRARY_PATH:~/libsignal-client/target/release/:~/path/to/...

Now go to signal-cli project-root, we will have to make some preparations. First prepare your phone number, if you use a number which does not support SMS, use the `--voice`-switch to receive a call instead. Your full phone number means your number, including your country code (including a leading `+`), your area code (without any leading zeros).

You also need a captcha-token, for this open a browser tab first. Then open the developer console, then *make sure to have 'persist-logs' on*, and only *after* that navigate to:

	https://signalcaptchas.org/registration/generate.html

You may or may not actually have to solve a chaptcha, in the console, after you the check succeeded,you will likely get a popup to open signal, ignore that and look into the dev-console, there should be something along the lines of:

	Navigated to: signalchaptcha://very_very_loooooooooooong_token

Copy everything after `signalchaptcha://` and use it as the token for the `--captcha`-argument. Be advised, the token isn't valid very long:

	cd build/install/signal-cli/bin/signal-cli
	signal-cli -u FULL_PHONE_NUMBER register --voice --captcha 'TOKEN'

You will now get a SMS/call with the verification-code, which you can use with:

	signal-cli -u FULL_PHONE_NUMBER verify CODE

You should consider setting a pin directly after, for help with this and other options use:

	signal-cli -h

You should use `signal-cli  receive` regulary, otherwise your account will be flagged inactive and potentially deleted. You may ommit the `-u` option if you only have registered one account with this user on this machine. Data (including private keys) are saved to `~/.local/share/signal-cli/`.

# Server Setup  
Add the target number(s) (one per line) to signal\_targets.txt, then set the a enviroment variable `SIGNAL_API_PASS`, which must be used withing a basic authentication during access to the gateway. Finally execute the server:


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

`SIGNAL_CLI_BIN` can also be set as an environment variable, which will overwrite any command line option.

# HTTP Request
The HTTP request must be a *POST*-request, with *Content-Type: application/json* and a json-field containing the key *"message"* with the value being the message you want to send.

The following locations are supported:

    /send-all   	# send a message to all subscribed clients
    /send-all-icinga 	# send a message based on icinga-noficiation format

# Example (curl)

    curl -u nobody:SIGNAL_API_PASS -X POST -H "Content-Type: application/json" --data '{"message":"hallo world"}' localhost:5000/send-all


