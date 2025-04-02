import random
import math
from enum import IntEnum

from battlecode25.stubs import *

# This is an example bot written by the developers!
# Use this to help write your own code, or run it against your bot to see how well you can do!


class MessageType(IntEnum):
    SAVE_CHIPS = 0,
    FLICKER = 7

def encode_flicker(loc):
    return loc.x * 64 + loc.y + 1


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
known_money_towers = []
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
is_painting_pattern = False 
painting_turns = 0
turns_without_attack = 0
painting_ruin_loc = None
tower_type = None
is_SRP_builder = False
SRP_positions = []
has_marked_tower = False

paint_tower_pattern = None
money_tower_pattern = None
defense_tower_pattern = None

tainted_ruins = []

is_flickering_tower = False
flicker_tower_loc = None

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
spawned_moppers = 0
spawned_soldiers = 0
spawned_splashers = 0
baseratio= int(math.sqrt(math.sqrt(height*width)))
is_starting_tower = False
mid_game_start = 100
end_game_start = 250

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
    global paint_tower_pattern
    global money_tower_pattern
    global defense_tower_pattern
    global is_SRP_builder
    global is_starting_tower
    global spawned_moppers
    global spawned_splashers
    global spawned_soldiers
    global mid_game_start
    global end_game_start
    turn_count += 1

    if turn_count == 1:
        paint_tower_pattern = get_tower_pattern(UnitType.LEVEL_ONE_PAINT_TOWER)
        money_tower_pattern = get_tower_pattern(UnitType.LEVEL_ONE_MONEY_TOWER)
        defense_tower_pattern = get_tower_pattern(UnitType.LEVEL_ONE_DEFENSE_TOWER)

    # block_width = int(math.sqrt(width)) 
    # block_height = int(math.sqrt(height))
    # i = 0
    # while i < width:
    #     targets.append(MapLocation(0,i))
    #     targets.append(MapLocation(height-1,i))
    #     i += block_width
    # i = 0
    # while i < height:
    #     targets.append(MapLocation(i,0))
    #     targets.append(MapLocation(i,width-1))
    #     i += block_height
    # if get_type() == UnitType.MOPPER and get_id() % 3 == 0:
    #     is_messenger = True
    round_num = get_round_num()
    if round_num == mid_game_start or round_num == end_game_start:
        spawned_moppers = 0
        spawned_splashers = 0
        spawned_soldiers = 0

    # Sets a part of soldiers as attackers
    if get_type() == UnitType.SOLDIER:
        if round_num <= 150: 
            if get_id() % 4 == 0:
                is_attackingsoldier = True
            else:
                is_attackingsoldier = True
        else:
            if get_id() % 4 == 0:
                is_attackingsoldier = True
            else:   
                is_attackingsoldier = True
        if round_num <= 100:
            is_SRP_builder = False
        else:
            if get_id() % 3 == 0:
                is_SRP_builder = False
            else:
                is_SRP_builder = True
    if get_type() == UnitType.SPLASHER:
        if get_id() % 4 == 0:
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
        if get_round_num():
            is_starting_tower = True
        run_tower()
    else:
        pass  # Other robot types?

def check_nearby_opp_paint():
    for tile in sense_nearby_map_infos(get_location(), 8):
        if tile.get_paint().is_enemy():
            return True
    return False

def build_tower_type(loc):
    global height
    global width
    tower_count = get_num_towers()
    if get_money() <= 1000:
        return UnitType.LEVEL_ONE_MONEY_TOWER
    if height * width <= 800:
        if tower_count % 4 == 0:
            return UnitType.LEVEL_ONE_PAINT_TOWER
        else:
            return UnitType.LEVEL_ONE_MONEY_TOWER
    else:
        mid_height = height // 2
        mid_width = width // 2
        sq_width = int(math.sqrt(35)) / 2
        sq_height = int(math.sqrt(35)) / 2
        if loc.x >= mid_width - sq_width and loc.x <= mid_width + sq_width and loc.y >= mid_height - sq_height and loc.y <= mid_height + sq_height and tower_count >= 6:
            return UnitType.LEVEL_ONE_DEFENSE_TOWER
        return UnitType.LEVEL_ONE_MONEY_TOWER

