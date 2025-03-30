import random
import math
from enum import IntEnum

from battlecode25.stubs import *

# This is an example bot written by the developers!
# Use this to help write your own code, or run it against your bot to see how well you can do!


class MessageType(IntEnum):
    SAVE_CHIPS = 0


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
tracing_turns = 0

height = get_map_height()
width = get_map_width()

# Bunny Variables
is_refilling = False
paint_capacity = 0

# Soldier Variables
is_searchsoldier = True
is_attackingsoldier = False
searchsoldier_type = [False] * 8
targets = [MapLocation(height-1,0), MapLocation(0,0), MapLocation(0, width-1), MapLocation(height-1, width-1)]
is_marking_SRP = False
has_marked_SRP = False
move_count = 0

# Mopper Variables
is_searchmopper = True
is_removing_enemy_paint = False

# Splasher Variables
is_searchsplasher = True
is_attackingsplasher = False

current_target = MapLocation(100000, 100000)

# Tower variables
be_attacked = 0
soldier_ratio = 70 
mopper_ratio = 72
spawned_defenders = 0
baseratio= int(math.sqrt(math.sqrt(height*width)))

def turn():
    """
    MUST be defined for robot to run
    This function will be called at the beginning of every turn and should contain the bulk of your robot commands
    """
    global turn_count
    global is_messenger
    global current_target
    global targets
    global is_refilling
    global paint_capacity
    global is_attackingsoldier
    global tracing_turns
    global is_attackingsplasher
    turn_count += 1

    block_width = int(math.sqrt(width)) 
    block_height = int(math.sqrt(height))
    i = 0
    while i < width:
        targets.append(MapLocation(0,i))
        targets.append(MapLocation(height-1,i))
        i += block_width
    i = 0
    while i < height:
        targets.append(MapLocation(i,0))
        targets.append(MapLocation(i,width-1))
        i += block_height
    # if get_type() == UnitType.MOPPER and get_id() % 3 == 0:
    #     is_messenger = True

    # Sets a part of soldiers as attackers
    if get_type() == UnitType.SOLDIER:
        if get_round_num() <= 300: 
            if get_id() % 4 == 0:
                is_attackingsoldier = True
            else:
                is_attackingsoldier = False
        else:
            if get_id() % 4 == 0:
                is_attackingsoldier = False
            else:   
                is_attackingsoldier = True
    if get_type() == UnitType.SPLASHER:
        if get_id() % 3 == 0:
            is_attackingsplasher = False
        else:
            is_attackingsplasher = True
    if current_target is not None and current_target == MapLocation(100000, 100000):
        current_target = MapLocation(random.randint(0, width-1), random.randint(0, height-1))
        tracing_turns = 0

    if get_type() == UnitType.SOLDIER:
        paint_capacity = 200
        run_soldier()
    elif get_type() == UnitType.MOPPER:
        paint_capacity = 100
        run_mopper()
    elif get_type() == UnitType.SPLASHER:
        paint_capacity = 300
        run_splasher()
    elif get_type().is_tower_type():
        run_tower()
    else:
        pass  # Other robot types?

def check_nearby_opp_paint():
    for tile in sense_nearby_map_infos(get_location(), 8):
        if tile.get_paint().is_enemy():
            return True
    return False

def build_tower_type(loc):
    tower_count = get_num_towers()
    if height * width <= 800:
        if tower_count % 4 == 0:
            return UnitType.LEVEL_ONE_PAINT_TOWER
        else:
            return UnitType.LEVEL_ONE_MONEY_TOWER
    else:
        mid_height = height // 2
        mid_width = width // 2
        sq_width = int(math.sqrt(35))
        sq_height = int(math.sqrt(35))
        if loc.x >= mid_width - sq_width and loc.x <= mid_width + sq_width and loc.y >= mid_height - sq_height and loc.y <= mid_height + sq_height and tower_count >= 6:
            return UnitType.LEVEL_ONE_DEFENSE_TOWER
        if tower_count < 7:
            return UnitType.LEVEL_ONE_MONEY_TOWER
        else:
            if tower_count % 2 == 1:
                return UnitType.LEVEL_ONE_PAINT_TOWER
            else:
                return UnitType.LEVEL_ONE_MONEY_TOWER

