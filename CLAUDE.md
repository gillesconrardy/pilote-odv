# Pilote ODV — fiche de reprise du projet

Projet de Gilles : 4 véhicules LEGO omnidirectionnels (ODV, configuration 05 : base 4×4, 4 véhicules)
pilotés par des Technic Hub sous Pybricks. **Toujours répondre en français.** Gilles est sur Windows ;
il pilote depuis Chrome sur Android (Safari/Chrome iPhone n'ont pas le Bluetooth web).

- Page en ligne : https://gillesconrardy.github.io/pilote-odv/ (GitHub Pages, branche `main`, racine)
- Simulateur : https://gillesconrardy.github.io/pilote-odv/simulateur/
- Dossier local de Gilles : `C:\Gestion\lego_Vehicle` (copie du projet dans `Pilote ODV\`)
- Noms Bluetooth des hubs : `vehicle1`, `vehicle2`, `vehicle3`, `vehicle4` (sans espace)
- Ne publier (git push) que quand Gilles le demande.

## Le matériel et le code d'origine
`choregraphies/0_origine_ODV_Cfg05_Vehicle01.py` = programme d'origine (4 fichiers identiques sauf
`VEHICLE_ID`). Unités : pas de grille, `GEAR_RATIO` 80°/pas, vitesse max 1400°/s, pas de 4 ms.
Repère : origine O en haut à droite (clôture en haut et à droite, picots rouges au coin), +X vers la
gauche, +Y vers le bas. Positions de départ : V1 (30,0), V2 (20,0), V3 (10,0), V4 (0,0).
Emprise d'un véhicule : 10 pas (Chebyshev < 10 = chevauchement ; 10 = côte à côte, autorisé).
Moteurs : X port C, Y port A. Recalage (homing) contre la clôture : un véhicule à la fois, dans l'ordre 1→4.

## Architecture
1. **`src/core.js`** : analyse les commandes `mvc.move / move_circ / wait_sync_ms` (boucles `for` dépliées,
   `while True` joué une fois) et les simule exactement comme le code d'origine ; détecte les collisions.
   Partagé par le simulateur et Pilote ODV.
2. **`src/odvgen.js`** : transforme une liste de chorégraphies en ligne du temps par véhicule
   (segments de 14 octets : attente / ligne / arc, coordonnées ×100, durée ms) et génère le programme
   Pybricks de chaque véhicule à partir de `src/runtime.py` (marqueurs `%VID% %GEN% %DATA%`…).
   Écart avec la simulation d'origine ≤ 0,1 pas.
3. **`src/runtime.py`** : programme qui tourne sur les hubs.
   - Horloge de spectacle commune : `v = V + R·(t − A)`, bornée par `S` ; R = 1 lecture, 0 pause,
     −1 retour, 9 urgence. Le véhicule 4 (émetteur) diffuse `(t+30, A, V, R+1+16·GEN, S)` toutes les 250 ms
     sur le canal BLE 1 ; les autres se synchronisent (même estimateur que l'original : max des écarts,
     pente après 60 s) et ignorent un émetteur d'une autre version `GEN`.
   - Les commandes s'appliquent 1 s plus tard (`LEAD`) pour que les 4 réagissent ensemble.
   - Commandes reçues sur stdin, une par ligne : `p` lecture, `z` pause, `h` stop + retour au départ
     (retrace la chorégraphie en cours vers son début, ou va à sa fin si plus court), `x` urgence
     (véhicule 4) ; `M` prise en main, `Gx,y` cible (×100), `Q` rendre la main (tous les véhicules).
   - Manuel : déplacement limité à 8 pas/s ; radio allégée sur le V4 pendant le manuel.
   - Le V4 imprime `ST <P|F|B|S> <w> <chor> <attente> <mV> <GEN>` toutes les 400 ms.
4. **`src/page.html`** : Pilote ODV (onglets Programme / Envoi / Pilotage). Compile avec
   `@pybricks/mpy-cross-v6@2.0.0` (chargé depuis jsDelivr, ou esm.sh en secours), envoie au hub
   (format multi-mpy6 : taille u32 + `__main__\0` + mpy ; commandes 0 stop, 3 meta, 4 RAM, 1 start,
   6 stdin), service Pybricks `c5f50001-8280-46da-89f4-6d8051e4aeef`.
   Fonctions : choix/ordre des chorégraphies, boucle, recalage, « Mettre à jour les 4 véhicules »
   (retour au départ → arrêt V4 → envoi 1,2,3,4 sans recalage), « Tout déconnecter » (vérifié),
   reconnexion automatique, joystick pour le véhicule 4 uniquement (anti-collision et bornes 0..30).
5. **`simulateur/template.html`** : simulateur visuel (plateau blanc à picots, véhicules gris
   « 01…04 » d'après la photo du montage), lecture, détection des chevauchements, édition du code.

## Construire, tester, publier
- `python build.py` → régénère `index.html` et `simulateur/index.html` (les chorégraphies sont lues
  dans `choregraphies/`). Les pages générées sont autonomes (un seul fichier).
- Tests (dans `tests/`) :
  - `node mkprogs.js <fichiers.py> <boucle 0|1> <recalage 0|1> <gen>` puis
    `python harness.py progs.json '<script>' <fin_ms>` : 4 hubs simulés (horloges décalées, latence
    radio, paquets perdus) ; `python analyze.py` vérifie synchro, pause, retour, urgence.
  - `t_page2.py`, `t_manual.py`, `t_joy.py` : Playwright + faux Bluetooth (envoi, mise à jour, joystick).
  - `sim_model.py` : modèle Python de référence des mouvements.
- Publier : commit de `index.html` (+ `simulateur/`) sur `main` ; en ligne en 1–2 min.
- Nouvelle chorégraphie : fichier de lignes `mvc.*` indentées de 4 espaces dans `choregraphies/`,
  partant de et revenant à (30,0)(20,0)(10,0)(0,0), sans chevauchement ; l'ajouter à `CHORS` dans
  `build.py`. `gen_cinq.py` / `gen_vague_spirale.py` montrent comment les générer et les valider.

## Non vérifié sur le vrai matériel (à surveiller)
- Paramètre `reset_angle=` de `Motor` (utilisé sans recalage) et taille max du programme par hub.
- Ressenti du joystick (8 envois/s) ; charge radio du V4 connecté + diffusion.
- Gilles a signalé : « Stop et retour » OK après coup ; perte de liaison V4 pendant le joystick
  (corrigé par allègement radio + reconnexion auto, à confirmer) ; déconnexion difficile (corrigée,
  à confirmer).

## Idées en attente
- Adoucir le demi-tour du « retour au départ » (courte pause avant de repartir en arrière).
- Allonger `LEAD` si un véhicule réagit en retard.
