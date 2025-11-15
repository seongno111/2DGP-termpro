world = [[], [], [], [], [], [], [], []] # layers for game objects

def add_object(o, depth):
    world[depth].append(o)

def add_objects(ol, depth):
    world[depth] += ol

def remove_object(o):
    for layer in world:
        if o in layer:
            layer.remove(o)
            return

    raise Exception("World 에 존재하지 않는 오브젝트를 지우려고 시도함")

def remove_collision_object(o):
    for pairs in collision_pairs.values():
        if o in pairs[0]:
            pairs[0].remove(o)
        if o in pairs[1]:
            pairs[1].remove(o)


def update():
    for layer in world:
        for o in layer:
            o.update()

def render():
    for layer in world:
        for o in layer:
            o.draw()
    handle_collisions()


def clear():
    for layer in world:
        layer.clear()

def in_attack_range(a, b):
    """
    a: 공격자(예: Knight) - must implement get_at_bound()
    b: 대상(예: Monster) - must implement get_bb()
    반환: 대상이 공격자의 get_at_bound() 범위에 들어있으면 True
    """
    try:
        left_a, bottom_a, right_a, top_a = a.get_at_bound()
    except Exception:
        return False
    try:
        left_b, bottom_b, right_b, top_b = b.get_bb()
    except Exception:
        return False

    if left_a > right_b: return False
    if right_a < left_b: return False
    if top_a < bottom_b: return False
    if bottom_a > top_b: return False
    return True

def collide(a, b):
    left_a, bottom_a, right_a, top_a = a.get_bb()
    left_b, bottom_b, right_b, top_b = b.get_bb()

    if left_a > right_b: return False
    if right_a < left_b: return False
    if top_a < bottom_b: return False
    if bottom_a > top_b: return False

    return True

collision_pairs = {}
def add_collision_pair(group, a, b):
    if group not in collision_pairs:
        print(f'Added new group {group}')
        collision_pairs[group] = [[],[]]
    if a:
        collision_pairs[group][0].append(a)
    if b:
        collision_pairs[group][1].append(b)

    return None

def handle_collisions():
    for group, pairs in collision_pairs.items():
        left, right = (group.split(':') + ['', ''])[:2]
        left = left.strip().upper()
        right = right.strip().upper()

        # 범위 판정을 사용할 공격자 그룹 목록 (필요시 확장)
        RANGE_ATTACKERS = {'KNIGHT', 'ARCHER'}

        use_range = ((left in RANGE_ATTACKERS and right == 'MONSTER') or
                     (right in RANGE_ATTACKERS and left == 'MONSTER'))

        for a in pairs[0]:
            for b in pairs[1]:
                try:
                    if use_range:
                        # 범위 판정과 물리 충돌을 따로 계산
                        in_range_a_b = in_attack_range(a, b)
                        in_range_b_a = in_attack_range(b, a)
                        phys_collide = collide(a, b)

                        if phys_collide:
                            # 실제 충돌이면 양쪽 모두 알림
                            a.handle_collision(group, b)
                            b.handle_collision(group, a)
                        else:
                            # 범위에만 들어간 경우: 공격자 쪽(왼/오른쪽 중 RANGE_ATTACKER인 쪽)만 알림
                            if left in RANGE_ATTACKERS and in_range_a_b:
                                a.handle_collision(group, b)
                            if right in RANGE_ATTACKERS and in_range_b_a:
                                b.handle_collision(group, a)
                    else:
                        if collide(a, b):
                            a.handle_collision(group, b)
                            b.handle_collision(group, a)
                except Exception:
                    pass