import random

from battlecode25.stubs import *

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


#paint capacities:
#mogger: 100
#splasher: 300
#soldier: 200

#    N
#    |
# W --- E
#    |
#    S

def getDir(x, y, newx, newy):
    if newx == x+1:
        if newy == y+1:
            return directions[1];
        elif newy == y-1:
            return directions[3];
        else:
            return directions[2];
    elif newx == x:
        if newy == y+1:
            return directions[0];
        else:
            return directions[4];
    elif newx == x-1:
        if newy == y+1:
            return directions[7];
        elif newy == y:
            return directions[6];
        else:
            return directions[5];


class troop:
    def __init__(self) -> None:
        self.defPath = 1;

def checkEvery():
    allRound = sense_nearby_map_infos(get_location());
    tot = len(allRound); cnt = 0;
    for current_tile in allRound:
        if not current_tile.get_paint().is_ally():
            cnt += 1;
    if cnt/tot <= 4/5:
        return False;
    return True;

storeID = {};
hasHealed = {};

def path1(x, y, ide):
    #this path exhaustively searches through every rows.
    if ide not in storeID:
        storeID[ide] = troop();
    if storeID[ide].defPath == 1:
        newx, newy = x, y;
        if y%2 == 1:
            if x == 0:
                newy += 1;
            else:
                newx -= 1;
        else:
            if not checkEvery():
                storeID[ide].defPath = storeID[ide].defPath+1;
            elif can_move(getDir(x, y, x+1, y)):
                newx += 1;
            elif can_move(getDir(x, y, x, y+1)):
                newy += 1;
            else:
                storeID[ide].defPath = storeID[ide].defPath+1;
        log(x, y, newx, newy);
        if can_move(getDir(x, y, newx, newy)):
            return getDir(x, y, newx, newy);
        else:
            return directions[random.randint(0, len(directions) - 1)];
    else:
        return directions[random.randint(0, len(directions) - 1)];


# Globals
turn_count = 0
tSo, tM, tSl = 0, 0, 0;
ratioes = [2, 1, 1];
def returnNeeded():
    global tSo, tM, tSl;
    aSo, aM, aSl = tSo/ratioes[0], tM/ratioes[1], tSl/ratioes[2];
    arr = [[aSo, 1], [aM, 2], [aSl, 3]];
    arr = sorted(arr); least = arr[0];
    # log(least[1], least);
    return least[1];

def turn():
    global tM, tSl, tSo;
    # global turn_count
    # turn_count += 1
    if get_type() == UnitType.SOLDIER:
        run_soldier();
    elif get_type() == UnitType.MOPPER:
        run_mopper();
    elif get_type() == UnitType.SPLASHER:
        run_splasher();
    elif get_type().is_tower_type():
        run_tower();
    else:
        pass  # Other robot types?

#current ratio:
#soldier = 2, mopper = 1, splaser = 1.

def run_tower():
    global tM, tSl, tSo;
    dir = directions[random.randint(0, len(directions) - 1)];
    next_loc = get_location().add(dir);
    robot_type = returnNeeded();
    if robot_type == 1 and can_build_robot(UnitType.SOLDIER, next_loc):
        build_robot(UnitType.SOLDIER, next_loc); tSo += 1;
    elif robot_type == 2 and can_build_robot(UnitType.MOPPER, next_loc):
        build_robot(UnitType.MOPPER, next_loc); tM += 1;
    elif robot_type == 3 and can_build_robot(UnitType.SPLASHER, next_loc):
        build_robot(UnitType.SPLASHER, next_loc); tSl += 1;


def run_soldier():
    cur = get_id();
    if cur not in hasHealed:
        hasHealed[cur] = True;
    if cur not in storeID:
        storeID[cur] = troop();
    if hasHealed[cur]:
        nearby_tiles = sense_nearby_map_infos();
        cur_ruin = None;
        for tile in nearby_tiles:
            if tile.has_ruin():
                cur_ruin = tile;
        # near = sense_nearby_ruins(team=get_team());
        # if len(near) > 0:
        #     # cur_ruin = nearby_tiles[0]; 
        #     log(near[0].x, near[0].y);

        
        #complete a ruin.
        if cur_ruin is not None and can_complete_tower_pattern(UnitType.LEVEL_ONE_PAINT_TOWER, cur_ruin.get_map_location()):
            target_loc = cur_ruin.get_map_location()
            dir = get_location().direction_to(target_loc)
            if can_move(dir):
                move(dir); log('uwu');
            should_mark = cur_ruin.get_map_location().subtract(dir)
            if sense_map_info(should_mark).get_mark() == PaintType.EMPTY and can_mark_tower_pattern(UnitType.LEVEL_ONE_PAINT_TOWER, target_loc):
                mark_tower_pattern(UnitType.LEVEL_ONE_PAINT_TOWER, target_loc)
            # Fill in any spots in the pattern with the appropriate paint.
            for pattern_tile in sense_nearby_map_infos(target_loc, 8):
                if pattern_tile.get_mark() != pattern_tile.get_paint() and pattern_tile.get_mark() != PaintType.EMPTY:
                    use_secondary = pattern_tile.get_mark() == PaintType.ALLY_SECONDARY
                    if can_attack(pattern_tile.get_map_location()):
                        attack(pattern_tile.get_map_location(), use_secondary)
            # Complete the ruin if we can.
            if can_complete_tower_pattern(UnitType.LEVEL_ONE_PAINT_TOWER, target_loc):
                complete_tower_pattern(UnitType.LEVEL_ONE_PAINT_TOWER, target_loc);
                set_timeline_marker("Tower built", 0, 255, 0);
                cur_ruin = None;
        #moving.
        curLoc = get_location();
        x, y = curLoc.x, curLoc.y;
        dir = path1(x, y, cur);
        if can_move(dir):
            move(dir)

        # Try to paint beneath us as we walk to avoid paint penalties.
        # Avoiding wasting paint by re-painting our own tiles.
        current_tile = sense_map_info(get_location())
        if not current_tile.get_paint().is_ally() and can_attack(get_location()):
            attack(get_location())


def run_mopper():
    cur = get_id();
    if cur not in storeID:
        storeID[cur] = troop();
    coord = get_location();
    x, y = coord.x, coord.y;
    dir = path1(x, y, cur);
    allRound = sense_nearby_map_infos(get_location());
    for current_tile in allRound:
        if not current_tile.get_paint().is_ally() and can_attack(get_location()):
            attack(get_location())
    if can_move(dir):
        move(dir);
    if can_mop_swing(dir):
        mop_swing(dir);
    update_enemy_robots();


def run_splasher():
    cur = get_id();
    if cur not in storeID:
        storeID[cur] = troop();
    if get_paint() >= 250:
        hasHealed[cur] = True;
    if get_paint() <= 100:
        hasHealed[cur] = False;
    if hasHealed[cur]:
        coord = get_location();
        x, y = coord.x, coord.y;
        dir = path1(x, y, cur);
        next_loc = get_location().add(dir);
        if can_move(dir):
            move(dir);
        if can_mop_swing(dir):
            mop_swing(dir);
        elif can_attack(next_loc):
            attack(next_loc);
        update_enemy_robots();
    else:
        if can_attack(get_location()):
            attack(get_location());



def update_enemy_robots():
    # Sensing methods can be passed in a radius of -1 to automatically 
    # use the largest possible value.
    enemy_robots = sense_nearby_robots(team=get_team().opponent())
    if len(enemy_robots) == 0:
        return

    set_indicator_string("There are nearby enemy robots! Scary!");

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