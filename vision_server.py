from flask import Flask, jsonify
from vision import CarDetector
from circuit import SectionType as ST
from circuit import *
import time

app = Flask(__name__)

round_circuit = Circuit([
    ST.SHORT, ST.SHORT, ST.TURN_LEFT,
    ST.LONG, ST.TURN_LEFT, ST.LONG, 
    ST.TURN_LEFT, ST.LONG, ST.TURN_LEFT, ST.SHORT,
])

def get_reference_points():
    # TODO: faire mieux avec des aruco
    # Longueur d'un virage sur le rail intérieur, different de longueur du milieu
    inside_turn_radius = SHORT_SECTION_LENGTH + SHORT_SECTION_LENGTH/4
    inside_turn_length = inside_turn_radius * math.pi / 2
    
    # 1. Milieu de la section START
    start_mid = SHORT_SECTION_LENGTH / 2
    
    # 2. Milieu de la première section LONG
    long1_mid = (SHORT_SECTION_LENGTH +        
                 SHORT_SECTION_LENGTH +        
                 inside_turn_length +          
                 LONG_SECTION_LENGTH / 2)      
             
    # 3. Milieu de la deuxième section LONG
    long2_mid = (SHORT_SECTION_LENGTH +        # START
                 SHORT_SECTION_LENGTH +        
                 inside_turn_length +          
                 LONG_SECTION_LENGTH +         
                 inside_turn_length +          
                 LONG_SECTION_LENGTH / 2)      
             
    # 4. Milieu de la troisième section LONG
    long3_mid = (SHORT_SECTION_LENGTH +        # START
                 SHORT_SECTION_LENGTH +        
                 inside_turn_length +          
                 LONG_SECTION_LENGTH +         
                 inside_turn_length +          
                 LONG_SECTION_LENGTH +         
                 inside_turn_length +          
                 LONG_SECTION_LENGTH / 2)      
             
    # Récupérer les positions sur le rail intérieur
    points = []
    for distance in [start_mid, long1_mid, long2_mid, long3_mid]:
        pos = round_circuit.get_position_at_rail(distance, True)
        points.append((pos.x, pos.y))
    
    return points

reference_points = get_reference_points()  
detector = CarDetector(round_circuit, reference_points, camera_id=0, debug=False)

@app.route('/car_position', methods=['GET'])
def get_car_position():
    try:
        position = detector.get_car_position()
        
        if position:
            x, y = position[0], position[1]
            rail_distance = round_circuit.position_to_rail_distance(x, y, True)
            return jsonify({
                'x': x, 'y': y, 
                'rail_distance': rail_distance,
                'timestamp': time.time()
            })
        else:
            return jsonify({'error': 'no position detected'}), 404
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'detector failed'}), 500

if __name__ == '__main__':
    app.run(host='localhost', port=5001, debug=False)
