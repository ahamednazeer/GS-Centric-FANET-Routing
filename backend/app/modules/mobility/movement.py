from __future__ import annotations

import random
from typing import List
from sqlmodel import Session, select
from app.models import Node, NodeRole
from app.config import DEFAULT_MOBILITY

# A bounded geographic area around a simulated center (e.g. some field in reality)
# We will use a center coordinate of (37.7749, -122.4194) (San Francisco) 
# and move nodes within a ~5km box.

CENTER_LAT = 37.7749
CENTER_LNG = -122.4194

# Roughly 1 degree of latitude is 111km. 
# So 0.01 degrees is ~1.1km.
# Let's keep nodes within +/- 0.05 degrees.
BOUND_LAT_MIN = CENTER_LAT - 0.05
BOUND_LAT_MAX = CENTER_LAT + 0.05
BOUND_LNG_MIN = CENTER_LNG - 0.05
BOUND_LNG_MAX = CENTER_LNG + 0.05

class MovementEngine:
    def __init__(self, tick_duration_seconds: float = 2.0) -> None:
        self.tick_duration = tick_duration_seconds
        
        # Max velocity in degrees per tick.
        # Let's say drones move at max 20 m/s.
        # 20 m/s = ~0.00018 degrees per second.
        self.max_deg_per_sec = 0.00018
        
    def step(self, session: Session) -> None:
        nodes = session.exec(select(Node).where(Node.role == NodeRole.UAV)).all()
        for node in nodes:
            # If a node doesn't have coordinates or velocity yet, initialize it
            if node.lat is None or node.lng is None:
                continue # wait for seed
            
            if node.vx is None or node.vy is None:
                self._assign_random_vector(node)
                
            # Randomly decide to change waypoint/vector (e.g., 5% chance per tick to turn)
            if random.random() < 0.05:
                self._assign_random_vector(node)
                
            # Move by velocity
            node.lat += node.vx * self.tick_duration # type: ignore
            node.lng += node.vy * self.tick_duration # type: ignore
            
            # Bounce off bounds
            if node.lat < BOUND_LAT_MIN:
                node.lat = BOUND_LAT_MIN
                node.vx *= -1  # type: ignore
            elif node.lat > BOUND_LAT_MAX:
                node.lat = BOUND_LAT_MAX
                node.vx *= -1  # type: ignore
                
            if node.lng < BOUND_LNG_MIN:
                node.lng = BOUND_LNG_MIN
                node.vy *= -1  # type: ignore
            elif node.lng > BOUND_LNG_MAX:
                node.lng = BOUND_LNG_MAX
                node.vy *= -1  # type: ignore
                
            session.add(node)
        session.commit()
        
    def _assign_random_vector(self, node: Node) -> None:
        speed = random.uniform(self.max_deg_per_sec * 0.2, self.max_deg_per_sec)
        angle = random.uniform(0, 3.14159 * 2) # radians
        import math
        node.vx = speed * math.cos(angle)
        node.vy = speed * math.sin(angle)
        node.vz = 0.0 # Keeping at static altitude for simple 2D map viewing