def run_tower():
    # Global variables
    global save_turns
    global should_save
    if (get_type() == UnitType.LEVEL_ONE_MONEY_TOWER or get_type() == UnitType.LEVEL_TWO_MONEY_TOWER) and turn_count >= 70 and check_nearby_opp_paint() == False and get_money() >= 5000 and get_num_towers() >= 3:
        disintegrate()

    dir = directions[random.randint(0, len(directions) - 1)]
    next_loc = get_location().add(dir)
    if get_round_num() == 1:
        if get_type() == UnitType.LEVEL_ONE_PAINT_TOWER:
            build_robot(UnitType.SOLDIER, next_loc)
            build_robot(UnitType.MOPPER, next_loc)
        else:
            build_robot(UnitType.SOLDIER, next_loc)
            build_robot(UnitType.SPLASHER, next_loc)
        return
    if get_round_num() == 2:
        if get_type() == UnitType.LEVEL_ONE_PAINT_TOWER:
            build_robot(UnitType.MOPPER, next_loc)
        else:
            build_robot(UnitType.SPLASHER, next_loc)
        return
    tower_count = get_num_towers()
    if get_round_num() <= 100:
        if tower_count <= 3:
            soldier_ratio = 65
            mopper_ratio = 85
        else:
            soldier_ratio = 55
            mopper_ratio = 65
    else:
        if tower_count <= 5:
            soldier_ratio = 50
            mopper_ratio = 60
        else:
            soldier_ratio = 45
            mopper_ratio = 55
    if save_turns == 0:
        # If we have no save turns remaining, start building robots
        should_save = False

        # Pick a direction to build in.
        dir = directions[random.randint(0, len(directions) - 1)]
        next_loc = get_location().add(dir)

        # Pick a random robot type to build.
        robot_type = random.randint(1, 100)
        if robot_type <= soldier_ratio and can_build_robot(UnitType.SOLDIER, next_loc):
            build_robot(UnitType.SOLDIER, next_loc)
            log("BUILT A SOLDIER")
        if robot_type > soldier_ratio and robot_type <= mopper_ratio and can_build_robot(UnitType.MOPPER, next_loc):
            build_robot(UnitType.MOPPER, next_loc)
            log("BUILT A MOPPER")
        if robot_type <= 100 and robot_type > mopper_ratio and can_build_robot(UnitType.SPLASHER, next_loc):
            build_robot(UnitType.SPLASHER, next_loc)
            log("BUILT A SPLASHER") 
    else:
        # Otherwise, tick down the number of remaining save turns
        set_indicator_string(f"Saving for {save_turns} more turns")
        save_turns -= 1

    # Read incoming messages
    messages = read_messages()
    for m in messages:
        log(f"Tower received message: '#{m.get_sender_id()}: {m.get_bytes()}'")

        # If we are not currently saving and we receive the save chips message, start saving
        if not should_save and m.get_bytes() == int(MessageType.SAVE_CHIPS):
            save_turns = 50
            should_save = True

    nearbyRobots = sense_nearby_robots(team=get_team().opponent())
    for robot in nearbyRobots:
        if (can_attack(robot.get_location())):
            attack(robot.get_location())

def upgrade_nearby_paint_towers():
    # Search for all nearby robots
    ally_robots  = sense_nearby_robots(team=get_team())
    for ally in ally_robots:
        # Only consider tower type
        if not ally.get_type().is_tower_type():
            continue

        ally_loc = ally.location
        if ((ally.get_type() == UnitType.LEVEL_ONE_PAINT_TOWER or ally.get_type() == UnitType.LEVEL_ONE_DEFENSE_TOWER) and get_money() >= 5000) and can_upgrade_tower(ally_loc):
            upgrade_tower(ally_loc)
        if ally.get_type() == UnitType.LEVEL_TWO_PAINT_TOWER and can_upgrade_tower(ally_loc) and get_money() >= 8000:
            upgrade_tower(ally_loc)
