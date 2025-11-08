import time
from pico2d import *
import game_world
from Knight import *
from Tile import Tile
import game_framework
from character import Character
from monster import Monster

stage_temp = [2, 2, 2, 2, 2, 2, 2, 2,2,2
             ,2, 2, 2, 2, 2, 2, 2, 2,2,2
             ,2, 2, 2, 2, 2, 2, 2, 2,2,2
             ,3, 1, 1, 1, 1, 1, 1, 1,1,1
             ,2, 2, 2, 2, 2, 2, 2, 2,2,2
             ,2, 2, 2, 2, 2, 2, 2, 2,2,2
             ,2, 2, 2, 2, 2, 2, 2, 2,2,2
             ,2, 2, 2, 2, 2, 2, 2, 2,2,2]

_spawn_positions = []
_spawn_index = 0
_last_spawn_time = 0.0
_spawn_interval = 5.0  # 초

def handle_events():
    global running

    event_list = get_events()
    for event in event_list:
        if event.type == SDL_QUIT:
            running = False
        elif event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            running = False


def init():
    global _spawn_positions, _spawn_index, _last_spawn_time
    tile = []
    character = Character()
    game_world.add_object(character, 2)
    for i in range(len(stage_temp)):
        if stage_temp[i] == 3:
            tile.append(Tile(i, 2))
            game_world.add_object(tile[i], 1)
        else:
            tile.append(Tile(i, stage_temp[i]-1))
            game_world.add_object(tile[i], stage_temp[i]-1)
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
            # 몬스터는 캐릭터 레이어(예: 2)에 추가
            game_world.add_object(monster, 2)
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


