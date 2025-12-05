from pico2d import load_image, load_font

import game_framework
import game_world
from state_machine import StateMachine
from unit_collision_helper import handle_unit_vs_monster_collision
from link_helper import update_link_states_for_dptank_vanguard

TIME_PER_ACTION = 0.8
ACTION_PER_TIME = 1.0 / TIME_PER_ACTION
FRAMES_PER_ACTION_ac = 3

class Idle:
    def __init__(self, dptank):
        self.dptank = dptank
    def enter(self, e):
        pass
    def exit(self, e):
        pass
    def do(self):
        if self.dptank.skill_state is True:
            self.dptank.skill_frame = (self.dptank.skill_frame + FRAMES_PER_ACTION_ac * ACTION_PER_TIME * game_framework.frame_time) % 5
        # 필요하면 아이들 애니메이션 처리
        self.dptank.frame = (self.dptank.frame + FRAMES_PER_ACTION_ac * ACTION_PER_TIME * game_framework.frame_time) % 2
    def draw(self):
        x = self.dptank.x
        y = self.dptank.y + 50
        if self.dptank.skill_state is True:
            self.dptank.sk_image[int(self.dptank.skill_frame)].clip_draw(0, 0, 63, 90, x, y, 150, 160)
        if getattr(self.dptank, 'face_dir', 0) == 0:
            self.dptank.image[int(self.dptank.frame)].clip_draw(0, 0, 100, 100, x, y, 150, 160)
        else:
            self.dptank.image[int(self.dptank.frame)].clip_composite_draw(0, 0, 100, 100, 0, 'h', x, y, 150, 160)