def has_nearby_robots():
    for tile in sense_nearby_map_infos():
        tile_loc = tile.get_map_location()
        if can_sense_location(tile_loc) == False:
            continue
        tile_robot = sense_robot_at_location(tile_loc)
        if tile_robot is not None and tile_robot.get_team() == get_team() and not tile_robot.get_type().is_tower_type():
            return True
    return False

def spawn_type():
    global height
    global width
    min_hw = height
    if width < min_hw:
        min_hw = width
    cur_round = get_round_num()
    cur_paint = get_paint()
    if get_type() == UnitType.LEVEL_ONE_PAINT_TOWER:
        if cur_round < mid_game_start:
            if min_hw <= 30 and spawned_splashers == 0:
                return UnitType.SPLASHER
            else:
                return UnitType.SOLDIER
        elif cur_round < end_game_start:
            soldier_count = spawned_soldiers / 3.0
            splasher_count = spawned_splashers / 1.0
            mopper_count = spawned_moppers / 2.0
            if splasher_count <= soldier_count and splasher_count <= mopper_count and get_num_towers() < 6:
                return UnitType.SPLASHER
            else:
                if mopper_count <= soldier_count - 0.5:
                    return UnitType.MOPPER
                if soldier_count <= mopper_count - 0.5:
                    return UnitType.SOLDIER
                if get_chips() >= 2000:
                    return UnitType.MOPPER
                else:
                    return UnitType.SOLDIER
        else:
            soldier_count = spawned_soldiers / 1.0
            splasher_count = spawned_splashers / 4.0
            mopper_count = spawned_moppers / 2.0
            if splasher_count <= soldier_count and splasher_count <= mopper_count:
                return UnitType.SPLASHER
            else:
                if mopper_count <= soldier_count - 2:
                    return UnitType.MOPPER
                if soldier_count <= mopper_count - 2:
                    return UnitType.SOLDIER
                if get_chips() >= 2000:
                    return UnitType.MOPPER
                else:
                    return UnitType.SOLDIER
    else:
        if cur_round < mid_game_start:
            if min_hw <= 30 and spawned_splashers == 0 and cur_paint >= 300:
                return UnitType.SPLASHER
            else:
                return UnitType.SOLDIER
        elif cur_round < end_game_start:
            if cur_paint < 200:
                return UnitType.MOPPER
            else:
                if get_chips() > 1500 and cur_paint >= 300:
                    return UnitType.SPLASHER
                else:
                    return UnitType.SOLDIER
        else:
            if cur_paint < 200:
                return UnitType.MOPPER
            elif cur_paint < 300:
                return UnitType.SOLDIER
            elif get_chips() > 1500 and get_round_num() % 10 != 0:
                return UnitType.SPLASHER
            else:
                return UnitType.SOLDIER

# def flicker():
#     if get_chips() < 2500 or get_paint() >= 100: 
#         return
#     if get_type() == UnitType.LEVEL_ONE_MONEY_TOWER:
#         nearby_tiles = sense_nearby_map_infos(get_location(), 8)
#         incorrect_paint = 0
#         for tile in nearby_tiles:
#             if tile.get_map_location() == get_location():
#                 continue
#             if tile.get_paint().is_enemy():
#                 return
#             if tile.get_paint() == PaintType.EMPTY or tile.get_paint() != tile.get_mark():
#                 incorrect_paint += 1
#         if incorrect_paint < 3 or get_chips() > 5000:
#             log("I need to flicker dumbass")
#             nearby_allies = sense_nearby_robots(team=get_team())
#             min_dist = 9999
#             closest_ally = None
#             for ally in nearby_allies:
#                 if ally.get_type() == UnitType.SOLDIER and can_send_message(ally.get_location()) and ally.get_paint_amount() > incorrect_paint * 5 + 10:
#                     dist = get_location().distance_squared_to(ally.get_location())
#                     if dist <= min_dist:
#                         min_dist = dist
#                         closest_ally = ally
#             if closest_ally is not None:
#                 nearby_enemies = sense_nearby_robots(team = get_team().opponent())
#                 for enemy in nearby_enemies:
#                     if enemy.get_type() == UnitType.MOPPER or enemy.get_type == UnitType.SPLASHER:
#                         return
#                 message = encode_flicker(get_location())
#                 if can_send_message(closest_ally.get_location(), message):
#                     log("Sending flicker message to abcxyz")
#                     send_message(closest_ally.get_location(), message)
#                 if closest_ally.get_location().distance_squared_to(get_location()) <= 2 and incorrect_paint == 0:
#                     disintegrate()

