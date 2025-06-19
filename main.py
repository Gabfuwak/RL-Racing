import pyray as raylib
from circuit import SectionType as ST
from circuit import *
from gymenv import *

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

def draw_car(position, color, radius=4):
    raylib.draw_circle_v(position, radius, color)

def draw_tangent(position, tangent, color, length=25):
    scaled_tangent = raylib.vector2_scale(tangent, length)
    end_pos = raylib.vector2_add(position, scaled_tangent)
    raylib.draw_line_v(position, end_pos, color)

def main():
    raylib.init_window(800, 600, "hii")
    raylib.set_target_fps(60)
    circuit = real_circuit

    env_inside = RailCarEnv(circuit, is_inside_rail=True)
    env_outside = RailCarEnv(circuit, is_inside_rail=False)

    obs_inside, _ = env_inside.reset()
    obs_outside, _ = env_outside.reset()

    while not raylib.window_should_close():
        raylib.begin_drawing()
        raylib.clear_background(raylib.WHITE)

        if raylib.is_key_down(raylib.KeyboardKey.KEY_A):
            action_inside = [1.0]  # Accélération max
        else:
            action_inside = [0.]

        if raylib.is_key_down(raylib.KeyboardKey.KEY_E):
            action_outside = [1.0]  # Accélération max
        else:
            action_outside = [0.]

        # Step envs
        obs_inside,  _, _, _, info_inside = env_inside.step(action_inside)
        obs_outside, _, _, _, info_outside = env_outside.step(action_outside)

        state_inside = info_inside['state']
        state_outside = info_outside['state']

        real_circuit.draw()

        # Voiture intérieure
        draw_car(state_inside['position'], raylib.RED)
        draw_tangent(state_inside['position'], state_inside['tangent'], raylib.MAROON)
        
        # Voiture extérieure  
        draw_car(state_outside['position'], raylib.BLUE)
        draw_tangent(state_outside['position'], state_outside['tangent'], raylib.DARKBLUE)
        
        # UI Info
        raylib.draw_text(f"Speed IN: {state_inside['speed']:.1f} | OUT: {state_outside['speed']:.1f}", 10, 60, 18, raylib.BLACK)
        
        raylib.end_drawing() 
        raylib.end_drawing()

if __name__ == "__main__":
    main()