class Attack:
    def __init__(self, dptank):
        self.dptank = dptank
        self.attack_timer = 0.0

    def enter(self, e):
        self.dptank.frame = 0
        self.attack_timer = 0.0
        if isinstance(e, tuple) and len(e) >= 3:
            self.dptank.target = e[2]

    def _collect_objects(self):
        # 우선적으로 game_world.world 플래트닝 사용
        try:
            if hasattr(game_world, 'world'):
                return [o for layer in game_world.world for o in layer]
        except Exception:
            pass
        # 기존 시도들 (호환성)
        objs = None
        if hasattr(game_world, 'get_objects') and callable(getattr(game_world, 'get_objects')):
            try:
                objs = game_world.get_objects()
            except Exception:
                objs = None
        if objs is None and hasattr(game_world, 'objects'):
            objs = getattr(game_world, 'objects')
        if objs is None and hasattr(game_world, 'all_objects'):
            objs = getattr(game_world, 'all_objects')
        return objs

    def _find_blocked_target(self):
        objs = self._collect_objects()
        if not objs:
            return None
        for o in list(objs):
            if o is None or o is self.dptank:
                continue
            if getattr(o, '_blocked_by', None) is self.dptank and getattr(o, 'Hp', 1) > 0:
                if game_world.in_attack_range(self.dptank, o):
                    return o
        return None

    def _bb_overlap(self, a_bb, b_bb):
        la, ba, ra, ta = a_bb
        lb, bb, rb, tb = b_bb
        return not (ra < lb or la > rb or ta < bb or ba > tb)

    def _find_colliding_target(self):
        objs = self._collect_objects()
        if not objs:
            return None
        my_bb = None
        if hasattr(self.dptank, 'get_bb'):
            try:
                my_bb = self.dptank.get_bb()
            except Exception:
                my_bb = None
        for o in list(objs):
            if o is None or o is self.dptank:
                continue
            if getattr(o, 'Hp', 0) <= 0:
                continue
            if not hasattr(o, 'get_bb'):
                continue
            try:
                if my_bb is None:
                    my_bb = self.dptank.get_bb()
                if self._bb_overlap(my_bb, o.get_bb()) and game_world.in_attack_range(self.dptank, o):
                    return o
            except Exception:
                continue
        return None

    def exit(self, e):
        self.dptank.frame = 0
        self.attack_timer = 0.0
        tgt = getattr(self.dptank, 'target', None)
        if tgt is not None and getattr(self.dptank, '_blocking_target', False):
            # 내가 진짜 막고 있던 타겟이면 now_stop 회수 및 block 해제
            try:
                self.dptank.now_stop = max(0, self.dptank.now_stop - 1)
            except Exception:
                pass
            try:
                if getattr(tgt, '_blocked_by', None) is self.dptank:
                    tgt._blocked_by = None
            except Exception:
                pass
        self.dptank.target = None
        self.dptank._blocking_target = False

    def do(self):
        self.dptank.frame = (self.dptank.frame + FRAMES_PER_ACTION_ac * ACTION_PER_TIME * game_framework.frame_time) % 4
        if self.dptank.skill_state is True:
            self.dptank.skill_frame = (self.dptank.skill_frame + FRAMES_PER_ACTION_ac * ACTION_PER_TIME * game_framework.frame_time) % 5

        target = getattr(self.dptank, 'target', None)

        # 1) 현재 타겟이 죽었거나(world에서 이미 빠졌거나) 더 이상 유효하지 않은 경우 먼저 깨끗이 정리
        try:
            if target is not None:
                died = getattr(target, 'Hp', 0) <= 0
                try:
                    in_world = any(target in layer for layer in game_world.world)
                except Exception:
                    in_world = False

                if died or not in_world:
                    # 안전하게 제거 시도 (중복 호출이어도 예외 없이 넘어가게 처리)
                    try:
                        if hasattr(target, 'die'):
                            target.die()
                    except Exception:
                        pass
                    try:
                        game_world.remove_object(target)
                    except Exception:
                        pass
                    try:
                        game_world.remove_collision_object(target)
                    except Exception:
                        pass
                    try:
                        if getattr(target, '_blocked_by', None) is self.dptank:
                            target._blocked_by = None
                            self.dptank.now_stop = max(0, self.dptank.now_stop - 1)
                    except Exception:
                        pass
                    target = None
                    self.dptank.target = None
        except Exception:
            pass

        # 2) 아직 유효한 타겟이 없거나, 공격 범위 밖이면 새 타겟을 찾는다
        if target is None or not game_world.in_attack_range(self.dptank, target):
            new_target = self._find_blocked_target()
            if new_target is None:
                new_target = self._find_colliding_target()
            if new_target is not None:
                self.dptank.target = new_target
                target = new_target
            else:
                # 정말로 더 이상 칠 수 있는 몬스터가 없으면 ATK 상태에서 빠져나온다.
                self.dptank.state_machine.handle_state_event(('SEPARATE', None))
                return

        # 3) 실제 공격 수행
        ATTACK_INTERVAL = 0.8
        self.attack_timer += game_framework.frame_time
        if self.attack_timer >= ATTACK_INTERVAL:
            self.attack_timer -= ATTACK_INTERVAL
            dmg = max(0, self.dptank.Atk - getattr(target, 'Def', 0))
            try:
                target.Hp -= dmg
            except Exception:
                pass
            print(f'Dptank attacked Monster dmg={dmg} target_hp={getattr(target, "Hp", "?")}')

            # 4) 공격 직후Hp<=0 이 되면 즉시 정리 후 새 타겟을 찾거나 상태 종료
            if getattr(target, 'Hp', 1) <= 0:
                print(f'{target.__class__.__name__} died by Dptank.')
                try:
                    if hasattr(target, 'die'):
                        target.die()
                except Exception:
                    pass
                try:
                    game_world.remove_object(target)
                except Exception:
                    pass
                try:
                    game_world.remove_collision_object(target)
                except Exception:
                    pass
                try:
                    if getattr(target, '_blocked_by', None) is self.dptank:
                        target._blocked_by = None
                        self.dptank.now_stop = max(0, self.dptank.now_stop - 1)
                except Exception:
                    pass

                # 4-1) 다른 블록 대상 또는 충돌 대상 중에서 새 타겟 탐색
                next_target = self._find_blocked_target()
                if next_target is None:
                    next_target = self._find_colliding_target()
                if next_target:
                    try:
                        if getattr(next_target, '_blocked_by', None) is None:
                            next_target._blocked_by = self.dptank
                            self.dptank.now_stop = min(self.dptank.stop, self.dptank.now_stop + 1)
                    except Exception:
                        pass
                    self.dptank.target = next_target
                    self.attack_timer = 0.0
                else:
                    # 더 이상 유효 타겟이 없으면 공격 상태 종료
                    self.dptank.target = None
                    self.dptank.state_machine.handle_state_event(('SEPARATE', None))
                    return

    def draw(self):
        x = self.dptank.x
        y = self.dptank.y + 50
        if self.dptank.skill_state is True:
            self.dptank.sk_image[int(self.dptank.skill_frame)].clip_draw(0, 0, 63, 90, x, y, 150, 160)
        if getattr(self.dptank, 'face_dir', 0) == 0:
            self.dptank.image[int(self.dptank.frame)+2].clip_draw(0, 0, 100, 100, x, y, 150, 160)
            self.dptank.at_image[int(self.dptank.frame)+1].clip_draw(0, 0, 123, 107, x+50, y, 150, 160)
        else:
            self.dptank.image[int(self.dptank.frame)+2].clip_composite_draw(0, 0, 100, 100, 0, 'h', x, y, 150, 160)
            self.dptank.at_image[int(self.dptank.frame)+1].clip_composite_draw(0, 0, 123, 107,0, 'h', x-50, y, 150, 160)

