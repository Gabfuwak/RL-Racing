import time
import os
import argparse
import numpy as np
from circuit import SectionType as ST
from gymenv import *
from circuit import *
import requests

last_toggle_press = 0.0
show_q_table_toggle = False

circuit = Circuit([
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

round_circuit = Circuit([
    ST.SHORT, ST.SHORT, ST.TURN_LEFT,
    ST.LONG, ST.TURN_LEFT, ST.LONG, 
    ST.TURN_LEFT, ST.LONG, ST.TURN_LEFT, ST.SHORT,
])

actions = np.linspace(0.0, 0.6, 3) # [0.0, 0.2, .., 1.0]


# Discrétisation de l'espace d'états, 3 samples (negatif, positif, nul) par distance d'angle
num_states = 3*3*3*3

q_table = np.zeros((num_states, len(actions)), dtype=float)


# Hyperparamètres du Q-learning
learning_rate = 0.3       # alpha
discount_factor = 0.9     # gamma
epsilon = 0.3             # taux d'exploration (epsilon-greedy)

learning_steps = 1000

prev_state = None
prev_action = None

# Q-table file for saving/loading
Q_TABLE_FILE = "q_table.npy"

# =================== Q-table Loading ===================
def load_q_table(file_path):
    """
    charge une Q-table depuis un fichier 
    """
    global q_table
    try:
        if os.path.exists(file_path):
            loaded_table = np.load(file_path)
            if loaded_table.shape == q_table.shape:
                q_table = loaded_table
                print(f"[Q-Learning] Q-table chargé depuis {file_path}")
            else:
                print(f"[Q-Learning] Warning: Q-Table {loaded_table.shape} "
                      f"n'a pas la meme forme que {q_table.shape}.")
        else:
            print(f"[Q-Learning] pas de Q-table a {file_path}.")
    except Exception as e:
        print(f"[Q-Learning] Erreur en chargeant la Q-table a {file_path}: {e}.")


def save_q_table():
    """
    enregistre la q-table courante
    """
    try:
        np.save(Q_TABLE_FILE, q_table)
        print(f"[Q-Learning] Q-table saved to {Q_TABLE_FILE}")
    except Exception as e:
        print(f"[Q-Learning] Error saving Q-table: {e}")


def compute_reward(rail_distance, nb_turns, speed, crashed):
    """
    Calcule la récompense en fonction de la vitesse, avec un gros negatif pour un crash.
    """
    if crashed:
        return -10000
    else:
        return 500*nb_turns + rail_distance


def update_q_table(state, action, reward, next_state):
    """
    Met à jour la Q-table en utilisant la formule de Bellman.
    """
    best_next_action = np.argmax(q_table[next_state])
    q_table[state, action] += learning_rate * (
        reward + discount_factor * q_table[next_state, best_next_action]
        - q_table[state, action]
    )

def obs_to_state(obs):
    """
    Prend un environement continu [vitesse, angle 1, angle 2, angle 3] et le transforme
    en un nombre entre 1 et le 3x3x3, avec chaque permutations des signes d'angle
    """
    angles = obs[1:4]  # [angle_10cm, angle_30cm, angle_50cm]
    speed = obs[0]
    
    # Vitesse en 3 catégories : lent/moyen/rapide
    if speed < 150:
        speed_cat = 0
    elif speed < 300:
        speed_cat = 1
    else:
        speed_cat = 2
    
    angle_state = 0
    for i, angle in enumerate(angles):
        if angle < -0.3:      # virage à gauche
            digit = 0
        elif angle > 0.3:     # virage à droite  
            digit = 2
        else:                 # tout droit
            digit = 1
        
        angle_state += digit * (3 ** i)  # base 3
    

    return angle_state * 3 + speed_cat
    

def choose_action(state):
    if np.random.rand() < epsilon:
        return np.random.choice(len(actions))  # Exploration
    else:
        return np.argmax(q_table[state])      # Exploitation

def draw_car(position, color, radius=4):
    raylib.draw_circle_v(position, radius, color)

def print_q_table(q_table):
    os.system("clear")  # Clear terminal (use "cls" on Windows)
    print("Q-TABLE :")
    print("-" * 70)
    print(f"{'State':<8} {'stop':<12} {'slow':<12} {'fast':<12}")
    print("-" * 70)
    for state in range(q_table.shape[0]):
        print(f"{state:<8} {q_table[state,0]:<12.2f} {q_table[state,1]:<12.2f} {q_table[state,2]:<12.2f}")
    print("-" * 70)

def send_training_data(state, action, reward, crashed, episode):
    """Send training data to dashboard"""
    try:
        requests.post("http://10.135.180.56:5000/training_data", json={
            'state': state,
            'action': action,
            'reward': reward,
            'crashed': crashed,
            'episode': episode
        }, timeout=0.1)
    except:
        pass

if __name__ == "__main__":
    episode_count = 0
    
    parser = argparse.ArgumentParser(description="Q-learning avec enregistrement de la q-table")
    parser.add_argument('--qtable', type=str, default=None, help="Chemin vers Q-table")
    parser.add_argument('--noraylib', type=str, default=None, help="Chemin vers Q-table")
    args = parser.parse_args()

    if args.qtable:
        load_q_table(args.qtable)
    
    env = RailCarRealEnv(round_circuit, is_inside_rail=True, endpoint="http://10.135.180.56:5000")
    obs, _ = env.reset()
    state = obs_to_state(obs)

    #while step_count < learning_steps:

    raylib.init_window(800, 600, "hii")
    raylib.set_target_fps(10)

    while not raylib.window_should_close():
        raylib.begin_drawing()
        raylib.clear_background(raylib.WHITE)

        action_idx = choose_action(state)
        action = [actions[action_idx]]
        
        obs, _, crashed, _, info = env.step(action)
        next_state = obs_to_state(obs)

        if crashed:
            episode_count += 1

        info_state = info['state']
        """if raylib.is_key_down(raylib.KeyboardKey.KEY_SPACE):
            circuit.draw()
            draw_car(info_state['voltage'], raylib.DARKBLUE)
                """

        
        reward = compute_reward(info_state['rail_distance'], info_state['nb_turns'], obs[0], crashed)  # -100 si crashed, sinon +speed
        
        if prev_state is not None and prev_action is not None:
            update_q_table(prev_state, prev_action, reward, next_state)
            send_training_data(
                state=state,
                action=action[0], 
                reward=reward,
                crashed=crashed,
                episode=episode_count
            )
            if raylib.is_key_down(raylib.KeyboardKey.KEY_SPACE):
                presstime = time.time()
                if presstime - last_toggle_press > 0.5:
                    show_q_table_toggle = not show_q_table_toggle

            if show_q_table_toggle:
                print_q_table(q_table)

        
        if crashed:
            print(f"crash at distance:{info_state['rail_distance']}")
            save_q_table()
            obs, _ = env.reset()
            next_state = obs_to_state(obs)
            prev_state = None  # Pas de continuité après crash
            prev_action = None
        else:
            prev_state = state
            prev_action = action_idx
        
        state = next_state
        raylib.end_drawing()
    save_q_table()
