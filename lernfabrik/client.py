import asyncio
import json
import sys
from random import randrange

import requests
import websockets


async def listen():
    url = "ws://127.0.0.1:8001"
    # url = 'ws://localhost:8001'
    # url = 'ws://127.0.0.1:8080/ws'

    # url = 'ws://tmp-testing.herokuapp.com/ws'
    # url = 'wss://tmp-testing.herokuapp.com/ws'

    async with websockets.connect(url) as ws:

        auth_credentials = {
            # 'admin_username': 'admin',
            'admin_password': 'admin',
            'participant_label': sys.argv[1],
        }

        await ws.send(json.dumps(auth_credentials))
        await ws.send('Hello Server')

        while True:
            # {'status': 'connected'} for first iteration
            # {'config': ch_settings} for second iteration
            msg = await ws.recv()
            print(msg)

            # If an arbitrary value is given in addition to the participant label,
            # sample data is sent to thingspeak. Provided that the respective participant is
            # Alice, Bob, Charlie or Debora.
            if 'config' in msg and len(sys.argv) == 3:
                msg = json.loads(msg)
                write_api_key = msg['config']['api_keys'][0]['api_key']

                while True:
                    if sys.argv[1] == 'Alice':
                        data = randrange(0, 5)
                    elif sys.argv[1] == 'Bob':
                        data = randrange(5, 10)
                    elif sys.argv[1] == 'Charlie':
                        data = randrange(10, 15)
                    elif sys.argv[1] == 'Debora':
                        data = randrange(15, 20)
                    else:
                        break

                    requests.get(f'https://api.thingspeak.com/update?api_key={write_api_key}&field1={data}')
                    await asyncio.sleep(1)

        #    if close_after:
        #        await asyncio.sleep(3)
        #        break

        # await ws.close()


# asyncio.get_event_loop().run_until_complete(listen())
asyncio.run(listen())
