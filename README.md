# honeyswarm_saltstack
Honeyswarrm honeypot for SaltStack Exposed ZeroMQ


We want to use an actual ZeroMQ implentation so that we can be "smarter" with connections that look real. However you can not get the source IP from python ZMQ, so . . . 


We run ZeroMQ application in localhost 4506
We use twisted portforwarding to manage the connections and the logging. 