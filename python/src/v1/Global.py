import random
import math
from enum import IntEnum

from battlecode25.stubs import *

class global_variables:
    # Globals
    turn_count = 0
    directions = [
        Direction.NORTH,
        Direction.NORTHEAST,
        Direction.EAST,
        Direction.SOUTHEAST,
        Direction.SOUTH,
        Direction.SOUTHWEST,
        Direction.WEST,
        Direction.NORTHWEST,
    ]

    # Variables for communication
    known_towers = []
    is_messenger = False
    should_save = False
    save_turns = 0

    # Bug1 Variables
    is_tracing = False # also used in bug 2
    smallest_distance = 10000000
    closest_location = None
    tracing_dir = None

    # Bug2 Variables
    prev_dest = MapLocation(100000, 100000)
    line = set()
    obstacle_start_dist = 0
    tracing_dir = None

    height = get_map_height()
    width = get_map_width()

    # Bunny Variables
    is_refilling = False
    paint_capacity = 0

    # Soldier Variables
    is_searchsoldier = True
    is_attackingsoldier = False
    searchsoldier_type = [False] * 8
    target_of_soldier = MapLocation(100000, 100000)
    targets = [MapLocation(height-1,0), MapLocation(0,0), MapLocation(0, width-1), MapLocation(height-1, width-1)]

    # Mopper Variables
    is_searchmopper = True
    target_of_mopper = MapLocation(100000, 100000)

    # Splasher Variables
    is_searchsplasher= True
    target_of_splasher = MapLocation(100000, 100000)