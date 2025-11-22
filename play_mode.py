import time
from pico2d import *

import character
import game_world
from Knight import *
from Tile import Tile
import game_framework
from character import Character
from monster import Monster

character = None

start_party = None

stage_temp = [2, 2, 2, 2, 2, 2, 2, 2,2,2
             ,2, 2, 2, 2, 2, 2, 2, 2,2,2
             ,2, 2, 2, 1, 2, 2, 2, 2,2,2
             ,3, 1, 1, 1, 1, 1, 1, 1,1,4
             ,2, 2, 2, 1, 2, 2, 2, 2,2,2
             ,2, 2, 2, 2, 2, 2, 2, 2,2,2
             ,2, 2, 2, 2, 2, 2, 2, 2,2,2
             ,2, 2, 2, 2, 2, 2, 2, 2,2,2]

_spawn_positions = []
_spawn_index = 0
_last_spawn_time = 0.0
_spawn_interval = 4.0  # 초

def handle_events():
    global running

    event_list = get_events()
    for event in event_list:
        if event.type == SDL_QUIT:
            running = False
        elif event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            running = False
        else:
            character.handle_event(event)


def init():
    global _spawn_positions, _spawn_index, _last_spawn_time, character, start_party
    tile = []

    for i in range(len(stage_temp)):
        if stage_temp[i] == 3:
            tile.append(Tile(i, 2))
            game_world.add_object(tile[i],  i//10)
        elif stage_temp[i] == 4:
            tile.append(Tile(i, 3))
            game_world.add_object(tile[i], i//10)
        else:
            tile.append(Tile(i, stage_temp[i]-1))
            game_world.add_object(tile[i], i//10)

    # start_party를 Character에 전달하여 사용할 유닛을 제한
    character = Character(start_party)
    # 초기화 후 소비(다음 전환에 영향 주지 않도록)
    start_party = None
    game_world.add_object(character, 7)

    _spawn_positions = [i for i, v in enumerate(stage_temp) if v == 3]
    _spawn_index = 0
    _last_spawn_time = time.time()

def spwan_monster():
    global _last_spawn_time, _spawn_index
    now = time.time()
    if _spawn_positions:
        if now - _last_spawn_time >= _spawn_interval:
            pos_index = _spawn_positions[_spawn_index]
            monster = Monster(pos_index)
            game_world.add_object(monster, (get_canvas_height() - monster.y) // 100)

            if character is not None and hasattr(character, 'unit_map'):
                for key in character.unit_map.keys():
                    group = f'{key.upper()}:MONSTER'
                    game_world.add_collision_pair(group, None, monster)

            try:
                for group, pairs in game_world.collision_pairs.items():
                    left, right = (group.split(':') + ['', ''])[:2]
                    if right.strip().upper() == 'MONSTER':
                        if monster not in pairs[1]:
                            pairs[1].append(monster)
            except Exception:
                pass

            _spawn_index = (_spawn_index + 1) % len(_spawn_positions)
            _last_spawn_time = now

def update():
    global _last_spawn_time, _spawn_index
    now = time.time()
    spwan_monster()
    game_world.update()



def draw():
    clear_canvas()
    game_world.render()
    update_canvas()


