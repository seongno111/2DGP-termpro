from pico2d import load_image, draw_rectangle, load_font, get_canvas_height
from sdl2 import SDL_BUTTON_LEFT, SDL_MOUSEBUTTONDOWN
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
        if self.knight.skill_state is True:
            self.knight.skill_frame = (self.knight.skill_frame + FRAMES_PER_ACTION * (
                        ACTION_PER_TIME + 2) * game_framework.frame_time) % 6

        # Idle에서는 자동으로 공격 시작 X, 충돌 시에만 Attack 상태로 진입
        try:
            pass
        except Exception:
            pass
    def draw(self):
        x = self.knight.x
        y = self.knight.y + 50
        # face_dir == 0 -> 오른쪽, 1 -> 왼쪽(수평 반전)
        if self.knight.skill_state is True:
            self.knight.image_sk[int(self.knight.skill_frame)].clip_draw(0, 0, 138, 154, x+10, y, 150, 160)
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
        # 이제는 특정 target을 고정하지 않고, Attack 상태에 있는 동안 범위 내의 모든 적을 타격
    def exit(self, e):
        # 기본 초기화
        self.knight.frame = 0
        self.attack_timer = 0.0
        # 넘어가며 타깃 참조 정리
        try:
            self.knight.target = None
        except Exception:
            pass
    def do(self):
        # 애니 프레임 업데이트
        self.knight.frame = (self.knight.frame + FRAMES_PER_ACTION_ac * ACTION_PER_TIME * game_framework.frame_time) % 5
        if self.knight.skill_state is True:
            self.knight.skill_frame = (self.knight.skill_frame + FRAMES_PER_ACTION * ACTION_PER_TIME * game_framework.frame_time) % 6

        # 공격 간격
        ATTACK_INTERVAL = 0.8
        self.attack_timer += game_framework.frame_time
        if self.attack_timer < ATTACK_INTERVAL:
            return
        self.attack_timer -= ATTACK_INTERVAL

        atk = getattr(self.knight, 'Atk', 100)

        # 저지(now_stop/stop)는 충돌 때만 증가시키고, 공격은 범위 안 모든 적에게 수행
        hit_any = False
        try:
            for layer in list(game_world.world):
                for obj in list(layer):
                    # Monster / Boss 판별
                    try:
                        from monster import Monster
                        from boss import Boss
                        if not isinstance(obj, (Monster, Boss)):
                            continue
                    except Exception:
                        name = obj.__class__.__name__
                        if name not in ('Monster', 'Boss'):
                            continue

                    if getattr(obj, 'Hp', 0) <= 0:
                        continue

                    # 공격 범위 내인지 확인
                    try:
                        if not game_world.in_attack_range(self.knight, obj):
                            continue
                    except Exception:
                        continue

                    dmg = max(0, atk - getattr(obj, 'Def', 0))
                    try:
                        obj.Hp -= dmg
                    except Exception:
                        continue
                    print(f'Knight multi-hit -> {obj.__class__.__name__} dmg={dmg} target_hp={getattr(obj, "Hp", "?")}')

                    if getattr(obj, 'Hp', 1) <= 0:
                        print(f'{obj.__class__.__name__} died by Knight.')
                        try:
                            game_world.remove_object(obj)
                            obj.die()
                        except Exception:
                            pass
                        try:
                            game_world.remove_collision_object(obj)
                        except Exception:
                            pass
                    hit_any = True
        except Exception:
            pass

        # 더 이상 in_attack_range 안에 적이 하나도 없으면 Idle 상태로 복귀
        if not hit_any:
            try:
                self.knight.state_machine.handle_state_event(('SEPARATE', None))
            except Exception:
                pass

    def draw(self):
        x = self.knight.x
        y = self.knight.y + 50
        # face_dir == 0 -> 오른쪽, 1 -> 왼쪽(수평 반전)
        if self.knight.skill_state is True:
            self.knight.image_sk[int(self.knight.skill_frame)].clip_draw(0, 0, 138, 154, x+10, y, 150, 160)
        if getattr(self.knight, 'face_dir', 0) == 0 or getattr(self.knight, 'face_dir', 0) == 2:
            self.knight.image[int(self.knight.frame)+1].clip_draw(0, 0, 100, 100, x, y, 150, 160)
            if self.knight.frame >= 3:
                if self.knight.skill_state is True:
                    self.knight.image_at[int(self.knight.frame) - 3].clip_draw(0, 0, 124, 117, x + 50, y + 40, 200, 260)
                else:
                    self.knight.image_at[int(self.knight.frame)-3].clip_draw(0, 0, 124, 117, x + 50, y-20, 200, 210)
        else:
            self.knight.image[int(self.knight.frame)+1].clip_composite_draw(0, 0, 100, 100, 0, 'h', x, y, 150, 160)
            if self.knight.frame >= 3:
                if self.knight.skill_state is True:
                    self.knight.image_at[int(self.knight.frame) - 3].clip_composite_draw(0, 0,  124, 117, 0, 'h', x-50, y+40, 250, 260)
                else:
                    self.knight.image_at[int(self.knight.frame)-3].clip_composite_draw(0, 0,  124, 117, 0, 'h', x-50, y-20, 200, 210)




