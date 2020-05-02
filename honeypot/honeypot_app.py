#!/usr/bin/python3.8
import os
import datetime
import json
import random
import asyncio
import zmq
import zmq.asyncio
import msgpack
from base64 import b64encode

# Generate a random root key at start so its consistent across sessions
ROOT_KEY = b64encode(bytearray(os.urandom(56)))

ctx = zmq.asyncio.Context()
LISTEN_PORT = 5555

async def async_process(message):
    print("Received: {0}".format(message))
    response = ""

    enc_type = message.get("enc")
    load = message.get("load")

    if not load:
        return "bad load"

    if not enc_type or not load:
        return "bad load"


    if load and enc_type == "clear":

        root_key = load.get('key')
        command = load.get('cmd')
        func = load.get('fun')

        # Do we have a root key, function and command:
        if root_key and command and func:
            # Do we want to validate they got the correct key?
            #if message['load']['key'] == str(ROOT_KEY)

            now = datetime.datetime.now()

            dtg_string = '{0:%Y%m%d%H%M%S%f}'.format(now)
            stamp_string = '{0:%Y-%m-%dT%H:%M:%S.%f}'.format(now)

            tag_line = "salt/{0}/{1}".format(command, dtg_string)

            fun_string = "{0}.{1}".format(command, func)

            response = {
                'tag': tag_line,
                'data': {
                    'fun': fun_string,
                    'jid': dtg_string,
                    'tag': tag_line,
                    'user': 'root',
                    '_stamp': stamp_string,
                    'return': [],
                    'success': True
                    }
                    }

        if command == "_prep_auth_info":
            response = [
                'user',
                'UserAuthenticationError',
                {
                    'root': str(ROOT_KEY)
                    },
                []
                ]

    print("Sending response")

    return response

async def recv_and_process():
    sock = ctx.socket(zmq.REP)
    sock.bind('tcp://127.0.0.1:{0}'.format(LISTEN_PORT))
    while True:
        try:


            # get the message
            raw_message = await sock.recv()

            # Unpack it
            unpacked_message = msgpack.unpackb(raw_message)

            # Process It
            reply = await async_process(unpacked_message)

            # pack the response
            response = msgpack.packb(reply, use_bin_type=True)

            # Send the response
            await sock.send(response)
        except Exception as err:
            # SaltStack Fails Silently so we want to match this experience 
            print("Error: ", err)
            

if __name__ == '__main__':

    asyncio.run(recv_and_process())