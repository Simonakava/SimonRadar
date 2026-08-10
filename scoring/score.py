def calculate_score(
    volume_ratio,
    momentum,
    acceleration,
    breakout
):
    """
    SCORE SIMON RADAR /100

    Mesure la puissance du mouvement actuel :
    - volume inhabituel
    - accélération du volume
    - momentum
    - breakout
    - cohérence globale
    """

    score = 0.0

    # =========================================================
    # VOLUME — 25 pts
    # =========================================================

    if volume_ratio >= 50:
        score += 25
    elif volume_ratio >= 30:
        score += 23
    elif volume_ratio >= 20:
        score += 21
    elif volume_ratio >= 15:
        score += 19
    elif volume_ratio >= 10:
        score += 17
    elif volume_ratio >= 7:
        score += 15
    elif volume_ratio >= 5:
        score += 12
    elif volume_ratio >= 3:
        score += 9
    elif volume_ratio >= 2:
        score += 5
    elif volume_ratio >= 1.5:
        score += 2

    # =========================================================
    # ACCELERATION — 20 pts
    # =========================================================

    if acceleration >= 20:
        score += 20
    elif acceleration >= 15:
        score += 18
    elif acceleration >= 10:
        score += 16
    elif acceleration >= 7:
        score += 14
    elif acceleration >= 5:
        score += 11
    elif acceleration >= 3:
        score += 8
    elif acceleration >= 2:
        score += 4
    elif acceleration >= 1.5:
        score += 2

    # =========================================================
    # MOMENTUM — 20 pts
    # =========================================================

    if momentum >= 20:
        score += 20
    elif momentum >= 15:
        score += 19
    elif momentum >= 10:
        score += 17
    elif momentum >= 7:
        score += 15
    elif momentum >= 5:
        score += 13
    elif momentum >= 3:
        score += 10
    elif momentum >= 2:
        score += 7
    elif momentum >= 1:
        score += 4
    elif momentum >= 0:
        score += 1
    else:
        score -= 12

    # =========================================================
    # BREAKOUT — 25 pts
    # =========================================================

    if breakout >= 6:
        score += 25
    elif breakout >= 4:
        score += 23
    elif breakout >= 3:
        score += 21
    elif breakout >= 2:
        score += 18
    elif breakout >= 1:
        score += 14
    elif breakout >= 0.5:
        score += 10
    elif breakout > 0:
        score += 5
    elif breakout == 0:
        score += 1
    else:
        score -= 15

    # =========================================================
    # COHÉRENCE — 10 pts
    # =========================================================

    factors = 0

    if volume_ratio >= 3:
        factors += 1

    if acceleration >= 3:
        factors += 1

    if momentum >= 2:
        factors += 1

    if breakout > 0:
        factors += 1

    if factors == 4:
        score += 10
    elif factors == 3:
        score += 7
    elif factors == 2:
        score += 4
    elif factors == 1:
        score += 1

    # =========================================================
    # BONUS VOLUME + ACCÉLÉRATION
    # =========================================================

    if volume_ratio >= 15 and acceleration >= 10:
        score += 5

    elif volume_ratio >= 10 and acceleration >= 7:
        score += 3

    # =========================================================
    # MALUS SURCHAUFFE
    # =========================================================

    if momentum >= 30:
        score -= 8

    elif momentum >= 25:
        score -= 5

    elif momentum >= 20:
        score -= 2

    # =========================================================
    # LIMITES
    # =========================================================

    return round(
        max(0, min(100, score))
    )