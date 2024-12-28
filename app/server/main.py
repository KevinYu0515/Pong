from .database import init_db
from .events import *
import websockets, os
import os, asyncio, json, threading
from .database.room import get_room_setting, delete_room
from ..utils import *
from ..game import Game_Server 

HOST = os.getenv('HOST', '0.0.0.0')
PORT = os.getenv('PORT', '10001')

connected_clients = set()
games = set()
groupSocket = GroupSocket()

# 平行處理接收的訊息
async def process_message(websocket, message):
    loop = asyncio.get_event_loop()
    event = json.loads(message)
    if event.get('type') == 'chat':
        await groupSocket.send_broadcast(websocket, event.get('data'))
        return

    response, is_refresh, boardcast = await handle_event(event)

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
        # game_server_port = get_free_port()
        game_server_port = 5555
        game_server_address = ('0.0.0.0', game_server_port)
        room = get_room_setting(event.get('data').get('room_id'))
        
        def start_game(event):
            game = Game_Server(game_server_address,
                                left_client_address,
                                right_client_address,
                                room.get('left_group'),
                                room.get('right_group'),
                                room.get('winning_points'),
                                room.get('duration'),
                                'normal' if room.get('mode') != 2 else 'chaos'
                                )
            games.add(game)
            game.run()

            print('Game ended')
            games.remove(game)
            delete_room(event.get('data').get('room_id'))
            groupSocket.groups.pop(f"{event.get('data').get('room_id')}_left")
            groupSocket.groups.pop(f"{event.get('data').get('room_id')}_right")
            async def send_refresh():
                message = json.dumps({"status": "refresh"})
                for client in connected_clients:
                    try:
                        await client.send(message)
                    except websockets.exceptions.ConnectionClosed:
                        connected_clients.remove(client)
            asyncio.run_coroutine_threadsafe(send_refresh(), loop)

        game_thread = threading.Thread(target=start_game, args=(event,))
        game_thread.start()

        server_address = (get_remote_address_from_websockets(websocket)[0], game_server_port)
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
            clients = connected_clients
        if boardcast:
            clients = groupSocket.groups[f"{event.get('data').get('room_id')}_left"].union(groupSocket.groups[f"{event.get('data').get('room_id')}_right"])
        for client in clients:
            print(f"Sending refresh to {client.remote_address}")
            if client.remote_address != websocket.remote_address:
                try:
                    await client.send(message)
                except websockets.exceptions.ConnectionClosed:
                    connected_clients.remove(client)

async def server(websocket):
    print(f"Client {websocket.remote_address} connected")
    connected_clients.add(websocket)

    try:
        while True:
            message = await websocket.recv()
            print(f"Received message: {message}")
            asyncio.create_task(process_message(websocket, message))

    except websockets.exceptions.ConnectionClosedOK:
        print("Client disconnected")
        connected_clients.remove(websocket)
        for group, clients in groupSocket.groups.items():
            if websocket in clients:
                clients.remove(websocket)
    except websockets.exceptions.ConnectionClosedError as e:
        print("Client disconnected with an error.")
        print(e)
        connected_clients.remove(websocket)
        for group, clients in groupSocket.groups.items():
            if websocket in clients:
                clients.remove(websocket)
    except KeyboardInterrupt:
        print("Server stopped")

async def main():
    init_db()
    async with websockets.serve(server, HOST, PORT) as websocket_server:
        print(f'start server: {HOST}:{PORT}')
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())