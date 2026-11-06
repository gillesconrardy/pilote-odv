    # ======================================================================
    # 3. TOURBILLONS : chaque véhicule tourne sur son propre petit cercle
    #   Quatre cercles de rayon 5 (move_circ), d'abord en décalage de phase comme
    #   des engrenages, puis tous en phase, puis en vague.
    # ======================================================================
    # mise en place
    mvc.move(30, 0,  20, 25,  10, 25,  0, 0)
    mvc.move(25, 10,  30, 25,  5, 20,  0, 5)
    mvc.wait_sync_ms(600)
    # engrenages : phases décalées de 90°
    mvc.move_circ(5, "CW", 720, 0, 90, 180, 270, speed=70)
    mvc.wait_sync_ms(400)
    # tous en phase
    mvc.move(25, 10,  25, 30,  5, 30,  5, 10)
    mvc.wait_sync_ms(300)
    mvc.move_circ(5, "CW", 720, 0, 0, 0, 0, speed=80)
    mvc.wait_sync_ms(400)
    # en vague (45° de décalage), sens inverse
    mvc.move(25, 0,  21.46, 21.46,  0, 25,  1.46, 8.54)
    mvc.wait_sync_ms(300)
    mvc.move_circ(5, "CCW", 720, 0, 45, 90, 135, speed=80)
    mvc.wait_sync_ms(400)
    # retour
    mvc.move(30, 0,  20, 25,  10, 25,  0, 0)
    mvc.move(30, 0,  20, 0,  10, 0,  0, 0)
    mvc.wait_sync_ms(1000)
