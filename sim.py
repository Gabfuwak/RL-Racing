import pyray as raylib
from circuit import SectionType as ST
from circuit import *

class RailCarSim:
    def __init__(self, circuit, is_inside_rail):
        self.circuit = circuit
        self.is_inside_rail = is_inside_rail
        self.rail_distance = 0.0
        self.speed = 0.0


        self.max_speed = 475.0 
        self.acceleration_factor = 4000.0
        # Note: La friction n'augmente pas avec la vitesse. Sur cette taille de systeme le frottement de l'air est negligeable.
        # Par contre il y a plus de friction dans les virages
        self.rolling_resistance = 1480.0 # cm/s² (friction constante)
        self.max_grip_force = 11000.0
        self.turn_friction_coef = 3000.0


    def step(self, force, dt = 1/60):

        acceleration = force * self.acceleration_factor
        self.speed += acceleration * dt

        # Friction du rail et des pneus (constante)
        # +
        # Friction supplementaire dans les virages (constante aussi)


        # On recupere la courbure (qu'on reutilise plus tard pour la verification de crash)
        tan_at_car = self.circuit.get_tangent_at_rail(self.rail_distance, False)
        tan_at_1cm = self.circuit.get_tangent_at_rail(self.rail_distance+1, False)

        if self.speed > 0:

            curvature = abs(raylib.vector2_angle(tan_at_car, tan_at_1cm))

            turn_friction = curvature * self.turn_friction_coef

            self.speed -= (self.rolling_resistance + turn_friction)* dt
            self.speed = max(0, self.speed)


        self.speed = max(0, min(self.speed, self.max_speed))

        self.rail_distance += self.speed * dt
        
        # Verification de crash
        angle= abs(raylib.vector2_angle(tan_at_car, tan_at_1cm))

        crash = False

        if self.speed < 50.0 or angle < 0.05:  # Cas triviaux
            crash = False
        else:
            # Rayon estimé : r = distance / angle = 1cm / angle
            # Force centrifuge : F = mv^2 / r  
            # F = mv^2 / (1/angle) = mv^2 × angle
            # Par unité de masse : F/m = v^2 × angle
            
            centrifugal_force = (self.speed ** 2) * angle
            
            # Crash si force centrifuge > capacité d'adhérence
            crash = centrifugal_force > self.max_grip_force

        return crash, self.get_state()

    def get_state(self):
        def get_angle_at_distance(distance_ahead):
            tan_current = self.circuit.get_tangent_at_rail(self.rail_distance, self.is_inside_rail)
            tan_ahead = self.circuit.get_tangent_at_rail(self.rail_distance + distance_ahead, self.is_inside_rail)
            return raylib.vector2_angle(tan_ahead, tan_current)

        position = self.circuit.get_position_at_rail(self.rail_distance, self.is_inside_rail)
        tangent = self.circuit.get_tangent_at_rail(self.rail_distance, self.is_inside_rail)
        return {
            'speed': self.speed,
            'angle_10cm': get_angle_at_distance(10),
            'angle_30cm': get_angle_at_distance(30),
            'angle_50cm': get_angle_at_distance(50),
            # Pour affichage/debug:
            'position': position,
            'tangent': tangent,
        }
    
    def reset(self):
        self.rail_distance = 0.0
        self.speed = 0.0
