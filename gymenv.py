import gymnasium as gym
import numpy as np
from gymnasium import spaces
import sim
import requests
import time


class RailCarSimEnv(gym.Env):

    def __init__(self, circuit, is_inside_rail, reward_function=None, reward_kwargs=None):
        super().__init__()

        self.simulator = sim.RailCarSim(circuit, is_inside_rail) # TODO

        self.action_space = spaces.Box(low=0.0, high=1.0, shape=(1,), dtype=np.float32)
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
        
        self.endpoint = endpoint  # "http://10.12.194.56:5000"
        self.circuit = circuit
        self.is_inside_rail = is_inside_rail
        
        # Pour l'instant : observation simple (juste voltage)
        self.action_space = spaces.Box(low=0.0, high=1.0, shape=(1,), dtype=np.float32)
        self.observation_space = spaces.Box(
            low=np.array([0.0], dtype=np.float32),    # [voltage]
            high=np.array([17.4], dtype=np.float32)   # [voltage max]
        )
        
        self.reward_function = reward_function or self._default_reward
        self.reward_kwargs = reward_kwargs or {}
        self.current_step = 0


    def step(self, action):
        # On envoie l'action
        duty_cycle = action[0] * 95.0
        requests.post(f"{self.endpoint}/control", json={"duty_cycle": duty_cycle})
        
        # On recuperer l'obs
        response = requests.get(f"{self.endpoint}/sensors")
        voltage = response.json()["voltage"]
        
        observation = np.array([voltage], dtype=np.float32)
        reward = self.reward_function({"voltage": voltage}, action[0], **self.reward_kwargs)
        
        # TODO: detection de crash
        terminated = False
        truncated = False
        
        info = {
            'state': {
                'voltage': voltage,
                'duty_cycle': duty_cycle
            }
        }
        
        return observation, reward, terminated, truncated, info


    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        
        # On arrete le moteur
        requests.post(f"{self.endpoint}/control", json={"duty_cycle": 0.0})
        time.sleep(10)  # On laisse 10sec pour remettre au debut du terrain
        
        # Get initial observation
        response = requests.get(f"{self.endpoint}/sensors")
        voltage = response.json()["voltage"]
        observation = np.array([voltage], dtype=np.float32)
        
        self.current_step = 0
        return observation, {}

    def _default_reward(self, state, action):
        return 1.0  # Simple pour commencer
