import time
from pico2d import *

import character
import game_world
from Knight import *
from Tile import Tile
import game_framework
from character import Character
from monster import Monster
import main_mode

character = None

start_party = None

monster_num = 0
killed_monster = 0

# 결과(승/패) 관련 상태
_result_shown = False
_result_start_time = 0.0
_result_type = None  # 'v' 또는 'd'
RESULT_DURATION = 3.0

# spawn 관리용 로컬 리스트 (화면의 몬스터 위치 검사용)
_monsters_list = []

stage_temp = [2, 2, 2, 2, 1, 2, 2, 2,2,2
             ,2, 2, 2, 2, 1, 2, 2, 2,2,2
             ,2, 2, 2, 1, 1, 2, 2, 2,2,2
             ,3, 1, 1, 1, 1, 1, 1, 1,1,4
             ,2, 2, 2, 1, 2, 2, 2, 2,2,2
             ,2, 2, 2, 2, 2, 2, 2, 2,2,2
             ,2, 2, 2, 2, 2, 2, 2, 2,2,2
             ,2, 2, 2, 2, 2, 2, 2, 2,2,2]

_spawn_positions = []
_spawn_index = 0
_last_spawn_time = 0.0
_spawn_interval = 4.0  # 초

# 이미지/폰트는 캔버스가 준비된 시점에 로드해야 함 -> init()에서 로드
v_image = None
d_image = None
font = None

def handle_events():
    global running

    event_list = get_events()
    for event in event_list:
        if event.type == SDL_QUIT:
            running = False
        elif event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            running = False
        else:
            if character:
                character.handle_event(event)


def init():
    global _spawn_positions, _spawn_index, _last_spawn_time, character, start_party
    global _result_shown, _result_start_time, _result_type, _monsters_list
    global v_image, d_image, font
    tile = []
    monster_killed = 0
    # 이미지/폰트는 여기서 로드 (캔버스 준비 후 안전)
    if v_image is None:
        v_image = load_image('victory.png')
    if d_image is None:
        d_image = load_image('defeat.png')
    if font is None:
        font = load_font('ENCR10B.TTF', 20)

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

    # 결과 상태 초기화
    _result_shown = False
    _result_start_time = 0.0
    _result_type = None
    _monsters_list = []


def spwan_monster():
    global _last_spawn_time, _spawn_index, monster_num
    if _result_shown:
        return
    now = time.time()
    # 디버그 출력
    print(f"[SPAWN_CHECK] monster_num={monster_num}, len(_spawn_positions)={len(_spawn_positions)}, elapsed={now - _last_spawn_time:.2f}s")
    if not _spawn_positions:
        print("[SPAWN_CHECK] no spawn positions")
        return
    if now - _last_spawn_time >= _spawn_interval and monster_num < 10:
        pos_index = _spawn_positions[_spawn_index]
        try:
            monster = Monster(pos_index)
        except Exception as e:
            print(f"[SPAWN_ERROR] Monster ctor failed: {e}")
            # 실패 시 마지막 시간 갱신하지 않아 즉시 재시도 가능하게 할 수도 있음
            _last_spawn_time = now
            return

        try:
            game_world.add_object(monster, (get_canvas_height() - monster.y) // 100)
        except Exception as e:
            print(f"[SPAWN_ERROR] add_object failed: {e}")
            return

        # 로컬 리스트에 보관 (위치 검사용)
        try:
            _monsters_list.append(monster)
        except Exception as e:
            print(f"[SPAWN_WARN] append to _monsters_list failed: {e}")

        # 충돌쌍 등록 시도 (안전하게)
        try:
            if character is not None and hasattr(character, 'unit_map'):
                for key in character.unit_map.keys():
                    group = f'{key.upper()}:MONSTER'
                    game_world.add_collision_pair(group, None, monster)

            for group, pairs in game_world.collision_pairs.items():
                left, right = (group.split(':') + ['', ''])[:2]
                if right.strip().upper() == 'MONSTER':
                    if monster not in pairs[1]:
                        pairs[1].append(monster)
        except Exception as e:
            print(f"[SPAWN_WARN] collision pair registration issue: {e}")

        _spawn_index = (_spawn_index + 1) % len(_spawn_positions)
        _last_spawn_time = now

        # 몬스터 카운트는 등록이 성공한 뒤에 증가
        monster_num += 1
        print(f"[SPAWN_OK] spawned at pos {pos_index}, new monster_num={monster_num}")


def _check_defeat_by_monster_enter_goal():
    global _result_shown, _result_start_time, _result_type
    if _result_shown:
        return
    TILE_W = 100
    TILE_H = 100
    COLS = 10
    try:
        for m in list(_monsters_list):
            # 유효한 몬스터인지 확인
            if not hasattr(m, 'x') or not hasattr(m, 'y'):
                continue
            # tile index 계산
            col = int(m.x // TILE_W)
            row = int((get_canvas_height() - m.y) // TILE_H)
            if col < 0 or row < 0:
                continue
            idx = row * COLS + col
            if 0 <= idx < len(stage_temp):
                if stage_temp[idx] == 4:
                    # 패배 트리거
                    _result_shown = True
                    _result_start_time = time.time()
                    _result_type = 'd'
                    return
    except Exception:
        pass


def update():
    global _last_spawn_time, _spawn_index
    global _result_shown, _result_start_time, _result_type, killed_monster
    now = time.time()

    # 결과 표시 중이면 스테이지 진행을 멈추고 시간만 체크
    if _result_shown:
        # 시작 시간이 미설정이면 지금으로 설정
        if _result_start_time == 0.0:
            _result_start_time = now
        # 지정 시간 경과 시 메인으로 전환 (스테이지는 멈춘 상태 유지)
        if now - _result_start_time >= RESULT_DURATION:
            # 결과 초기화 및 씬 전환
            _result_shown = False
            _result_start_time = 0.0
            _result_type = None
            game_framework.change_mode(main_mode)
        return

    spwan_monster()

    # 패배(몬스터가 타일 4에 들어감) 우선 검사
    _check_defeat_by_monster_enter_goal()

    # 승리(처치 수) 검사
    if not _result_shown and killed_monster >= 10:
        _result_shown = True
        _result_start_time = time.time()
        _result_type = 'v'

    game_world.update()

def draw():
    clear_canvas()

    game_world.render()

    # 결과 이미지 오버레이(중앙 표시), 크기 87x81
    if _result_shown and _result_type is not None:
        cx = get_canvas_width() // 2
        cy = get_canvas_height() // 2
        if _result_type == 'v' and v_image:
            v_image.clip_draw(0, 0, 87, 81, cx, cy, 400, 400)
        elif _result_type == 'd' and d_image:
            d_image.clip_draw(0, 0, 87, 81, cx, cy, 400, 400)

    update_canvas()

def finish():
    global character, v_image, d_image, font
    game_world.clear()
    character = None
    v_image = None
    d_image = None
    font = None