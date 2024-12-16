from database import init_db
from events import *
import websockets, os
import os, asyncio, json

HOST = os.getenv('HOST', 'localhost')
PORT = os.getenv('PORT', '10001')
connected_clients = set()

def handle_event(event):
    
    response, refresh = {}, True
    if event.get('type') == 'login':
        response = login(event.get('data'))
        refresh = False
    if event.get('type') == 'logout':
        response = logout(event.get('data'))
        refresh = False
    if event.get('type') == 'get_all_rooms':
        response = get_all_rooms()
        refresh = False
    if event.get('type') == 'get_players':
        response = get_players(event.get('data'))
        refresh = False

    if event.get('type') == 'create_room':
        response = create_room(event.get('data'))
    if event.get('type') == 'group_action':
        response = group_action(event.get('action'), event.get('data'))
    
    return [response, refresh]    

async def server(websocket):

    print(f"Client {websocket.remote_address} connected")
    connected_clients.add(websocket)

    try:
        while True:
            message = await websocket.recv()
            print(f"Received message: {message}")
            event = json.loads(message)
            response, is_refresh = handle_event(event)
            await websocket.send(json.dumps(response))
            print(f"Sending response: {response}")
            if is_refresh:
                message = json.dumps({"status": "refresh"})
                print(websocket.remote_address[0])
                for client in connected_clients:
                    print(f"Sending refresh to {client.remote_address}")
                    if client.remote_address != websocket.remote_address:
                        try:
                            await client.send(message)
                        except websockets.exceptions.ConnectionClosed:
                            connected_clients.remove(client)
                            break

    except websockets.exceptions.ConnectionClosedOK:
        print("Client disconnected")
        connected_clients.remove(websocket)
    except websockets.exceptions.ConnectionClosedError:
        print("Client disconnected with an error.")
    except KeyboardInterrupt:
        print("Server stopped")

async def main():
    init_db()
    async with websockets.serve(server, HOST, PORT):
        print(f'start server: {HOST}:{PORT}')
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())