def run_tower():
    # Global variables
    global save_turns
    global should_save
    global height
    global width
    global spawned_moppers
    global spawned_splashers
    global spawned_soldiers
    global mid_game_start
    global end_game_start
    global directions


    if (get_type() == UnitType.LEVEL_ONE_MONEY_TOWER or get_type() == UnitType.LEVEL_TWO_MONEY_TOWER) and turn_count >= 65 and check_nearby_opp_paint() == False and get_money() >= 2500 and get_num_towers() >= 3 and has_nearby_robots():
        disintegrate()
    # flicker()
    cur_round = get_round_num()
    next_loc = None
    for dir in directions:
        loc = get_location().add(dir)
        if sense_map_info(loc).is_passable():
            next_loc = loc
            break
    if cur_round <= 3 and is_starting_tower:
        build_robot(UnitType.SOLDIER, next_loc)
    else:
        # if cur_round > 4:
        #     nearby_enemy_robots = sense_nearby_robots(team = get_team().opponent())
        #     cur_type = get_type()
        #     if len(nearby_enemy_robots) > 0 and (cur_type == UnitType.LEVEL_ONE_PAINT_TOWER or cur_type == UnitType.LEVEL_TWO_PAINT_TOWER or cur_type == UnitType.LEVEL_THREE_PAINT_TOWER):
        #         has_attacker = False
        #         for robot in nearby_enemy_robots:
        #             if robot.get_type() == UnitType.SOLDIER or robot.get_type() == UnitType.SPLASHER:
        #                 has_attacker = True
        #         if has_attacker and can_build_robot(UnitType.MOPPER, next_loc):
        #             build_robot(UnitType.MOPPER, next_loc)

        bot_type = spawn_type()
        if get_chips() > bot_type.money_cost + 1000 and get_paint() > bot_type.paint_cost:
            build_robot(bot_type, next_loc)
            if bot_type == UnitType.SOLDIER:
                spawned_soldiers += 1
            elif bot_type == UnitType.SPLASHER:
                spawned_splashers += 1
            else:
                spawned_moppers += 1

    # if height * width <= 800:
    #     soldier_ratio = 60
    #     mopper_ratio = 63
    # elif height * width <= 1600:
    #     soldier_ratio = 65
    #     mopper_ratio = 67
    # else:
    #     if cur_round <= 200:
    #         soldier_ratio = 90
    #         mopper_ratio = 92
    #     elif cur_round <= 400:
    #         soldier_ratio = 55
    #         mopper_ratio = 59
    #     else:
    #         soldier_ratio = 50
    #         mopper_ratio = 55
    # if cur_round >= 700 and get_num_towers() <= 4:
    #     soldier_ratio = 50
    #     mopper_ratio = 55 

    # Read incoming messages
    messages = read_messages()
    for m in messages:
        log(f"Tower received message: '#{m.get_sender_id()}: {m.get_bytes()}'")

        # If we are not currently saving and we receive the save chips message, start saving
        if not should_save and m.get_bytes() == int(MessageType.SAVE_CHIPS):
            save_turns = 50
            should_save = True

    nearbyRobots = sense_nearby_robots(team=get_team().opponent())
    min_health = 9999
    min_health_enemy = None
    for robot in nearbyRobots:
        robot_health = robot.get_health()
        if (can_attack(robot.get_location()) and robot_health < min_health):
            min_health = robot_health
            min_health_enemy = robot.get_location()
    attack(min_health_enemy)
    # t_type = get_type()
    # if len(nearbyRobots) > 0 and has_spawned_mopper == False and (t_type == UnitType.LEVEL_ONE_PAINT_TOWER or t_type == UnitType.LEVEL_TWO_PAINT_TOWER or t_type == UnitType.LEVEL_THREE_PAINT_TOWER):
    #     if can_build_robot( )

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
    if not can_mark_resource_pattern(get_location()) or get_paint() <= 150 or get_num_towers() < 4 or get_round_num() <= 75:
        return False
    min_dist = 9999
    for tower_loc in known_money_towers:
        dist = get_location().distance_squared_to(tower_loc)
        if dist < min_dist:
            min_dist = dist
    if min_dist < 32:
        return False
    for tile in sense_nearby_map_infos(get_location(), 8):
        tile_robot = sense_robot_at_location(tile.get_map_location())
        if tile.get_paint().is_enemy() or tile.get_mark() != PaintType.EMPTY:
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
        has_marked_SRP = False

