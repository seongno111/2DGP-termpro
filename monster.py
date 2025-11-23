from pico2d import load_image, get_canvas_height

import game_framework
import game_world
import stage01
from Tile import Tile
from state_machine import StateMachine

PIXEL_PER_METER = (10.0 / 0.3)  # 10 pixel 30 cm
RUN_SPEED_KMPH = 20.0  # Km / Hour
RUN_SPEED_MPM = (RUN_SPEED_KMPH * 1000.0 / 60.0)
RUN_SPEED_MPS = (RUN_SPEED_MPM / 60.0)
RUN_SPEED_PPS = (RUN_SPEED_MPS * PIXEL_PER_METER)

TIME_PER_ACTION = 0.8
ACTION_PER_TIME = 1.0 / TIME_PER_ACTION
FRAMES_PER_ACTION = 2
FRAMES_PER_ACTION_ac = 3

class Idle:
    def __init__(self, monster):
        self.monster = monster
    def enter(self, e):
        pass
    def exit(self, e):
        pass
    def do(self):
        self.monster.x += RUN_SPEED_PPS * game_framework.frame_time
        self.monster.frame = (self.monster.frame + FRAMES_PER_ACTION * ACTION_PER_TIME * game_framework.frame_time) % 2
        pass
    def draw(self):
        x = self.monster.x
        y = self.monster.y + 30
        face = getattr(self.monster, 'face_dir', 0)
        # face == 0: 오른쪽(정방향), 그 외: 좌우 반전
        if face == 0:
            self.monster.image[int(self.monster.frame)].clip_draw(0, 0, 100, 100, x, y, 150, 150)
        else:
            self.monster.image[int(self.monster.frame)].clip_composite_draw(0, 0, 100, 100, 0, 'h', x, y, 150, 150)

class Atack_state:
    def __init__(self, monster):
        self.monster = monster
    def enter(self, e):
        self.monster.frame = 0
        self.attack_timer = 0.0
        if isinstance(e, tuple) and len(e) >= 3:
            self.monster.target = e[2]
        else:
            self.monster.target = None
    def exit(self, e):
        self.monster.frame = 0
        self.attack_timer = 0.0
    def do(self):
        self.monster.frame = (self.monster.frame + FRAMES_PER_ACTION_ac * ACTION_PER_TIME * game_framework.frame_time) % 3
        target = getattr(self.monster, 'target', None)
        # 만약 대상이 없거나 충돌이 끊기면 SEPARATE 이벤트 발생
        if target is None or not game_world.collide(self.monster, target):
            self.monster.state_machine.handle_state_event(('SEPARATE', None))
            return
        # 공격 간격 (초)
        ATTACK_INTERVAL = 0.8
        self.attack_timer += game_framework.frame_time
        if self.attack_timer >= ATTACK_INTERVAL:
            self.attack_timer -= ATTACK_INTERVAL
            dmg = max(0, self.monster.Atk - getattr(target, 'Def', 0))
            # 체력 감소
            target.Hp -= dmg
            # 디버그 출력
            print(
                f'Monster({self.monster.num}) attacked {target.__class__.__name__} dmg={dmg} target_hp={getattr(target, "Hp", "?")}')
            # 대상이 죽으면 제거 및 충돌 리스트에서 제거, 상태복귀
            if getattr(target, 'Hp', 1) <= 0:
                print(f'{target.__class__.__name__} died.')
                # 오버레이가 있으면 먼저 제거
                try:
                    if hasattr(target, '_overlay'):
                        game_world.remove_object(target._overlay)
                except Exception:
                    pass

                # 유닛 객체 제거 및 충돌 정보 제거
                try:
                    game_world.remove_object(target)
                except Exception:
                    pass
                try:
                    game_world.remove_collision_object(target)
                except Exception:
                    pass

                # play_mode.character가 있으면 배치 상태와 occupied_tiles 갱신
                try:
                    import stage01
                    ch = getattr(stage01, 'character', None)
                    if ch is not None:
                        key = getattr(target, '_placed_key', None)
                        idx = getattr(target, '_placed_idx', None)
                        if key:
                            ch.unit_placed[key] = False
                        if idx is not None and idx in ch.occupied_tiles:
                            ch.occupied_tiles.remove(idx)
                except Exception:
                    pass

                self.monster.target = None
                self.monster.state_machine.handle_state_event(('SEPARATE', None))

    def draw(self):
        x = self.monster.x
        y = self.monster.y + 30
        face = getattr(self.monster, 'face_dir', 0)
        # face == 0: 오른쪽(정방향), 그 외: 좌우 반전
        if face == 0:
            self.monster.image[int(self.monster.frame)].clip_draw(0, 0, 100, 100, x, y, 150, 150)
        else:
            self.monster.image[int(self.monster.frame)].clip_composite_draw(0, 0, 100, 100, 0, 'h', x, y, 150, 150)

