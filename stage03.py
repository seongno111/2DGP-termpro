import heapq
import time
from pico2d import *

import character
import game_world
from Knight import *
from Tile import Tile
import game_framework
from boss import Boss
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

stage_temp = [2, 2, 2, 2, 2, 2, 2, 4,2,2
             ,2, 2, 2, 2, 2, 2, 2, 1,2,2
             ,2, 2, 2, 2, 2, 2, 2, 1,2,2
             ,3, 1, 1, 1, 6, 1, 1, 1,2,2
             ,2, 1, 2, 2, 2, 2, 2, 1,2,2
             ,2, 1, 2, 2, 2, 2, 2, 1,2,2
             ,2, 1, 1, 1, 1, 1, 1, 1,2,2
             ,2, 2, 2, 2, 2, 2, 2, 2,2,2]

_spawn_positions = []
_spawn_index = 0
_last_spawn_time = 0.0
_spawn_interval = 4.0  # 초
_spawn_batch_count = 0  # 현재 스폰 포인트에서 몇 마리 스폰했는지
special_roc = 34

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

def _grid_neighbors(idx, cols, rows):
    col = idx % cols
    row = idx // cols
    for dc, dr in ((1,0),(-1,0),(0,1),(0,-1)):
        nc, nr = col+dc, row+dr
        if 0 <= nc < cols and 0 <= nr < rows:
            yield nr * cols + nc

def _build_walkable(stage_list):
    # walkable: 타일 값 1 또는 4(목표), spawn(3)도 통과시작 가능
    return {i for i, v in enumerate(stage_list) if v in (1,3,4,5,6)}

def _dijkstra(start_idx, goals, stage_list, cols=10):
    rows = len(stage_list) // cols
    walkable = _build_walkable(stage_list)
    INF = 10**9
    dist = {i: INF for i in walkable}
    prev = {}
    if start_idx not in walkable:
        return None  # 경로 없음
    dist[start_idx] = 0
    pq = [(0, start_idx)]
    while pq:
        d, u = heapq.heappop(pq)
        if d != dist.get(u, INF):
            continue
        if u in goals:
            # 도착한 목표 중 가장 빠른 것을 찾으면 경로 복원
            path = []
            cur = u
            while True:
                path.append(cur)
                if cur == start_idx:
                    break
                cur = prev.get(cur)
                if cur is None:
                    break
            path.reverse()
            return path
        for v in _grid_neighbors(u, cols, rows):
            if v not in walkable:
                continue
            nd = d + 1
            if nd < dist.get(v, INF):
                dist[v] = nd
                prev[v] = u
                heapq.heappush(pq, (nd, v))
    return None

