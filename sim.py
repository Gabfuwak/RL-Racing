import pyray as raylib
from circuit import SectionType as ST
from circuit import *

test_L_circuit = Circuit([
    ST.LONG,
    ST.TURN_LEFT,
    ST.SHORT
])

test_circuit = Circuit([
    ST.LONG,
    ST.TURN_LEFT,
    ST.SHORT,
    ST.TURN_LEFT,
    ST.LONG,
    ST.TURN_LEFT,
    ST.SHORT,
    ST.TURN_LEFT
])

real_circuit = Circuit([
    ST.SHORT,
    ST.SHORT,
    ST.TURN_RIGHT,
    ST.SHORT,
    ST.SHORT,
    ST.SHORT,
    ST.TURN_RIGHT,
    ST.TURN_LEFT,
    ST.SHORT,
    ST.TURN_LEFT,
    ST.SHORT,
    ST.TURN_RIGHT,
    ST.SHORT,
    ST.TURN_LEFT,
    ST.TURN_LEFT,
    ST.LONG,
    ST.LONG,
    ST.LONG,
    ST.LONG,
    ST.LONG,
    ST.LONG,
    ST.LONG,
    ST.TURN_LEFT,
    ST.SHORT,
    ST.SHORT,
    ST.SHORT,
    ST.TURN_LEFT,
    ST.LONG,
    ST.SHORT,
    ST.TURN_RIGHT,
    ST.TURN_LEFT,
    ST.TURN_LEFT,
])


def main():
    car_position = 0.0  # Distance sur le circuit en cm
    car_speed = 20.0
    raylib.init_window(800, 600, "hii")
    raylib.set_target_fps(60)
    while not raylib.window_should_close():
        car_position += car_speed * raylib.get_frame_time()  # Avancer avec le temps
        car_pos_2d = real_circuit.get_position_at(car_position, False)
        raylib.begin_drawing()
        raylib.clear_background(raylib.WHITE)
        raylib.draw_text("circuit", 190, 200, 20, raylib.VIOLET)
        real_circuit.draw()
        raylib.draw_circle_v(car_pos_2d, 3, raylib.BLUE)
        raylib.draw_text(f"Position: {car_position:.1f}cm", 10, 10, 20, raylib.BLACK)
        raylib.end_drawing()
    pass



if __name__ == "__main__":
    main()
