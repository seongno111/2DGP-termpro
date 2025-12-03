from pico2d import load_image, load_font

import game_framework
import game_world
from state_machine import StateMachine


TIME_PER_ACTION = 0.8
ACTION_PER_TIME = 1.0 / TIME_PER_ACTION
FRAMES_PER_ACTION_ac = 5

class Idle:
    def __init__(self, hptank):
        self.hptank = hptank
    def enter(self, e):
        pass
    def exit(self, e):
        pass
    def do(self):
        # 간단한 idle 애니메이션
        self.hptank.frame = (self.hptank.frame + FRAMES_PER_ACTION_ac * ACTION_PER_TIME * game_framework.frame_time) % 2
    def draw(self):
        x = self.hptank.x
        y = self.hptank.y + 50
        if getattr(self.hptank, 'face_dir', 0) == 0:
            self.hptank.image[int(self.hptank.frame)].clip_draw(0, 0, 100, 100, x, y, 150, 160)
        else:
            self.hptank.image[int(self.hptank.frame)].clip_composite_draw(0, 0, 100, 100, 0, 'h', x, y, 150, 160)

class Attack:
    def __init__(self, hptank):
        self.hptank = hptank
        self.attack_timer = 0.0
    def enter(self, e):
        self.hptank.frame = 0
        self.attack_timer = 0.0
        if isinstance(e, tuple) and len(e) >= 3:
            self.hptank.target = e[2]
    def exit(self, e):
        self.hptank.frame = 0
        self.attack_timer = 0.0
        # 정리: 타겟이 이 Hptank에 의해 저지된 상태면 카운트 감소 및 링크 해제
        try:
            tgt = getattr(self.hptank, 'target', None)
            if tgt is not None and getattr(tgt, '_blocked_by', None) is self.hptank:
                try:
                    self.hptank.now_stop = max(0, self.hptank.now_stop - 1)
                except Exception:
                    pass
                try:
                    tgt._blocked_by = None
                except Exception:
                    pass
                try:
                    if getattr(tgt, 'target', None) is self.hptank:
                        tgt.target = None
                except Exception:
                    pass
        except Exception:
            pass
        try:
            self.hptank.target = None
        except Exception:
            pass
    def do(self):
        self.hptank.frame = (self.hptank.frame + FRAMES_PER_ACTION_ac * ACTION_PER_TIME * game_framework.frame_time) % 5
        target = getattr(self.hptank, 'target', None)
        # 타겟이 없거나 범위 밖이면 SEPARATE
        if target is None or not game_world.in_attack_range(self.hptank, target):
            self.hptank.state_machine.handle_state_event(('SEPARATE', None))
            return
        ATTACK_INTERVAL = 0.8
        self.attack_timer += game_framework.frame_time
        if self.attack_timer >= ATTACK_INTERVAL:
            self.attack_timer -= ATTACK_INTERVAL
            dmg = max(0, self.hptank.Atk - getattr(target, 'Def', 0))
            target.Hp -= dmg
            print(f'Hptank attacked Monster dmg={dmg} target_hp={getattr(target, "Hp", "?")}')
            if getattr(target, 'Hp', 1) <= 0:
                print(f'{target.__class__.__name__} died by Hptank.')
                # 오버레이가 있으면 제거
                try:
                    if hasattr(target, '_overlay'):
                        game_world.remove_object(target._overlay)
                except Exception:
                    pass
                # 대상 객체와 충돌 등록 제거
                try:
                    game_world.remove_object(target)
                    target.die()
                except Exception:
                    pass
                try:
                    game_world.remove_collision_object(target)
                except Exception:
                    pass
                # 배치 상태 갱신 (있을 경우)
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
                # 타겟 정리 및 상태 복귀
                self.hptank.target = None
                self.hptank.state_machine.handle_state_event(('SEPARATE', None))
    def draw(self):
        x = self.hptank.x
        y = self.hptank.y + 50
        if getattr(self.hptank, 'face_dir', 0) == 0:
            self.hptank.image[int(self.hptank.frame)+2].clip_draw(0, 0, 100, 100, x, y, 150, 160)
            if self.hptank.frame >= 3:
                self.hptank.at_image[int(self.hptank.frame) -3].clip_draw(0, 0, 157, 158, x, y, 150, 160)
        else:
            self.hptank.image[int(self.hptank.frame)+2].clip_composite_draw(0, 0, 100, 100, 0, 'h', x, y, 150, 160)
            if self.hptank.frame >= 3:
                self.hptank.at_image[int(self.hptank.frame) -3].clip_composite_draw(0, 0, 157, 158, 0, 'h', x, y, 150, 160)

