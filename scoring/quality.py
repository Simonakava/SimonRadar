def calculate_quality(
    volume_ratio,
    momentum,
    acceleration,
    breakout,
    risk_percent
):
    """
    QUALITÉ DU SIGNAL /100

    Le score mesure la puissance.
    La qualité mesure si cette puissance est
    exploitable sans être complètement surchauffée.
    """

    quality = 0.0

    # ---------------------------------------------------------
    # VOLUME
    # ---------------------------------------------------------

    if volume_ratio >= 10:
        quality += 20
    elif volume_ratio >= 5:
        quality += 16
    elif volume_ratio >= 3:
        quality += 12
    elif volume_ratio >= 2:
        quality += 7
    elif volume_ratio >= 1.5:
        quality += 3

    # ---------------------------------------------------------
    # ACCÉLÉRATION
    # ---------------------------------------------------------

    if acceleration >= 10:
        quality += 20
    elif acceleration >= 7:
        quality += 17
    elif acceleration >= 5:
        quality += 14
    elif acceleration >= 3:
        quality += 10
    elif acceleration >= 2:
        quality += 5

    # ---------------------------------------------------------
    # MOMENTUM
    # ---------------------------------------------------------

    if 3 <= momentum <= 15:
        quality += 20
    elif 15 < momentum <= 20:
        quality += 17
    elif 2 <= momentum < 3:
        quality += 13
    elif 0 <= momentum < 2:
        quality += 6
    elif momentum > 20:
        quality += 10
    else:
        quality -= 10

    # ---------------------------------------------------------
    # BREAKOUT
    # ---------------------------------------------------------

    if 0.5 <= breakout <= 4:
        quality += 20
    elif 4 < breakout <= 7:
        quality += 17
    elif breakout > 7:
        quality += 10
    elif breakout > 0:
        quality += 8
    else:
        quality -= 10

    # ---------------------------------------------------------
    # RISQUE
    # ---------------------------------------------------------

    if risk_percent <= 1:
        quality += 20
    elif risk_percent <= 1.5:
        quality += 17
    elif risk_percent <= 2:
        quality += 14
    elif risk_percent <= 3:
        quality += 10
    elif risk_percent <= 5:
        quality += 5
    else:
        quality -= 5

    return round(
        max(0, min(100, quality))
    )