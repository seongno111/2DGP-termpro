from pico2d import load_image

import game_framework
import game_world
from state_machine import StateMachine
from link_helper import update_link_states_for_hptank_healer

HEAL_INTERVAL = 0.8
heal_timer = 0.0
TIME_PER_ACTION = 0.8
ACTION_PER_TIME = 1.0 / TIME_PER_ACTION
FRAMES_PER_ACTION_ac = 3

class Idle:
    def __init__(self, healer):
        self.healer = healer
    def enter(self, e):
        pass
    def exit(self, e):
        pass
    def do(self):
        # 애니메이션 프레임은 매프레임 갱신
        self.healer.frame = (self.healer.frame + FRAMES_PER_ACTION_ac * ACTION_PER_TIME * game_framework.frame_time) % 2
        if self.healer.skill_state:
            self.healer.skill_frame = (self.healer.skill_frame + FRAMES_PER_ACTION_ac * ACTION_PER_TIME * game_framework.frame_time) % 2

        # 스캔 쿨다운 초기화
        if not hasattr(self.healer, 'scan_cooldown'):
            self.healer.scan_cooldown = 0.2
            self.healer.scan_timer = 0.0

        self.healer.scan_timer += game_framework.frame_time
        if self.healer.scan_timer < self.healer.scan_cooldown:
            return
        self.healer.scan_timer = 0.0

        # 1순위: 링크 상태일 때 Hptank 는 거리 제한 없이 항상 힐 대상 후보
        hptank_always = None
        if getattr(self.healer, 'linked', False):
            for layer in game_world.world:
                for obj in layer[:]:
                    if obj is self.healer:
                        continue
                    if obj.__class__.__name__ != 'Hptank':
                        continue
                    if not hasattr(obj, 'Hp') or not hasattr(obj, 'max_hp'):
                        continue
                    if getattr(obj, 'Hp', 0) >= getattr(obj, 'max_hp', 0):
                        continue
                    hptank_always = obj
                    break
                if hptank_always is not None:
                    break

        if hptank_always is not None:
            self.healer.target = hptank_always
            print(f'Healer.IDLE(linked) -> Hptank always target Hp={hptank_always.Hp}/{hptank_always.max_hp}')
            self.healer.state_machine.handle_state_event(('COLLIDE', 'HEALER:HPTANK', hptank_always))
            return

        # 2순위: 그 외 유닛들은 기존처럼 공격(힐) 범위 안에 있을 때만 힐
        for layer in game_world.world:
            for obj in layer[:]:
                if obj is self.healer:
                    continue
                if not hasattr(obj, 'Hp') or not hasattr(obj, 'max_hp'):
                    continue
                if getattr(obj, 'Hp', 0) >= getattr(obj, 'max_hp', 0):
                    continue
                try:
                    in_range = game_world.in_attack_range(self.healer, obj)
                except Exception:
                    in_range = False
                if in_range:
                    self.healer.target = obj
                    print(f'Healer.IDLE -> found target={obj.__class__.__name__} Hp={getattr(obj,"Hp", "?")}/{getattr(obj,"max_hp", "?")} in_range={in_range}')
                    self.healer.state_machine.handle_state_event(('COLLIDE', 'HEALER:UNIT', obj))
                    return
    def draw(self):
        x = self.healer.x
        y = self.healer.y + 50
        if self.healer.skill_state:
            self.healer.sk_image[int(self.healer.skill_frame)].clip_draw(0, 0, 256, 246, x, y + 50, 160, 150)

        if getattr(self.healer, 'face_dir', 0) == 0:
            self.healer.image[int(self.healer.frame)].clip_draw(0, 0, 100, 100, x, y+50, 150, 160)
        else:
            self.healer.image[int(self.healer.frame)].clip_composite_draw(0, 0, 100, 100, 0, 'h', x, y+50, 150, 160)

