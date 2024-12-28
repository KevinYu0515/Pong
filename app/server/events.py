from .database import user, room, group
from collections import defaultdict
import json

# 群組事件
class GroupSocket():
    def __init__(self):
        self.groups = defaultdict(set)

    # 加入廣播群組（房間）
    def add_broadcast(self, websocket, data):  
        group_name = f"{data.get('room_id')}_{data.get('side')}"
        self.groups[group_name].add(websocket)

    # 廣播群組訊息（房間）
    async def send_broadcast(self, websocket, data):
        group_name = f"{data.get('room_id')}_{data.get('side')}"
        response = {
            "status": "refresh",
            "data": {
                "chat": data.get('message')
            }
        }
        for client in self.groups[group_name]:
            await client.send(json.dumps(response))

    # 退出廣播群組（房間）
    def remove_broadcast(self, websocket, data):
        group_name = f"{data.get('room_id')}_{data.get('side')}"
        self.groups[group_name].remove(websocket)

# 其他事件
# 非同步處裡事件（等待資料庫回應）
async def handle_event(event):

    response, refresh, boardcast = {}, True, False
    if event.get('type') == 'login':
        response = login(event.get('data'))
        refresh = False
    if event.get('type') == 'logout':
        response = logout(event.get('data'))
        refresh = True
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
        boardcast = True
    if event.get('type') == 'toggle_ready':
        response = toggle_ready(event.get('data'))
        refresh = False
        boardcast = True
    if event.get('type') == 'delete_room':
        response = delete_room(event.get('data'))
        refresh = True
    
    return [response, refresh, boardcast]

def login(data):
    name = data.get('name')
    if not name:
        return {"status": "error", "message": "缺少使用者名稱"}

    if not user.user_exists(name):
        user.add_user(name)
    elif not user.user_online(name):
        user.user_login(name)
    else:
        return {"status": "error", "message": "使用者已登入"}

    return {"status": "success", "message": f"歡迎 {name}！登入成功，最後登入時間已更新。"}

def logout(data):
    name = data.get('name')
    if not name:
        return {"status": "error", "message": "缺少使用者 name"}

    user.user_logout(name)
    return {"status": "success", "message": "登出成功"}

def get_all_rooms():
    rooms = room.get_all_room_settings()
    return {"status": "success", "data": rooms}

def create_room(data):
    mode = data.get('mode', -1)
    player_limit = data.get('player_limit', -1)
    duration = data.get('duration', -1)
    winning_points = data.get('winning_points', -1)

    if mode == -1 or player_limit == -1 or duration == -1 or winning_points == -1:
        return {"status": "error", "message": "缺少房間設定"}

    room_id = room.add_room_setting(mode, player_limit, duration, winning_points)
    group.add_new_groups(room_id)
    return {"status": "success", "message": "房間已新增", "data": {"room_id": room_id}}

def get_players(data):
    room_id = data.get('room_id')
    room_settings = room.get_room_setting(room_id)
    limit = room_settings.get('player_limit')
    left_group = room_settings.get('left_group')
    right_group = room_settings.get('right_group')
    return {"status": "success", "data": {"player_limit": limit, "left_group": left_group, "right_group": right_group}}

def group_action(action, data):
    room_id = data.get('room_id')
    username = data.get('username')
    side = data.get('side')
    position = data.get('position')

    message = ""
    if action == "leave_room":
        message = "成功離開房間"
        user.set_user_group(username, None, None, None)
        user.set_user_ready_status(username, False)
        user.set_user_position(username, None)
    if action == "change_group":
        message = "成功切換陣營"    
        user.set_user_group(username, room_id, side, position)
        user.set_user_ready_status(username, False)
    if action == "join_group":
        message = "成功加入陣營"
        user.set_user_group(username, room_id, side, position)
    return {"status": "success", "message": message}

def switch_position(data):
    name1 = data.get('name1')
    position1 = data.get('position1')
    name2 = data.get('name2')
    position2 = data.get('position2')
    user.set_user_position(name1, position1)
    user.set_user_position(name2, position2)
    return {"status": "success", "message": "成功切換位置"}

def toggle_ready(data):
    name = data.get('name')
    status = data.get('status')
    is_last_player = data.get('is_last_player')
    user.set_user_ready_status(name, status)
    if is_last_player:
        return {"status": "success", "message": "Game Start"}
    return {"status": "success", "message": "成功切換準備狀態"}

def delete_room(data):
    room_id = data.get('room_id')
    room.delete_room(room_id)
    return {"status": "success", "message": "房間已刪除"}