def refill_paint():
    # Global variables
    global is_refilling
    global paint_capacity

    # Resets refilling to 0
    if not len(known_towers) > 0:
        is_refilling = False
        return
    
    # Finds the nearest tower
    cur_tower = None
    cur_dist = 9999999
    for tower in known_towers:
        check_dist = tower.distance_squared_to(get_location())
        if check_dist < cur_dist:
            cur_dist = check_dist
            cur_tower = tower

    if cur_tower is not None:
        # Find robot at the tower's location
        dir = get_location().direction_to(cur_tower)
        set_indicator_string(f"Returning to {cur_tower}")
        next_dir = bug2(cur_tower)
        if next_dir is not None:
            move(next_dir)
        if can_sense_robot_at_location(cur_tower):
            tower_robot = sense_robot_at_location(cur_tower)
            amount_needed = -get_paint()
            if paint_capacity <= tower_robot.get_paint_amount():
                amount_needed += paint_capacity
            else:
                amount_needed += tower_robot.get_paint_amount()
            
            if amount_needed > 0 and can_transfer_paint(cur_tower, -amount_needed):
                log("Refilled Paint for Robot")
                transfer_paint(cur_tower, -amount_needed)
                is_refilling = False
    else:
        is_refilling = False

def mark_patterns():
    for tile in sense_nearby_map_infos():
        if tile.has_ruin() and sense_robot_at_location(tile.get_map_location()) == None:
            tile_loc = tile.get_map_location()
            if can_complete_tower_pattern(UnitType.LEVEL_ONE_DEFENSE_TOWER, tile_loc):
                complete_tower_pattern(UnitType.LEVEL_ONE_DEFENSE_TOWER, tile_loc)
            if can_complete_tower_pattern(UnitType.LEVEL_ONE_PAINT_TOWER, tile_loc):
                complete_tower_pattern(UnitType.LEVEL_ONE_PAINT_TOWER, tile_loc)
            if can_complete_tower_pattern(UnitType.LEVEL_ONE_MONEY_TOWER, tile_loc):
                complete_tower_pattern(UnitType.LEVEL_ONE_MONEY_TOWER, tile_loc)

def can_SRP():
    if not can_mark_resource_pattern(get_location()):
        return False
    for tile in sense_nearby_map_infos(get_location(), 8):
        tile_robot = sense_robot_at_location(tile.get_map_location())
        if tile.get_paint().is_enemy():
            return False
        elif tile.get_paint() == PaintType.ALLY_SECONDARY and tile_robot is not None and tile_robot.get_team() == get_team() and tile_robot.get_type().is_robot_type():
            return False
    return True

def SRP_mark():
    global is_marking_SRP
    global has_marked_SRP
    cur_loc = get_location()
    if has_marked_SRP == False:
        mark_resource_pattern(cur_loc)
        has_marked_SRP = True
    for pattern_tile in sense_nearby_map_infos(cur_loc, 8):
            if pattern_tile.get_mark() != pattern_tile.get_paint() and pattern_tile.get_mark() != PaintType.EMPTY:
                use_secondary = pattern_tile.get_mark() == PaintType.ALLY_SECONDARY
                if can_attack(pattern_tile.get_map_location()):
                    attack(pattern_tile.get_map_location(), use_secondary)
    if can_complete_resource_pattern(cur_loc):
        complete_resource_pattern(cur_loc)
        is_marking_SRP = False

