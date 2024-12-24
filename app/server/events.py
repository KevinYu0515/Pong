import database.user as user
import database.room as room
import database.group as group

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
    disconnection = data.get('disconnection', -1)

    if mode == -1 or player_limit == -1 or duration == -1 or winning_points == -1 or disconnection == -1:
        return {"status": "error", "message": "缺少房間設定"}

    room_id = room.add_room_setting(mode, player_limit, duration, winning_points, disconnection)
    group.add_new_groups(room_id)
    return {"status": "success", "message": "房間已新增"}

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
    message = ""
    if action == "leave_room":
        message = "成功離開房間"
        user.set_user_group(username, None, None)
    if action == "change_group":
        message = "成功切換陣營"    
        user.set_user_group(username, room_id, side) 
    if action == "join_group":
        message = "成功加入陣營"
        user.set_user_group(username, room_id, side)
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
    user.set_user_ready_status(name, status)
    return {"status": "success", "message": "成功切換準備狀態"}

def start_game(data):
    room_id = data.get('room_id')
    room_settings = room.get_room_setting(room_id)
    player_limit = room_settings.get('player_limit')
    left_group = room_settings.get('left_group')
    right_group = room_settings.get('right_group')
    if sum(1 for player in left_group if player.get('ready')) < player_limit or sum(1 for player in right_group if player.get('ready')) < player_limit:
        return {"status": "error", "message": "陣營人數不足"}
    return {"status": "success", "message": "遊戲開始"}