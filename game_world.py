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

def _should_send_separate(attacker, target):
    """SEPARATE 이벤트를 보낼지 여부를 결정.

    기존에는 attacker.target 이 현재 target 이 아니면 SEPARATE 를 보내지 않도록 해
    여러 유닛이 한 몬스터를 동시에 때리거나, 다른 유닛이 막고 있는 동안에는
    공격 상태가 풀리는 일이 없도록 했지만,

    이제 요구사항에 맞게 "공격 범위(get_at_bound) 안에만 있으면"
    다른 유닛의 블록 상태와 관계없이 계속 공격하게 만들기 위해
    다음과 같이 조건을 단순화한다.
    """
    try:
        # 1) 공격 범위 안에 있다면 SEPARATE 를 보내지 않는다.
        #    -> 공격 상태 유지
        try:
            if in_attack_range(attacker, target):
                return False
        except Exception:
            # 범위 판정이 실패하면 아래 기본 규칙으로 진행
            pass

        # 2) 그 외의 경우에는 SEPARATE 를 허용해서 자연스럽게 Idle 등으로 돌아가게 한다.
        return True
    except Exception:
        # 예외 상황에서는 보수적으로 SEPARATE 를 허용
        return True

def handle_collisions():
    global collision_states
    for group, pairs in collision_pairs.items():
        left, right = (group.split(':') + ['', ''])[:2]
        left = left.strip().upper()
        right = right.strip().upper()

        RANGE_ATTACKERS = {'KNIGHT', 'ARCHER', 'VANGUARD'}

        use_range = ((left in RANGE_ATTACKERS and right == 'MONSTER') or
                     (right in RANGE_ATTACKERS and left == 'MONSTER'))

        for a in pairs[0][:]:
            if not any(a in layer for layer in world):
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
                    if use_range:
                        in_range_a_b = in_attack_range(a, b)
                        in_range_b_a = in_attack_range(b, a)
                        phys_collide = collide(a, b)

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

                        # 시작
                        if a_should and key_a not in collision_states:
                            a.handle_collision(group, b)
                            collision_states.add(key_a)
                        # 종료
                        if not a_should and key_a in collision_states:
                            if _should_send_separate(a, b):
                                try:
                                    a.state_machine.handle_state_event(('SEPARATE', None))
                                except Exception:
                                    pass
                            collision_states.discard(key_a)

                        if b_should and key_b not in collision_states:
                            b.handle_collision(group, a)
                            collision_states.add(key_b)
                        if not b_should and key_b in collision_states:
                            if _should_send_separate(b, a):
                                try:
                                    b.state_machine.handle_state_event(('SEPARATE', None))
                                except Exception:
                                    pass
                            collision_states.discard(key_b)
                    else:
                        # 기존 근접 충돌 로직은 그대로 두되,
                        # 종료 시에도 _should_send_separate 로 필터링
                        phys_collide = collide(a, b)
                        key_a = (id(a), id(b), group, 'a')
                        key_b = (id(a), id(b), group, 'b')

                        if phys_collide:
                            if key_a not in collision_states:
                                a.handle_collision(group, b)
                                collision_states.add(key_a)
                            if key_b not in collision_states:
                                b.handle_collision(group, a)
                                collision_states.add(key_b)
                        else:
                            if key_a in collision_states:
                                if _should_send_separate(a, b):
                                    try:
                                        a.state_machine.handle_state_event(('SEPARATE', None))
                                    except Exception:
                                        pass
                                collision_states.discard(key_a)
                            if key_b in collision_states:
                                if _should_send_separate(b, a):
                                    try:
                                        b.state_machine.handle_state_event(('SEPARATE', None))
                                    except Exception:
                                        pass
                                collision_states.discard(key_b)

                except Exception:
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