class Monster:
    image = []
    image.append(None)
    image.append(None)
    image.append(None)
    def __init__(self, num):
        self.num = num
        col = num % 10
        row = num // 10
        tw, th = Tile.TILE_W, Tile.TILE_H
        canvas_h = get_canvas_height()
        tile_cx = col * tw + tw // 2
        tile_cy = canvas_h - (row * th + th // 2)
        self.dead = False
        self.x, self.y = tile_cx, tile_cy
        self.Hp = 300
        self.Def = 5
        self.Atk = 50
        self.frame = 0
        self.face_dir = 0  # 1: right, -1: left
        self.target = None
        if self.image[0] is None:
            self.image[0] = load_image('brownbear_01.png')
            self.image[1] = load_image('brownbear_02.png')
            self.image[2] = load_image('brownbear_03.png')
        self.IDLE = Idle(self)
        self.ATK = Atack_state(self)

        # 이벤트 검사기들
        def _on_collide(ev):
            return isinstance(ev, tuple) and len(ev) >= 3 and ev[0] == 'COLLIDE' and isinstance(ev[2], object)

        def _on_separate(ev):
            return isinstance(ev, tuple) and len(ev) >= 1 and ev[0] == 'SEPARATE'

        self.state_machine = StateMachine(
            self.IDLE,
            {
                self.IDLE: {
                    _on_collide: self.ATK
                },
                self.ATK: {
                    _on_separate: self.IDLE
                }
            }
        )
        unit_groups = ['KNIGHT', 'ARCHER', 'HPTANK', 'DPTANK', 'HEALER', 'VANGUARD']
        for ug in unit_groups:
            game_world.add_collision_pair(f'{ug}:MONSTER', None, self)

    def die(self):
        # 중복 처리 방지
        if getattr(self, 'dead', False):
            return
        self.dead = True

        # 처치 카운트 증가
        try:
            stage01.killed_monster += 1
            print(f"[MONSTER_DIE] killed_monster={stage01.killed_monster}")
        except Exception as e:
            print(f"[MONSTER_DIE_ERR] failed increment killed_monster: {e}")

        # 스테이지 로컬 리스트에서 제거
        try:
            if self in stage01._monsters_list:
                stage01._monsters_list.remove(self)
        except Exception:
            pass

        # 충돌 목록 등에서 제거(프로젝트 구조에 맞게 추가)
        try:
            # game_world.remove_object 가 있으면 호출
            game_world.remove_object(self)
        except Exception:
            # 없으면 game_world 내부 자료구조 직접 제거 필요
            print("[MONSTER_DIE_WARN] game_world.remove_object failed or not implemented")

    def draw(self):
        self.state_machine.draw()
    def update(self):
        self.state_machine.update()
        if self.x > 950:
            game_world.remove_object(self)
            try:
                game_world.remove_collision_object(self)
            except Exception:
                pass
            try:
                game_world.remove_object(self)
            except Exception:
                pass
    def get_bb(self):
        return self.x - 50, self.y - 50, self.x + 50, self.y + 50
    def handle_event(self, event):
        self.state_machine.handle_state_event(('INPUT', event))
    def handle_collision(self, group, other):
        # 다른 객체가 없으면 무시
        if other is None:
            return

        # Knight와 충돌하는 경우: Knight의 now_stop/stop 검사
        try:
            other_cls = other.__class__.__name__ if hasattr(other, '__class__') else ''
            if other_cls == 'Knight':
                now_stop = getattr(other, 'now_stop', None)
                stop = getattr(other, 'stop', None)
                if now_stop is not None and stop is not None:
                    # 용량 초과면 통과(충돌 무시)
                    if now_stop >= stop:
                        print(f'[MONSTER_COLLIDE] passing Knight (now_stop={now_stop}, stop={stop})')
                        return
                    # 제한 미달이면 카운트 증가 후 충돌 처리
                    try:
                        other.now_stop += 1
                        print(f'[MONSTER_COLLIDE] incremented Knight.now_stop -> {other.now_stop}')
                    except Exception:
                        pass
        except Exception:
            pass

        # 기본 충돌 처리: 타겟 설정 및 상태 이벤트 전달
        self.target = other
        try:
            self.state_machine.handle_state_event(('COLLIDE', group, other))
        except Exception:
            pass