class Heal:
    def __init__(self, healer):
        self.healer = healer
        self.heal_timer = 0.0

    def enter(self, e):
        self.healer.frame = 0
        self.heal_timer = 0.0
        if isinstance(e, tuple) and len(e) >= 3:
            self.healer.target = e[2]
        else:
            self.healer.target = getattr(self.healer, 'target', None)
        print(f'Healer.HEAL.enter target={getattr(self.healer,"target",None)}')

    def exit(self, e):
        self.healer.frame = 0
        self.heal_timer = 0.0

    def do(self):
        self.healer.frame = (self.healer.frame + FRAMES_PER_ACTION_ac * ACTION_PER_TIME * game_framework.frame_time) % 5
        if self.healer.skill_state:
            self.healer.skill_frame = (self.healer.skill_frame + FRAMES_PER_ACTION_ac * ACTION_PER_TIME * game_framework.frame_time) % 2
        target = getattr(self.healer, 'target', None)

        if target is None:
            print('Healer.HEAL.do: no target -> SEPARATE')
            self.healer.state_machine.handle_state_event(('SEPARATE', None))
            return

        # 유효성 체크: 월드에 남아있는지
        try:
            in_world = any(target in layer for layer in game_world.world)
        except Exception:
            in_world = False
        if not in_world:
            print(f'Healer.HEAL.do: target not in world -> {target}')
            self.healer.target = None
            self.healer.state_machine.handle_state_event(('SEPARATE', None))
            return

        # 링크 상태 + Hptank 라면 거리 제한 없이 힐, 그 외에는 기존처럼 범위 체크
        if not (getattr(self.healer, 'linked', False) and target.__class__.__name__ == 'Hptank'):
            try:
                in_range = game_world.in_attack_range(self.healer, target)
            except Exception as ex:
                in_range = False
                print(f'Healer.HEAL.do: in_attack_range raised {ex}')
            if not in_range:
                print('Healer.HEAL.do: not in range -> SEPARATE')
                self.healer.state_machine.handle_state_event(('SEPARATE', None))
                return

        if getattr(target, 'Hp', 0) >= getattr(target, 'max_hp', 0):
            print('Healer.HEAL.do: target full HP -> SEPARATE')
            self.healer.state_machine.handle_state_event(('SEPARATE', None))
            return

        # 힐 처리 및 이펙트 생성
        self.heal_timer += game_framework.frame_time
        if self.heal_timer >= HEAL_INTERVAL:
            self.heal_timer -= HEAL_INTERVAL
            heal_amount = getattr(self.healer, 'Atk', 100)
            if self.healer.skill_state:
                heal_amount = int(heal_amount * 2.0)
            target.Hp = min(target.max_hp, target.Hp + heal_amount)
            print(f'Healer healed {target.__class__.__name__} +{heal_amount} hp -> {getattr(target, "Hp", "?")}')

            # 이펙트 생성: at_image를 사용, 대상에 _overlay로 참조 저장
            try:
                # 안전하게 속성 가져오기
                healer_obj = getattr(self, 'healer', None)
                # 힐러가 overlay_depth를 제공하면 사용, 아니면 기본 6층 사용
                depth_for_effect = 6
                if healer_obj is not None:
                    depth_for_effect = getattr(healer_obj, 'overlay_depth', depth_for_effect)
                # 유효한 depth인지 검사 (game_world.world 길이 기준)
                try:
                    max_depth = len(game_world.world)
                except Exception:
                    max_depth = 8
                if not isinstance(depth_for_effect, int) or not (0 <= depth_for_effect < max_depth):
                    depth_for_effect = 6

                effect = HealEffect(target=target, life=0.5, depth=depth_for_effect)

                # 기존 오버레이가 있으면 안전 제거
                old_overlay = getattr(target, '_overlay', None)
                if old_overlay is not None:
                    try:
                        game_world.remove_object(old_overlay)
                    except Exception:
                        pass

                target._overlay = effect
                game_world.add_object(effect, effect.depth)
            except Exception:
                pass

    def draw(self):
        x = self.healer.x
        y = self.healer.y + 50
        if self.healer.skill_state:
            self.healer.sk_image[int(self.healer.skill_frame)].clip_draw(0, 0, 256, 246, x, y+50, 160, 150)
        if getattr(self.healer, 'face_dir', 0) == 0:
            idx = min(len(self.healer.image)-1, int(self.healer.frame))
            self.healer.image[idx].clip_draw(0, 0, 100, 100, x, y+50, 150, 160)
        else:
            idx = min(len(self.healer.image)-1, int(self.healer.frame))
            self.healer.image[idx].clip_composite_draw(0, 0, 100, 100, 0, 'h', x, y+50, 150, 160)

