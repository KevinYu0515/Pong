import database.user_db as user_db
import database.room_db as room_db
import json

def login(data):
    name = data.get('name')
    if not name:
        return {"status": "error", "message": "缺少使用者名稱"}

    if not user_db.user_exists(name):
        user_db.add_user(name)
    elif not user_db.user_online(name):
        user_db.user_login(name)
    else:
        return {"status": "error", "message": "使用者已登入"}

    return {"status": "success", "message": f"歡迎 {name}！登入成功，最後登入時間已更新。"}

def logout(data):
    name = data.get('name')
    if not name:
        return {"status": "error", "message": "缺少使用者 name"}

    user_db.user_logout(name)
    return {"status": "success", "message": "登出成功"}

def get_all_rooms():
    rooms = room_db.get_all_room_settings()
    return {"status": "success", "data": rooms}

def create_room(data):
    mode = data.get('mode', -1)
    player_limit = data.get('player_limit', -1)
    duration = data.get('duration', -1)
    winning_points = data.get('winning_points', -1)
    disconnection = data.get('disconnection', -1)

    if mode == -1 or player_limit == -1 or duration == -1 or winning_points == -1 or disconnection == -1:
        return {"status": "error", "message": "缺少房間設定"}

    room_db.add_room_setting(mode, player_limit, duration, winning_points, disconnection)
    return {"status": "success", "message": "房間已新增"}

def get_players(data):
    room_id = data.get('room_id')
    room = room_db.get_room_setting(room_id)
    return {"status": "success", "data": {"left_group": json.loads(room.left_group), "right_group": json.loads(room.right_group)}}

def group_action(action, data):
    room_id = data.get('room_id')
    left_group = data.get('left_group')
    right_group = data.get('right_group')

    room_db.update_room_groups(room_id, json.dumps(left_group), json.dumps(right_group))
    message = ""
    if action == "leave_room":
        message = "成功離開房間"
    if action == "change_group":
        message = "成功切換陣營"
    if action == "join_group":
        message = "成功加入陣營"
    return {"status": "success", "message": message}