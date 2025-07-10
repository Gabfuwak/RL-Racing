import cv2
import numpy as np
from circuit import SectionType as ST
from circuit import *
import time


class CarDetector:
    def __init__(self, circuit, reference_points, camera_id=0, debug=False):
        self.debug = debug
        self.circuit = circuit
        self.camera_id = camera_id
        self.cap = cv2.VideoCapture(camera_id)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.projection_points = []  # Coordonnées sur l'image. A definir via calibration
        self.reference_points = reference_points # Coordonnées sur le circuit
        self.last_position = None
        self.background_model = None
        self.circuit_mask = None


        # Store transformation parameters for consistent coordinate mapping
        self.transform_offset_x = 0
        self.transform_offset_y = 0
        self.transform_scale = 1.0
        self.transform_padding = 10


        self._calibrate()


    def _apply_perspective_transform(self, frame):
        if len(self.projection_points) == 4:
            src_points = np.float32(self.projection_points)
            
            # Calculate the bounding box of reference points
            x_coords = [p[0] for p in self.reference_points]
            y_coords = [p[1] for p in self.reference_points]
            
            min_x, min_y = min(x_coords), min(y_coords)
            max_x, max_y = max(x_coords), max(y_coords)
            
            # Calculate dimensions
            circuit_width = max_x - min_x
            circuit_height = max_y - min_y
            
            # Add padding for better quality
            padding = self.transform_padding
            
            # Calculate scale to fit in a reasonable size while maintaining quality
            target_width = 800  # TODO: make this in function of circuit size or other parameters
            target_height = 600
            scale = min(target_width / (circuit_width + 2 * padding), 
                       target_height / (circuit_height + 2 * padding))
            
            # Store transformation parameters
            self.transform_scale = scale
            self.transform_offset_x = max(0, -min_x) + padding
            self.transform_offset_y = max(0, -min_y) + padding
            
            # Create destination points with offset, padding, and scaling
            dst_points = []
            for px, py in self.reference_points:
                # Apply offset (handle negative coords), padding, and scaling
                dst_x = (px - min_x + padding) * scale
                dst_y = (py - min_y + padding) * scale
                dst_points.append([dst_x, dst_y])
            
            dst_points = np.float32(dst_points)
            
            # Get perspective transformation matrix
            matrix = cv2.getPerspectiveTransform(src_points, dst_points)
            
            # Calculate output size
            output_width = int((circuit_width + 2 * padding) * scale)
            output_height = int((circuit_height + 2 * padding) * scale)
            
            # Apply transformation
            transformed = cv2.warpPerspective(frame, matrix, (output_width, output_height))
            
            return transformed, matrix
        
        return None, None 

    def _reference_to_transformed_coords(self, ref_x, ref_y):

        # Get reference bounds for offset calculation
        x_coords = [p[0] for p in self.reference_points]
        y_coords = [p[1] for p in self.reference_points]
        min_x, min_y = min(x_coords), min(y_coords)
        
        # Apply the same transformation as in _apply_perspective_transform
        transformed_x = (ref_x - min_x + self.transform_padding) * self.transform_scale
        transformed_y = (ref_y - min_y + self.transform_padding) * self.transform_scale
        
        return int(transformed_x), int(transformed_y)

    def _transformed_to_reference_coords(self, trans_x, trans_y):

        # Get reference bounds for offset calculation
        x_coords = [p[0] for p in self.reference_points]
        y_coords = [p[1] for p in self.reference_points]
        min_x, min_y = min(x_coords), min(y_coords)
        
        # Reverse the transformation
        ref_x = (trans_x / self.transform_scale) + min_x - self.transform_padding
        ref_y = (trans_y / self.transform_scale) + min_y - self.transform_padding
        
        return ref_x, ref_y


    def _calibrate(self):
        print("Calibration mode:")
        print("- Clic gauche: ajouter un point (4 max)")
        print("- 'r': reset tous les points") 
        print("- 'q': valider et quitter")
        
        cv2.namedWindow("Calibration")
        cv2.setMouseCallback("Calibration", self._calibration_mouse_callback)
        
        self.projection_points = []
        
        # Phase 1: Calibration perspective
        while True:
            ret, frame = self.cap.read()
            if not ret:
                continue  # Skip bad frames, don't break
                
            display_frame = frame.copy()

            # Dessiner les points déjà placés
            for i, point in enumerate(self.projection_points):
                cv2.circle(display_frame, point, 8, (0, 255, 0), -1)
                cv2.putText(display_frame, f"{i+1}", 
                           (point[0]+10, point[1]-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            cv2.putText(display_frame, f"Points: {len(self.projection_points)}/4", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            cv2.imshow("Calibration", display_frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('r'):
                self.projection_points = []
                print("Points reset")



        ret, frame = self.cap.read()
        transformed, matrix = self._apply_perspective_transform(frame)
        if transformed is not None:
            gray = cv2.cvtColor(transformed, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            self.background_model = blurred
        
        cv2.destroyWindow("Calibration")
        self._generate_circuit_mask()
        

    def _generate_circuit_mask(self):
        # self.background_model is already grayscale, so we don't need to convert it
        if len(self.background_model.shape) == 3:
            # If somehow it's still BGR, convert it
            gray = cv2.cvtColor(self.background_model, cv2.COLOR_BGR2GRAY)
        else:
            # It's already grayscale, use it directly
            gray = self.background_model
            
        track_mask = cv2.inRange(gray, 10, 90)
        # Trouver tous les blobs blancs

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
        eroded_mask = cv2.morphologyEx(track_mask, cv2.MORPH_OPEN, kernel)

        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(eroded_mask, connectivity=8)

        clean_mask = np.zeros_like(eroded_mask)
        for i in range(1, num_labels):  # Skip background (0)
            area = stats[i, cv2.CC_STAT_AREA]

            if (area > 1000 ):
                clean_mask[labels == i] = 255

        kernel_enlarge = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (40, 40))
        self.circuit_mask = cv2.dilate(clean_mask, kernel_enlarge, iterations=1) 
    
    def _calibration_mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            if len(self.projection_points) < 4:
                self.projection_points.append((x, y))
                print(f"Point {len(self.projection_points)}: ({x}, {y})")

    def get_car_position(self):
        ret, frame = self.cap.read()
            
        center = self._detect_car_in_frame(frame)
        if center is None:
            return None
            
        # Convert to reference coordinates for circuit calculations
        ref_x, ref_y = self._transformed_to_reference_coords(center[0], center[1])
        
        rail_distance = self.circuit.position_to_rail_distance(ref_x, ref_y, False)
        
        self.last_position = (ref_x, ref_y, rail_distance)
        return self.last_position

    def _detect_car_in_frame(self, frame):
        transformed, matrix = self._apply_perspective_transform(frame)

        if transformed is not None:
            # Recuperer les parties sombres
            gray = cv2.cvtColor(transformed, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (7, 7), 0)
            
            diff = cv2.absdiff(self.background_model, blurred)

            _, car_mask = cv2.threshold(diff, 40, 255, cv2.THRESH_BINARY)

            if self.circuit_mask is not None:
                car_mask = cv2.bitwise_and(car_mask, self.circuit_mask)
            # On recupere la position de tous les pixels de voiture qu'on a trouvé et on fait la moyenne pour estimer la position
            y_coords, x_coords = np.where(car_mask >= 128)


            if self.debug:
                cv2.imshow("initial_frame", frame)
                cv2.imshow("transformed", transformed)
                cv2.imshow("car_mask", car_mask)
                cv2.imshow("circuit_mask", self.circuit_mask)
                cv2.waitKey(1)

            if len(x_coords) > 0:
                # Detected center in transformed coordinates
                center_x = int(np.mean(x_coords))
                center_y = int(np.mean(y_coords))
                
                if self.debug:
                    # Draw red circle at detected position (transformed coordinates)
                    cv2.circle(transformed, (center_x, center_y), 30, (0, 0, 255), 5)
                    
                    # Convert to reference coordinates for circuit calculation
                    ref_x, ref_y = self._transformed_to_reference_coords(center_x, center_y)
                    rail_distance = self.circuit.position_to_rail_distance(ref_x, ref_y, False)
                    expected_pos = round_circuit.get_position_at_rail(rail_distance, False)
                    
                    print("detected (transformed):", (center_x, center_y))
                    print("detected (reference):", (ref_x, ref_y))
                    print("expected (reference):", (expected_pos.x, expected_pos.y))

                    # Convert expected position to transformed coordinates for drawing
                    expected_trans_x, expected_trans_y = self._reference_to_transformed_coords(
                        expected_pos.x, expected_pos.y)
                    
                    print("expected (transformed):", (expected_trans_x, expected_trans_y))
                    
                    # Draw blue circle at expected position (in transformed coordinates)
                    cv2.circle(transformed, (expected_trans_x, expected_trans_y), 30, (255, 0, 0), 5)

                    # Add legend
                    cv2.putText(transformed, "Red: Detected", (10, 30), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    cv2.putText(transformed, "Blue: Expected", (10, 60), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

                    cv2.imshow("detection", transformed)
                    
                return (center_x, center_y)  # Return in transformed coordinates
            else:
                return None 


if __name__ == "__main__":
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
    detector = CarDetector(round_circuit, reference_points, camera_id=2, debug=True)

    while True:
        
        detector.get_car_position()

        time.sleep(1/20)
        