def isWithinPattern(cur_loc, ruin_loc):
    return abs(cur_loc.x - ruin_loc.x) <= 2 and abs(cur_loc.y - ruin_loc.y) <= 2 and ruin_loc != cur_loc

def get_is_secondary(ruin_loc, paint_loc, tower_type):
    global defense_tower_pattern
    global money_tower_pattern
    global paint_tower_pattern  
    if isWithinPattern(paint_loc, ruin_loc) == False:
        return False
    col = paint_loc.x - ruin_loc.x + 2
    row = paint_loc.y - ruin_loc.y + 2
    if tower_type == UnitType.LEVEL_ONE_DEFENSE_TOWER:
        return defense_tower_pattern[col][row]
    elif tower_type == UnitType.LEVEL_ONE_MONEY_TOWER:
        return money_tower_pattern[col][row]
    else:
        return paint_tower_pattern[col][row]

def run_paint_pattern():
    global turns_without_attack
    global painting_turns
    global painting_ruin_loc
    global tower_type
    global is_painting_pattern
    global has_marked_tower
    if has_marked_tower == False and can_mark_tower_pattern(tower_type, painting_ruin_loc):
        mark_tower_pattern(tower_type, painting_ruin_loc)
        has_marked_tower = True
    if painting_turns % 2 == 0:
        to_ruin = get_location().direction_to(painting_ruin_loc)
        tangent = to_ruin.rotate_right().rotate_right()
        dist = get_location().distance_squared_to(painting_ruin_loc)
        
        if dist > 4:
            tangent = tangent.rotate_left()
        if can_move(tangent):
            move(tangent)
    if is_action_ready():
        infos = sense_nearby_map_infos(radius_squared=3)
        attacked = False
        for info in infos:
            info_paint = info.get_paint()
            loc = info.get_map_location()
            isSecondary = get_is_secondary(painting_ruin_loc, loc, tower_type)
            if can_attack(loc) and (info_paint == PaintType.EMPTY or info_paint.is_secondary() != isSecondary) and isWithinPattern(loc, painting_ruin_loc):
                attack(loc, isSecondary)
                attacked = True
                turns_without_attack = 0
                break
        if attacked == False:
            turns_without_attack += 1
    
    if (can_complete_tower_pattern(tower_type, painting_ruin_loc)):
        complete_tower_pattern(tower_type, painting_ruin_loc)
        is_painting_pattern = False
        has_marked_tower = False

    if turns_without_attack > 3:
        is_painting_pattern = False

def taint():
    if is_action_ready() == False:
        return
    global tainted_ruins
    nearby_ruins = sense_nearby_ruins()
    for ruin in nearby_ruins:
        if ruin in tainted_ruins:
            return
        robot = sense_robot_at_location(ruin)
        if robot is None:
            ruin_tiles = sense_nearby_map_infos(ruin, 8)
            tainted = False
            min_dist = 9999
            attack_loc = None
            for tile in ruin_tiles:
                if tile.get_paint().is_ally():
                    tainted = True
                    break
                if tile.get_paint() == PaintType.EMPTY:
                    if get_location().distance_squared_to(tile.get_map_location()) <= min_dist:
                        min_dist = get_location().distance_squared_to(tile.get_map_location())
                        attack_loc = tile.get_map_location()
            if tainted:
                tainted_ruins.append(ruin)
            if tainted == False and attack_loc is not None:
                if can_attack(attack_loc):
                    attack(attack_loc)
                    tainted_ruins.append(ruin)

