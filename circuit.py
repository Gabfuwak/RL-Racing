import pyray as raylib
import math
from enum import Enum

LONG_SECTION_LENGTH = 34.2
SHORT_SECTION_LENGTH = 11.4
CIRCUIT_WIDTH = SHORT_SECTION_LENGTH
TURN_RADIUS = 17.1 # (3*SHORT_SECTION_LENGTH)/2, millieu entre le inside radius qui est de 1*SHORT_SECTION_LENGTH et outside radius qui est de 2*SHORT_SECTION_LENGTH
TURN_LENGTH = math.pi * TURN_RADIUS / 2  # 90 degrees = π/2 radians

class SectionType(Enum):
    LONG = 1
    SHORT = 2
    TURN_LEFT = 3
    TURN_RIGHT = 4


class Circuit:
    # Attention: Dans cette classe quand on parle de distance/longueur c'est la distance globale au CENTRE de la route (entre les deux rails)
    # Ce n'est pas equivalent a la distance vraiment parcourue par les voitures qui sont légerement excentrées
    # Le rail interieur est un peu plus court que le rail exterieur

    def __init__(self, sections):
        self.sections = sections # Liste de sections
        self._section_data = self._precompute_sections()
        self._length = self._get_circuit_length()
        self._inside_rail_length = self._get_rail_length(True)
        self._outside_rail_length = self._get_rail_length(False)
        self._position_lookup = self._precompute_position_lookup()

    def draw(self):
        self._draw_circuit_outlines()
        self._draw_rails(is_inside_rail=True)
        self._draw_rails(is_inside_rail=False)

    def _get_circuit_length(self):
        ret = 0
        for section in self._section_data:
            ret += self._get_section_length(section)
        return ret

    def _get_section_length(self, section):
        if section['section_type'] == SectionType.LONG:
            return LONG_SECTION_LENGTH
        elif section['section_type'] == SectionType.SHORT:
            return SHORT_SECTION_LENGTH
        else: #section['section_type'] == SectionType.TURN_LEFT or section['section_type'] == SectionType.TURN_RIGHT:
            return TURN_LENGTH

    def _get_rail_length_in_section(self, section, is_inside_rail):
        if section['section_type'] == SectionType.LONG:
            return LONG_SECTION_LENGTH
        elif section['section_type'] == SectionType.SHORT:
            return SHORT_SECTION_LENGTH

        # On tourne dans le sens trigonometique, donc l'exterieur des virages a droite se retrouve a l'interieur du circuit, l'inverse pour les virages a gauche
        # TODO(?): Rendre ça plus modulaire et ajouter la feature pour tourner dans les deux sens
        elif section['section_type'] == SectionType.TURN_LEFT:
            rail_radius = (SHORT_SECTION_LENGTH + SHORT_SECTION_LENGTH/4) if is_inside_rail else (2*SHORT_SECTION_LENGTH - SHORT_SECTION_LENGTH/4)
            return rail_radius * math.pi / 2
        else: #section['section_type'] == SectionType.TURN_RIGHT
            rail_radius = (2*SHORT_SECTION_LENGTH - SHORT_SECTION_LENGTH/4) if is_inside_rail else (SHORT_SECTION_LENGTH + SHORT_SECTION_LENGTH/4)
            return rail_radius * math.pi / 2

    
    def _get_rail_length(self, is_inside_rail):
        ret = 0
        for section in self._section_data:
            ret += self._get_rail_length_in_section(section, is_inside_rail)
        return ret

    def _get_section_data_at(self, distance):
        # TODO (minor): On pourrait optimiser en faisant une recherche dichotomique ici, mais les circuits vont pas etre a ce point longs
        curr_dist = 0
        distance = distance % self._length
        for section in self._section_data:
            if distance < section['start_distance'] + section['length']:
                return section
            curr_dist += section['length']
        raise Exception("Should be unreachable (Circuit::_get_section_data_at)") 

    def _get_distance_in_section(self, section, distance):
        distance = distance % self._length
        return distance - section['start_distance']
        
    def _get_rail_distance_in_section(self, section_data, distance, is_inside_rail):
        rail_length = self._inside_rail_length if is_inside_rail else self._outside_rail_length
        start_distance = section_data['start_distance_inside'] if is_inside_rail else section_data['start_distance_outside']
        distance = distance % rail_length
        return distance - start_distance

    def _center_distance_to_rail_distance(self, center_distance, is_inside_rail):
        # Parcourt les sections et convertit
        self._get_section_data_at(center_distance);
        #todo
        pass

    def position_to_rail_distance(self, x, y, is_inside_rail=True):
        rail_name = 'inside' if is_inside_rail else 'outside'
        min_x, min_y, resolution = self._position_lookup['bounds']

        grid_x = int((x - min_x) / resolution)
        grid_y = int((y - min_y) / resolution)

        grid = self._position_lookup[rail_name]
        if 0 <= grid_x < len(grid[0]) and 0 <= grid_y < len(grid):
            distance = grid[grid_y][grid_x]
            return distance if distance is not None else None

        return None

    def get_position_at_rail(self, rail_distance, is_inside_rail):
        section_data = self._get_section_data_at_rail(rail_distance, is_inside_rail)
        
        if section_data['section_type'] == SectionType.LONG or section_data['section_type'] == SectionType.SHORT:
            # Pour les sections droites, la conversion par progress fonctionne bien
            distance_in_section_rail = self._get_rail_distance_in_section(section_data, rail_distance, is_inside_rail)
    
            # Position de départ du rail (décalée du centre)
            angle = -90 if is_inside_rail else 90
            dir_to_side = raylib.vector2_rotate(section_data['facing'], math.radians(angle))
            offset_to_side = raylib.vector2_scale(dir_to_side, CIRCUIT_WIDTH/4)
            rail_start_pos = raylib.vector2_add(section_data['start_pos'], offset_to_side)
            
            # Avancer le long du rail
            offset = raylib.vector2_scale(section_data['facing'], distance_in_section_rail)
            return raylib.vector2_add(rail_start_pos, offset)


        else: # section_data['section_type'] == SectionType.TURN_LEFT or section_data['section_type'] == SectionType.TURN_RIGHT:
            dist_in_circle = self._get_rail_distance_in_section(section_data, rail_distance, is_inside_rail)
            rotation_direction = 1 if section_data['section_type'] == SectionType.TURN_RIGHT else -1

            # Note: c'est un peu sale et je pense pouvoir faire mieux mais ça marche
            # On recupere le facing precedent
            turn_angle = 90 if section_data['section_type'] == SectionType.TURN_RIGHT else -90
            previous_facing = raylib.vector2_rotate(section_data['facing'], math.radians(-turn_angle))

            # On calcule l'offset du centre au rail
            angle = -90 if is_inside_rail else 90
            dir_to_side = raylib.vector2_rotate(previous_facing, math.radians(angle))
            offset_to_side = raylib.vector2_scale(dir_to_side, CIRCUIT_WIDTH/4)
            rail_start_pos = raylib.vector2_add(section_data['start_pos'], offset_to_side)

            # On calcule le vecteur entre le centre du cercle et le debut du rail
            radius_vector = raylib.vector2_subtract(rail_start_pos, section_data['center'])


            initial_radial_angle_rad = math.atan2(radius_vector.y, radius_vector.x)
            
            # On tourne dans le sens trigonometique, donc l'exterieur des virages a droite se retrouve a l'interieur du circuit, l'inverse pour les virages a gauche
            # TODO(?): Rendre ça plus modulaire et ajouter la feature pour tourner dans les deux sens
            if section_data['section_type'] == SectionType.TURN_LEFT:
                rail_radius = (SHORT_SECTION_LENGTH + SHORT_SECTION_LENGTH/4) if is_inside_rail else (2*SHORT_SECTION_LENGTH - SHORT_SECTION_LENGTH/4)
            else:  # TURN_RIGHT
                rail_radius = (2*SHORT_SECTION_LENGTH - SHORT_SECTION_LENGTH/4) if is_inside_rail else (SHORT_SECTION_LENGTH + SHORT_SECTION_LENGTH/4)

            angle_offset_rad = rotation_direction * dist_in_circle / rail_radius
            final_radial_angle_rad = initial_radial_angle_rad + angle_offset_rad
            
            offset_angle = raylib.Vector2(math.cos(final_radial_angle_rad), math.sin(final_radial_angle_rad))
            offset_dist = raylib.vector2_scale(offset_angle, rail_radius)

            return raylib.vector2_add(section_data['center'], offset_dist)

    def get_tangent_at_rail(self, rail_distance, is_inside_rail):
        section_data = self._get_section_data_at_rail(rail_distance, is_inside_rail)
        
        if section_data['section_type'] == SectionType.LONG or section_data['section_type'] == SectionType.SHORT:
            return section_data['facing']
        else: # section_data['section_type'] == SectionType.TURN_LEFT or section_data['section_type'] == SectionType.TURN_RIGHT:
            dist_in_circle = self._get_rail_distance_in_section(section_data, rail_distance, is_inside_rail)
            rotation_direction = 1 if section_data['section_type'] == SectionType.TURN_RIGHT else -1

            # Note: c'est un peu sale et je pense pouvoir faire mieux mais ça marche
            # On recupere le facing precedent
            turn_angle = 90 if section_data['section_type'] == SectionType.TURN_RIGHT else -90
            previous_facing = raylib.vector2_rotate(section_data['facing'], math.radians(-turn_angle))

            # On calcule l'offset du centre au rail
            angle = -90 if is_inside_rail else 90
            dir_to_side = raylib.vector2_rotate(previous_facing, math.radians(angle))
            offset_to_side = raylib.vector2_scale(dir_to_side, CIRCUIT_WIDTH/4)
            rail_start_pos = raylib.vector2_add(section_data['start_pos'], offset_to_side)

            # On calcule le vecteur entre le centre du cercle et le debut du rail
            radius_vector = raylib.vector2_subtract(rail_start_pos, section_data['center'])

            
            initial_radial_angle_rad = math.atan2(radius_vector.y, radius_vector.x)
            
            # On tourne dans le sens trigonometique, donc l'exterieur des virages a droite se retrouve a l'interieur du circuit, l'inverse pour les virages a gauche
            # TODO(?): Rendre ça plus modulaire et ajouter la feature pour tourner dans les deux sens
            if section_data['section_type'] == SectionType.TURN_LEFT:
                rail_radius = (SHORT_SECTION_LENGTH + SHORT_SECTION_LENGTH/4) if is_inside_rail else (2*SHORT_SECTION_LENGTH - SHORT_SECTION_LENGTH/4)
            else:  # TURN_RIGHT
                rail_radius = (2*SHORT_SECTION_LENGTH - SHORT_SECTION_LENGTH/4) if is_inside_rail else (SHORT_SECTION_LENGTH + SHORT_SECTION_LENGTH/4)

            angle_offset_rad = rotation_direction * dist_in_circle / rail_radius
            final_radial_angle_rad = initial_radial_angle_rad + angle_offset_rad
            radial_vector = raylib.Vector2(math.cos(final_radial_angle_rad), math.sin(final_radial_angle_rad))

            # La tangente est le vecteur orthonormal au vecteur radial
            turn_direction = -90 if section_data['section_type'] == SectionType.TURN_LEFT else 90
            tangent = raylib.vector2_rotate(radial_vector, math.radians(turn_direction))

            return tangent


    def _get_section_data_at_rail(self, rail_distance, is_inside_rail):
        # Utilise les conversions pour trouver la bonne section
        curr_dist = 0
        rail_length = self._inside_rail_length if is_inside_rail else self._outside_rail_length
        distance = rail_distance % rail_length
        for section in self._section_data:
            start_distance = section['start_distance_inside'] if is_inside_rail else section['start_distance_outside']
            section_length = section['length_inside'] if is_inside_rail else section['length_outside']
            if distance < start_distance + section_length:
                return section
            curr_dist += section_length
        raise Exception("Should be unreachable (Circuit::_get_section_data_at_rail)") 


    def get_position_in_rail_at(self, distance, is_inside_rail):
        section_data = self._get_section_data_at(distance)
        if section_data['section_type'] == SectionType.LONG or section_data['section_type'] == SectionType.SHORT:

            angle = -90 if is_inside_rail else 90
            dir_to_side = raylib.vector2_rotate(section_data['facing'], math.radians(angle))
            offset_to_side = raylib.vector2_scale(dir_to_side, CIRCUIT_WIDTH/4)
            rail_start_pos = raylib.vector2_add(section_data['start_pos'], offset_to_side)
            
            offset = raylib.vector2_scale(section_data['facing'], self._get_distance_in_section(section_data, distance))
            return raylib.vector2_add(rail_start_pos, offset)

        else: # section_data['section_type'] == SectionType.TURN_LEFT or section_data['section_type'] == SectionType.TURN_RIGHT:
            dist_in_circle = self._get_distance_in_section(section_data, distance)
            rotation_direction = 1 if section_data['section_type'] == SectionType.TURN_RIGHT else -1


            radius_vector = raylib.vector2_subtract(section_data['start_pos'], section_data['center'])
            initial_radial_angle_rad = math.atan2(radius_vector.y, radius_vector.x)
            
            # On tourne dans le sens trigonometique, donc l'exterieur des virages a droite se retrouve a l'interieur du circuit, l'inverse pour les virages a gauche
            # TODO(?): Rendre ça plus modulaire et ajouter la feature pour tourner dans les deux sens
            if section_data['section_type'] == SectionType.TURN_LEFT:
                rail_radius = (SHORT_SECTION_LENGTH + SHORT_SECTION_LENGTH/4) if is_inside_rail else (2*SHORT_SECTION_LENGTH - SHORT_SECTION_LENGTH/4)
            else:  # TURN_RIGHT
                rail_radius = (2*SHORT_SECTION_LENGTH - SHORT_SECTION_LENGTH/4) if is_inside_rail else (SHORT_SECTION_LENGTH + SHORT_SECTION_LENGTH/4)

            angle_offset_rad = rotation_direction * dist_in_circle / rail_radius
            final_radial_angle_rad = initial_radial_angle_rad + angle_offset_rad
            
            offset_angle = raylib.Vector2(math.cos(final_radial_angle_rad), math.sin(final_radial_angle_rad))

            offset_dist = raylib.vector2_scale(offset_angle, rail_radius)

            return raylib.vector2_add(section_data['center'], offset_dist)

    def get_tangent_at(self, distance, is_inside_rail):
        section_data = self._get_section_data_at(distance)
        if section_data['section_type'] == SectionType.LONG or section_data['section_type'] == SectionType.SHORT:
            return section_data['facing']
        else: # section_data['section_type'] == SectionType.TURN_LEFT or section_data['section_type'] == SectionType.TURN_RIGHT:
            dist_in_circle = self._get_distance_in_section(section_data, distance)
            rotation_direction = 1 if section_data['section_type'] == SectionType.TURN_RIGHT else -1


            radius_vector = raylib.vector2_subtract(section_data['start_pos'], section_data['center'])
            initial_radial_angle_rad = math.atan2(radius_vector.y, radius_vector.x)
            
            # On tourne dans le sens trigonometique, donc l'exterieur des virages a droite se retrouve a l'interieur du circuit, l'inverse pour les virages a gauche
            # TODO(?): Rendre ça plus modulaire et ajouter la feature pour tourner dans les deux sens
            if section_data['section_type'] == SectionType.TURN_LEFT:
                rail_radius = (SHORT_SECTION_LENGTH + SHORT_SECTION_LENGTH/4) if is_inside_rail else (2*SHORT_SECTION_LENGTH - SHORT_SECTION_LENGTH/4)
            else:  # TURN_RIGHT
                rail_radius = (2*SHORT_SECTION_LENGTH - SHORT_SECTION_LENGTH/4) if is_inside_rail else (SHORT_SECTION_LENGTH + SHORT_SECTION_LENGTH/4)

            angle_offset_rad = rotation_direction * dist_in_circle / rail_radius
            final_radial_angle_rad = initial_radial_angle_rad + angle_offset_rad
            radial_vector = raylib.Vector2(math.cos(final_radial_angle_rad), math.sin(final_radial_angle_rad))

            # La tangente est le vecteur orthonormal au vecteur radial
            turn_direction = -90 if section_data['section_type'] == SectionType.TURN_LEFT else 90
            tangent = raylib.vector2_rotate(radial_vector, math.radians(turn_direction))

            return tangent

        
    def _precompute_position_lookup(self, resolution=1.0):  # grille de 1cm
        """Crée une grille 2D (x,y) -> distance_sur_rail"""
        
        # Calculer les bounds du circuit
        all_positions = []
        for rail_type in [True, False]:  # inside/outside
            rail_length = self._inside_rail_length if rail_type else self._outside_rail_length
            for distance in range(0, int(rail_length), 1):  # échantillonner tous les 1cm
                pos = self.get_position_at_rail(distance, rail_type)
                all_positions.append((pos.x, pos.y))
        
        min_x = min(p[0] for p in all_positions) - 50  # marge
        max_x = max(p[0] for p in all_positions) + 50
        min_y = min(p[1] for p in all_positions) - 50 
        max_y = max(p[1] for p in all_positions) + 50
        
        # Créer la grille
        width = int((max_x - min_x) / resolution) + 1
        height = int((max_y - min_y) / resolution) + 1
        
        lookup_grid = {
            'inside': [[None for _ in range(width)] for _ in range(height)],
            'outside': [[None for _ in range(width)] for _ in range(height)],
            'bounds': (min_x, min_y, resolution)
        }
        
        # Remplir la grille
        for rail_type in [True, False]:
            rail_name = 'inside' if rail_type else 'outside'
            rail_length = self._inside_rail_length if rail_type else self._outside_rail_length
            
            for distance in range(0, int(rail_length), 1):
                pos = self.get_position_at_rail(distance, rail_type)
                
                # Convertir en indices de grille
                grid_x = int((pos.x - min_x) / resolution)
                grid_y = int((pos.y - min_y) / resolution)
                
                # Remplir aussi les cases voisines (anti-aliasing)
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        gx, gy = grid_x + dx, grid_y + dy
                        if 0 <= gx < width and 0 <= gy < height:
                            if lookup_grid[rail_name][gy][gx] is None:
                                lookup_grid[rail_name][gy][gx] = distance
        
        return lookup_grid

    def _precompute_sections(self):
        # Traverse le circuit et stocke des metadonnées sur sa composition pour eviter d'avoir a le traverser a chaque fois 
        
        section_data = []
        curr_pos = raylib.Vector2(400, 300) # TODO: remove hardcoded value
        facing = raylib.Vector2(1,0) # Left: (-1, 0); Right: (1, 0), Up: (0, 1), Down: (0, -1)
        cumulative_distance = 0.0
        cumulative_distance_inside = 0.0
        cumulative_distance_outside = 0.0
        
        for section in self.sections:
            if section == SectionType.LONG:
                length = LONG_SECTION_LENGTH

                data = {
                    'start_distance': cumulative_distance,
                    'start_distance_inside': cumulative_distance_inside,
                    'start_distance_outside': cumulative_distance_outside,
                    'length_inside': length,
                    'length_outside': length,
                    'length': length,
                    'section_type': section,
                    'start_pos': curr_pos,
                    'facing': facing
                }
                section_data.append(data)
                
                # Avancer pour la prochaine section
                section_offset = raylib.vector2_scale(facing, length)
                curr_pos = raylib.vector2_add(curr_pos, section_offset)
                cumulative_distance += length
                cumulative_distance_inside += length
                cumulative_distance_outside += length

            elif section == SectionType.SHORT:
                length = SHORT_SECTION_LENGTH
                data = {
                    'start_distance': cumulative_distance,
                    'start_distance_inside': cumulative_distance_inside,
                    'start_distance_outside': cumulative_distance_outside,
                    'length': length,
                    'length_inside': length,
                    'length_outside': length,
                    'section_type': section,
                    'start_pos': curr_pos,
                    'facing': facing
                }
                section_data.append(data)
                
                # Avancer pour la prochaine section
                section_offset = raylib.vector2_scale(facing, length)
                curr_pos = raylib.vector2_add(curr_pos, section_offset)
                cumulative_distance += length
                cumulative_distance_inside += length
                cumulative_distance_outside += length

            elif section == SectionType.TURN_LEFT or section == SectionType.TURN_RIGHT:
                inside_length = (SHORT_SECTION_LENGTH + SHORT_SECTION_LENGTH/4) * math.pi / 2
                outside_length = (2*SHORT_SECTION_LENGTH - SHORT_SECTION_LENGTH/4) * math.pi / 2
                
                # Pour TURN_LEFT: inside=inside, outside=outside
                # Pour TURN_RIGHT: inside=outside, outside=inside (géométrie inversée)
                length_inside = inside_length if section == SectionType.TURN_LEFT else outside_length
                length_outside = outside_length if section == SectionType.TURN_LEFT else inside_length

                # On tourne d'abord facing pour pouvoir placer le centre du cercle et calculer l'angle de fin
                turn_angle = 90 if section == SectionType.TURN_RIGHT else -90
                new_facing = raylib.vector2_rotate(facing, math.radians(turn_angle))

                # On calcule le centre de l'arc de cercle
                center_offset = raylib.vector2_scale(new_facing, TURN_RADIUS)
                center = raylib.vector2_add(curr_pos, center_offset)

                start_angle = math.degrees(math.atan2(facing.y, facing.x))
                arc_length = math.pi * TURN_RADIUS / 2  # 90 degrees = π/2 radians
                
                data = {
                    'start_distance': cumulative_distance,
                    'start_distance_inside': cumulative_distance_inside,
                    'start_distance_outside': cumulative_distance_outside,
                    'length': arc_length,
                    'length_inside': length_inside,
                    'length_outside': length_outside,
                    'section_type': section,
                    'start_pos': curr_pos,
                    'facing': new_facing,
                    'center': center,
                    'start_angle': start_angle,
                    'total_angle': turn_angle
                }
                section_data.append(data)
                
                # On calcule la position de fin
                end_offset = raylib.vector2_scale(facing, TURN_RADIUS)
                curr_pos = raylib.vector2_add(center, end_offset)
                facing = new_facing
                cumulative_distance += arc_length
                cumulative_distance_inside += length_inside
                cumulative_distance_outside += length_outside
        
        return section_data

    def _draw_circuit_outlines(self):
        for data in self._section_data:
            if data['section_type'] == SectionType.LONG:
                self._draw_straight_outline_from_data(data, raylib.DARKGREEN)
            elif data['section_type'] == SectionType.SHORT:
                self._draw_straight_outline_from_data(data, raylib.GREEN)
            elif data['section_type'] == SectionType.TURN_LEFT or data['section_type'] == SectionType.TURN_RIGHT:
                self._draw_turn_outline_from_data(data)

    def _draw_rails(self, is_inside_rail):
        for data in self._section_data:
            if data['section_type'] == SectionType.LONG or data['section_type'] == SectionType.SHORT:
                self._draw_straight_rail_from_data(data, is_inside_rail)
            elif data['section_type'] == SectionType.TURN_LEFT or data['section_type'] == SectionType.TURN_RIGHT:
                self._draw_turn_rail_from_data(data, is_inside_rail)

    def _draw_straight_outline_from_data(self, data, color):
        curr_pos = data['start_pos']
        facing = data['facing']
        length = data['length']
        
        section_offset = raylib.vector2_scale(facing, length)
        end_pos = raylib.vector2_add(curr_pos, section_offset)

        # left side
        dir_to_left = raylib.vector2_rotate(facing, math.radians(-90))
        offset_to_left = raylib.vector2_scale(dir_to_left, CIRCUIT_WIDTH/2)
        left_side_start = raylib.vector2_add(curr_pos, offset_to_left)
        left_side_end = raylib.vector2_add(end_pos, offset_to_left)
        raylib.draw_line_v(left_side_start, left_side_end, color)

        # right side
        dir_to_right = raylib.vector2_rotate(facing, math.radians(90))
        offset_to_right = raylib.vector2_scale(dir_to_right, CIRCUIT_WIDTH/2)
        right_side_start = raylib.vector2_add(curr_pos, offset_to_right)
        right_side_end = raylib.vector2_add(end_pos, offset_to_right)
        raylib.draw_line_v(right_side_start, right_side_end, color)

    def _draw_turn_outline_from_data(self, data):
        center = data['center']
        start_angle = data['start_angle']
        total_angle = data['total_angle']
        end_angle = start_angle - total_angle

        # Note: En soit on pourrait draw un seul ring avec SHORT_SECTION_LENGTH inside et 2*SHORT_SECTION_LENGTH outside mais j'ai envie d'avoir que les outlines
        # Interieur
        raylib.draw_ring(
            center,
            SHORT_SECTION_LENGTH-1,
            SHORT_SECTION_LENGTH,
            start_angle,
            end_angle,
            32,
            raylib.RED
        )

        # Exterieur
        raylib.draw_ring(
            center,
            2*SHORT_SECTION_LENGTH - 1,
            2*SHORT_SECTION_LENGTH,
            start_angle,
            end_angle,
            32,
            raylib.RED
        )

    def _draw_straight_rail_from_data(self, data, is_inside_rail):
        curr_pos = data['start_pos']
        facing = data['facing']
        length = data['length']
        
        section_offset = raylib.vector2_scale(facing, length)
        end_pos = raylib.vector2_add(curr_pos, section_offset)

        # left rail si inside, right rail si outside
        angle = -90 if is_inside_rail else 90
        dir_to_side = raylib.vector2_rotate(facing, math.radians(angle))
        offset_to_side = raylib.vector2_scale(dir_to_side, CIRCUIT_WIDTH/4)
        rail_start = raylib.vector2_add(curr_pos, offset_to_side)
        rail_end = raylib.vector2_add(end_pos, offset_to_side)
        raylib.draw_line_v(rail_start, rail_end, raylib.BLACK)

    def _draw_turn_rail_from_data(self, data, is_inside_rail):
        center = data['center']
        start_angle = data['start_angle']
        total_angle = data['total_angle']
        end_angle = start_angle - total_angle

        # Rail interieur si inside, exterieur si outside
        # Note: ici inside/outside represente l'interieur/exterieur du virage, pas du circuit. Pour interieur/exterieur du circuit voir logique dans get_position_at
        rail_radius = (SHORT_SECTION_LENGTH + SHORT_SECTION_LENGTH/4) if is_inside_rail else (2*SHORT_SECTION_LENGTH - SHORT_SECTION_LENGTH/4)
        raylib.draw_ring(
            center,
            rail_radius - 1,
            rail_radius,
            start_angle,
            end_angle,
            32,
            raylib.BLACK
        )