class Hptank:
    image = []
    at_image = []
    for i in range(8):
        image.append(None)
    for i in range(3):
        at_image.append(None)
    def __init__(self):
        self.depth = 0
        self.x, self.y = 0, 0
        self.frame = 0
        self.face_dir = 0
        self.stop = 4
        self.now_stop = 0
        self.max_hp = 2000
        self.Hp = 2000
        self.Def = 10
        self.Atk = 60
        self.number = 3
        self.skill = 10
        self._skill_timer = 0.0
        self.skill_state = False
        self.tile_w = 100
        self.tile_h = 100
        self.tile_center_x = 0
        self.tile_center_y = 0
        self.font = load_font('ENCR10B.TTF', 30)
        if self.image[0] is None:
            self.image[0] = load_image('klat01_01.png')
            self.image[1] = load_image('klat01_02.png')
            self.image[2] = load_image('klat01_03.png')
            self.image[3] = load_image('klat01_04.png')
            self.image[4] = load_image('klat01_05.png')
            self.image[5] = load_image('klat01_06.png')
            self.image[6] = load_image('klat01_07.png')
            self.at_image[0] = load_image('hp_at_ef_01.png')
            self.at_image[1] = load_image('hp_at_ef_02.png')
            self.at_image[2] = load_image('hp_at_ef_03.png')
        self.IDLE = Idle(self)
        self.ATK = Attack(self)

        def _on_collide(ev):
            return isinstance(ev, tuple) and len(ev) >= 3 and ev[0] == 'COLLIDE' and isinstance(ev[2], object)
        def _on_separate(ev):
            return isinstance(ev, tuple) and len(ev) >= 1 and ev[0] == 'SEPARATE'

        # ATK 상태에서 중복 COLLIDE 이벤트를 무시하려면 ATK에 _on_collide를 자기 자신으로 매핑 가능
        self.state_machine = StateMachine(
            self.IDLE,
            {
                self.IDLE : { _on_collide: self.ATK },
                self.ATK  : { _on_separate: self.IDLE, _on_collide: self.ATK }
             }
        )
        self.target = None

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
        for i in range(int((self.Hp / 2000) * 100 // 10)):
            self.font.draw(self.x - 50 + i * 10, self.y + 80, f'/', (100, 250, 100))

    def get_bb(self):
        return self.x - 40, self.y - 40, self.x + 40, self.y + 40

    def handle_collision(self, group, other):
        try:
            if not any(other in layer for layer in game_world.world):
                return
        except Exception:
            return
        if getattr(other, 'Hp', 1) <= 0:
            return

        left, right = (group.split(':') + ['', ''])[:2]
        left = left.strip().upper()
        right = right.strip().upper()

        # 이미 다른 유닛에 의해 저지되었으면 패스
        if getattr(other, '_blocked_by', None) is not None:
            return

        if (left == 'HPTANK' and right == 'MONSTER') or (left == 'MONSTER' and right == 'HPTANK'):
            if self.now_stop < self.stop:
                other._blocked_by = self
                self.now_stop += 1
                if getattr(self, 'target', None) is None:
                    self.target = other
                try:
                    self.state_machine.handle_state_event(('COLLIDE', group, other))
                except Exception:
                    pass
            return

        # fallback
        if self.now_stop < self.stop:
            other._blocked_by = self
            self.now_stop += 1
            if getattr(self, 'target', None) is None:
                self.target = other
            try:
                self.state_machine.handle_state_event(('COLLIDE', group, other))
            except Exception:
                pass
        return

    def update(self):
        self.state_machine.update()
        try:
            dt = game_framework.frame_time
        except Exception:
            dt = 0.0

        if self.skill_state is True:
            self._skill_timer += dt
            while self._skill_timer >= 1.0 and self.skill > 0:
                self.skill = max(0, self.skill - 1)
                self._skill_timer -= 1.0
                if self.skill == 0:
                    self.skill_state = False

        else:
            self._skill_timer += dt
            while self._skill_timer >= 1.0 and self.skill < 10:
                self.skill = min(10, self.skill + 1)
                self._skill_timer -= 1.0
    def handle_event(self, event):
        self.state_machine.handle_state_event(('INPUT', event))