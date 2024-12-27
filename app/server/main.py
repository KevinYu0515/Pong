from .database import init_db
from .events import *
import websockets, os
import os, asyncio, json, threading
from .database.room import get_room_setting, delete_room
from ..utils import *
from ..game import Game_Server 

HOST = os.getenv('HOST', 'localhost')
PORT = os.getenv('PORT', '10001')

connected_clients = set()
games = set()
groupSocket = GroupSocket()

# 平行處理接收的訊息
async def process_message(websocket, message):
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
                    break

    if event.get('type') == 'start_game' and response.get('status') == 'success':
        left_client_sockets =  groupSocket.groups[f"{event.get('data').get('room_id')}_left"]
        right_client_sockets = groupSocket.groups[f"{event.get('data').get('room_id')}_right"]
        left_client_address = [get_remote_address_from_websockets(socket) for socket in left_client_sockets]
        right_client_address = [get_remote_address_from_websockets(socket) for socket in right_client_sockets]
        game_server_port = get_free_port()
        game_server_address = ('0.0.0.0', game_server_port)
        room = get_room_setting(event.get('data').get('room_id'))
        
        print(left_client_address, right_client_address, game_server_address)
        game = Game_Server(game_server_address,
                               left_client_address,
                               right_client_address,
                               room.get('left_group'),
                               room.get('right_group'),
                               room.get('winning_points'))

        games.add(game)
        game_thread = threading.Thread(target=game.run)
        game_thread.start()

        def after_game_end(game, game_thread):
            game_thread.join()
            games.remove(game)
            delete_room(event.get('data').get('room_id'))

        threading.Thread(target=after_game_end, args=(game, game_thread, )).start()

        for player_socket in left_client_sockets.union(right_client_sockets):
            await player_socket.send(json.dumps({
                                        "status": "start_game", 
                                        "data": {
                                            "server_address": (HOST, game_server_port),
                                            "left_players": room.get('left_group'),
                                            "right_players": room.get('right_group')
                                        }}
                                    ))

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