import json
import os
import glob
from skopt import gp_minimize
from skopt.space import Real
import circuit
from sim import RailCarSim
from circuit import SectionType as ST
from circuit import Circuit

round_circuit = Circuit([
    ST.SHORT, ST.SHORT, ST.TURN_LEFT,
    ST.LONG, ST.TURN_LEFT, ST.LONG, 
    ST.TURN_LEFT, ST.LONG, ST.TURN_LEFT, ST.SHORT,
])

def load_all_experiments():
    json_files = glob.glob("output/*.json")
    experiments = []
    
    for filepath in json_files:
        with open(filepath, 'r') as f:
            data = json.load(f)
            experiments.append(data)
    
    return experiments

def simulate_experiment(params, experiment_data):
    acceleration_factor, rolling_resistance, max_grip_force, turn_friction_coef = params

    sim = RailCarSim(round_circuit, is_inside_rail=True, acceleration_factor = acceleration_factor, rolling_resistance = rolling_resistance, max_grip_force = max_grip_force, turn_friction_coef= turn_friction_coef)


    sim.reset()


    # On recupere les timestamps et on les trie au cas ou (ça devrait etre redondant mais on ne sait jamais
    timestamps = sorted([float(t) for t in experiment_data.keys()])



    experiment_loss = 0
    sim_crashed = False

    raw_rail_distance = experiment_data[str(timestamps[0])]["rail_distance"]
    nb_turns = experiment_data[str(timestamps[0])]["nb_turns"]
    sim.rail_distance = nb_turns * round_circuit._get_rail_length(True) + raw_rail_distance


    for i in range(len(timestamps) - 1):
        t_curr = timestamps[i]
        t_next = timestamps[i+1]
        dt = t_next - t_curr



        current_data = experiment_data[str(t_curr)]
        input_val = current_data['input']


        crashed, sim_state = sim.step(input_val, dt=dt)

        next_data = experiment_data[str(t_next)]


        raw_rail_distance = next_data["rail_distance"]
        nb_turns = next_data["nb_turns"]
        data_rail_distance = nb_turns * round_circuit._get_rail_length(True) + raw_rail_distance



        # MSE
        experiment_loss += (data_rail_distance - sim_state["rail_distance"]) **2


        if crashed:
            sim_crashed = True
            if not next_data['crashed']:
                experiment_loss += 100  # Pénalité crash prématuré
            break


        
    if not sim_crashed and any(experiment_data[str(t)]['crashed'] for t in timestamps):
        experiment_loss += 100

    return experiment_loss




def objective_function(params):
    """Fonction objectif pour l'optimisation bayésienne"""
    experiments = load_all_experiments()
    
    total_loss = 0
    for experiment in experiments:
        exp_loss = simulate_experiment(params, experiment)
        total_loss += exp_loss
    
    avg_loss = total_loss / len(experiments)
    return avg_loss

    


def optimize_simulator():
    
    # Espace de recherche
    space = [
        Real(2000, 12000, name='acceleration_factor'),
        Real(100, 5000, name='rolling_resistance'),
        Real(3000, 15000, name='max_grip_force'),
        Real(1000, 6000, name='turn_friction_coef')
    ]
    
    # Optimisation
    result = gp_minimize(
        func=objective_function,
        dimensions=space,
        n_calls=50,
        n_initial_points=10,
        random_state=42
    )
    
    # Résultats
    print("Best loss:", result.fun)
    print("Best parameters:")
    param_names = ['acceleration_factor', 'rolling_resistance', 'max_grip_force', 'turn_friction_coef']
    for name, value in zip(param_names, result.x):
        print(f"  {name}: {value:.2f}")
    
    return result


if __name__ == "__main__":
    result = optimize_simulator()
