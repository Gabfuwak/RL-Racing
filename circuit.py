import pyray as raylib
import math
from enum import Enum

LONG_SECTION_LENGTH = 34.2
SHORT_SECTION_LENGTH = 11.4
CIRCUIT_WIDTH = SHORT_SECTION_LENGTH
TURN_RADIUS = 17.1 # (3*SHORT_SECTION_LENGTH)/2, millieu entre le inside radius qui est de 1*SHORT_SECTION_LENGTH et outside radius qui est de 2*SHORT_SECTION_LENGTH

class SectionType(Enum):
    LONG = 1
    SHORT = 2
    TURN_LEFT = 3
    TURN_RIGHT = 4


class Circuit:
    def __init__(self, sections):
        self.sections = sections # Liste de sections

    def draw(self):
        curr_pos = raylib.Vector2(400, 300) # TODO: remove hardcoded value
        facing = raylib.Vector2(1,0) # Left: (-1, 0); Right: (1, 0), Up: (0, 1), Down: (0, -1) 
        for section in self.sections:
            if section == SectionType.LONG:
                section_offset = raylib.vector2_scale(facing, LONG_SECTION_LENGTH)
                end_pos = raylib.vector2_add(curr_pos, section_offset)

                # left side 
                dir_to_left = raylib.vector2_rotate(facing, math.radians(-90))
                offset_to_left = raylib.vector2_scale(dir_to_left, CIRCUIT_WIDTH/2)
                left_side_start = raylib.vector2_add(curr_pos, offset_to_left)
                left_side_end = raylib.vector2_add(end_pos, offset_to_left)
                raylib.draw_line_v(left_side_start, left_side_end, raylib.DARKGREEN)

                # right side
                dir_to_right = raylib.vector2_rotate(facing, math.radians(90))
                offset_to_right = raylib.vector2_scale(dir_to_right, CIRCUIT_WIDTH/2)
                right_side_start = raylib.vector2_add(curr_pos, offset_to_right)
                right_side_end = raylib.vector2_add(end_pos, offset_to_right)
                raylib.draw_line_v(right_side_start, right_side_end, raylib.DARKGREEN)

                curr_pos = end_pos

            elif section == SectionType.SHORT:
                section_offset = raylib.vector2_scale(facing, SHORT_SECTION_LENGTH)
                end_pos = raylib.vector2_add(curr_pos, section_offset)

                # left side 
                dir_to_left = raylib.vector2_rotate(facing, math.radians(-90))
                offset_to_left = raylib.vector2_scale(dir_to_left, CIRCUIT_WIDTH/2)
                left_side_start = raylib.vector2_add(curr_pos, offset_to_left)
                left_side_end = raylib.vector2_add(end_pos, offset_to_left)
                raylib.draw_line_v(left_side_start, left_side_end, raylib.GREEN)

                # right side
                dir_to_right = raylib.vector2_rotate(facing, math.radians(90))
                offset_to_right = raylib.vector2_scale(dir_to_right, CIRCUIT_WIDTH/2)
                right_side_start = raylib.vector2_add(curr_pos, offset_to_right)
                right_side_end = raylib.vector2_add(end_pos, offset_to_right)
                raylib.draw_line_v(right_side_start, right_side_end, raylib.GREEN)

                curr_pos = end_pos

            elif section == SectionType.TURN_LEFT:
                # On tourne d'abord facing pour pouvoir placer le centre du cercle et calculer l'angle de fin
                new_facing = raylib.vector2_rotate(facing, math.radians(-90))

                # On calcule le centre de l'arc de cercle
                center_offset = raylib.vector2_scale(new_facing, TURN_RADIUS)
                center = raylib.vector2_add(curr_pos, center_offset)

                # On calcule la position de fin
                end_offset = raylib.vector2_scale(facing, TURN_RADIUS)
                curr_pos = raylib.vector2_add(center, end_offset)

                start_angle = math.degrees(math.atan2(facing.y, facing.x))
                end_angle = start_angle + 90
                
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

                facing = new_facing


            elif section == SectionType.TURN_RIGHT:
                # On tourne d'abord facing pour pouvoir placer le centre du cercle et calculer l'angle de fin
                new_facing = raylib.vector2_rotate(facing, math.radians(90))

                # On calcule le centre de l'arc de cercle
                center_offset = raylib.vector2_scale(new_facing, TURN_RADIUS)
                center = raylib.vector2_add(curr_pos, center_offset)

                # On calcule la position de fin
                end_offset = raylib.vector2_scale(facing, TURN_RADIUS)
                curr_pos = raylib.vector2_add(center, end_offset)

                start_angle = math.degrees(math.atan2(facing.y, facing.x))
                end_angle = start_angle - 90
                
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
                facing = new_facing

