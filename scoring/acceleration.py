def calculate_volume_acceleration(candles):
    """
    Mesure l'accélération récente du volume.

    Compare :
        - volume très récent
        - volume de référence précédent

    L'objectif est de détecter une montée en puissance
    avant que le mouvement ne soit complètement développé.
    """

    if candles is None:
        return None

    if len(candles) < 20:
        return None

    volumes = [
        float(candle[5] or 0)
        for candle in candles
    ]

    # =========================================================
    # 1 — FILTRAGE DES VOLUMES NULS
    # =========================================================

    active = [
        v for v in volumes
        if v > 0
    ]

    if len(active) < 10:
        return None

    # =========================================================
    # 2 — VOLUME DE RÉFÉRENCE
    # =========================================================
    #
    # 10 périodes précédentes.
    #
    # Cela donne une référence relativement stable.

    reference = volumes[-20:-5]

    reference = [
        v for v in reference
        if v > 0
    ]

    if not reference:
        return None

    reference_average = (
        sum(reference)
        / len(reference)
    )

    if reference_average <= 0:
        return None

    # =========================================================
    # 3 — VOLUME RÉCENT
    # =========================================================
    #
    # On regarde les 5 dernières bougies.
    #
    # Cela rend le radar beaucoup plus réactif.

    recent = volumes[-5:]

    recent = [
        v for v in recent
        if v > 0
    ]

    if not recent:
        return None

    recent_average = (
        sum(recent)
        / len(recent)
    )

    if recent_average <= 0:
        return None

    # =========================================================
    # 4 — ACCÉLÉRATION
    # =========================================================

    acceleration = (
        recent_average
        / reference_average
    )

    # =========================================================
    # 5 — DÉTECTION D'ACCÉLÉRATION TRÈS RÉCENTE
    # =========================================================
    #
    # On compare également les 2 dernières bougies
    # à la moyenne de référence.
    #
    # Cela permet de repérer une explosion qui vient
    # tout juste de commencer.

    last_two = volumes[-2:]

    last_two = [
        v for v in last_two
        if v > 0
    ]

    if len(last_two) == 2:

        last_two_average = (
            sum(last_two)
            / 2
        )

        instant_acceleration = (
            last_two_average
            / reference_average
        )

        # Bonus progressif.
        #
        # On ne remplace pas l'accélération principale.
        # On la renforce seulement si le mouvement
        # s'accélère encore.

        if instant_acceleration >= 20:
            acceleration *= 1.30

        elif instant_acceleration >= 10:
            acceleration *= 1.20

        elif instant_acceleration >= 7:
            acceleration *= 1.15

        elif instant_acceleration >= 5:
            acceleration *= 1.10

    # =========================================================
    # 6 — LIMITE DE SÉCURITÉ
    # =========================================================
    #
    # Évite qu'une bougie aberrante produise un score
    # complètement disproportionné.

    acceleration = min(
        acceleration,
        100
    )

    return acceleration