from __future__ import annotations

import math
from typing import Tuple

# Standard Free Space Path Loss (FSPL) or Log-Distance approximation
# For drones, let's use a 5.8 GHz frequency carrier model.

TX_POWER_DBM = 20.0     # 100mW transmit power
TX_GAIN_DB = 2.0        # Antenna gain
RX_GAIN_DB = 2.0
FREQ_MHZ = 5800.0       

NOISE_FLOOR_DBM = -95.0 # Typical receiver noise floor

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance between two points on the earth in meters."""
    R = 6371000  # radius of Earth in meters
    phi_1 = math.radians(lat1)
    phi_2 = math.radians(lat2)

    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi_1) * math.cos(phi_2) * \
        math.sin(delta_lambda / 2.0) ** 2

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def calculate_rssi(distance_m: float) -> float:
    """Calculates RSSI based on Free Space Path Loss."""
    if distance_m <= 0:
        return TX_POWER_DBM + TX_GAIN_DB + RX_GAIN_DB
        
    # Free space path loss formula: 20*log10(d) + 20*log10(f) - 27.55 (when d in meters, f in MHz)
    fspl = 20 * math.log10(distance_m) + 20 * math.log10(FREQ_MHZ) - 27.55
    
    rssi = TX_POWER_DBM + TX_GAIN_DB + RX_GAIN_DB - fspl
    return rssi

def calculate_link_metrics(lat1: float, lng1: float, lat2: float, lng2: float) -> Tuple[float, float]:
    """
    Returns (rssi, packet_loss_rate) for the link between two coordinates.
    """
    dist = haversine_distance(lat1, lng1, lat2, lng2)
    rssi = calculate_rssi(dist)
    
    # Simple packet loss model based on RSSI and Noise Floor
    # Margin = RSSI - NoiseFloor
    # If margin > 15 dB, PLR is ~0.
    # If margin < 5 dB, PLR is very high.
    
    margin = rssi - NOISE_FLOOR_DBM
    
    if margin >= 15.0:
        plr = 0.0
    elif margin <= 0.0:
        plr = 1.0 # 100% loss, connection dropped
    else:
        # Linear degradation from 15dB down to 0dB margin
        plr = 1.0 - (margin / 15.0)
        
    # Add a tiny bit of random noise (0-2%) to PLR if connected
    if plr < 1.0:
        import random
        plr += random.uniform(0.0, 0.02)
        plr = min(1.0, plr)
        
    return rssi, plr