# def input_messages():
#     global flicker_tower_loc
#     global is_flickering_tower
#     messages_1 = read_messages(get_round_num() - 1)
#     messages_2 = read_messages(get_round_num())
#     messages = messages_1 + messages_2
#     for message in messages:
#         msg_bytes = message.get_bytes()
#         if msg_bytes < 1:
#             continue
#         adjusted = msg_bytes - 1  # Subtract the +1 added during encoding
#         x = adjusted // 64
#         y = adjusted % 64
#         tower_loc = MapLocation(x, y)
#         flicker_tower_loc = tower_loc
#         is_flickering_tower = True

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
    global is_painting_pattern
    global painting_turns
    global turns_without_attack
    global painting_ruin_loc
    global tower_type
    global SRP_positions
    global is_SRP_builder

    cur_loc = get_location()

    if is_SRP_builder:
        if is_marking_SRP:
            SRP_mark()
            return
        else:
            if can_SRP():
                is_marking_SRP = True
                return

    if turn_count == 1:
        move_count = 0

    upgrade_nearby_paint_towers()

    # input_messages()

    # if is_flickering_tower:
    #     if flicker_tower_loc is None:
    #         is_flickering_tower = False
    #     tower_dist = get_location().distance_squared_to(flicker_tower_loc)
    #     dir = bug2(flicker_tower_loc)
    #     if dir is not None:
    #         move(dir)
    #     for pattern_tile in sense_nearby_map_infos(flicker_tower_loc, 8):
    #         if pattern_tile.get_mark() != pattern_tile.get_paint() and pattern_tile.get_mark() != PaintType.EMPTY:
    #             use_secondary = pattern_tile.get_mark() == PaintType.ALLY_SECONDARY
    #             if can_attack(pattern_tile.get_map_location()):
    #                 attack(pattern_tile.get_map_location(), use_secondary)
    #     if can_complete_tower_pattern(UnitType.LEVEL_ONE_MONEY_TOWER, flicker_tower_loc):
    #         complete_tower_pattern(UnitType.LEVEL_ONE_MONEY_TOWER, flicker_tower_loc)
    #         set_timeline_marker("Tower built", 0, 255, 0)
    #         log("Built a tower at " + str(flicker_tower_loc) + "!")
    #         is_flickering_tower = False
    #         flicker_tower_loc = None
    #     return

    #Checks if refilling is needed
    if get_paint() <= 20:
        is_refilling = True
    if is_refilling == True: 
        refill_paint()
        return
    
    taint()

    if is_painting_pattern:
        run_paint_pattern()
        painting_turns += 1
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

    if cur_ruin is not None:
        if cur_dist > 1: 
            set_indicator_dot(get_location(), 0,0,255)
            move_dir = bug2(cur_ruin.get_map_location())
            if move_dir is not None:
                move(move_dir)
            return
        else:
            # is_painting_pattern = True
            # turns_without_attack = 0
            # painting_turns = 0
            # painting_ruin_loc = cur_ruin.get_map_location()
            # tower_type = build_tower_type(painting_ruin_loc)
            # return
            target_loc = cur_ruin.get_map_location()
            if tower_type == None:
                tower_type = build_tower_type(target_loc)
            dir = get_location().direction_to(target_loc)
            if can_move(dir):
                move(dir)

            # Mark the pattern we need to draw to build a tower here if we haven't already.
            should_mark = cur_ruin.get_map_location().subtract(dir)
            if sense_map_info(should_mark).get_mark() == PaintType.EMPTY and can_mark_tower_pattern(UnitType.LEVEL_ONE_MONEY_TOWER, target_loc):
                mark_tower_pattern(UnitType.LEVEL_ONE_MONEY_TOWER, target_loc)
                log("Trying to build a tower at " + str(target_loc))
            
            # Fill in any spots in the pattern with the appropriate paint.
            for pattern_tile in sense_nearby_map_infos(target_loc, 8):
                if pattern_tile.get_mark() != pattern_tile.get_paint() and pattern_tile.get_mark() != PaintType.EMPTY:
                    use_secondary = pattern_tile.get_mark() == PaintType.ALLY_SECONDARY
                    if can_attack(pattern_tile.get_map_location()):
                        attack(pattern_tile.get_map_location(), use_secondary)

            # Complete the ruin if we can.
            if can_complete_tower_pattern(UnitType.LEVEL_ONE_MONEY_TOWER, target_loc):
                complete_tower_pattern(UnitType.LEVEL_ONE_MONEY_TOWER, target_loc)
                set_timeline_marker("Tower built", 0, 255, 0)
                log("Built a tower at " + str(target_loc) + "!")

            if sense_robot_at_location(target_loc):
                tower_type = None
        
    if is_attackingsoldier and (turn_count == 1 or current_target is None):
        rand = random.randint(1,3)
        if rand == 1:
            current_target = MapLocation(cur_loc.x, height - cur_loc.y)
        elif rand == 2:
            current_target = MapLocation(width-cur_loc.x,height-cur_loc.y)
        else:
            current_target = MapLocation(width - cur_loc.x, cur_loc.y)
        move_count = 0

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
    if get_round_num() > 150:
        current_tile = sense_map_info(get_location())
        if not current_tile.get_paint().is_ally() and can_attack(get_location()):
            attack(get_location())
        else:
            for tile in sense_nearby_map_infos(get_location(), 3):
                if tile.get_paint() == PaintType.EMPTY and can_attack(tile.get_map_location()):
                    attack(tile.get_map_location())

