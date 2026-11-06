    # ======================================================================
    # 5. FORMATION : un bloc 2×2 qui voyage, explose et se reforme
    #   Les quatre véhicules collés se déplacent comme un seul objet (carré puis
    #   cercle avec move_circ), s'écartent vers les coins, tournent, et se regroupent.
    # ======================================================================
    # assemblage du bloc
    mvc.move(30, 0,  20, 0,  10, 10,  0, 10)
    mvc.move(30, 0,  20, 0,  30, 10,  20, 10)
    mvc.wait_sync_ms(600)
    # le bloc fait le tour du plateau
    mvc.move(10, 0,  0, 0,  10, 10,  0, 10, speed=70)
    mvc.move(10, 20,  0, 20,  10, 30,  0, 30, speed=70)
    mvc.move(30, 20,  20, 20,  30, 30,  20, 30, speed=70)
    mvc.move(30, 0,  20, 0,  30, 10,  20, 10, speed=70)
    mvc.wait_sync_ms(400)
    # le bloc décrit un cercle
    mvc.move(30, 10,  20, 10,  30, 20,  20, 20)
    mvc.move_circ(10, "CW", 360, 90, 90, 90, 90, speed=70)
    mvc.wait_sync_ms(300)
    # explosion vers les coins, deux fois
    mvc.move(20, 10,  10, 10,  20, 20,  10, 20)
    mvc.wait_sync_ms(400)
    mvc.move(30, 0,  0, 0,  30, 30,  0, 30, speed=60)
    mvc.wait_sync_ms(400)
    mvc.move(20, 10,  10, 10,  20, 20,  10, 20, speed=60)
    mvc.wait_sync_ms(400)
    mvc.move(30, 0,  0, 0,  30, 30,  0, 30, speed=100)
    mvc.wait_sync_ms(400)
    mvc.move(20, 10,  10, 10,  20, 20,  10, 20, speed=100)
    mvc.wait_sync_ms(300)
    mvc.move(30, 0,  0, 0,  30, 30,  0, 30)
    # ronde des coins
    mvc.move(0, 0,  0, 30,  30, 0,  30, 30, speed=90)
    mvc.move(0, 30,  30, 30,  0, 0,  30, 0, speed=90)
    mvc.move(30, 30,  30, 0,  0, 30,  0, 0, speed=90)
    mvc.move(30, 0,  0, 0,  30, 30,  0, 30, speed=90)
    mvc.wait_sync_ms(400)
    # regroupement et retour
    mvc.move(20, 10,  10, 10,  20, 20,  10, 20)
    mvc.move(30, 0,  20, 0,  30, 10,  20, 10)
    mvc.move(30, 0,  20, 0,  10, 10,  0, 10)
    mvc.move(30, 0,  20, 0,  10, 0,  0, 0)
    mvc.wait_sync_ms(1000)