class Healer:
    image = []
    sk_image = []
    image_l = None
    for i in range(7):
        image.append(None)
    for i in range(3):
        sk_image.append(None)
    def __init__(self):
        self.depth = 1
        self.x, self.y = 0, 0
        self.frame = 0
        self.skill_frame = 0
        self.face_dir = 0
        self.max_hp = 800
        self.Hp = 800
        self.Def = 10
        self.Atk = 200
        self.number = 5
        self.tile_w = 100
        self.tile_h = 100
        # 스킬: 게이지 0~10, 상태 및 지속시간 별도 관리
        self.skill = 0
        self._skill_timer = 0.0
        self.skill_state = False
        self.skill_state_time = 0.0
        self.skill_state_duration = 10.0
        self.linked = False
        self.tile_center_x = 0
        self.tile_center_y = 0
        if self.image[0] is None:
            self.image[0] = load_image('char/luna01_01.png')
            self.image[1] = load_image('char/luna01_02.png')
            self.image[2] = load_image('char/luna01_03.png')
            self.image[3] = load_image('char/luna01_04.png')
            self.image[4] = load_image('char/luna01_05.png')
            self.image[5] = load_image('char/luna01_06.png')
            self.image[6] = load_image('char/luna01_07.png')

            self.sk_image[0] = load_image('char/luna_skill1.png')
            self.sk_image[1] = load_image('char/luna_skill2.png')
        if self.image_l is None:
            self.image_l = load_image('char/luna_link.png')
        self.HEAL_INTERVAL = HEAL_INTERVAL
        self.heal_timer = 0.0

        self.IDLE = Idle(self)
        self.ATK = Heal(self)

        def _on_collide(ev):
            return isinstance(ev, tuple) and len(ev) >= 3 and ev[0] == 'COLLIDE' and isinstance(ev[2], object)
        def _on_separate(ev):
            return isinstance(ev, tuple) and len(ev) >= 1 and ev[0] == 'SEPARATE'

        # ATK 상태에서 _on_collide을 허용해 타겟 교체도 할 수 있게 함
        self.state_machine = StateMachine(
            self.IDLE,
            {
                self.IDLE: { _on_collide: self.ATK },
                self.ATK : { _on_separate: self.IDLE, _on_collide: self.ATK }
            }
        )
        self.target = None

    def get_at_bound(self):
        if self.face_dir == 0:
            x1, y1, x2, y2 =  self.x - 150, self.y - 150, self.x + 250, self.y + 170
        elif self.face_dir == 1:
            x1, y1, x2, y2 = self.x + 150, self.y - 150, self.x - 250, self.y + 170
        elif self.face_dir == 2:
            x1, y1, x2, y2 = self.x - 150, self.y - 120, self.x + 150, self.y + 250
        else:
            x1, y1, x2, y2 = self.x - 150, self.y + 170, self.x + 150, self.y - 250

        left = min(x1, x2)
        bottom = min(y1, y2)
        right = max(x1, x2)
        top = max(y1, y2)
        return left, bottom, right, top

    def draw(self):
        self.state_machine.draw()

    def update(self):
        # Healer는 Idle/Heal 상태 로직은 state_machine 내부에 있으므로, 여기서는 스킬 상태/게이지만 관리
        try:
            dt = game_framework.frame_time
        except Exception:
            dt = 0.0

        # 링크 상태 자동 갱신
        try:
            update_link_states_for_hptank_healer()
        except Exception:
            pass

        # 1) 스킬 발동 중이면 지속시간만 관리 (힐 2배 효과는 Heal.do 에서 skill_state로 판단)
        if self.skill_state:
            self.skill_state_time += dt
            if self.skill_state_time >= self.skill_state_duration:
                # 10초 유지 후 스킬 종료 및 게이지 0으로 초기화
                self.skill_state = False
                self.skill_state_time = 0.0
                self.skill = 0
        else:
            # 2) 스킬이 꺼져 있는 동안만 쿨다운 게이지 채우기
            self._skill_timer += dt
            while self._skill_timer >= 1.0 and self.skill < 10:
                self.skill = min(10, self.skill + 1)
                self._skill_timer -= 1.0

    def get_bb(self):
        return self.x - 20, self.y - 20, self.x + 20, self.y + 20

    def handle_collision(self, group, other):
        # 기존 핸들러는 유지하되, 이제 직접 스캔으로도 동작하므로 충돌에 의존하지 않음
        print(f'Healer.handle_collision group={group} other={other}')
        try:
            if not any(other in layer for layer in game_world.world):
                return
        except Exception:
            return
        if not hasattr(other, 'Hp') or not hasattr(other, 'max_hp'):
            return

        left, right = (group.split(':') + ['', ''])[:2]
        left = left.strip().upper()
        right = right.strip().upper()

        FRIEND_UNITS = {'KNIGHT', 'ARCHER', 'HPTANK', 'DPTANK', 'VANGUARD', 'HEALER'}
        if (left == 'HEALER' and right in FRIEND_UNITS) or (right == 'HEALER' and left in FRIEND_UNITS):
            if getattr(self, 'target', None) is other:
                return
            self.target = other
            self.state_machine.handle_state_event(('COLLIDE', group, other))
            return

class HealEffect:
    image = None
    def __init__(self, target=None, life=0.5, depth=7):
        self.target = target
        if self.image is None:
            self.image = load_image('char/hl_at_ef.png')
        # 초기 위치: 타겟이 있으면 따라붙음
        if self.target is not None:
            try:
                self.x = self.target.x
                self.y = self.target.y + 50
            except Exception:
                self.x, self.y = 0, 0
        else:
            self.x, self.y = 0, 0
        self.life = life
        self.timer = 0.0
        self.depth = depth
        self.removed = False

    def update(self):
        # 대상이 월드에 있으면 따라다님
        try:
            if self.target is not None and any(self.target in layer for layer in game_world.world):
                self.x = self.target.x
                self.y = self.target.y + 50
            else:
                # 대상이 없으면 바로 제거 준비
                self.timer = self.life
        except Exception:
            self.timer = self.life

        # 수명 검사
        self.timer += game_framework.frame_time
        if self.timer >= self.life:
            # 대상의 _overlay 참조 정리
            try:
                if self.target is not None and getattr(self.target, '_overlay', None) is self:
                    self.target._overlay = None
            except Exception:
                pass
            # 안전 제거
            if not self.removed:
                try:
                    game_world.remove_object(self)
                except Exception:
                    pass
                self.removed = True

    def draw(self):
        self.image.clip_draw(0, 0, 140, 170, self.x, self.y, 80, 150)