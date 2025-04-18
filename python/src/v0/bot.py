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

height = get_map_height()
width = get_map_width()

# Bunny Variables
is_refilling = False
paint_capacity = 0

# Soldier Variables
is_searchsoldier = True
searchsoldier_type = [False] * 8
target_of_soldier = MapLocation(100000, 100000)
targets = [MapLocation(height-1,0), MapLocation(0,0), MapLocation(0, width-1), MapLocation(height-1, width-1)]

# Mopper Variables
is_searchmopper = True
target_of_mopper = MapLocation(100000, 100000)

# Splasher Variables
is_searchsplasher= True
target_of_splasher = MapLocation(100000, 100000)

def turn():
    """
    MUST be defined for robot to run
    This function will be called at the beginning of every turn and should contain the bulk of your robot commands
    """
    global turn_count
    global is_messenger
    global target_of_soldier
    global target_of_mopper
    global targets
    global is_refilling
    global paint_capacity
    turn_count += 1

    block_width = math.sqrt(width)
    block_height = math.sqrt(height)
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
    # Assign messenger to about half of our moppers
    # if get_type() == UnitType.MOPPER and get_id() % 3 == 0:
    #     is_messenger = True
    if get_type() == UnitType.SOLDIER:
        paint_capacity = 200
        if target_of_soldier == MapLocation(100000, 100000):
            target_of_soldier = targets[random.randint(0, len(targets)-1)]
        run_soldier()
    elif get_type() == UnitType.MOPPER:
        if target_of_mopper == MapLocation(100000, 100000):
            target_of_mopper = targets[random.randint(0, len(targets)-1)]
        paint_capacity = 100
        run_mopper()
    elif get_type() == UnitType.SPLASHER:
        paint_capacity = 300
        run_splasher()
    elif get_type().is_tower_type():
        run_tower()
    else:
        pass  # Other robot types?


def run_tower():
    global save_turns
    global should_save

    if save_turns == 0:
        # If we have no save turns remaining, start building robots
        should_save = False

        # Pick a direction to build in.
        dir = directions[random.randint(0, len(directions) - 1)]
        next_loc = get_location().add(dir)

        # Pick a random robot type to build.
        robot_type = random.randint(1, 100)
        if robot_type <= 50 and can_build_robot(UnitType.SOLDIER, next_loc):
            build_robot(UnitType.SOLDIER, next_loc)
            log("BUILT A SOLDIER")
        if robot_type > 50 and robot_type <= 55 and can_build_robot(UnitType.MOPPER, next_loc):
            build_robot(UnitType.MOPPER, next_loc)
            log("BUILT A MOPPER")
        if robot_type <= 100 and robot_type > 55 and can_build_robot(UnitType.SPLASHER, next_loc):
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

    nearbyRobots = sense_nearby_robots()
    for robot in nearbyRobots:
        if (can_attack(robot.get_location())):
            attack(robot.get_location())

def refill_paint():
    global is_refilling
    global paint_capacity
    if not len(known_towers) > 0:
        is_refilling = False
        return
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
        amount_needed = paint_capacity - get_paint()
        if can_transfer_paint(cur_tower, -amount_needed):
            log("Refilled Paint for Robot")
            transfer_paint(cur_tower, -amount_needed)
            is_refilling = False
    else:
        is_refilling = False
        

def run_soldier():
    global is_refilling
    update_friendly_towers()
    if get_paint() <= 20:
        is_refilling = True
    if is_refilling == True: 
        refill_paint()
        return
    global target_of_soldier
    global targets
    # Sense information about all visible nearby tiles.
    nearby_tiles = sense_nearby_map_infos()

    # Search for the closest nearby ruin to complete.
    cur_ruin = None
    cur_dist = 9999999
    for tile in nearby_tiles:
        if tile.has_ruin() and sense_robot_at_location(tile.get_map_location()) == None:
            check_dist = tile.get_map_location().distance_squared_to(get_location())
            if check_dist < cur_dist:
                cur_dist = check_dist
                cur_ruin = tile

    if cur_ruin is not None:
        target_loc = cur_ruin.get_map_location()
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
    update_friendly_towers()
    # Move and attack randomly if no objective.
    if is_searchsoldier == False:
        dir = directions[random.randint(0, len(directions) - 1)]
        next_loc = get_location().add(dir)
        if can_move(dir):
            move(dir)
    elif target_of_soldier is not None:
        if get_location() == target_of_soldier:
            log("Reached target, now changing to new target")
            target_of_soldier = targets[random.randint(0, len(targets)-1)]
        search_dir = bug2(target_of_soldier)
        if search_dir is not None:
            move(search_dir)
 
    # Try to paint beneath us as we walk to avoid paint penalties.
    # Avoiding wasting paint by re-painting our own tiles.
    current_tile = sense_map_info(get_location())
    if not current_tile.get_paint().is_ally() and can_attack(get_location()):
        attack(get_location())