def run_soldier():
    if is_attackingsoldier:
        set_indicator_dot(get_location(), 255,0,0)
    # Global variables
    global is_refilling
    global current_target
    global targets
    global tracing_turns
    global SRP_position
    global is_marking_SRP
    global move_count 

    cur_loc = get_location()

    # if is_marking_SRP == False and can_SRP() == True:
    #     is_marking_SRP = True

    # if is_marking_SRP:
    #     SRP_mark()
    #     return
    
    if turn_count == 1 :
        move_count = 0
    if is_attackingsoldier and (turn_count == 1 or current_target is None):
        rand = random.randint(1,3)
        if rand == 1:
            current_target = MapLocation(cur_loc.x, height - cur_loc.y)
        elif rand == 2:
            current_target = MapLocation(width-cur_loc.x,height-cur_loc.y)
        else:
            current_target = MapLocation(width - cur_loc.x, cur_loc.y)
        move_count = 0

    upgrade_nearby_paint_towers()

    #Checks if refilling is needed
    if get_paint() <= 20:
        is_refilling = True
    if is_refilling == True: 
        refill_paint()
        return
    
    # Sense information about all visible nearby tiles.
    nearby_tiles = sense_nearby_map_infos()

    # Search for the closest nearby ruin to complete.
    cur_ruin = None
    cur_dist = 9999999
    # Search if there are any enemy towers
    cur_enemy_tower = None
    for tile in nearby_tiles:
        if tile.has_ruin() and sense_robot_at_location(tile.get_map_location()) == None:
            check_dist = tile.get_map_location().distance_squared_to(get_location())
            if check_dist < cur_dist:
                cur_dist = check_dist
                cur_ruin = tile
        if is_attackingsoldier:
            tile_robot = sense_robot_at_location(tile.get_map_location())
            if tile_robot is not None and tile_robot.get_type().is_tower_type() and not tile_robot.get_team() == get_team():
                cur_enemy_tower = tile.get_map_location()

    if cur_ruin is not None:
        target_loc = cur_ruin.get_map_location()
        dir = get_location().direction_to(target_loc)
        if can_move(dir):
            move(dir)

        # Mark the pattern we need to draw to build a tower here if we haven't already.
        should_mark = cur_ruin.get_map_location().subtract(dir)
        if sense_map_info(should_mark).get_mark() == PaintType.EMPTY and can_mark_tower_pattern(build_tower_type(target_loc), target_loc):
            mark_tower_pattern(build_tower_type(target_loc), target_loc)
            log("Trying to build a tower at " + str(target_loc))
        
        # Fill in any spots in the pattern with the appropriate paint.
        for pattern_tile in sense_nearby_map_infos(target_loc, 8):
            if pattern_tile.get_mark() != pattern_tile.get_paint() and pattern_tile.get_mark() != PaintType.EMPTY:
                use_secondary = pattern_tile.get_mark() == PaintType.ALLY_SECONDARY
                if can_attack(pattern_tile.get_map_location()):
                    attack(pattern_tile.get_map_location(), use_secondary)

        # Complete the ruin if we can.
        if can_complete_tower_pattern(build_tower_type(target_loc), target_loc):
            complete_tower_pattern(build_tower_type(target_loc), target_loc)
            set_timeline_marker("Tower built", 0, 255, 0)
            log("Built a tower at " + str(target_loc) + "!")

    # Attacks enemy tower 
    if cur_enemy_tower is not None and is_attackingsoldier:
        enemy_tower_dist = get_location().distance_squared_to(cur_enemy_tower)
        dir = bug2(cur_enemy_tower)
        if enemy_tower_dist > 4:
            if dir is not None:
                move(dir)
            if can_attack(cur_enemy_tower):
                log("Gotta kill em all")
                attack(cur_enemy_tower)
        else:
            if can_attack(cur_enemy_tower):
                log("Gotta kill em all")
                attack(cur_enemy_tower)
            away = get_location().direction_to(cur_enemy_tower).opposite()
            if can_move(away):
                move(away)
            elif can_move(away.rotate_left()):
                move(away.rotate_left())
            elif can_move(away.rotate_right()):
                move(away.rotate_right())

    mark_patterns()

    update_friendly_towers()

    # for tile in nearby_tiles:
    #     if tile.get_paint() == PaintType.EMPTY:
    #         if can_attack(tile.get_map_location()):
    #             attack(tile.get_map_location())
            
    if is_attackingsoldier == False and current_target is None:
        current_target = MapLocation(random.randint(0, width-1), random.randint(0, height-1))

    # Movement
    if is_searchsoldier == False:
        dir = directions[random.randint(0, len(directions) - 1)]
        next_loc = get_location().add(dir)
        if can_move(dir):
            move(dir)
    elif current_target is not None:
        if is_attackingsoldier == False and (get_location().distance_squared_to(current_target) <= 5 or move_count >= 100):
            log("Reached target, now changing to new target")
            current_target = MapLocation(random.randint(0, width-1), random.randint(0, height-1))
            tracing_turns = 0
            move_count = 0
        if is_attackingsoldier and get_location().distance_squared_to(current_target) <= 2:
            current_target = None
        move_count += 1
        if current_target is not None:
            search_dir = bug2(current_target)
            if search_dir is not None:
                move(search_dir)
 
    # Try to paint beneath us as we walk to avoid paint penalties.
    # Avoiding wasting paint by re-painting our own tiles.
    current_tile = sense_map_info(get_location())
    if not current_tile.get_paint().is_ally() and can_attack(get_location()):
        attack(get_location())
    else:
        for tile in sense_nearby_map_infos(get_location(), 3):
            if tile.get_paint() == PaintType.EMPTY and can_attack(tile.get_map_location()):
                attack(tile.get_map_location())


