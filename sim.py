import pyray as raylib
from circuit import SectionType as ST
from circuit import *

test_L_circuit = Circuit([
    ST.LONG,
    ST.TURN_LEFT,
    ST.SHORT
])

round_circuit = Circuit([
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
    rail_distance_inside = 0.0
    rail_distance_outside = 0.0
    car_speed = 50.0
    raylib.init_window(800, 600, "hii")
    raylib.set_target_fps(60)
    max_angle_inside = 0
    max_angle_outside = 0
    
    circuit = real_circuit
    while not raylib.window_should_close():
        # update pos
        rail_distance_inside += car_speed * raylib.get_frame_time()
        rail_distance_outside += car_speed * raylib.get_frame_time()

        car_pos_inside = circuit.get_position_at_rail(rail_distance_inside, True)
        car_pos_outside = circuit.get_position_at_rail(rail_distance_outside, False)
        
        # === VOITURE INTÉRIEURE (rail inside) ===
        tan_at_car_inside = circuit.get_tangent_at_rail(rail_distance_inside, True)
        tan_at_car_inside_10cm = circuit.get_tangent_at_rail(rail_distance_inside+10, True)
        
        angle_inside = abs(raylib.vector2_angle(tan_at_car_inside_10cm, tan_at_car_inside))
        if angle_inside > max_angle_inside:
            max_angle_inside = angle_inside
        
        # === VOITURE EXTÉRIEURE (rail outside) ===
        tan_at_car_outside = circuit.get_tangent_at_rail(rail_distance_outside, False)
        tan_at_car_outside_10cm = circuit.get_tangent_at_rail(rail_distance_outside+10, False)
        
        angle_outside = abs(raylib.vector2_angle(tan_at_car_outside_10cm, tan_at_car_outside))
        if angle_outside > max_angle_outside:
            max_angle_outside = angle_outside

        raylib.begin_drawing()
        raylib.clear_background(raylib.WHITE)
        raylib.draw_text("circuit", 190, 200, 20, raylib.VIOLET)
        circuit.draw()

        # Voiture inteirueure
        raylib.draw_circle_v(car_pos_inside, 4, raylib.RED)
        
        # Tangente voiture intérieure
        scaled_tan_inside = raylib.vector2_scale(tan_at_car_inside, 25)
        tan_end_inside = raylib.vector2_add(scaled_tan_inside, car_pos_inside)
        raylib.draw_line_v(car_pos_inside, tan_end_inside, raylib.MAROON)
        
        # Tangente 10cm devant voiture intérieure
        car_pos_inside_10cm = circuit.get_position_at_rail(rail_distance_inside+10, True)
        scaled_tan_inside_10cm = raylib.vector2_scale(tan_at_car_inside_10cm, 25)
        tan_end_inside_10cm = raylib.vector2_add(scaled_tan_inside_10cm, car_pos_inside_10cm)
        raylib.draw_line_v(car_pos_inside_10cm, tan_end_inside_10cm, raylib.MAROON)

        # Voiture exeterieure
        raylib.draw_circle_v(car_pos_outside, 4, raylib.BLUE)
        
        # Tangente voiture extérieure
        scaled_tan_outside = raylib.vector2_scale(tan_at_car_outside, 25)
        tan_end_outside = raylib.vector2_add(scaled_tan_outside, car_pos_outside)
        raylib.draw_line_v(car_pos_outside, tan_end_outside, raylib.DARKBLUE)
        
        # Tangente 10cm devant voiture extérieure
        car_pos_outside_10cm = circuit.get_position_at_rail(rail_distance_outside+10, False)
        scaled_tan_outside_10cm = raylib.vector2_scale(tan_at_car_outside_10cm, 25)
        tan_end_outside_10cm = raylib.vector2_add(scaled_tan_outside_10cm, car_pos_outside_10cm)
        raylib.draw_line_v(car_pos_outside_10cm, tan_end_outside_10cm, raylib.BLUE)

        raylib.draw_text(f"Max angle INSIDE (rouge): {math.degrees(max_angle_inside):.2f}°", 10, 10, 18, raylib.RED)
        raylib.draw_text(f"Max angle OUTSIDE (bleu): {math.degrees(max_angle_outside):.2f}°", 10, 35, 18, raylib.BLUE)
        raylib.draw_text(f"Inside: {rail_distance_inside:.1f}cm\nOutside: {rail_distance_outside:.1f}cm", 10, 65, 18, raylib.BLACK)
        
        raylib.end_drawing()

if __name__ == "__main__":
    main()

