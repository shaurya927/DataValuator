import asyncio, websockets
async def test():
    async with websockets.connect('ws://localhost:8000/ws/training') as ws:
        print('Connected!')
        await asyncio.sleep(2)
        print('Done')
asyncio.run(test())
