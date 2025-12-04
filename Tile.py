from pico2d import load_image, get_canvas_height

import game_framework
import game_world
from boss import Boss

TIME_PER_ACTION = 0.3
ACTION_PER_TIME = 1.0 / TIME_PER_ACTION
FRAMES_PER_ACTION = 2

class Tile:
    image_first = None
    image_second = None
    image_third = None
    image_forth = None
    s_image = None
    d_image = None
    frame = 0
    TILE_W = 100
    TILE_H = 100
    def __init__(self,index, depth):
        self.index = index
        self.depth = depth
        if self.image_first is None and self.image_second is None:
            self.image_first = load_image('ground.png')
            self.image_second = load_image('floor_nd.png')
        if self.image_third is None and self.depth == 2:
            self.image_first = load_image('ground.png')
            self.image_third = load_image('cave.png')
        if self.image_forth is None and self.depth == 3 :
            self.image_first = load_image('ground.png')
            self.image_forth = load_image('de_place.png')
        if self.s_image is None and self.depth == 4:
            self.s_image = load_image('special_tile_recover.png')
        if self.d_image is None and self.depth == 5:
            self.d_image = load_image('special_tile_damage.png')

    def draw(self):
        canvas_h = get_canvas_height()
        col = self.index % 10
        row = self.index // 10
        x = col * Tile.TILE_W + Tile.TILE_W // 2
        # 위에서부터 그리려면 캔버스 높이에서 오프셋을 뺌
        y = canvas_h - (row * Tile.TILE_H + Tile.TILE_H // 2)
        if self.depth == 0:
            self.image_first.clip_draw(0, 0, 100, 100, x, y)
        elif self.depth == 1:
            self.image_second.clip_draw(0, 0, 47, 65, x, y, 100, 160)
        elif self.depth == 4:
            self.s_image.clip_draw(0, 0, 100, 100, x, y)
        elif self.depth == 5:
            self.d_image.clip_draw(0, 0, 100, 100, x, y)
        if self.depth == 2:
            self.image_first.clip_draw(0, 0, 100, 100, x, y)
            self.image_third.clip_composite_draw(0, 0, 78, 47, 0, 'h', x, y, 140, 160)
        if self.depth == 3:
            self.image_first.clip_draw(0, 0, 100, 100, x, y)
            self.image_forth.clip_draw(int(self.frame)*48, 0, 48, 45, x, y, 100, 100)


    def update(self):
        if self.depth == 3:
            self.frame = (self.frame + FRAMES_PER_ACTION * ACTION_PER_TIME * game_framework.frame_time) % 3
        cols = 10
        col = self.index % cols
        row = self.index // cols
        cx = col * self.TILE_W + self.TILE_W // 2
        cy = get_canvas_height() - (row * self.TILE_H + self.TILE_H // 2)

        # 1) depth == 4 : 위에 배치된 유닛 회복
        if self.depth == 4:
            HEAL_PER_SEC = 20.0
            dt = getattr(game_framework, 'frame_time', 0.0)
            if dt > 0.0:
                for layer in list(game_world.world):
                    for obj in list(layer):
                        try:
                            # 배치 유닛인지 간단히 판정: 위치가 이 타일 중심 근처, Hp / max_hp 보유
                            if not (hasattr(obj, 'Hp') and
                                    (hasattr(obj, 'max_hp') or hasattr(obj, 'MaxHp')) and
                                    hasattr(obj, 'x') and hasattr(obj, 'y')):
                                continue

                            # 이 타일 위인지 판정 (타일 경계 안)
                            if (cx - self.TILE_W // 2 <= obj.x <= cx + self.TILE_W // 2 and
                                    cy - self.TILE_H // 2 <= obj.y <= cy + self.TILE_H // 2):
                                max_hp = getattr(obj, 'max_hp', getattr(obj, 'MaxHp', None))
                                if max_hp is None:
                                    continue
                                new_hp = obj.Hp + HEAL_PER_SEC * dt
                                obj.Hp = min(new_hp, max_hp)
                        except Exception:
                            pass

        # 2) depth == 5 : 이 타일을 지나가는 몬스터 damage 플래그 ON
        if self.depth == 5:
            for layer in list(game_world.world):
                for obj in list(layer):
                    # 몬스터 / 보스 필터링
                    try:
                        from monster import Monster
                        from boss import Boss
                        if not isinstance(obj, (Monster, Boss)):
                            continue
                    except Exception:
                        # isinstance 실패 시 이름으로 fallback
                        name = obj.__class__.__name__
                        if name not in ('Monster', 'Boss'):
                            continue

                    if not (hasattr(obj, 'x') and hasattr(obj, 'y')):
                        continue

                    # 몬스터/보스가 이 타일 위에 있는지 체크
                    if (cx - self.TILE_W // 2 <= obj.x <= cx + self.TILE_W // 2 and
                            cy - self.TILE_H // 2 <= obj.y <= cy + self.TILE_H // 2):
                        try:
                            obj.damaged = True  # monster.py, boss.py 둘 다에서 사용하는 플래그
                        except Exception:
                            pass
