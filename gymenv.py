import gymnasium as gym
import pyray as raylib
import numpy as np
from gymnasium import spaces
import sim
import requests
import time


class RailCarSimEnv(gym.Env):

    def __init__(self, circuit, is_inside_rail, reward_function=None, reward_kwargs=None):
        super().__init__()

        self.simulator = sim.RailCarSim(circuit, is_inside_rail) # TODO

        self.action_space = spaces.Box(low=0.0, high=0.5, shape=(1,), dtype=np.float32)
        self.observation_space = spaces.Box(
            # les angles sont les angles entre la tangente du circuit au la position de la voiture et la tangente x cm devant la voiture 
            # space: [vitesse (cm/s), angle 10cm, angle 30cm, angle 50cm]
            low=np.array([0, -1, -1, -1], dtype=np.float32),
            high=np.array([200, 1, 1, 1], dtype=np.float32)
        )

        self.reward_function = reward_function or self._default_reward
        self.reward_kwargs = reward_kwargs or {}

        self.current_step = 0

    def _default_reward(self, state, action):
        # TODO
        return 1

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        
        self.simulator.reset()
        self.current_step = 0
        
        state = self.simulator.get_state()
        observation = self._state_to_obs(state)
        
        return observation, {}

    def step(self, action):
        force = action[0]
        
        # Simulation
        terminated, state = self.simulator.step(force)
        observation = self._state_to_obs(state)
        
        # Reward (pour plus tard)
        reward = self.reward_function(state, force, **self.reward_kwargs)
        
        self.current_step += 1

        truncated = False
        
        info = {'state': state}
        
        return observation, reward, terminated, truncated, info

    def _state_to_obs(self, state):
        # Convertit l'état en observation numpy
        return np.array([
            state['speed'], 
            state['angle_10cm'],
            state['angle_30cm'],
            state['angle_50cm']
        ], dtype=np.float32)



class RailCarRealEnv(gym.Env):
    def __init__(self, circuit, is_inside_rail, endpoint, reward_function=None, reward_kwargs=None):
        super().__init__()
        
        self.endpoint = endpoint
        self.circuit = circuit
        self.is_inside_rail = is_inside_rail
        
        # ✅ Tension au lieu de vitesse
        self.action_space = spaces.Box(low=0.0, high=1.0, shape=(1,), dtype=np.float32)
        self.observation_space = spaces.Box(
            # [tension (V), angle 10cm, angle 30cm, angle 50cm]
            low=np.array([0, -1, -1, -1], dtype=np.float32),
            high=np.array([17.4, 1, 1, 1], dtype=np.float32)  # 17.4V = tension max batterie
        )
        
        self.reward_function = reward_function or self._default_reward
        self.reward_kwargs = reward_kwargs or {}
        
        self.rail_distance = 0
        self.nb_turns = 0
        self.current_step = 0
        self.last_rail_distance = 0

    def step(self, action):
        try:
            # Envoyer action moteur
            duty_cycle = action[0] * 95.0
            requests.post(f"{self.endpoint}/control", json={"duty_cycle": duty_cycle}, timeout=1)

            # Vision pour position
            vision_response = requests.get("http://localhost:5001/car_position", timeout=1)
            if vision_response.status_code == 200:
                self.last_rail_distance = self.rail_distance
                self.rail_distance = vision_response.json()['rail_distance']
                if self.rail_distance < self.last_rail_distance - 10.0:
                    self.nb_turns += 1

            # Capteurs pour tension
            sensor_response = requests.get(f"{self.endpoint}/sensors", timeout=1)
            voltage = sensor_response.json()["voltage"]

            def get_angle_at_distance(distance_ahead):
                tan_current = self.circuit.get_tangent_at_rail(self.rail_distance, self.is_inside_rail)
                tan_ahead = self.circuit.get_tangent_at_rail(self.rail_distance + distance_ahead, self.is_inside_rail)
                return raylib.vector2_angle(tan_ahead, tan_current)

            state = {
                'voltage': voltage,
                'angle_10cm': get_angle_at_distance(10),
                'angle_30cm': get_angle_at_distance(30),
                'angle_50cm': get_angle_at_distance(50),
                'rail_distance': self.rail_distance,
                'nb_turns': self.nb_turns,
                'duty_cycle': duty_cycle
            }

            observation = self._state_to_obs(state)
            reward = self.reward_function(state, action[0], **self.reward_kwargs)

            terminated = False
            truncated = False

            # Detection de crash
            terminated = state['voltage'] > 14.0 and state['voltage'] > (duty_cycle/100.0) * 14.5

            
            info = {'state': state}
            
            return observation, reward, terminated, truncated, info

        except requests.exceptions.RequestException as e:
            print(f"[RailCarRealEnv] Network error: {e}")
            # Return a dummy state to avoid KeyError
            dummy_state = {
                'rail_distance': 0,
                'nb_turns': 0,
                'voltage': 0,
                'angle_10cm': 0,
                'angle_30cm': 0,
                'angle_50cm': 0,
                'duty_cycle': 0,
            }
            observation = self._state_to_obs(dummy_state)
            return observation, 0, True, False, {'state': dummy_state}

    def _state_to_obs(self, state):
        return np.array([
            state['voltage'], # TODO: faire la conversion en force et en vitesse
            state['angle_10cm'],
            state['angle_30cm'],
            state['angle_50cm']
        ], dtype=np.float32)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        
        requests.post(f"{self.endpoint}/control", json={"duty_cycle": 0.0})
        print("Reset de l'environnement! Mettez la voiture sur la ligne de depart et appuyez sur ENTRER")
        input()
        
        self.rail_distance = 0
        self.current_step = 0
        self.nb_turns = 0
        
        # Observation initiale avec tension de repos
        try:
            response = requests.get(f"{self.endpoint}/sensors", timeout=1)
            voltage = response.json()["voltage"]
            observation = np.array([voltage, 0, 0, 0], dtype=np.float32)
        except:
            observation = np.array([14.7, 0, 0, 0], dtype=np.float32)  # Tension par défaut
        
        return observation, {}

    def _default_reward(self, state, action):
        return 1.0