def _tile_index_to_center(idx):
    cols = 10
    col = idx % cols
    row = idx // cols
    tw, th = Tile.TILE_W, Tile.TILE_H
    canvas_h = get_canvas_height()
    cx = col * tw + tw // 2
    cy = canvas_h - (row * th + th // 2)
    return cx, cy

def find_path_indices_from(start_idx, stage_list):
    # 목표 타일 인덱스들(값 4)
    goals = {i for i, v in enumerate(stage_list) if v == 4}
    if not goals:
        return None
    return _dijkstra(start_idx, goals, stage_list, cols=10)


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
        elif stage_temp[i] == 5:
            tile.append(Tile(i, 4))
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

def _build_one_loop_on_ones(start_idx, stage_list, cols, rows):
    # 단순 DFS 기반 루프 탐색
    stack = [(start_idx, [start_idx])]
    visited_global = set()

    def neighbors_ones(idx):
        col = idx % cols
        row = idx // cols
        for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nc = col + dc
            nr = row + dr
            if 0 <= nc < cols and 0 <= nr < rows:
                nidx = nr * cols + nc
                if stage_list[nidx] == 1:
                    yield nidx

    while stack:
        cur, path = stack.pop()
        if cur in visited_global:
            continue
        visited_global.add(cur)

        for n in neighbors_ones(cur):
            if n == start_idx and len(path) >= 4:
                # 시작점으로 되돌아오는 루프 완성
                return path + [start_idx]
            if n not in path:
                stack.append((n, path + [n]))

    # 루프를 못 찾았으면 None
    return None


def find_boss_path_indices_from(start_idx, stage_list):
    cols = 10
    rows = len(stage_list) // cols

    # 1) 우선 목표(값 4) 위치를 찾는다.
    goals = {i for i, v in enumerate(stage_list) if v == 4}
    if not goals:
        return []
    goal_idx = next(iter(goals))  # 이 맵에서는 4가 한 개라고 가정(인덱스 7)

    # 2) 이 맵 전용 도넛 루프 인덱스 직접 정의
    #    (현재 stage_temp 구조에 맞춰 수동 설계)
    #
    # 행/열(0-based)로 보면:
    #   3행: (1,3)~(7,3)
    #   4행: (1,4)       (7,4)
    #   5행: (1,5)       (7,5)
    #   6행: (1,6)~(7,6)
    #
    # 인덱스 = row * 10 + col
    donut_loop = [
        # 윗줄 (row 3, col 1~7)
        31, 32, 33, 34, 35, 36, 37,
        # 오른쪽 세로 (row 4~5, col 7)
        47, 57,
        # 아랫줄 (row 6, col 7~1)
        67, 66, 65, 64, 63, 62, 61,
        # 왼쪽 세로 (row 5~3, col 1)
        51, 41, 31
    ]

    boss_path = []

    # 3) 스폰 위치에서 도넛 시작점(31)까지 경로가 필요하면 붙인다.
    loop_start = donut_loop[0]
    if start_idx != loop_start:
        head_path = _dijkstra(start_idx, [loop_start], stage_list, cols)
        if head_path:
            boss_path.extend(head_path)

    # 4) 도넛 루프를 3바퀴 돈다.
    for _ in range(3):
        for i, idx in enumerate(donut_loop):
            # 바로 앞 인덱스와 중복 시작 방지
            if boss_path and i == 0 and boss_path[-1] == idx:
                continue
            boss_path.append(idx)

    # 5) 마지막 도넛 위치에서 목표(4)까지 최단 경로를 붙인다.
    cur_idx = boss_path[-1] if boss_path else start_idx
    tail_path = _dijkstra(cur_idx, [goal_idx], stage_list, cols)
    if tail_path:
        if boss_path and tail_path[0] == boss_path[-1]:
            tail_path = tail_path[1:]
        boss_path.extend(tail_path)

    return boss_path

def spwan_monster():
    global _last_spawn_time, _spawn_index, monster_num, _spawn_batch_count, _monsters_list
    if _result_shown:
        return

    now = time.time()
    if not _spawn_positions:
        return

    if monster_num >= whole_mon:
        return

    if now - _last_spawn_time < _spawn_interval:
        return

    pos_index = _spawn_positions[_spawn_index]
    is_boss = (monster_num + 1 == whole_mon)

    try:
        if is_boss:
            path_indices = find_boss_path_indices_from(pos_index, stage_temp)
        else:
            path_indices = find_path_indices_from(pos_index, stage_temp)
    except Exception as e:
        print(f"[STAGE03][PATH_WARN] path calc failed: {e}")
        path_indices = None

    path_coords = None
    if path_indices:
        path_coords = [_tile_index_to_center(i) for i in path_indices]

    try:
        if is_boss:
            monster = Boss(pos_index, path=path_coords)
        else:
            monster = Monster(pos_index, path=path_coords)
    except Exception as e:
        print(f"[STAGE03][SPAWN_ERROR] Monster/Boss ctor failed: {e}")
        _last_spawn_time = now
        return

    try:
        depth = (get_canvas_height() - monster.y) // 100
        game_world.add_object(monster, depth)
    except Exception as e:
        print(f"[STAGE03][SPAWN_ERROR] add_object failed: {e}")
        return

    # \_monsters_list에 일반 몬스터와 보스를 모두 넣어준다.
    try:
        if monster not in _monsters_list:
            _monsters_list.append(monster)
    except Exception:
        pass

    try:
        if character is not None and hasattr(character, 'unit_map'):
            for key in character.unit_map.keys():
                group = f"{key.upper()}:MONSTER"
                game_world.add_collision_pair(group, None, monster)

        for group, pairs in game_world.collision_pairs.items():
            left, right = (group.split(':') + ["", ""])[:2]
            if right.strip().upper() == "MONSTER":
                if monster not in pairs[1]:
                    pairs[1].append(monster)
    except Exception as e:
        print(f"[STAGE03][SPAWN_WARN] collision pair registration issue: {e}")

    monster_num += 1
    _last_spawn_time = now

    _spawn_batch_count += 1
    if _spawn_batch_count >= 3:
        _spawn_batch_count = 0
        _spawn_index = (_spawn_index + 1) % len(_spawn_positions)

    print(f"[STAGE03][SPAWN_OK] idx={pos_index} boss={is_boss} "
          f"path_len={(len(path_indices) if path_indices else 0)} monster_num={monster_num}")


def _check_defeat_by_monster_enter_goal():
    global _result_shown, _result_start_time, _result_type
    if _result_shown:
        return
    TILE_W = 100
    TILE_H = 100
    COLS = 10
    try:
        for m in list(_monsters_list):
            if not hasattr(m, 'x') or not hasattr(m, 'y'):
                continue

            col = int(m.x // TILE_W)
            row = int((get_canvas_height() - m.y) // TILE_H)
            if col < 0 or row < 0:
                continue

            idx = row * COLS + col
            if 0 <= idx < len(stage_temp) and stage_temp[idx] == 4:
                _result_shown = True
                _result_start_time = time.time()
                _result_type = 'd'
                return
    except Exception:
        pass

whole_mon = 1

def update():
    global _last_spawn_time, _spawn_index
    global _result_shown, _result_start_time, _result_type, killed_monster
    now = time.time()

    # 결과 표시 중이면 스테이지 진행을 멈추고 시간만 체크
    if _result_shown:
        if _result_start_time == 0.0:
            _result_start_time = now
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
    if not _result_shown and killed_monster >= whole_mon:
        _result_shown = True
        _result_start_time = time.time()
        _result_type = 'v'

    game_world.update()

    HEAL_PER_SEC = 20.0
    try:
        import game_framework as gf
        ft = getattr(gf, 'frame_time', 0.0)
    except Exception:
        ft = 0.0
    if ft > 0.0:
        try:
            # game_world.world는 레이어 리스트
            for layer in list(game_world.world):
                for obj in list(layer):
                    try:
                        if getattr(obj, '_placed_on_depth', None) == 4 and getattr(obj, 'Hp', None) is not None:
                            max_hp = getattr(obj, 'max_hp', None)
                            if max_hp is None:
                                # 일부 클래스는 max_hp 대신 max_hp (fallback handled)
                                max_hp = getattr(obj, 'max_hp', getattr(obj, 'MaxHp', None))
                            if max_hp is None:
                                continue
                            new_hp = getattr(obj, 'Hp', 0) + HEAL_PER_SEC * ft
                            # clamp to max_hp
                            obj.Hp = min(new_hp, max_hp)
                    except Exception:
                        pass
        except Exception:
            pass


def draw():
    clear_canvas()

    game_world.render()

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