def run_mopper():
    update_friendly_towers()
    global target_of_mopper
    global targets
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

    nearby_tiles = sense_nearby_map_infos()
    cur_ruin = None
    cur_dist = 9999999
    for tile in nearby_tiles:
        if tile.has_ruin() and sense_robot_at_location(tile.get_map_location()) == None:
            check_dist = tile.get_map_location().distance_squared_to(get_location())
            if check_dist < cur_dist:
                cur_dist = check_dist
                cur_ruin = tile
    if cur_ruin != None:
        target_loc = cur_ruin.get_map_location()
        for tile in sense_nearby_map_infos(target_loc, 8):
            if tile.get_paint().is_enemy():
                if can_attack(tile.get_map_location()):
                    attack(tile.get_map_location())
        if can_complete_tower_pattern(UnitType.LEVEL_ONE_MONEY_TOWER, target_loc):
                complete_tower_pattern(UnitType.LEVEL_ONE_MONEY_TOWER, target_loc)
                set_timeline_marker("Tower built", 0, 255, 0)
                log("Built a tower at " + str(target_loc) + "!")
    update_friendly_towers()
    # Move and attack randomly.
    if is_searchmopper == False:
        dir = directions[random.randint(0, len(directions) - 1)]
        next_loc = get_location().add(dir)
        if can_move(dir):
            move(dir)
        if can_mop_swing(dir):
            mop_swing(dir)
            log("Mop Swing! Booyah!")
        elif can_attack(next_loc):
            attack(next_loc)
    elif target_of_mopper is not None:
        if get_location() == target_of_mopper:
            log("Reached target, now changing to new target")
            target_of_mopper = targets[random.randint(0, len(targets)-1)]
        search_dir = bug2(target_of_mopper)
        if search_dir is not None:
            next_loc = get_location().add(search_dir)
            if can_mop_swing(search_dir):
                mop_swing(search_dir)
                log("Mop Swing! Booyah!")
            elif can_attack(next_loc):
                attack(next_loc)
            move(search_dir)

    # We can also move our code into different methods or classes to better organize it!
    update_enemy_robots()

    if is_messenger:
        # Set a useful indicator at this mopper's location so we can see who is a messenger
        set_indicator_dot(get_location(), 255, 0, 0)

        update_friendly_towers()
        check_nearby_ruins()

def run_splasher():
    global is_refilling
    update_friendly_towers()
    if get_paint() <= 20:
        is_refilling = True
    if is_refilling == True: 
        refill_paint()
        return
    nearby_tiles = sense_nearby_map_infos()
    cur_ruin = None
    cur_dist = 9999999
    for tile in nearby_tiles:
        if tile.has_ruin() and sense_robot_at_location(tile.get_map_location()) == None:
            check_dist = tile.get_map_location().distance_squared_to(get_location())
            if check_dist < cur_dist:
                cur_dist = check_dist
                cur_ruin = tile
    if cur_ruin != None:
        target_loc = cur_ruin.get_map_location()
        if can_complete_tower_pattern(UnitType.LEVEL_ONE_MONEY_TOWER, target_loc):
                complete_tower_pattern(UnitType.LEVEL_ONE_MONEY_TOWER, target_loc)
                set_timeline_marker("Tower built", 0, 255, 0)
                log("Built a tower at " + str(target_loc) + "!")
    update_friendly_towers()
    dir = directions[random.randint(0, len(directions) - 1)]
    next_loc = get_location().add(dir)
    if can_move(dir):
        move(dir)
    if can_attack(next_loc):
        attack(next_loc)

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
    global prev_dest, line, is_tracing, obstacle_start_dist, tracing_dir

    if target.compare_to(prev_dest) != 0:
        prev_dest = target
        line = create_line(get_location(), target)

    if not is_tracing:
        delta = get_direction_to(get_location(), target)
        dir_to_target = None
        for d in directions:
            if d.value == delta:
                dir_to_target = d
                break
        if dir_to_target is None:
            dir_to_target = Direction.CENTER  # Fallback, though unlikely

        if can_move(dir_to_target):
            return dir_to_target
        else:
            is_tracing = True
            obstacle_start_dist = get_location().distance_squared_to(target)
            tracing_dir = dir_to_target
    else:
        if (get_location() in line 
                and get_location().distance_squared_to(target) < obstacle_start_dist):
            is_tracing = False
            return tracing_dir

        for _ in range(9):
            if can_move(tracing_dir):
                old_tracing_dir = tracing_dir
                tracing_dir = tracing_dir.rotate_right().rotate_right()
                return old_tracing_dir
            else:
                tracing_dir = tracing_dir.rotate_left()
        return None  # Explicit, though should be handled by loop


def create_line(a, b):
    locs = set()

    x, y = a.x, a.y
    dx = b.x - a.x
    dy = b.y - a.y
    sx = int(sign(dx))
    sy = int(sign(dy))
    dx = abs(dx)
    dy = abs(dy)

    d = d = dx if dx > dy else dy
    r = d // 2

    if dx > dy:
        for _ in range(d):
            locs.add(MapLocation(x, y))
            x += sx
            r += dy
            if r >= dx:
                locs.add(MapLocation(x, y))
                y += sy
                r -= dx
    else:
        for _ in range(d):
            locs.add(MapLocation(x, y))
            y += sy
            r += dx
            if r >= dy:
                locs.add(MapLocation(x, y))
                x += sx
                r -= dy

    locs.add(MapLocation(x, y))
    return locs

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