class Knight:
    image = []
    image_at = []
    image_sk = []
    for i in range(8):
        image.append(None)
    for i in range(3):
        image_at.append(None)
    for i in range(7):
        image_sk.append(None)
    def __init__(self):
        self.depth = 0
        self.x, self.y = 0, 0
        self.frame = 0
        self.skill_frame = 0
        self.face_dir = 0 # 0오른쪽, 1왼쪽, 2위, 3아래
        self.max_hp = 1000
        self.stop = 3
        self.now_stop = 0
        self.Hp = 1000
        self.Def = 20
        self.Atk = 100
        self.skill = 0
        self._skill_timer = 0.0
        self.skill_state = False
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
            self.image[6] = load_image('tuar03_07.png')
        if self.image_at[0] is None:
            self.image_at[0] = load_image('k_at_ef_01.png')
            self.image_at[1] = load_image('k_at_ef_02.png')
            self.image_at[2] = load_image('k_at_ef_03.png')
        if self.image_sk[0] is None:
            self.image_sk[0] = load_image('tuar_skill01.png')
            self.image_sk[1] = load_image('tuar_skill02.png')
            self.image_sk[2] = load_image('tuar_skill03.png')
            self.image_sk[3] = load_image('tuar_skill04.png')
            self.image_sk[4] = load_image('tuar_skill05.png')
            self.image_sk[5] = load_image('tuar_skill06.png')

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

    def on_hit_by_monster(self, attacker):
        """
        몬스터에게 피격되었을 때 호출된다.
        기존처럼 on_hit_by_monster에서 target을 하나만 고정하지 않고,
        Attack 상태로만 진입하게 유지해도 되지만, 여기서는 기존 기능을 유지한다.
        """
        if self.state_machine.cur_state is self.ATK:
            return

        try:
            if not game_world.in_attack_range(self, attacker):
                return
        except Exception:
            return

        if getattr(self, 'target', None) is None:
            try:
                self.target = attacker
            except Exception:
                pass
            try:
                self.state_machine.handle_state_event(('COLLIDE', 'KNIGHT:MONSTER', attacker))
            except Exception:
                pass
    def get_at_bound(self):
        if self.face_dir == 0:
            x1, y1, x2, y2 = self.x - 50, self.y - 50, self.x + 150, self.y + 50
        elif self.face_dir == 1:
            x1, y1, x2, y2 = self.x - 150, self.y - 50, self.x + 50, self.y + 50
        elif self.face_dir == 2:
            x1, y1, x2, y2 = self.x - 50, self.y - 50, self.x + 50, self.y + 150
        else:
            x1, y1, x2, y2 = self.x - 50, self.y - 150, self.x + 50, self.y + 50

        left = min(x1, x2)
        bottom = min(y1, y2)
        right = max(x1, x2)
        top = max(y1, y2)
        return left, bottom, right, top

    def draw(self):
        self.state_machine.draw()
        for i in range(int((self.Hp/1000)*100//10)):
            self.font.draw(self.x-50+i*10, self.y+80, f'/', (100, 250, 100))

    def get_bb(self):
        return self.x - 40, self.y - 40, self.x + 40, self.y + 40

    def update(self):
        self.state_machine.update()
        try:
            dt = game_framework.frame_time
        except Exception:
            dt = 0.0

        if self.skill_state is True:
            self._skill_timer += dt
            self.Atk = 200
            while self._skill_timer >= 1.0 and self.skill > 0:
                self.skill = max(0, self.skill - 1)
                self._skill_timer -= 1.0
                if self.skill == 0:
                    self.skill_state = False

        else:
            self._skill_timer += dt
            self.Atk = 100
            while self._skill_timer >= 1.0 and self.skill < 10:
                self.skill = min(10, self.skill + 1)
                self._skill_timer -= 1.0



    def handle_event(self, event):
        self.state_machine.handle_state_event(('INPUT', event))

    def handle_collision(self, group, other):
        left, right = (group.split(':') + ['', ''])[:2]
        left = left.strip().upper()
        right = right.strip().upper()

        # 충돌 처리 공통 로직: 이미 다른 유닛에 의해 저지 중이면 pass
        if getattr(other, '_blocked_by', None) not in (None, self):
            return

        # KNIGHT와 MONSTER 간 충돌에서만 now_stop/stop을 사용해 저지수 관리
        if (left == 'KNIGHT' and right == 'MONSTER') or (left == 'MONSTER' and right == 'KNIGHT'):
            if self.now_stop < self.stop:
                try:
                    other._blocked_by = self
                except Exception:
                    pass
                self.now_stop += 1
                if getattr(self, 'target', None) is None:
                    self.target = other
                try:
                    self.state_machine.handle_state_event(('COLLIDE', group, other))
                except Exception:
                    pass
            return

        # 그 외 그룹은 저지수와 상관없이 단순히 Attack 상태로만 진입
        try:
            self.state_machine.handle_state_event(('COLLIDE', group, other))
        except Exception:
            pass
        return
