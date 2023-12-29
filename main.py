import asyncio
import base64
import http
from datetime import datetime
import json
import aiohttp

import websocket
import websockets as websockets

uri = 'wss://eu-push.kambicdn.com/socket.io/?EIO=4&transport=websocket'
headers = {
    'Host': 'eu-push.kambicdn.com',
    'Connection': 'Upgrade',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Upgrade': 'websocket',
    'Origin': 'https://ca.unibet.com',
    'Sec-WebSocket-Version': 13,
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
    'Sec-WebSocket-Key': 'qINeCZgqRdsazfMp101kjw==',
    'Sec-WebSocket-Extensions': 'permessage-deflate; client_max_window_bits',
}
pingInterval_ms = 55000


def extract_between_brackets(input_string, bracket_type):
    match bracket_type:
        case '[':
            char1 = '['
            char2 = ']'
        case '{':
            char1 = '{'
            char2 = '}'
    first_start_index = input_string.find(char1)
    second_start_index = input_string.find(char1, first_start_index + 1)
    end_index = input_string.rfind(char2)

    if first_start_index != -1 and second_start_index != -1 and end_index != -1 and second_start_index < end_index:
        result = input_string[second_start_index:end_index + 1]
        return result
    else:
        return None


def parse(x):
    print(f'{datetime.now()} parse : {x}')
    # print(json.dumps(x, indent=2))


def process_message(msg, char_type):
    # format msg and convert to json
    def format_msg(msg):
        print(f'format msg : {msg}')
        response = extract_between_brackets(msg, char_type)
        response = response.replace("\\", "")
        response = response[:-2]
        print(response)
        return json.loads(response)

    # if 'ping' in msg:

    response_json = format_msg(msg)
    for x in response_json:
        parse(x)


async def on_message(message, message_count, websocket):
    await asyncio.sleep(0)
    print(f'{datetime.now()} msg {message_count} : {message}')
    if message == '2':  # '2' means ping for unibet
        await pong()
    else:
        match message_count:
            case 0:  # find pingInterval, pingtimeout in timeout # usually  55 seconds
                response = '42["subscribe",{"topic":"v2018.ubca.ev.json"}]'
                message = json.loads(message[1:])
                pingInterval = message["pingInterval"]  # todo : store in class variable
                #print(f'pingInterval : {pingInterval}')
                await websocket.send(response)
                # print(f"{datetime.now()} Sent response message: {msg1}")
            case 1:  # sid
                response = '42["subscribe",{"topic":"v2018.ubca.en.ev.json"}]'
                await websocket.send(response)
                # print(f"{datetime.now()} Sent response message: {msg2}")
            case _:
                pass


async def on_error(exception, websocket):
    print(f"WebSocket error: {exception}")
    await websocket.close()
    #await start_websocket(uri)
    # Add your logic to handle errors


async def ping(websocket, pingInterval_ms):
    pingInterval_sec = pingInterval_ms / 1000
    while True:
        print(f'ping()')
        await asyncio.sleep(pingInterval_sec)
        ping_msg = '3'
        await websocket.send(ping_msg)

async def pong(websocket):
    print(f'pong()')
    ping_msg = '3'
    await websocket.send(ping_msg)


async def listen_to_websocket(websocket):
    try:
        message_count = 0
        while True:
            async for message in websocket:
                await on_message(message, message_count, websocket)
                message_count += 1

    except websockets.exceptions.WebSocketException as e:
        await on_error(e, websocket)


if __name__ == '__main__':
    # todo : setup proxy
    async def start_websocket(uri):
        async with websockets.connect(uri,
                                      extra_headers=headers) as websocket:

            #asyncio.create_task(ping(websocket, pingInterval_ms))
            try:
                message_count = 0
                while True:
                    async for message in websocket:
                        await on_message(message, message_count, websocket)
                        message_count += 1

            except websockets.exceptions.WebSocketException as e:
                await on_error(e, websocket)

            #await asyncio.gather(asyncio.create_task(listen_to_websocket(websocket)),
            #                     asyncio.create_task(ping(websocket, pingInterval_ms)))





    # asyncio.get_event_loop().run_until_complete(start_socket())
    asyncio.get_event_loop().run_until_complete(start_websocket(uri))

    # websocket.on_message = \
    #     lambda msg: asyncio.get_event_loop().run_until_complete(on_message(msg, 0, websocket))            # async for message in websocket:

    #
    # await on_message(message, message_count, websocket)
    # message_count = 0
    # while True:
    #     message = await websocket.recv()
    #     message_count += 1
    #     await on_message(message, message_count, websocket)

# while True:
#     #initial handshake
#     message = await websocket.recv()
#     print(f"Received message: {message}")
#     msg1 = '42["subscribe",{"topic":"v2018.ubca.ev.json"}]'
#     print(f"Received message: {msg1}")
#     await websocket.send(msg1)
#     print(f"Sent response message: {msg1}")
#
#     msg2 = '42["subscribe",{"topic":"v2018.ubca.en.ev.json"}]'
#     print(f"Received message: {msg2}")
#     await websocket.send(msg2)
#     print(f"Sent response message: {msg2}")
#
#     message = await websocket.recv()
#     print(f"Received message: {message}")
#
# # while True:
# #     # todo : add keep alive (send msg=3) see handshake timeout
# #     message = await websocket.recv()
# #     if message is not None:
# #         print(f"Received message: {message}")
# #         process_message(message)