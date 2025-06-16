import pyray as raylib

def main():
    raylib.init_window(600, 400, "hii")
    while not raylib.window_should_close():
        raylib.begin_drawing()
        raylib.clear_background(raylib.WHITE)
        raylib.draw_text("Hello world", 190, 200, 20, raylib.VIOLET)
        raylib.end_drawing()
    pass



if __name__ == "__main__":
    main()
