from .database import init_db
from .events import *
import websockets, os
import os, asyncio, json, threading
from collections import defaultdict
from .database.room import get_room_setting
from ..utils import *
from ..game import Game_Server 

HOST = os.getenv('HOST', 'localhost')
PORT = os.getenv('PORT', '10001')

connected_clients = set()
groups = defaultdict(set)
games = set()

async def handle_event(event):
    
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
    if event.get('type') == 'switch_position':
        response = switch_position(event.get('data'))
        refresh = False
    if event.get('type') == 'toggle_ready':
        response = toggle_ready(event.get('data'))
        refresh = False
    if event.get('type') == 'start_game':
        response = start_game(event.get('data'))
        refresh = False
    
    return [response, refresh]

async def add_broadcast(websocket, data):  
    group_name = f"{data.get('room_id')}_{data.get('side')}"
    groups[group_name].add(websocket)

async def send_broadcast(websocket, data):
    group_name = f"{data.get('room_id')}_{data.get('side')}"
    response = {
        "status": "refresh",
        "data": {
            "chat": data.get('message')
        }
    }
    for client in groups[group_name]:
        await client.send(json.dumps(response))

async def remove_broadcast(websocket, data):
    group_name = f"{data.get('room_id')}_{data.get('side')}"
    groups[group_name].remove(websocket)

async def server(websocket):
    print(f"Client {websocket.remote_address} connected")
    connected_clients.add(websocket)

    try:
        while True:
            message = await websocket.recv()
            print(f"Received message: {message}")
            event = json.loads(message)
            if event.get('type') == 'chat':
                await send_broadcast(websocket, event.get('data'))
                continue

            response, is_refresh = await handle_event(event)

            if event.get('type') == 'group_action' and event.get('action') == 'join_group':
                await add_broadcast(websocket, event.get('data'))
            if event.get('type') == 'group_action' and event.get('action') == 'leave_room':
                await remove_broadcast(websocket, event.get('data'))
            await websocket.send(json.dumps(response))
            print(f"Sending response: {response}")

            if is_refresh:
                message = json.dumps({"status": "refresh"})
                for client in connected_clients:
                    print(f"Sending refresh to {client.remote_address}")
                    if client.remote_address != websocket.remote_address:
                        try:
                            await client.send(message)
                        except websockets.exceptions.ConnectionClosed:
                            connected_clients.remove(client)
                            break

            if event.get('type') == 'start_game' and response.get('status') == 'success':
                left_client_sockets =  groups[f"{event.get('data').get('room_id')}_left"]
                right_client_sockets = groups[f"{event.get('data').get('room_id')}_right"]
                left_client_address = [get_remote_address_from_websockets(socket) for socket in left_client_sockets]
                right_client_address = [get_remote_address_from_websockets(socket) for socket in right_client_sockets]
                game_server_port = get_free_port()
                game_server_address = ('0.0.0.0', game_server_port)
                room = get_room_setting(event.get('data').get('room_id'))
                
                print(left_client_address, right_client_address, game_server_address)
                new_game = Game_Server(game_server_address, left_client_address, right_client_address, room.get('left_group'), room.get('right_group'))
                games.add(new_game)
                threading.Thread(target=new_game.run).start()

                for player_socket in left_client_sockets.union(right_client_sockets):
                    await player_socket.send(json.dumps({
                                                "status": "start_game", 
                                                "data": {
                                                    "server_address": (HOST, game_server_port),
                                                    "left_players": room.get('left_group'),
                                                    "right_players": room.get('right_group')
                                                }}
                                            ))

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
