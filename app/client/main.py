from components import App
from server.database.room_db import init_app

def main():
    # 初始化 Database
    init_app()

    # 初始化遊戲應用
    app = App(themename='superhero', title='Neon Pong', geometry='800x800')
    app.run()

if __name__ == "__main__":
    main()
