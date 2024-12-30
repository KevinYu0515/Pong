from .database import init_db
from .events import *
import websockets, os
import os, asyncio, json, threading
from .database.room import get_room_setting, delete_room
from ..utils import *
from ..game import Game_Server 
from .database.user import user_logout

HOST = os.getenv('HOST', '0.0.0.0')
PORT = os.getenv('PORT', '10001')

connected_clients = dict()
games = set()
groupSocket = GroupSocket()

def end_action(websocket):
    name = next((key for key, value in connected_clients.items() if value == websocket), None)
    if name is not None:
        user_logout(name)
        del connected_clients[name]
    for group, clients in groupSocket.groups.items():
        if websocket in clients:
            clients.remove(websocket)

# 平行處理接收的訊息
async def process_message(websocket, message):
    loop = asyncio.get_event_loop()
    event = json.loads(message)
    if event.get('type') == 'chat':
        await groupSocket.send_broadcast(websocket, event.get('data'))
        return

    response, is_refresh, boardcast = await handle_event(event)

    if event.get('type') == 'login' and response.get('status') == 'success':
        connected_clients[event.get('data').get('name')] = websocket

    if event.get('type') == 'group_action' and event.get('action') == 'join_group':
        groupSocket.add_broadcast(websocket, event.get('data'))
    if event.get('type') == 'group_action' and event.get('action') == 'leave_room':
        groupSocket.remove_broadcast(websocket, event.get('data'))
    if event.get('type') == 'group_action' and event.get('action') == 'change_group':
        groupSocket.remove_broadcast(websocket, {
            "room_id": event.get('data').get('room_id'),
            "side": 'left' if event.get('data').get('side') == 'right' else 'right'
        })
        groupSocket.add_broadcast(websocket, {
            "room_id": event.get('data').get('room_id'),
            "side": event.get('data').get('side')
        })

    if response.get('message') == 'Game Start' and response.get('status') == 'success':
        left_client_sockets =  groupSocket.groups[f"{event.get('data').get('room_id')}_left"]
        right_client_sockets = groupSocket.groups[f"{event.get('data').get('room_id')}_right"]
        left_client_address = [get_remote_address_from_websockets(socket) for socket in left_client_sockets]
        right_client_address = [get_remote_address_from_websockets(socket) for socket in right_client_sockets]
        game_server_port = get_free_port()
        game_server_address = ('0.0.0.0', game_server_port)
        room = get_room_setting(event.get('data').get('room_id'))
        delete_room(event.get('data').get('room_id'))
        async def send_refresh():
            message = json.dumps({"status": "refresh"})
            for name, client in connected_clients.items():
                try:
                    await client.send(message)
                except websockets.exceptions.ConnectionClosed:
                    end_action(client)

        asyncio.run_coroutine_threadsafe(send_refresh(), loop)

        def start_game(event):
            game = Game_Server(game_server_address,
                                left_client_address,
                                right_client_address,
                                room.get('left_group'),
                                room.get('right_group'),
                                room.get('winning_points'),
                                room.get('duration'),
                                int(room.get('mode'))
                                )
            games.add(game)
            game.run()

            print('Game ended')
            games.remove(game)
            groupSocket.groups.pop(f"{event.get('data').get('room_id')}_left")
            groupSocket.groups.pop(f"{event.get('data').get('room_id')}_right")

        game_thread = threading.Thread(target=start_game, args=(event,))
        game_thread.start()

        server_address = (get_local_address_from_websockets(websocket)[0], game_server_port)
        for player_socket in left_client_sockets.union(right_client_sockets):
            await player_socket.send(json.dumps({
                                        "status": "start_game", 
                                        "data": {
                                            "server_address": server_address,
                                            "left_players": room.get('left_group'),
                                            "right_players": room.get('right_group')
                                        }}
                                    ))
        return

    await websocket.send(json.dumps(response))
    print(f"Sending response: {response}")

    # 全部玩家更新畫面或是群組玩家更新畫面
    if is_refresh or boardcast:
        message = json.dumps({"status": "refresh"})
        if is_refresh:
            clients = connected_clients.values()
        if boardcast:
            clients = groupSocket.groups[f"{event.get('data').get('room_id')}_left"].union(groupSocket.groups[f"{event.get('data').get('room_id')}_right"])
        for client in clients:
            print(f"Sending refresh to {client.remote_address}")
            if client.remote_address != websocket.remote_address:
                try:
                    await client.send(message)
                except websockets.exceptions.ConnectionClosed:
                    end_action(client)

async def serve(websocket):
    print(f"Client {websocket.remote_address} connected")

    try:
        while True:
            message = await websocket.recv()
            print(f"Received message: {message}")
            asyncio.create_task(process_message(websocket, message))

    except websockets.exceptions.ConnectionClosedOK:
        print("Client disconnected")
        end_action(websocket)
    except websockets.exceptions.ConnectionClosedError as e:
        print("Client disconnected with an error.")
        print(e)
        end_action(websocket)
    

async def shutdown_server(server):
    print("Server shutting down...")
    for name, client in connected_clients.items():
        await client.close()
        print(name)
        if name is not None:
            user_logout(name)
    server.close()
    await server.wait_closed()
    print("Server is closed")
    
        

async def main():
    init_db()
    server = await websockets.serve(serve, HOST, PORT)
    print(f"Start server: {HOST}:{PORT}")
    try:
        await asyncio.Future()
    except asyncio.CancelledError:
        pass
    finally:
        await shutdown_server(server)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server interrupted by user.")
        