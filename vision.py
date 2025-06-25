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

def apply_perspective_transform(projection_points, frame, margin_ratio=0.1):  # 10% de marge par défaut
    if len(projection_points) == 4:
        src_points = np.float32(projection_points)
        reference_points = get_reference_points()
        
        x_coords = [p[0] for p in reference_points]
        y_coords = [p[1] for p in reference_points]
        
        circuit_width = max(x_coords) - min(x_coords)
        circuit_height = max(y_coords) - min(y_coords)
        
        # Ajouter la marge
        margin_x = circuit_width * margin_ratio
        margin_y = circuit_height * margin_ratio
        
        total_width = circuit_width + 2 * margin_x
        total_height = circuit_height + 2 * margin_y
        
        # Garder le ratio mais mapper vers une taille raisonnable
        scale = min(800/total_width, 600/total_height)
        
        min_x, min_y = min(x_coords), min(y_coords)
        dst_points = []
        for px, py in reference_points:
            # Normaliser, ajouter la marge, puis scaler
            norm_x = (px - min_x + margin_x) * scale
            norm_y = (py - min_y + margin_y) * scale
            dst_points.append([norm_x, norm_y])
        
        dst_points = np.float32(dst_points)
        
        matrix = cv2.getPerspectiveTransform(src_points, dst_points)
        
        output_width = int(total_width * scale) + 50
        output_height = int(total_height * scale) + 50
        
        transformed = cv2.warpPerspective(frame, matrix, (output_width, output_height))
        
        return transformed, matrix
    
    return None, None


def mouse_callback(event, x, y, flags, param):
    global projection_points
    if event == cv2.EVENT_LBUTTONDOWN:
        if len(projection_points) < 4:
            projection_points.append((x, y))
    elif event == cv2.EVENT_RBUTTONDOWN:
        projection_points = []

def apply_digital_zoom(frame, center, zoom_factor):
    if zoom_factor <= 1.0:
        return frame
    
    h, w = frame.shape[:2]
    
    crop_w = int(w / zoom_factor)
    crop_h = int(h / zoom_factor)
    
    center_x, center_y = center
    start_x = center_x - crop_w // 2
    start_y = center_y - crop_h // 2
    
    start_x = max(0, min(start_x, w - crop_w))
    start_y = max(0, min(start_y, h - crop_h))
    
    cropped = frame[start_y:start_y+crop_h, start_x:start_x+crop_w]
    
    return cropped

def main():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    


    cv2.namedWindow(WINDOW_NAME)
    cv2.setMouseCallback(WINDOW_NAME, mouse_callback)
    if not cap.isOpened():
        print("Error: Unable to access camera.")
        exit()
    try:
        while True:
            ret, frame = cap.read()
            zoom_center = (850, 740)
            frame = apply_digital_zoom(frame, zoom_center, 2.3)
            
            if not ret:
                print("Error: Unable to get frame.")
                break
            display_frame = frame.copy()
            
            # Transformation perspective si 4 points définis
            transformed, matrix = apply_perspective_transform(projection_points, frame)
            
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
