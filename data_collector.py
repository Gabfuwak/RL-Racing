from gymenv import *
import time
import json
import math
from circuit import SectionType as ST
from circuit import *

round_circuit = Circuit([
    ST.SHORT, ST.SHORT, ST.TURN_LEFT,
    ST.LONG, ST.TURN_LEFT, ST.LONG, 
    ST.TURN_LEFT, ST.LONG, ST.TURN_LEFT, ST.SHORT,
])

class CarDataCollector:

    def __init__(self, circuit, is_inside_rail, endpoint):

        self.env = RailCarRealEnv(circuit, is_inside_rail=is_inside_rail, endpoint=endpoint)
        self.env.reset()




    def collect_data(self, pattern):
        """
        pattern is a function that takes in a timestamp and returns a value between 0 and 1
        """

        start_time =  time.time()
        collected_data = {}

        crashed = False
        try:
            while not crashed:
                curr_time =  time.time() - start_time
                input = pattern(curr_time)
                obs, reward, crashed, _, info = self.env.step([input])

                info = info['state']


                collected_data[curr_time] = {'input': input, 'rail_distance': info['rail_distance'], 'nb_turns': info['nb_turns'], 'crashed': crashed}
            




            date_str = time.strftime('%Y_%m_%d_%H%M%S', time.localtime(start_time))
        except:
            date_str = time.strftime('%Y_%m_%d_%H%M%S', time.localtime(start_time))

        with open('output/' + date_str + '.json', 'w') as file:
            json.dump(collected_data, file)






if __name__ == "__main__":

    def alternate_pattern(time_since_start):
        if int(time_since_start) % 2 == 0:
            return 0.5
        else:
            return 0

    def slow_alternate_pattern(time_since_start):
        if int(time_since_start) % 2 == 0:
            return 0.25
        else:
            return 0

    
    def fast_alternate_pattern(time_since_start):
        if int(time_since_start) % 2 == 0:
            return 0.8
        else:
            return 0
    
    def sine_pattern(time_since_start):
        return (math.sin(time_since_start) + 1)/3 # sinus entre 0 et 2/3, periode de 2pi

    def constant_veryslow_pattern(time_since_start):
        return 0.1

    def constant_slow_pattern(time_since_start):
        return 0.20

    def constant_medium_pattern(time_since_start):
        return 0.5

    def constant_fast_pattern(time_since_start):
        return 0.8

    def constant_veryfast_pattern(time_since_start):
        return 1

    
    data_collector = CarDataCollector(round_circuit, True, "http://10.135.180.56:5000")

    """
    for i in range(3):
        data_collector.collect_data(alternate_pattern)
        data_collector.env.reset()
        
    
    for i in range(3):
        data_collector.collect_data(slow_alternate_pattern)
        data_collector.env.reset()
    

    for i in range(3):
        data_collector.collect_data(fast_alternate_pattern)
        data_collector.env.reset()

    for i in range(3):
        data_collector.collect_data(sine_pattern)
        data_collector.env.reset()
        """

    for i in range(3):
        data_collector.collect_data(constant_slow_pattern)
        data_collector.env.reset()

        
        """
    for i in range(3):
        data_collector.collect_data(constant_medium_pattern)
        data_collector.env.reset()

    for i in range(3):
        data_collector.collect_data(constant_fast_pattern)
        data_collector.env.reset()
        """
