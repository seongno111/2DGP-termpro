import game_world


def update_link_states_for_knight_archer():
    """Knight와 Archer가 동시에 필드에 존재하면 거리와 상관없이 서로 linked 를 True 로 맞춘다.

    여기서는 Knight/Archer 클래스를 직접 import 하지 않고,
    obj.__class__.__name__ 문자열을 사용해 타입을 구분함으로써
    import 순환 및 'cannot import name' 문제를 피한다.
    """
    try:
        knights = []
        archers = []
        for layer in game_world.world:
            for obj in layer:
                name = obj.__class__.__name__
                if name == 'Knight':
                    knights.append(obj)
                elif name == 'Archer':
                    archers.append(obj)
    except Exception:
        return

    if not knights or not archers:
        for k in knights:
            k.linked = False
        for a in archers:
            a.linked = False
        return

    # 둘 다 하나 이상 존재하면 전부 링크 ON
    for k in knights:
        k.linked = True
    for a in archers:
        a.linked = True
