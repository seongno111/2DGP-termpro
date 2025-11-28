world = [[], [], [], [], [], [], [], []] # layers for game objects

def add_object(o, depth):
    try:
        nd = int(max(0, min(int(depth), len(world) - 1)))
    except Exception:
        nd = 0
    world[nd].append(o)

def add_objects(ol, depth):
    try:
        nd = int(max(0, min(int(depth), len(world) - 1)))
    except Exception:
        nd = 0
    world[nd] += ol
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
    handle_collisions()

def render():
    for layer in world:
        for o in layer:
            o.draw()



def clear():
    for layer in world:
        layer.clear()

def in_attack_range(a, b):
    try:
        left_a, bottom_a, right_a, top_a = a.get_at_bound()
    except Exception:
        return False
    try:
        left_b, bottom_b, right_b, top_b = b.get_bb()
    except Exception:
        return False

    if left_a > right_b:
        res = False
    elif right_a < left_b:
        res = False
    elif top_a < bottom_b:
        res = False
    elif bottom_a > top_b:
        res = False
    else:
        res = True

    # 힐러 관련 디버그 출력만 활성화 (로그 과다 방지)
    attacker_name = a.__class__.__name__ if hasattr(a, '__class__') else str(type(a))
    if attacker_name.upper() == 'HEALER' or getattr(a, 'number', None) == 5:
        print(f'in_attack_range: attacker={attacker_name} bounds=({left_a},{bottom_a},{right_a},{top_a}) target={b.__class__.__name__} bb=({left_b},{bottom_b},{right_b},{top_b}) -> {res}')

    return res

def collide(a, b):
    left_a, bottom_a, right_a, top_a = a.get_bb()
    left_b, bottom_b, right_b, top_b = b.get_bb()

    if left_a > right_b: return False
    if right_a < left_b: return False
    if top_a < bottom_b: return False
    if bottom_a > top_b: return False

    return True

collision_pairs = {}
collision_states = set()
def add_collision_pair(group, a, b):
    if group not in collision_pairs:
        print(f'Added new group {group}')
        collision_pairs[group] = [[],[]]
    # 중복 방지하여 추가
    if a:
        if a not in collision_pairs[group][0]:
            collision_pairs[group][0].append(a)
    if b:
        if b not in collision_pairs[group][1]:
            collision_pairs[group][1].append(b)
    return None

def handle_collisions():
    global collision_states
    for group, pairs in collision_pairs.items():
        left, right = (group.split(':') + ['', ''])[:2]
        left = left.strip().upper()
        right = right.strip().upper()

        RANGE_ATTACKERS = {'KNIGHT', 'ARCHER', 'VANGUARD'}

        use_range = ((left in RANGE_ATTACKERS and right == 'MONSTER') or
                     (right in RANGE_ATTACKERS and left == 'MONSTER'))

        # 안전히 복사본으로 순회
        for a in pairs[0][:]:
            if not any(a in layer for layer in world):
                # 만약 월드에서 제거된 객체 관련된 상태 제거
                # (a가 제거됐을 때 남아있는 collision_states 정리)
                for key in list(collision_states):
                    if key[0] == id(a):
                        collision_states.discard(key)
                continue
            for b in pairs[1][:]:
                if not any(b in layer for layer in world):
                    for key in list(collision_states):
                        if key[1] == id(b):
                            collision_states.discard(key)
                    continue
                try:
                    # 판단값 계산
                    if use_range:
                        in_range_a_b = in_attack_range(a, b)
                        in_range_b_a = in_attack_range(b, a)
                        phys_collide = collide(a, b)

                        # A 쪽 충돌 여부 판정
                        a_should = False
                        b_should = False
                        if phys_collide:
                            a_should = True
                            b_should = True
                        else:
                            if left in RANGE_ATTACKERS and in_range_a_b:
                                a_should = True
                            if right in RANGE_ATTACKERS and in_range_b_a:
                                b_should = True

                        key_a = (id(a), id(b), group, 'a')
                        key_b = (id(a), id(b), group, 'b')

                        # 시작: 아직 상태에 없으면 한 번만 호출
                        if a_should and key_a not in collision_states:
                            a.handle_collision(group, b)
                            collision_states.add(key_a)
                        # 종료: 상태에 있는데 더 이상 조건이 아니면 SEPARATE 발생
                        if not a_should and key_a in collision_states:
                            try:
                                a.state_machine.handle_state_event(('SEPARATE', None))
                            except Exception:
                                pass
                            collision_states.discard(key_a)

                        if b_should and key_b not in collision_states:
                            b.handle_collision(group, a)
                            collision_states.add(key_b)
                        if not b_should and key_b in collision_states:
                            try:
                                b.state_machine.handle_state_event(('SEPARATE', None))
                            except Exception:
                                pass
                            collision_states.discard(key_b)

                    else:
                        phys_collide = collide(a, b)
                        key_a = (id(a), id(b), group, 'a')
                        key_b = (id(a), id(b), group, 'b')

                        if phys_collide:
                            # 시작이면 한 번만 호출
                            if key_a not in collision_states:
                                a.handle_collision(group, b)
                                collision_states.add(key_a)
                            if key_b not in collision_states:
                                b.handle_collision(group, a)
                                collision_states.add(key_b)
                        else:
                            # 종료 시 SEPARATE 한 번만 호출
                            if key_a in collision_states:
                                try:
                                    a.state_machine.handle_state_event(('SEPARATE', None))
                                except Exception:
                                    pass
                                collision_states.discard(key_a)
                            if key_b in collision_states:
                                try:
                                    b.state_machine.handle_state_event(('SEPARATE', None))
                                except Exception:
                                    pass
                                collision_states.discard(key_b)

                except Exception:
                    # 안전하게 무시하되 상태 정리 필요 시 정리
                    pass
def change_object_depth(o, new_depth):
    """객체를 안전하게 다른 depth(레이어)로 이동시킴."""
    try:
        nd = int(max(0, min(new_depth, len(world) - 1)))
        # 현재 레이어에서 제거 (있다면)
        for layer in world:
            if o in layer:
                layer.remove(o)
                break
        # 새 레이어에 추가
        world[nd].append(o)
    except Exception:
        pass