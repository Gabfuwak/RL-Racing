import cv2
import numpy as np
from circuit import SectionType as ST
from circuit import *


class CarDetector:
    def __init__(self, circuit, reference_points, camera_id=0, debug=False):
        self.debug = debug
        self.circuit = circuit
        self.camera_id = camera_id
        self.cap = cv2.VideoCapture(camera_id)
        self.projection_points = []  # Coordonnées sur l'image. A definir via calibration
        self.reference_points = reference_points # Coordonnées sur le circuit
        self.last_position = None
        self._calibrate()


    def _apply_perspective_transform(self, frame, margin_ratio=0.1):  # 10% de marge par défaut
        if len(self.projection_points) == 4:
            src_points = np.float32(self.projection_points)
            
            x_coords = [p[0] for p in self.reference_points]
            y_coords = [p[1] for p in self.reference_points]
            
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
            for px, py in self.reference_points:
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


    def _calibrate(self):
        print("Calibration mode:")
        print("- Clic gauche: ajouter un point (4 max)")
        print("- 'r': reset tous les points") 
        print("- 'q': valider et quitter")
        
        cv2.namedWindow("Calibration")
        cv2.setMouseCallback("Calibration", self._calibration_mouse_callback)
        
        self.projection_points = []  # Reset
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
                
            display_frame = frame.copy()
            
            # Dessiner les points déjà placés
            for i, point in enumerate(self.projection_points):
                cv2.circle(display_frame, point, 8, (0, 255, 0), -1)
                cv2.putText(display_frame, f"{i+1}", 
                           (point[0]+10, point[1]-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Instructions
            cv2.putText(display_frame, f"Points: {len(self.projection_points)}/4", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            cv2.imshow("Calibration", display_frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('r'):  # ← Reset avec 'r'
                self.projection_points = []
                print("Points reset")
                
        cv2.destroyWindow("Calibration")

    
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
            
        x, y = center
        
        rail_distance = self.circuit.position_to_rail_distance(x, y, True)
        
        self.last_position = (x, y, rail_distance)
        return self.last_position 

    def _detect_car_in_frame(self, frame):
        transformed, matrix = self._apply_perspective_transform(frame)

        if transformed is not None:
            # Recuperer les parties sombres
            gray = cv2.cvtColor(transformed, cv2.COLOR_BGR2GRAY)
            track_mask = cv2.inRange(gray, 10, 90)

            # Eroder pour separer le terrain des autres objets sombres (exemple: eroder va supprimer les fils entre le terrain et le raspi)
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
            eroded_mask = cv2.morphologyEx(track_mask, cv2.MORPH_OPEN, kernel)

            # Trouver tous les blobs blancs restants
            num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(eroded_mask, connectivity=8)

            # supprimer les blobs blacs trop petits pour etre le circuit
            clean_mask = np.zeros_like(eroded_mask)
            for i in range(1, num_labels):  # Skip background (0)
                area = stats[i, cv2.CC_STAT_AREA]
                
                if (area > 1000 ):
                    clean_mask[labels == i] = 255

            # Elargir tous les blobs blancs pour remplir les trous qu'on a crée dans le terrain avec les rails ou les bords par exemple
            kernel_enlarge = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (40, 40))
            enlarged_track = cv2.dilate(clean_mask, kernel_enlarge, iterations=1)

            # On se sert de notre terrain sans trou comme masque pour detecter les pixels verts (yoshi)
            # TODO: ameliorer ça, peut etre avec une detection de mouvement pour pouvoir detecter n'importe quelle voiture
            hsv = cv2.cvtColor(transformed, cv2.COLOR_BGR2HSV)
            masked_hsv = cv2.bitwise_and(hsv, hsv, mask=enlarged_track)


            lower_green = np.array([40, 50, 50])   # Vert foncé
            upper_green = np.array([80, 255, 255]) # Vert clair

            car_mask = cv2.inRange(masked_hsv, lower_green, upper_green)

            # cleanup les tous petits blobs qui sont juste du bruit
            num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(car_mask, connectivity=8)

            clean_car_mask = np.zeros_like(car_mask)
            for i in range(1, num_labels):  # Skip background (0)
                area = stats[i, cv2.CC_STAT_AREA]
                
                if (area > 10):
                    clean_car_mask[labels == i] = 255

            # On recuperer la position de tous les pixels de voiture qu'on a trouvé et on fait la moyenne pour estimer la position
            y_coords, x_coords = np.where(clean_car_mask == 255)

            if self.debug:
                cv2.imshow("initial_frame", frame)
                cv2.imshow("transformed", transformed)
                cv2.imshow("track_mask", track_mask)
                cv2.imshow("eroded_mask", eroded_mask)
                cv2.imshow("clean_mask", clean_mask)
                cv2.imshow("enlarged_track", enlarged_track)
                cv2.imshow("car_mask", car_mask)
                cv2.waitKey(1)

            if len(x_coords) > 0:
                center_x = int(np.mean(x_coords))
                center_y = int(np.mean(y_coords))
                return (center_x, center_y)
            else:
                return None

