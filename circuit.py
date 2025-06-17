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
        self._draw_circuit_outlines()
        self._draw_rails(is_inside_rail=True)
        self._draw_rails(is_inside_rail=False)

    def _draw_circuit_outlines(self):
        curr_pos = raylib.Vector2(400, 300) # TODO: remove hardcoded value
        facing = raylib.Vector2(1,0) # Left: (-1, 0); Right: (1, 0), Up: (0, 1), Down: (0, -1)
        for section in self.sections:
            if section == SectionType.LONG:
                curr_pos, facing = self._draw_straight_outline(curr_pos, facing, LONG_SECTION_LENGTH, raylib.DARKGREEN)
            elif section == SectionType.SHORT:
                curr_pos, facing = self._draw_straight_outline(curr_pos, facing, SHORT_SECTION_LENGTH, raylib.GREEN)
            elif section == SectionType.TURN_LEFT:
                curr_pos, facing = self._draw_turn_outline(curr_pos, facing, turn_right=False)
            elif section == SectionType.TURN_RIGHT:
                curr_pos, facing = self._draw_turn_outline(curr_pos, facing, turn_right=True)

    def _draw_rails(self, is_inside_rail):
        curr_pos = raylib.Vector2(400, 300) # TODO: remove hardcoded value
        facing = raylib.Vector2(1,0) # Left: (-1, 0); Right: (1, 0), Up: (0, 1), Down: (0, -1)
        for section in self.sections:
            if section == SectionType.LONG:
                curr_pos, facing = self._draw_straight_rail(curr_pos, facing, LONG_SECTION_LENGTH, is_inside_rail)
            elif section == SectionType.SHORT:
                curr_pos, facing = self._draw_straight_rail(curr_pos, facing, SHORT_SECTION_LENGTH, is_inside_rail)
            elif section == SectionType.TURN_LEFT:
                curr_pos, facing = self._draw_turn_rail(curr_pos, facing, turn_right=False, is_inside_rail=is_inside_rail)
            elif section == SectionType.TURN_RIGHT:
                curr_pos, facing = self._draw_turn_rail(curr_pos, facing, turn_right=True, is_inside_rail=is_inside_rail)

    def _draw_straight_outline(self, curr_pos, facing, length, color):
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

        return end_pos, facing

    def _draw_turn_outline(self, curr_pos, facing, turn_right):
        # On tourne d'abord facing pour pouvoir placer le centre du cercle et calculer l'angle de fin
        turn_angle = 90 if turn_right else -90
        new_facing = raylib.vector2_rotate(facing, math.radians(turn_angle))

        # On calcule le centre de l'arc de cercle
        center_offset = raylib.vector2_scale(new_facing, TURN_RADIUS)
        center = raylib.vector2_add(curr_pos, center_offset)

        # On calcule la position de fin
        end_offset = raylib.vector2_scale(facing, TURN_RADIUS)
        curr_pos = raylib.vector2_add(center, end_offset)

        start_angle = math.degrees(math.atan2(facing.y, facing.x))
        end_angle = start_angle - turn_angle

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

        return curr_pos, new_facing

    def _draw_straight_rail(self, curr_pos, facing, length, is_inside_rail):
        section_offset = raylib.vector2_scale(facing, length)
        end_pos = raylib.vector2_add(curr_pos, section_offset)

        # left rail si inside, right rail si outside
        angle = -90 if is_inside_rail else 90
        dir_to_side = raylib.vector2_rotate(facing, math.radians(angle))
        offset_to_side = raylib.vector2_scale(dir_to_side, CIRCUIT_WIDTH/4)
        rail_start = raylib.vector2_add(curr_pos, offset_to_side)
        rail_end = raylib.vector2_add(end_pos, offset_to_side)
        raylib.draw_line_v(rail_start, rail_end, raylib.BLACK)

        return end_pos, facing

    def _draw_turn_rail(self, curr_pos, facing, turn_right, is_inside_rail):
        # On tourne d'abord facing pour pouvoir placer le centre du cercle et calculer l'angle de fin
        turn_angle = 90 if turn_right else -90
        new_facing = raylib.vector2_rotate(facing, math.radians(turn_angle))

        # On calcule le centre de l'arc de cercle
        center_offset = raylib.vector2_scale(new_facing, TURN_RADIUS)
        center = raylib.vector2_add(curr_pos, center_offset)

        # On calcule la position de fin
        end_offset = raylib.vector2_scale(facing, TURN_RADIUS)
        curr_pos = raylib.vector2_add(center, end_offset)

        start_angle = math.degrees(math.atan2(facing.y, facing.x))
        end_angle = start_angle - turn_angle

        # Rail interieur si inside, exterieur si outside
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

        return curr_pos, new_facing


# Export direct des valeurs
LONG = SectionType.LONG
SHORT = SectionType.SHORT
TURN_LEFT = SectionType.TURN_LEFT
TURN_RIGHT = SectionType.TURN_RIGHT
