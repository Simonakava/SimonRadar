def calculate_entry_quality(
    score,
    volume_ratio,
    momentum,
    acceleration,
    breakout,
    risk_percent
):
    """
    Qualité réelle de l'entrée /100.

    Cherche à distinguer :
    - une crypto déjà très étendue
    - d'une vraie configuration d'entrée
    """

    quality = 0

    # =====================================================
    # VOLUME — 20 POINTS
    # =====================================================

    if volume_ratio >= 20:
        quality += 20
    elif volume_ratio >= 10:
        quality += 17
    elif volume_ratio >= 5:
        quality += 14
    elif volume_ratio >= 3:
        quality += 10
    elif volume_ratio >= 2:
        quality += 6

    # =====================================================
    # ACCÉLÉRATION — 20 POINTS
    # =====================================================

    if acceleration >= 15:
        quality += 20
    elif acceleration >= 10:
        quality += 17
    elif acceleration >= 7:
        quality += 14
    elif acceleration >= 5:
        quality += 11
    elif acceleration >= 3:
        quality += 7
    elif acceleration >= 2:
        quality += 4

    # =====================================================
    # MOMENTUM — 20 POINTS
    # =====================================================

    if 3 <= momentum <= 15:
        quality += 20

    elif 2 <= momentum < 3:
        quality += 15

    elif 15 < momentum <= 20:
        quality += 15

    elif 1 <= momentum < 2:
        quality += 9

    elif 20 < momentum <= 25:
        quality += 8

    elif momentum > 25:
        quality += 2

    elif momentum < 0:
        quality -= 15

    # =====================================================
    # BREAKOUT — 20 POINTS
    # =====================================================

    if 1 <= breakout <= 5:
        quality += 20

    elif 0.5 <= breakout < 1:
        quality += 15

    elif 5 < breakout <= 8:
        quality += 13

    elif breakout > 8:
        quality += 5

    elif 0 < breakout < 0.5:
        quality += 8

    elif breakout <= 0:
        quality -= 10

    # =====================================================
    # RISQUE — 10 POINTS
    # =====================================================

    if risk_percent <= 1:
        quality += 10

    elif risk_percent <= 1.5:
        quality += 8

    elif risk_percent <= 2:
        quality += 6

    elif risk_percent <= 2.5:
        quality += 4

    elif risk_percent <= 3:
        quality += 2

    else:
        quality -= 5

    # =====================================================
    # COHÉRENCE — 10 POINTS
    # =====================================================

    confirmations = 0

    if volume_ratio >= 3:
        confirmations += 1

    if acceleration >= 3:
        confirmations += 1

    if momentum >= 2:
        confirmations += 1

    if breakout > 0:
        confirmations += 1

    if confirmations == 4:
        quality += 10

    elif confirmations == 3:
        quality += 6

    elif confirmations == 2:
        quality += 3

    # =====================================================
    # MALUS SURCHAUFFE
    # =====================================================

    if momentum >= 25:
        quality -= 10

    elif momentum >= 20:
        quality -= 5

    if breakout >= 10:
        quality -= 5

    # =====================================================
    # BONUS SCORE GLOBAL
    # =====================================================

    if score >= 90:
        quality += 5

    elif score >= 80:
        quality += 3

    # =====================================================
    # LIMITES
    # =====================================================

    quality = max(0, quality)
    quality = min(100, quality)

    return round(quality)