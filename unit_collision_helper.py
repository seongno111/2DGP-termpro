import game_world

def handle_unit_vs_monster_collision(unit, group, other):
    if other is None:
        return False
    try:
        if not any(other in layer for layer in game_world.world):
            return False
    except Exception:
        return False

    if getattr(unit, 'Hp', 1) <= 0:
        return False

    left, right = (group.split(':') + ['', ''])[:2]
    left = left.strip().upper()
    right = right.strip().upper()

    if not (
        (left == unit.__class__.__name__.upper() and right == 'MONSTER') or
        (right == unit.__class__.__name__.upper() and left == 'MONSTER')
    ):
        return False

    # 이미 다른 유닛이 저지 중이면 스킵
    if getattr(other, '_blocked_by', None) not in (None, unit):
        return False

    now_stop = getattr(unit, 'now_stop', 0)
    stop = getattr(unit, 'stop', 0)
    if now_stop >= stop:
        # 슬롯 여유 없음 -> 타겟/이벤트 건드리지 않음
        return False

    # 여기까지 오면 실제로 슬롯을 새로 소비
    try:
        other._blocked_by = unit
    except Exception:
        pass
    try:
        unit.now_stop = now_stop + 1
    except Exception:
        pass

    if getattr(unit, 'target', None) is None:
        try:
            unit.target = other
        except Exception:
            pass

    sm = getattr(unit, 'state_machine', None)
    if sm is not None:
        try:
            sm.handle_state_event(('COLLIDE', group, other))
        except Exception:
            pass

    # 슬롯을 실제로 썼다는 의미로 True 반환
    return True