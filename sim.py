import pyray as raylib
from circuit import *

test_L_circuit = Circuit([
    SectionType.LONG,
    SectionType.TURN_LEFT,
    SectionType.SHORT
])

test_circuit = Circuit([
    SectionType.LONG,
    SectionType.TURN_LEFT,
    SectionType.SHORT,
    SectionType.TURN_LEFT,
    SectionType.LONG,
    SectionType.TURN_LEFT,
    SectionType.SHORT,
    SectionType.TURN_LEFT
])

def main():
    raylib.init_window(800, 600, "hii")
    raylib.set_target_fps(60)
    while not raylib.window_should_close():
        raylib.begin_drawing()
        raylib.clear_background(raylib.WHITE)
        raylib.draw_text("circuit", 190, 200, 20, raylib.VIOLET)
        test_circuit.draw()
        raylib.end_drawing()
    pass



if __name__ == "__main__":
    main()
