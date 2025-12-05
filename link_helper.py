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


def update_link_states_for_dptank_vanguard():
    """Dptank와 Vanguard가 동시에 필드에 존재하면 거리와 상관없이 서로 linked 를 True 로 맞춘다.

    Knight-Archer 링크 방식과 동일하게, 클래스 이름 문자열로 타입을 구분해
    import 순환 문제를 피한다.
    """
    try:
        dps = []
        vgs = []
        for layer in game_world.world:
            for obj in layer:
                name = obj.__class__.__name__
                if name == 'Dptank':
                    dps.append(obj)
                elif name == 'Vanguard':
                    vgs.append(obj)
    except Exception:
        return

    # 둘 중 하나라도 없으면 둘 다 False
    if not dps or not vgs:
        for u in dps:
            u.linked = False
        for u in vgs:
            u.linked = False
        return

    # 둘 다 하나 이상 존재하면 전부 링크 ON
    for u in dps:
        u.linked = True
    for u in vgs:
        u.linked = True


def update_link_states_for_hptank_healer():
    """Hptank와 Healer가 동시에 필드에 존재하면 거리와 상관없이 서로 linked 를 True 로 맞춘다.

    다른 링크 함수들처럼 클래스 이름 문자열로 타입을 구분해
    import 순환 문제를 피한다.
    """
    try:
        hps = []
        heals = []
        for layer in game_world.world:
            for obj in layer:
                name = obj.__class__.__name__
                if name == 'Hptank':
                    hps.append(obj)
                elif name == 'Healer':
                    heals.append(obj)
    except Exception:
        return

    # 둘 중 하나라도 없으면 둘 다 False
    if not hps or not heals:
        for u in hps:
            u.linked = False
        for u in heals:
            u.linked = False
        return

    # 둘 다 하나 이상 존재하면 전부 링크 ON
    for u in hps:
        u.linked = True
    for u in heals:
        u.linked = True