def max(a, b):
    if a < b:
        return a
    return b

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

    cur_loc = get_location()
    enemy_robots= sense_nearby_robots(get_location(),5,team = get_team().opponent())

    count_west = 0
    count_north = 0
    count_east = 0
    count_south = 0

    for robot in enemy_robots:
        loc = robot.get_location()  # Ensure get_location() returns an object or tuple
        robot_x, robot_y = loc.x, loc.y
        if robot_x > cur_loc.x:
            count_east += 1
        if robot_x < cur_loc.x:
            count_west += 1
        if robot_y > cur_loc.y:
            count_north += 1
        if robot_y < cur_loc.y:
            count_south += 1


    ma_count = max(count_east, max(count_north, max(count_south, count_west)))

    if count_west == ma_count:
        if can_mop_swing(directions.WEST):
            mop_swing(directions.WEST)
    elif count_north == ma_count:
        if can_mop_swing(directions.NORTH):
            mop_swing(directions.NORTH)
    elif count_south == ma_count:
        if can_mop_swing(directions.SOUTH):
            mop_swing(directions.SOUTH)
    elif count_east == ma_count:
        if can_mop_swing(directions.EAST):
            mop_swing(directions.EAST)

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

    if is_messenger:
        # Set a useful indicator at this mopper's location so we can see who is a messenger
        set_indicator_dot(get_location(), 255, 0, 0)

        update_friendly_towers()
        check_nearby_ruins()

def splasher_profit(cur_loc):
    team_paint = 0
    opponent_paint = 0
    opponent_paint_near_ruin = 0
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
            if paint.is_ally() or tile.is_wall():
                team_paint += 1
            elif paint.is_enemy():
                ntiles = sense_nearby_map_infos(cur_loc, 8)
                for t in ntiles:
                    if t.has_ruin():
                        robot = sense_robot_at_location(t.get_map_location())
                        if robot is None or robot.get_team() == get_team():
                            opponent_paint_near_ruin += 1
                opponent_paint += 1
        else:
            not_painted += 1
    return enemy_tower * 4 + opponent_paint * 2 + not_painted - team_paint + opponent_paint * 3

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
        if ally.get_type() == UnitType.LEVEL_ONE_MONEY_TOWER:
            known_money_towers.append(ally_loc)
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