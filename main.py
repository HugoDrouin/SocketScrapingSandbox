import asyncio
from datetime import datetime
import json
import logging
import websockets as websockets

from ProxyConnect import proxy_connect, Proxy

logging.basicConfig(
    format="%(asctime)s - %(message)s",
    level=logging.DEBUG,
)

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
    'Sec-WebSocket-Key': 'qINeCZgqRdsazfMp101kjw==',    #mW1i7yEpth2RDztOvqEm9w== 3 i helloworld123 or HelloOpenAI123 or "GPTisAwesome123" in base 64
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

# message types  :
# mcu : match clock update
# mt :
# bor : bet offer (new?)
# boou : bet outcomes odds update (could be new odds, or suspended = False)
# boa : bet odds ? (SUSPENDED - à valider)
# bosu : bet offer (SUSPENDED valider)
# score : score
# stats : game statistics
def process_update(update):
    logging.info(f'{datetime.now()} parsed msg : {update}')
    #print(json.dumps(x, indent=2))
    msg_type = list(update.keys())[2]
    #print(msg_type[2])
    if msg_type == 'boou':
        find_new_odds(update)

def find_new_odds(update):
    try:
        event_id = update['boou']['eventId']
        # todo : use odds/1000 rather than oddsAmerican?
        new_odds_list = []
        for outcome in update['boou']['outcomes']: # usually len= 2, sometimes 1
            outcome_id = outcome['id']
            bet_offer_id = outcome['betOfferId']
            milli_odds1 = outcome['odds']
            new_odds_list.append({'event_id': event_id,
                        'outcome_id': outcome_id,
                        'bet_offer_id': bet_offer_id,
                        'milli_odds': milli_odds1})
        logging.info(f'new_odds : {new_odds_list.__repr__()}')
    except KeyError as e:
        logging.error(f'find-new_odds keyError : {e} {update}')


# format msg and convert to json
def format_msg(msg, char_type):
    #print(f'format msg : {msg}')
    response = extract_between_brackets(msg, char_type)
    response = response.replace("\\", "")
    response = response[:-2]
    logging.info(f'{datetime.now()} response')
    return json.loads(response)

def process_message(msg, char_type):
    response_json = format_msg(msg, char_type)
    for update in response_json:
        process_update(update)


async def on_message_old(message, message_count, websocket):
    await asyncio.sleep(0)
    match message_count:
        case 0:  # find pingInterval, pingtimeout in timeout # usually  55 seconds
            response = '42["subscribe",{"topic":"v2018.ubca.ev.json"}]'
            message = json.loads(message[1:])
            pingInterval = message["pingInterval"]  # todo : store in class variable
            # print(f'pingInterval : {pingInterval}')
            await websocket.send(response)
            # print(f"{datetime.now()} Sent response message: {msg1}")
        case 1:  # sid
            response = '42["subscribe",{"topic":"v2018.ubca.en.ev.json"}]'
            await websocket.send(response)
            # print(f"{datetime.now()} Sent response message: {msg2}")
        case _:
            process_message(message, '[')

async def on_message(message, message_count, websocket):
    await asyncio.sleep(0)
    if message == '2':
        await send_pong(websocket)
    else:
        match message_count:
            case 0:  # find pingInterval, pingtimeout in timeout # usually  55 seconds
                response = '40'
                await websocket.send(response)
            case 1:  # sid
                response = '42["subscribe",{"topic":"v2018.ubca.en.ev.json"}]'
                await websocket.send(response)
                response = '42["subscribe",{"topic":"v2018.ubca.ev.json"}]'
                await websocket.send(response)
                # print(f"{datetime.now()} Sent response message: {msg2}")
            case _:
                process_message(message, '[')


async def on_error(exception, websocket):
    print(f"WebSocket error: {exception}")
    await websocket.close()
    await start_websocket(uri)
    # Add your logic to handle errors

async def pong_waiter(websocket):
    logging.debug(f'{datetime.now()}pong()')
    await send_pong(websocket)

async def send_pong(websocket):
    logging.info(f'{datetime.now()} pong()')
    pong_msg = '3'
    await websocket.send(pong_msg)


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
        #proxy_url = 'http://91.200.212.129:12323:14ab1dba13fec:9c4da8462e'
        proxy_url = 'http://14ab1dba13fec:9c4da8462e@91.200.212.129:12323'  # format
        proxy = Proxy.from_url(proxy_url)
        async with proxy_connect(uri,
                                 proxy=proxy,
                                 extra_headers=headers,
                                 ping_timeout=None, ping_interval=None) as websocket:
        #async with websockets.connect(uri,
        #                              extra_headers=headers) as websocket:

            task1 = asyncio.create_task(listen_to_websocket(websocket))
            #task2 = asyncio.create_task(pong(websocket))
            await asyncio.gather(task1)


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