def run_mopper():
    # Global Variables
    global current_target
    global targets
    global tracing_turns
    global is_removing_enemy_paint

    upgrade_nearby_paint_towers()
    
    if should_save and len(known_towers) > 0:
        # Move to first known tower if we are saving
        cur_tower = None
        cur_dist = 9999999
        for tower in known_towers:
            check_dist = tower.get_map_location().distance_squared_to(get_location())
            if check_dist < cur_dist:
                cur_dist = check_dist
                cur_tower = tower
        dir = get_location().direction_to(cur_tower)
        set_indicator_string(f"Returning to {known_towers[0]}")
        if cur_tower != None:
            next_dir = bug2(cur_tower)
            move(next_dir)

    # Finds ruins nearby and checks if it is buildable
    nearby_tiles = sense_nearby_map_infos()
    for tile in nearby_tiles:
        if is_removing_enemy_paint:
            break
        tile_loc = tile.get_map_location()
        robot_tile = sense_robot_at_location(tile_loc)
        if tile.has_ruin() and (robot_tile == None or (robot_tile.get_team() == get_team())):
            for ntile in sense_nearby_map_infos(tile_loc, 8):
                if can_sense_location(ntile.get_map_location()) and ntile.get_paint().is_enemy():
                    current_target = ntile.get_map_location()
                    is_removing_enemy_paint = True
                    break

    update_friendly_towers()

    mark_patterns()

    if is_removing_enemy_paint and (can_attack(current_target) or (can_sense_location(current_target) and sense_map_info(current_target).get_paint().is_ally())):
        if can_attack(current_target):
            attack(current_target)
        current_target = None
        is_removing_enemy_paint = False

    enemy_robots = sense_nearby_robots(get_location(),2,team=get_team().opponent())    
    for robot in enemy_robots:
        robot_dir = get_location().direction_to(robot.get_location())
        if can_mop_swing(robot_dir):
            mop_swing(robot_dir)

    if current_target is None or (is_removing_enemy_paint == False and get_location().distance_squared_to(current_target) <= 5):
        log("Reached target, now changing to new target")
        current_target = MapLocation(random.randint(0, width-1), random.randint(0, height-1))
        tracing_turns = 0

    # Move and attack.
    if is_searchmopper == False:
        dir = directions[random.randint(0, len(directions) - 1)]
        next_loc = get_location().add(dir)
        if can_move(dir):
            move(dir)
        if can_attack(next_loc):
            attack(next_loc)
    elif current_target is not None:
        search_dir = bug2(current_target)
        if search_dir is not None:
            next_loc = get_location().add(search_dir)
            move(search_dir)

    for tile in sense_nearby_map_infos(get_location(), 2):
        if tile.get_paint().is_enemy() and can_attack(tile.get_map_location()):
            attack(tile.get_map_location())

    update_enemy_robots()

    if is_messenger:
        # Set a useful indicator at this mopper's location so we can see who is a messenger
        set_indicator_dot(get_location(), 255, 0, 0)

        update_friendly_towers()
        check_nearby_ruins()

def splasher_profit(cur_loc):
    team_paint = 0
    opponent_paint = 0
    not_painted = 0
    enemy_tower = 0
    for tile in sense_nearby_map_infos(cur_loc, 4):
        if tile is None:
            continue  # Skip invalid tiles
        robot_tile = sense_robot_at_location(tile.get_map_location())
        if tile.has_ruin() and robot_tile is not None and robot_tile.get_type().is_tower_type() and robot_tile.get_team() == get_team().opponent():
            enemy_tower += 1
        paint = tile.get_paint()
        if paint != PaintType.EMPTY:
            if paint.is_ally():
                team_paint += 1
            elif paint.is_enemy():
                opponent_paint += 1
        else:
            not_painted += 1
    return enemy_tower * 4 + opponent_paint * 2 + not_painted - team_paint

