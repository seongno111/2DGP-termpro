from pico2d import load_image, draw_rectangle, load_font

import game_framework
import game_world
from state_machine import StateMachine


TIME_PER_ACTION = 0.8
ACTION_PER_TIME = 1.0 / TIME_PER_ACTION
FRAMES_PER_ACTION = 2
FRAMES_PER_ACTION_ac = 5

class Idle:
    def __init__(self, knight):
        self.knight = knight
    def enter(self, e):
        pass
    def exit(self, e):
        pass
    def do(self):
        self.knight.frame = (self.knight.frame + FRAMES_PER_ACTION_ac * ACTION_PER_TIME * game_framework.frame_time) % 2
        pass
    def draw(self):
        x = self.knight.x
        y = self.knight.y + 50
        # face_dir == 0 -> 오른쪽, 1 -> 왼쪽(수평 반전)
        if getattr(self.knight, 'face_dir', 0) == 0 or getattr(self.knight, 'face_dir', 0) == 2:
            self.knight.image[int(self.knight.frame)].clip_draw(0, 0, 100, 100, x, y, 150, 160)
        else:
            # 'h' 플래그로 수평 반전
            self.knight.image[int(self.knight.frame)].clip_composite_draw(0, 0, 100, 100, 0, 'h', x, y, 150, 160)

class Attack:
    def __init__(self, knight):
        self.knight = knight
        self.attack_timer = 0.0
    def enter(self, e):
        self.knight.frame = 0
        self.attack_timer = 0.0
        if isinstance(e, tuple) and len(e) >= 3:
            # event 형태: ('COLLIDE', group, other)
            self.knight.target = e[2]
        # else target might already be set in handle_collision
    def exit(self, e):
        self.knight.frame = 0
        self.attack_timer = 0.0
    def do(self):
        # 애니 프레임 업데이트
        self.knight.frame = (self.knight.frame + FRAMES_PER_ACTION_ac * ACTION_PER_TIME * game_framework.frame_time) % 5
        target = getattr(self.knight, 'target', None)
        # 충돌이 끊기거나 타겟이 없으면 분리
        if target is None or not game_world.collide(self.knight, target):
            self.knight.state_machine.handle_state_event(('SEPARATE', None))
            return
        # 공격 간격
        ATTACK_INTERVAL = 0.8
        self.attack_timer += game_framework.frame_time
        if self.attack_timer >= ATTACK_INTERVAL:
            self.attack_timer -= ATTACK_INTERVAL
            dmg = max(0, self.knight.Atk - getattr(target, 'Def', 0))
            target.Hp -= dmg
            print(f'Knight attacked Monster dmg={dmg} target_hp={getattr(target, "Hp", "?")}')
            if getattr(target, 'Hp', 1) <= 0:
                print(f'{target.__class__.__name__} died by Knight.')
                # 몬스터 제거 및 충돌 제거
                try:
                    game_world.remove_object(target)
                except Exception:
                    pass
                try:
                    game_world.remove_collision_object(target)
                except Exception:
                    pass
                # 타겟 비우고 상태 복귀
                self.knight.target = None
                self.knight.state_machine.handle_state_event(('SEPARATE', None))
    def draw(self):
        x = self.knight.x
        y = self.knight.y + 50
        if getattr(self.knight, 'face_dir', 0) == 0 or getattr(self.knight, 'face_dir', 0) == 2:
            self.knight.image[int(self.knight.frame)+1].clip_draw(0, 0, 100, 100, x, y, 150, 160)
        else:
            self.knight.image[int(self.knight.frame)+1].clip_composite_draw(0, 0, 100, 100, 0, 'h', x, y, 150, 160)


class Knight:
    image = []
    for i in range(8):
        image.append(None)
    def __init__(self):
        self.depth = 0
        self.x, self.y = 0, 0
        self.frame = 0
        self.face_dir = 0 # 0오른쪽, 1왼쪽, 2위, 3아래
        self.Hp = 1000
        self.Def = 10
        self.Atk = 100
        self.number = 1
        self.tile_w = 100
        self.tile_h = 100
        self.tile_center_x = 0
        self.tile_center_y = 0
        self.font = load_font('ENCR10B.TTF', 30)
        if self.image[0] is None:
            self.image[0] = load_image('tuar03_01.png')
            self.image[1] = load_image('tuar03_02.png')
            self.image[2] = load_image('tuar03_03.png')
            self.image[3] = load_image('tuar03_04.png')
            self.image[4] = load_image('tuar03_05.png')
            self.image[5] = load_image('tuar03_06.png')
            self.image[7] = load_image('tuar03_07.png')
        self.IDLE = Idle(self)
        self.ATK = Attack(self)

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
        self.target = None
    def get_at_bound(self):
        if self.face_dir == 0:
            return self.x-50, self.y - 50, self.x + 150, self.y + 50
        elif self.face_dir == 1:
            return self.x+50, self.y - 50, self.x - 150, self.y + 50
        elif self.face_dir == 2:
            return self.x -50, self.y -50, self.x +50, self.y + 150
        else:
            return self.x -50, self.y +50, self.x +50, self.y - 150

    def draw(self):
        self.state_machine.draw()
        for i in range(int((self.Hp/1000)*100//10)):
            self.font.draw(self.x-50+i*10, self.y+80, f'/', (100, 250, 100))

    def get_bb(self):
        return self.x - 50, self.y - 50, self.x + 50, self.y + 50

    def update(self):
        self.state_machine.update()

    def handle_event(self, event):
        self.state_machine.handle_state_event(('INPUT',event))

    def handle_collision(self, group, other):
        left, right = (group.split(':') + ['', ''])[:2]
        left = left.strip().upper()
        right = right.strip().upper()

        # KNIGHT와 MONSTER 간 충돌인 경우에만 특별 처리 (양방향 허용)
        if (left == 'KNIGHT' and right == 'MONSTER') or (left == 'MONSTER' and right == 'KNIGHT'):
            self.target = other
            self.state_machine.handle_state_event(('COLLIDE', group, other))
            return

        # 기본 폴백
        self.target = other
        self.state_machine.handle_state_event(('COLLIDE', group, other))