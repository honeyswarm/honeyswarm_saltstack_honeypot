#!/usr/bin/python3.8
import os
import random
import json
import msgpack

from uuid import uuid4

from twisted.internet.protocol import Factory, Protocol
from twisted.internet.endpoints import TCP4ServerEndpoint, HostnameEndpoint
from twisted.internet import endpoints, reactor

from hpfeeds.twisted import ClientSessionService


HPFSERVER = os.environ.get("HPFSERVER", "172.17.0.1")
HPFPORT = int(os.environ.get("HPFPORT", 20000))
HPFIDENT = os.environ.get("HPFIDENT", "testing")
HPFSECRET = os.environ.get("HPFSECRET", "secretkey")
HIVEID = os.environ.get("HIVEID", "UnknownHive")
CHANNEL = "saltstack.sessions"


import sys
from twisted.internet import reactor
from twisted.internet.protocol import ServerFactory, ClientFactory, Protocol
from twisted.protocols import basic
from twisted.python import log

LISTEN_PORT = 4506
SERVER_PORT = 5555

class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (bytes, bytearray)):
            return obj.decode("ASCII") # <- or any other encoding of your choice
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)


class ServerProtocol(Protocol):
    def __init__(self):
        endpoint = HostnameEndpoint(reactor, HPFSERVER, HPFPORT)
        self.hpf_client = ClientSessionService(endpoint, HPFIDENT, HPFSECRET)
        self.hpf_client.startService()

        self.session = {
            "session_id": str(uuid4().hex[:12]),
            "rx_data": [],
            "honeypot_type": "SaltStack",
            "service": "ZeroMQ",
            "port": 4506,

        }


        self.buffer = None
        self.client = None

    def connectionMade(self):
        factory = ClientFactory()
        factory.protocol = ClientProtocol
        factory.server = self

        connection_details = self.transport.getPeer()
        self.session['source_ip'] = connection_details.host
        self.session['source_port'] = connection_details.port

        reactor.connectTCP('localhost', SERVER_PORT, factory)

    def dataReceived(self, data):
        if (self.client != None):
            self.client.write(data)
        else:
            self.buffer = data

        try:
            # Strip the socket header to we can log the payload. 
            # This only works on msgpack data specific to our SaltStack Payloads
            payload_offset = data.index(b'\x82')
            payload_data = data[payload_offset:]
            client_data = msgpack.unpackb(payload_data)
        except Exception as err:
            # Otherwise hex encode and send it all to the session logger. 
            client_data = data.hex()

        self.session['rx_data'].append(client_data)


    def write(self, data):
        self.transport.write(data)

    def connectionLost(self, reason):
        try:
            self.hpf_client.publish('saltstack.sessions', json.dumps(self.session, cls=MyEncoder).encode('utf-8'))
        except Exception as err:
            print("Error creating session: ", err)
        self.hpf_client.stopService()

        self.client.transport.abortConnection()

class ClientProtocol(Protocol):

    def connectionMade(self):

        self.factory.server.client = self
        self.write(self.factory.server.buffer)
        self.factory.server.buffer = ''

    def dataReceived(self, data):
        self.factory.server.write(data)

    def write(self, data):
        self.transport.write(data)


def main():
    import sys
    from twisted.python import log

    log.startLogging(sys.stdout)

    factory = ServerFactory()
    factory.protocol = ServerProtocol

    reactor.listenTCP(LISTEN_PORT, factory)
    reactor.run()

if __name__ == '__main__':
    main()