def run_splasher():
    # Global variables
    global is_refilling
    global current_target
    global tracing_turns
    global move_count
    global is_attackingsplasher

    cur_loc = get_location()

    upgrade_nearby_paint_towers()

    # Checks if needs refill
    if get_paint() <= 20:
        is_refilling = True
    if is_refilling == True: 
        refill_paint()
        return

    update_friendly_towers()

    mark_patterns()

    if turn_count == 1 :
        move_count = 0
    if is_attackingsplasher and (turn_count == 1 or current_target is None):
        rand = random.randint(1,3)
        if rand == 1:
            current_target = MapLocation(cur_loc.x, height - cur_loc.y)
        elif rand == 2:
            current_target = MapLocation(width-cur_loc.x,height-cur_loc.y)
        else:
            current_target = MapLocation(width - cur_loc.x, cur_loc.y)
        move_count = 0

    if is_attackingsplasher == False and current_target is None:
        current_target = MapLocation(random.randint(0, width-1), random.randint(0, height-1))

    if is_searchsplasher == False:
        dir = directions[random.randint(0, len(directions) - 1)]
        next_loc = cur_loc.add(dir)
        if can_move(dir):
            move(dir)
        if can_attack(next_loc):
            attack(next_loc)
    elif current_target is not None:
        if is_attackingsplasher == False and (cur_loc.distance_squared_to(current_target) <= 5 or move_count >= 100):
            log("Reached target, now changing to new target")
            current_target = MapLocation(random.randint(0, width-1), random.randint(0, height-1))
            tracing_turns = 0
            move_count = 0
        if is_attackingsplasher and cur_loc.distance_squared_to(current_target) <= 2:
            current_target = None
        move_count += 1
        if current_target is not None:
            search_dir = bug2(current_target)
            if search_dir is not None:
                move(search_dir)
    max_splasher_profit = 0
    cur_loc = get_location()
    attack_position = cur_loc
    for tile in sense_nearby_map_infos(cur_loc, 4):
        if not can_attack(tile.get_map_location()):
            continue
        cur_profit = splasher_profit(tile.get_map_location())
        if cur_profit > max_splasher_profit:
            max_splasher_profit = cur_profit
            attack_position = tile.get_map_location()
    if max_splasher_profit >= 6:
        attack(attack_position)

def update_friendly_towers():
    global should_save

    # Search for all nearby robots
    ally_robots  = sense_nearby_robots(team=get_team())
    for ally in ally_robots:
        # Only consider tower type
        if not ally.get_type().is_tower_type():
            continue

        ally_loc = ally.location
        if ally_loc in known_towers:
            # Send a message to the nearby tower
            if should_save and can_send_message(ally_loc):
                send_message(ally_loc, int(MessageType.SAVE_CHIPS))
                should_save = False

            # Skip adding to the known towers array
            continue

        # Add to our known towers array
        known_towers.append(ally_loc)
        set_indicator_string(f"Found tower {ally.get_id()}")


def check_nearby_ruins():
    global should_save

    # Search for nearby ruins
    nearby_tiles = sense_nearby_map_infos()
    for tile in nearby_tiles:
        tile_loc = tile.get_map_location()

        # Skip completed ruins
        if not tile.has_ruin() or sense_robot_at_location(tile_loc) != None:
            continue

        # Heuristic to see if the ruin is trying to be built on
        mark_loc = tile_loc.add(tile_loc.direction_to(get_location()))
        mark_info = sense_map_info(mark_loc)
        if not mark_info.get_mark().is_ally():
            continue

        should_save = True

        # Return early
        return


def update_enemy_robots():
    # Sensing methods can be passed in a radius of -1 to automatically 
    # use the largest possible value.
    enemy_robots = sense_nearby_robots(team=get_team().opponent())
    if len(enemy_robots) == 0:
        return

    set_indicator_string("There are nearby enemy robots! Scary!")

    # Save an array of locations with enemy robots in them for possible future use.
    enemy_locations = [None] * len(enemy_robots)
    for i in range(len(enemy_robots)):
        enemy_locations[i] = enemy_robots[i].get_location()

    # Occasionally try to tell nearby allies how many enemy robots we see.
    ally_robots = sense_nearby_robots(team=get_team())
    if get_round_num() % 20 == 0:
        for ally in ally_robots:
            if can_send_message(ally.location):
                send_message(ally.location, len(enemy_robots))

