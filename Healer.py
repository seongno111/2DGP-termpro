from pico2d import load_image

import game_framework
import game_world
from state_machine import StateMachine

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

        # 스캔 쿨다운 초기화
        if not hasattr(self.healer, 'scan_cooldown'):
            self.healer.scan_cooldown = 0.2
            self.healer.scan_timer = 0.0

        self.healer.scan_timer += game_framework.frame_time
        if self.healer.scan_timer < self.healer.scan_cooldown:
            return
        self.healer.scan_timer = 0.0

        # 범위 스캔: 대상 발견 시 먼저 healer.target에 할당하고 로그 출력 후 이벤트 전송
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
                    # 선할당(이벤트와 상태 진입 시 race 예방), 디버그 출력
                    self.healer.target = obj
                    print(f'Healer.IDLE -> found target={obj.__class__.__name__} Hp={getattr(obj,"Hp", "?")}/{getattr(obj,"max_hp", "?")} in_range={in_range}')
                    self.healer.state_machine.handle_state_event(('COLLIDE', 'HEALER:UNIT', obj))
                    return
    def draw(self):
        x = self.healer.x
        y = self.healer.y + 50
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
            # 안전: IDLE에서 이미 설정했을 수도 있음
            self.healer.target = getattr(self.healer, 'target', None)
        print(f'Healer.HEAL.enter target={getattr(self.healer,"target",None)}')

    def exit(self, e):
        self.healer.frame = 0
        self.heal_timer = 0.0

    def do(self):
        self.healer.frame = (self.healer.frame + FRAMES_PER_ACTION_ac * ACTION_PER_TIME * game_framework.frame_time) % 5

        target = getattr(self.healer, 'target', None)

        # 디버그: 타겟 존재/월드/HP/바운드 정보 출력 및 범위 판정 직전 상태 확인
        if target is None:
            print('Healer.HEAL.do: no target -> SEPARATE')
            self.healer.state_machine.handle_state_event(('SEPARATE', None))
            return

        try:
            in_world = any(target in layer for layer in game_world.world)
        except Exception:
            in_world = False
        if not in_world:
            print(f'Healer.HEAL.do: target not in world -> {target}')
            self.healer.target = None
            self.healer.state_machine.handle_state_event(('SEPARATE', None))
            return

        # 바운드와 BB 수집 (for debug)
        try:
            atk_bounds = self.healer.get_at_bound()
        except Exception as ex:
            print(f'Healer.HEAL.do: get_at_bound exception: {ex}')
            atk_bounds = None
        try:
            tgt_bb = target.get_bb()
        except Exception as ex:
            print(f'Healer.HEAL.do: target.get_bb exception: {ex}')
            tgt_bb = None

        # 범위 판정 및 상세 로그
        try:
            in_range = game_world.in_attack_range(self.healer, target)
        except Exception as ex:
            in_range = False
            print(f'Healer.HEAL.do: in_attack_range raised {ex}')

        print(f'Healer.HEAL.do: target={target.__class__.__name__} Hp={getattr(target,"Hp","?")}/{getattr(target,"max_hp","?")} bounds={atk_bounds} bb={tgt_bb} in_range={in_range}')

        if not in_range:
            # 이유 로그 후 SEPARATE
            print('Healer.HEAL.do: not in range -> SEPARATE')
            self.healer.state_machine.handle_state_event(('SEPARATE', None))
            return

        if getattr(target, 'Hp', 0) >= getattr(target, 'max_hp', 0):
            print('Healer.HEAL.do: target full HP -> SEPARATE')
            self.healer.state_machine.handle_state_event(('SEPARATE', None))
            return

        # 힐 처리
        self.heal_timer += game_framework.frame_time
        if self.heal_timer >= HEAL_INTERVAL:
            self.heal_timer -= HEAL_INTERVAL
            heal_amount = getattr(self.healer, 'Atk', 100)
            target.Hp = min(target.max_hp, target.Hp + heal_amount)
            print(f'Healer healed {target.__class__.__name__} +{heal_amount} hp -> {getattr(target, "Hp", "?")}')
            if getattr(target, 'Hp', 0) >= getattr(target, 'max_hp', 0):
                self.healer.target = None
                self.healer.state_machine.handle_state_event(('SEPARATE', None))

    def draw(self):
        x = self.healer.x
        y = self.healer.y + 50
        if getattr(self.healer, 'face_dir', 0) == 0:
            idx = min(len(self.healer.image)-1, int(self.healer.frame))
            self.healer.image[idx].clip_draw(0, 0, 100, 100, x, y+50, 150, 160)
        else:
            idx = min(len(self.healer.image)-1, int(self.healer.frame))
            self.healer.image[idx].clip_composite_draw(0, 0, 100, 100, 0, 'h', x, y+50, 150, 160)

class Healer:
    image = []
    for i in range(7):
        image.append(None)

    def __init__(self):
        from pico2d import load_image
        from state_machine import StateMachine

        self.depth = 1
        self.x, self.y = 0, 0
        self.frame = 0
        self.face_dir = 0
        self.max_hp = 800
        self.Hp = 800
        self.Def = 10
        self.Atk = 200
        self.number = 5
        self.tile_w = 100
        self.tile_h = 100
        self.tile_center_x = 0
        self.tile_center_y = 0
        if self.image[0] is None:
            self.image[0] = load_image('luna01_01.png')
            self.image[1] = load_image('luna01_02.png')
            self.image[2] = load_image('luna01_03.png')
            self.image[3] = load_image('luna01_04.png')
            self.image[4] = load_image('luna01_05.png')
            self.image[5] = load_image('luna01_06.png')
            self.image[6] = load_image('luna01_07.png')

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
        self.state_machine.update()

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