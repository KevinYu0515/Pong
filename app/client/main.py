from .windows import App

def main():
    app = App(themename='superhero', title='Neon Pong', geometry='800x800')
    app.run()

if __name__ == "__main__":
   main()