class Dptank:
    image = []
    image_l = None
    for i in range(7):
        image.append(None)
    at_image = []
    for i in range(6):
        at_image.append(None)
    sk_image = []
    for i in range(6):
        sk_image.append(None)
    def __init__(self):
        self.depth = 0
        self.x, self.y = 0, 0
        self.frame = 0
        self.face_dir = 0
        self.stop = 4
        self.target = None
        self._blocking_target = False
        self.skill_frame = 0
        self.now_stop = 0
        self.max_hp = 1500
        self.Hp = 1500
        self.Def = 50
        self.Atk = 10
        self.number = 4
        # 스킬 게이지/상태: 게이지 0~10, 상태 및 지속시간 별도 관리
        self.skill = 0
        self._skill_timer = 0.0
        self.skill_state = False
        self.skill_state_time = 0.0
        self.skill_state_duration = 10.0
        self.linked = False
        self.tile_w = 100
        self.tile_h = 100
        self.tile_center_x = 0
        self.tile_center_y = 0
        self.font = load_font('ENCR10B.TTF', 30)
        if self.image[0] is None:
            self.image[0] = load_image('char/ext01_01.png')
            self.image[1] = load_image('char/ext01_02.png')
            self.image[2] = load_image('char/ext01_03.png')
            self.image[3] = load_image('char/ext01_04.png')
            self.image[4] = load_image('char/ext01_05.png')
            self.image[5] = load_image('char/ext01_06.png')
            self.at_image[0] = load_image('char/dp_at_ef_01.png')
            self.at_image[1] = load_image('char/dp_at_ef_02.png')
            self.at_image[2] = load_image('char/dp_at_ef_03.png')
            self.at_image[3] = load_image('char/dp_at_ef_04.png')
            self.at_image[4] = load_image('char/dp_at_ef_05.png')
            self.sk_image[0] = load_image('char/ext_skill1.png')
            self.sk_image[1] = load_image('char/ext_skill2.png')
            self.sk_image[2] = load_image('char/ext_skill3.png')
            self.sk_image[3] = load_image('char/ext_skill4.png')
            self.sk_image[4] = load_image('char/ext_skill5.png')
        if self.image_l is None:
            self.image_l = load_image('char/ext_link.png')
        self.IDLE = Idle(self)
        self.ATK = Attack(self)

        def _on_collide(ev):
            return isinstance(ev, tuple) and len(ev) >= 3 and ev[0] == 'COLLIDE' and isinstance(ev[2], object)
        def _on_separate(ev):
            return isinstance(ev, tuple) and len(ev) >= 1 and ev[0] == 'SEPARATE'

        self.state_machine = StateMachine(
            self.IDLE,
            {
                self.IDLE: { _on_collide: self.ATK },
                self.ATK : { _on_separate: self.IDLE }
            }
        )
        self.target = None
    def on_hit_by_monster(self, attacker):
        """몬스터에게 피격되었을 때 호출된다."""
        # 이미 공격 중이면 굳이 Idle -> Attack 전환 시도 안 함
        if self.state_machine.cur_state is self.ATK:
            return

        # 공격 가능한 범위 안인지 확인
        try:
            if not game_world.in_attack_range(self, attacker):
                return
        except Exception:
            return

        # 현재 타겟이 없을 때만 이 몬스터를 타겟으로 삼고 공격 상태 진입
        if getattr(self, 'target', None) is None:
            try:
                self.target = attacker
            except Exception:
                pass
            try:
                # Idle 상태에서 몬스터에게 공격받으면 ATK 상태로 넘기기 위한 이벤트
                self.state_machine.handle_state_event(('COLLIDE', 'DPTANK:MONSTER', attacker))
            except Exception:
                pass
    def get_at_bound(self):
        if self.face_dir == 0:
            x1, y1, x2, y2 = self.x - 50, self.y - 50, self.x + 50, self.y + 50
        elif self.face_dir == 1:
            x1, y1, x2, y2 = self.x - 50, self.y - 50, self.x + 50, self.y + 50
        elif self.face_dir == 2:
            x1, y1, x2, y2 = self.x - 50, self.y - 50, self.x + 50, self.y + 50
        else:
            x1, y1, x2, y2 = self.x - 50, self.y - 50, self.x + 50, self.y + 50
        left = min(x1, x2)
        bottom = min(y1, y2)
        right = max(x1, x2)
        top = max(y1, y2)
        return left, bottom, right, top

    def draw(self):
        self.state_machine.draw()
        for i in range(int((self.Hp / 1500) * 100 // 10)):
            self.font.draw(self.x - 50 + i * 10, self.y + 80, f'/', (100, 250, 100))

    def update(self):
        self.state_machine.update()
        try:
            dt = game_framework.frame_time
        except Exception:
            dt = 0.0

        # Dptank-Vanguard 링크 상태 자동 갱신
        try:
            update_link_states_for_dptank_vanguard()
        except Exception:
            pass

        # 스킬 발동 중일 때는 방어력 증가 및 (link 상태면) 스킬 사용 시 코스트 회복 로직은 기존 Attack/do 쪽에서 유지
        if self.skill_state:
            self._skill_timer += dt
            self.skill_state_time += dt
            if self.skill_state_time >= self.skill_state_duration:
                # 10초 유지 후 스킬 종료 및 게이지 0으로 초기화
                self.skill_state = False
                self.skill_state_time = 0.0
                self.skill = 0
        else:
            # 스킬이 꺼져 있는 동안만 쿨다운 게이지 채우기 (10초 동안 0→10)
            self._skill_timer += dt
            while self._skill_timer >= 1.0 and self.skill < 10:
                self.skill = min(10, self.skill + 1)
                self._skill_timer -= 1.0

    def get_bb(self):
        return self.x - 40, self.y - 40, self.x + 40, self.y + 40


    def handle_collision(self, group, other):
        blocked = handle_unit_vs_monster_collision(self, group, other)
        if blocked and other is self.target:
            self._blocking_target = True
        return


    def handle_event(self, event):
        self.state_machine.handle_state_event(('INPUT', event))