#Bug 0
def bug0(target):
    # get direction from current location to target
    dir = get_location().direction_to(target)
    nextLoc = get_location().add(dir)

    # try to move in target direction
    if(can_move(dir)):
        move(dir)

    # keep turning left until we can move
    for i in range(8):
        dir = dir.rotate_left()
        if can_move(dir):
            move(dir)
            break

#Bug 1
def bug1(target):
    global is_tracing, smallest_distance, map_location, closest_location, tracing_dir

    if not is_tracing:
        # proceed as normal
        dir = get_location().direction_to(target)
        next_loc = get_location().add(dir)

        # try to move in target direction
        if can_move(dir):
            move(dir)
        else:
            is_tracing = True
            tracing_dir = dir
    else:
        # in tracing mode

        # need a stopping condition - this will be when we see the closest location again
        if closest_location is not None and get_location() == closest_location: 
            # reset global tracing variables
            is_tracing = False
            smallest_distance = 10000000
            closest_location = None
            tracing_dir = None
        else:
            # continue tracing

            # update closest_location and smallest_distance
            dist_to_target = get_location().distance_squared_to(target)
            if dist_to_target < smallest_distance:
                smallest_distance = dist_to_target
                closest_location = get_location()
            
            # go along perimeter of obstacle
            if can_move(tracing_dir):
                # move forward & try to turn right
                move(tracing_dir)
                tracing_dir = tracing_dir.rotate_right()
                tracing_dir = tracing_dir.rotate_right()
            else:
                # turn left because we can't move forward; keep turning left until we can move again
                for i in range(8):
                    tracing_dir = tracing_dir.rotate_left()
                    if can_move(tracing_dir):
                        move(tracing_dir)
                        tracing_dir = tracing_dir.rotate_right()
                        tracing_dir = tracing_dir.rotate_right()
                        break
            
#Bug 2

def bug2(target):
    global prev_dest, line, is_tracing, obstacle_start_dist, tracing_dir, tracing_turns

    current_loc = get_location()
    
    # Reset line if target changes
    if target.compare_to(prev_dest) != 0:
        prev_dest = target
        line = create_line(current_loc, target)
        is_tracing = False

    if not is_tracing:
        # Try to move directly toward target
        dir_to_target = current_loc.direction_to(target)
        
        if can_move(dir_to_target):
            tracing_turns = 0
            return dir_to_target
        else:
            # Start tracing obstacle
            is_tracing = True
            obstacle_start_dist = current_loc.distance_squared_to(target)
            # Start by hugging the obstacle to the right
            tracing_dir = dir_to_target.rotate_right().rotate_right()
            tracing_turns = 0

    # Obstacle tracing logic
    if is_tracing:
        tracing_turns += 1
        
        # Check exit condition: back on line closer to target
        if current_loc in line and current_loc.distance_squared_to(target) < obstacle_start_dist:
            is_tracing = False
            tracing_turns = 0
            return current_loc.direction_to(target)

        # Try to follow obstacle contour (keep wall on right)
        for _ in range(8):
            # Try to move forward in current tracing direction
            if can_move(tracing_dir):
                next_dir = tracing_dir
                # Prepare next direction to keep wall on right
                tracing_dir = tracing_dir.rotate_left()
                return next_dir
            else:
                # Rotate clockwise to find new path
                tracing_dir = tracing_dir.rotate_right()

        # Emergency exit if completely stuck
        if tracing_turns > 50:
            is_tracing = False
            return None

    return None  # Should never reach here

def create_line(a, b):
    line = set()
    x0, y0 = a.x, a.y
    x1, y1 = b.x, b.y
    
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    
    while True:
        line.add(MapLocation(x0, y0))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy
            
    return line

def sign(num):
    """Return the sign of num (-1, 0, or 1)."""
    if num > 0:
        return 1
    elif num < 0:
        return -1
    return 0

def get_direction_to(a, b):
    """Return a grid direction (dx, dy) from a to b."""
    dx = b.x - a.x
    dy = b.y - a.y
    return (sign(dx), sign(dy))