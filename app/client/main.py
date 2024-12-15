from components import App
import socket, asyncio, websockets, threading



def main():
    app = App(themename='superhero', title='Neon Pong', geometry='800x800')
    app.run()

if __name__ == "__main__":
   main()
