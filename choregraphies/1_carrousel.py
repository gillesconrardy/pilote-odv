    # ======================================================================
    # 1. CARROUSEL : 4 véhicules sur un anneau de 8 cases, pas à pas
    #   Les véhicules occupent une case sur deux et avancent ensemble d'une case.
    #   Lent avec des pauses, puis rapide, puis demi-tour.
    # ======================================================================
    # mise en place
    mvc.move(30, 0,  20, 25,  10, 25,  0, 0)
    mvc.move(25, 5,  25, 25,  5, 25,  5, 5)
    mvc.wait_sync_ms(600)
    # un tour lent, case par case
    mvc.move(25, 15,  15, 25,  5, 15,  15, 5, speed=45)
    mvc.wait_sync_ms(150)
    mvc.move(25, 25,  5, 25,  5, 5,  25, 5, speed=45)
    mvc.wait_sync_ms(150)
    mvc.move(15, 25,  5, 15,  15, 5,  25, 15, speed=45)
    mvc.wait_sync_ms(150)
    mvc.move(5, 25,  5, 5,  25, 5,  25, 25, speed=45)
    mvc.wait_sync_ms(150)
    mvc.move(5, 15,  15, 5,  25, 15,  15, 25, speed=45)
    mvc.wait_sync_ms(150)
    mvc.move(5, 5,  25, 5,  25, 25,  5, 25, speed=45)
    mvc.wait_sync_ms(150)
    mvc.move(15, 5,  25, 15,  15, 25,  5, 15, speed=45)
    mvc.wait_sync_ms(150)
    mvc.move(25, 5,  25, 25,  5, 25,  5, 5, speed=45)
    mvc.wait_sync_ms(150)
    # un tour rapide
    mvc.move(25, 15,  15, 25,  5, 15,  15, 5)
    mvc.move(25, 25,  5, 25,  5, 5,  25, 5)
    mvc.move(15, 25,  5, 15,  15, 5,  25, 15)
    mvc.move(5, 25,  5, 5,  25, 5,  25, 25)
    mvc.move(5, 15,  15, 5,  25, 15,  15, 25)
    mvc.move(5, 5,  25, 5,  25, 25,  5, 25)
    mvc.move(15, 5,  25, 15,  15, 25,  5, 15)
    mvc.move(25, 5,  25, 25,  5, 25,  5, 5)
    mvc.wait_sync_ms(500)
    # demi-tour : un tour dans l'autre sens
    mvc.move(15, 5,  25, 15,  15, 25,  5, 15, speed=80)
    mvc.move(5, 5,  25, 5,  25, 25,  5, 25, speed=80)
    mvc.move(5, 15,  15, 5,  25, 15,  15, 25, speed=80)
    mvc.move(5, 25,  5, 5,  25, 5,  25, 25, speed=80)
    mvc.move(15, 25,  5, 15,  15, 5,  25, 15, speed=80)
    mvc.move(25, 25,  5, 25,  5, 5,  25, 5, speed=80)
    mvc.move(25, 15,  15, 25,  5, 15,  15, 5, speed=80)
    mvc.move(25, 5,  25, 25,  5, 25,  5, 5, speed=80)
    mvc.wait_sync_ms(500)
    # retour
    mvc.move(30, 0,  20, 25,  10, 25,  0, 0)
    mvc.move(30, 0,  20, 0,  10, 0,  0, 0)
    mvc.wait_sync_ms(1000)
