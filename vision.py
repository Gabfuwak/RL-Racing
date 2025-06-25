import cv2
import numpy as np
from circuit import SectionType as ST
from circuit import *

WINDOW_NAME = "Car Detector"
projection_points = []

round_circuit = Circuit([
    ST.SHORT, # section depart
    ST.SHORT,
    ST.TURN_LEFT,
    ST.LONG,
    ST.TURN_LEFT,
    ST.LONG,
    ST.TURN_LEFT,
    ST.LONG,
    ST.TURN_LEFT,
    ST.SHORT,
])

def get_reference_points():
    # Longueur d'un virage sur le rail intérieur, different de longueur du milieu
    inside_turn_radius = SHORT_SECTION_LENGTH + SHORT_SECTION_LENGTH/4
    inside_turn_length = inside_turn_radius * math.pi / 2
    
    # 1. Milieu de la section START
    start_mid = SHORT_SECTION_LENGTH / 2
    
    # 2. Milieu de la première section LONG
    long1_mid = (SHORT_SECTION_LENGTH +        # START
                 SHORT_SECTION_LENGTH +        # deuxième SHORT  
                 inside_turn_length +          # premier TURN_LEFT (rail intérieur)
                 LONG_SECTION_LENGTH / 2)      # milieu de première LONG
    
    # 3. Milieu de la deuxième section LONG
    long2_mid = (SHORT_SECTION_LENGTH +        # START
                 SHORT_SECTION_LENGTH +        # deuxième SHORT
                 inside_turn_length +          # premier TURN_LEFT
                 LONG_SECTION_LENGTH +         # première LONG complète
                 inside_turn_length +          # deuxième TURN_LEFT  
                 LONG_SECTION_LENGTH / 2)      # milieu de deuxième LONG
    
    # 4. Milieu de la troisième section LONG
    long3_mid = (SHORT_SECTION_LENGTH +        # START
                 SHORT_SECTION_LENGTH +        # deuxième SHORT
                 inside_turn_length +          # premier TURN_LEFT
                 LONG_SECTION_LENGTH +         # première LONG complète
                 inside_turn_length +          # deuxième TURN_LEFT
                 LONG_SECTION_LENGTH +         # deuxième LONG complète
                 inside_turn_length +          # troisième TURN_LEFT
                 LONG_SECTION_LENGTH / 2)      # milieu de troisième LONG
    
    # Récupérer les positions sur le rail intérieur
    points = []
    for distance in [start_mid, long1_mid, long2_mid, long3_mid]:
        pos = round_circuit.get_position_at_rail(distance, True)
        points.append((pos.x, pos.y))
    
    return points

def apply_perspective_transform(frame):
    if len(projection_points) == 4:
        # Points source (cliqués dans l'image)
        src_points = np.float32(projection_points)
        
        # Points destination (circuit virtuel)
        reference_points = get_reference_points()
        dst_points = np.float32(reference_points)
        
        # Calculer la matrice de transformation
        matrix = cv2.getPerspectiveTransform(src_points, dst_points)
        
        # Taille de sortie (à ajuster selon tes besoins)
        output_size = (800, 600)
        transformed = cv2.warpPerspective(frame, matrix, output_size)
        
        return transformed, matrix
    
    return None, None


def mouse_callback(event, x, y, flags, param):
    global projection_points
    if event == cv2.EVENT_LBUTTONDOWN:
        if len(projection_points) < 4:
            projection_points.append((x, y))
    elif event == cv2.EVENT_RBUTTONDOWN:
        projection_points = []

def main():
    cap = cv2.VideoCapture(2)
    cv2.namedWindow(WINDOW_NAME)
    cv2.setMouseCallback(WINDOW_NAME, mouse_callback)
    if not cap.isOpened():
        print("Error: Unable to access camera.")
        exit()
    try:
        while True:
            ret, frame = cap.read()
            
            if not ret:
                print("Error: Unable to get frame.")
                break
            display_frame = frame.copy()
            
            # Transformation perspective si 4 points définis
            transformed, matrix = apply_perspective_transform(frame)
            
            # Affichage
            cv2.imshow(WINDOW_NAME, display_frame)
            if transformed is not None:
                cv2.imshow("Circuit View", transformed)
            
            cv2.imshow(WINDOW_NAME, frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
