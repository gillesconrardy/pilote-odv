# F4 Square (ex-Pilote ODV) — fiche de reprise du projet

Projet de Gilles : 4 véhicules LEGO omnidirectionnels (ODV, configuration 05 : base 4×4, 4 véhicules)
pilotés par des Technic Hub sous Pybricks. **Toujours répondre en français.** Gilles est sur Windows ;
il pilote depuis Chrome sur Android (Safari/Chrome iPhone n'ont pas le Bluetooth web).

- Page en ligne : https://gillesconrardy.github.io/pilote-odv/ (GitHub Pages, branche `main`, racine)
- Simulateur : https://gillesconrardy.github.io/pilote-odv/simulateur/
- Dossier local de Gilles : `C:\Gestion\lego_Vehicle` (copie du projet dans `Pilote ODV\`)
- Noms Bluetooth des hubs : `vehicle1`, `vehicle2`, `vehicle3`, `vehicle4` (sans espace)
- Ne publier (git push) que quand Gilles le demande.
- Nom de l'application : **F4 Square** (depuis v1.29 ; titre, en-tête, manifest, simulateur), écrit en police **Russo One** (Google Fonts), « F4 » en clair et « SQUARE » en ambre (`h1.brand`). Le dépôt et l'adresse restent `pilote-odv`.

**Couleurs des véhicules** : V1 bleu, V2 orange, V3 vert, **V4 rouge depuis v1.87** (demande de Gilles ; `--v4` dans la page et le simulateur, `VHUE`, comète de la matrice, plan de Mise en place).

## Le matériel et le code d'origine
`choregraphies/0_origine_ODV_Cfg05_Vehicle01.py` = programme d'origine (4 fichiers identiques sauf
`VEHICLE_ID`). Unités : pas de grille, `GEAR_RATIO` 80°/pas, vitesse max 1400°/s, pas de 4 ms.
Repère : origine O en haut à droite (clôture en haut et à droite, picots rouges au coin), +X vers la
gauche, +Y vers le bas. Positions de départ : V1 (30,0), V2 (20,0), V3 (10,0), V4 (0,0).
Plateau : 49 cm de côté = 40 pas → 1 pas = 12,25 mm (compteurs de distance/vitesse de l'onglet Pilotage). Emprise d'un véhicule : 10 pas (Chebyshev < 10 = chevauchement ; 10 = côte à côte, autorisé).
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
     (véhicule 4), `e` fin des programmes des véhicules 1 à 3 (ils s'arrêtent sur place pour redevenir
     visibles en Bluetooth : un hub qui exécute un programme n'est pas joignable) ; `M` prise en main, `Gx,y` cible (×100), `Q` rendre la main (tous les véhicules).
   - Manuel : vitesse choisie au curseur dans la page (1 à 16 pas/s), plafond hub 16 pas/s ; radio allégée sur le V4.
   - Télécommande LEGO (V4, en manuel seulement) : `C` la connecte (Remote, 6 s), `O1x,y`..`O3x,y` donnent
     la position des 3 autres (anti-collision côté hub), `V<pas/s×100>` la vitesse ; boutons gauche = moteur
     port C (X : + → +X), droite = port A (Y : + → −Y), comme le programme télécommande de Gilles ; une cible
     `G` de l'appli est prioritaire 400 ms ; le V4 imprime `POS x y <bouge>` (×100) et `RC 0|1`. **Bug v1.69–v1.85 corrigé en v1.86** : les boutons étaient ignorés dès que `hand` était vrai (mode pousser actif d'office) ; maintenant acceptés en `h_mode == 2` hors glissade et hors main pendant le spectacle (`sp`).
   - **Évitement en conduite manuelle — ANNULÉ en v1.59** (bug signalé par Gilles en prise en main du V4) : l'appli n'envoie plus `E` ;
     `evade_tick` et la commande `E` sont entre marqueurs `#[JEUX` (retirés du programme). « Suivre la main » marche sans lui (jeu 0).
     Ancienne description : après `M`, l'appli envoie `E` (→ `EON`, jeu 5). Le V4 calcule V1..V3
     (`evade_tick`) : à moins de 14 pas du V4 (cible ou position), un véhicule s'écarte (à l'opposé, sinon sur un axe, sinon de
     côté ; `b_ok` : 11 pas, prévu ET d'il y a 250–500 ms) à 1,4× la vitesse manuelle (≤ 16,5 pas/s) ; à plus de 17 pas, il
     revient doucement à sa place (en restant à 15 du V4). Diffusion et `JP` comme les jeux. Le V4 ne coupe pas de coin
     (`v4_ok`) et sa cible évite aussi les positions anciennes (`free_at`, 10,5). Les suiveurs ne coupent pas le coin d'un autre
     suiveur en rattrapant leur retard (`rx_ok`, cibles `RXO`). `Q` refusé (BUSY) en jeu 5 : « Rendre la main » envoie `K`
     (→ `JRET`), range par `tidyPlan` + `W…`/`Z` (V4 compris), puis `G` + `Q`. Appli : `M.evade`, `M.home3`, `M.tidying`.
     Test : `t_evade.py` ; harness : physiquement jamais < 10 pas.
   - **ORIENTATION DU CAPTEUR (v1.70, précisé par Gilles)** : le capteur est sur le **côté droit du V4, au-dessus de la clôture**
     (il ne la voit pas) et regarde vers **−X** (la main se présente à l'extérieur du plateau, à droite). Tout ce qui suit a été
     adapté : suivre = avance/recule sur X (loin → −X), recherche latérale sur Y ; pousser = vers +X ou en biais/haut/bas (jamais −X) ;
     filtre « véhicule devant » = même ligne (|Δy| < 10) et x plus petit ; `sonarMask` idem ; `drawSensor` dessine le faisceau vers
     la droite de l'écran (rotation −90°). Les descriptions « +Y / avant du plateau » plus bas datent d'avant.
   - **Suivre la main** (v1.56, capteur de distance LEGO `UltrasonicSensor` sur le **port B du V4**, tourné vers l'avant du
     plateau = +Y) : bouton « ✋ Suivre la main » (Pilotage, en conduite manuelle avec évitement) → `H1` (→ `HON`, ou `HNO` si pas de
     capteur) / `H0`. `hand_tick` : médiane des 4 dernières mesures (toutes les 40 ms) ; < 6 cm recule à 16 pas/s, 6–13 cm recule
     (proportionnel), 13–17 cm immobile, 17–30 cm avance (proportionnel), > 30 cm ou véhicule reconnu devant (même colonne, distance
     attendue ± 25 mm) → arrêt ; ne bouge que sur Y, dans 0..30, avec `free_at`. Joystick, `G` et télécommande ignorés pendant ce
     temps. Le V4 imprime `HD <mm>` toutes les 250 ms (affiché sous le bouton), yeux du capteur allumés quand une main est vue.
     **Latéral avec un seul capteur** : si la main disparaît > 150 ms (et que ce n'est pas un véhicule), recherche sur le côté
     autour du dernier x où elle était vue : +4, −4, +8, −8, +12, −12 pas (× `h_dir`, le côté où on l'a retrouvée la dernière
     fois), à 10 pas/s, sauf si bloqué (`free_at`) ; retrouvée → reprend le suivi ; sinon attend (`h_state` 0 suit / 1 cherche /
     2 attend, envoyé dans `HD <mm> <état>`). Harness : `HARNESS_SONAR='[[t_ms, mm], …]'`, ou `HARNESS_HAND='[[t_ms, x_main, mm], …]'`
     (main vue si |x V4 − x main| ≤ 2,5 pas).
   - **Pousser avec la main** (v1.68, remplace « Piloter avec la main » de v1.67 jugé trop compliqué ; bouton « 👋 Pousser avec la main »
     `#axGo`, `H2` → `HON`, `hand_tick` avec `h_mode = 2`) : main à < 5 cm du capteur → glissade (`h_v` = 16 pas/s, freinage
     exponentiel 600 ms, ≈ 10 pas) dans la direction la plus dégagée qui ne va pas vers la main : arrière, biais arrière, gauche ou
     droite (`free_at` pas à pas sur 10 pas, bonus aux directions vers l'arrière) ; imprime `PU` ; bloqué → arrêt. Un véhicule à
     < 6 pas juste devant n'est pas une main. `HD <mm> <5|6>` (5 glisse, 6 attend). Le joystick reste utilisable dans ce mode
     (`G` accepté quand il ne glisse pas) ; `POS` toutes les 200 ms en mode main. Test : `t_push.py` + harness.
     **Depuis v1.69** (demande de Gilles) : actif par défaut dès la prise en main du V4 (`manGo` → `handStart(2, true)`, silencieux
     si pas de capteur) ; la main doit rester **2 s** à < 5 cm (`h_lost` = début de l'appui, `HD … 7` pendant l'attente : compte à
     rebours sous le bouton, anneau rouge qui se remplit sur le plateau, `SNS.hold`). Quitter « Suivre la main » revient à « Pousser ».
     **Depuis v1.71** : seuil **10 cm pendant 1 s** (au lieu de 5 cm / 2 s) ; un véhicule à < 10 pas juste à droite n'est pas une main.
     **Depuis v1.72 (demande de Gilles) : plus de boutons** (`#handGo`, `#axGo` masqués) ; le mode `H2` est activé seul à la prise
     en main. Pas de suivi de la main (Gilles : « entre 10 et 30 cm, il ne faut rien faire »). Main < 10 cm pendant 1 s → **au hasard**
     (`local % 2`) : poussée (s'écarte) ou **attaque** : il fonce vers la main (−X, `PU -100 0`) s'il a la place (x ≥ 1,5), LED du hub
     rouge pendant la glissade puis `VCOL`, yeux du capteur qui clignotent (le capteur n'a que des LED blanches). Appli : flèche et ondes
     rouges, « Attaque ! » sous Conduite manuelle.
     **Depuis v1.73** : la poussée part dans une direction **au hasard** (`urandom.randint`) parmi les 7 directions (tout sauf −X pur,
     réservé à l'attaque) qui ont au moins 4 pas de place, sinon la plus dégagée ; l'attaque = `h_gx == -1` (exactement −X).
     **v1.75** : « Rendre la main » coupe d'abord le capteur (`H0`, `M.hand = false`), sinon le V4 n'acceptait pas le retour (bug Gilles).
     **Sur le plateau de Pilotage** (`drawSensor`, état `SNS`, alimenté par `DS`/`HD` et `PU <gx×100> <gy×100>`) : faisceau ambre
     vers l'avant du V4 (40 cm ≈ 32,6 pas), écho + point qui pulse là où il voit quelque chose (rouge < 5 cm) ; à la poussée,
     ondes de choc à l'endroit de la main, traînée derrière le V4 et flèche dans le sens de la glissade (1 s).
   - **Distance du capteur dans Pilotage** (v1.63 ; depuis **v1.78** : jauge `#dsBar` **sous le plateau** (design « B · Jauge » choisi
     par Gilles : « DISTANCE · CAPTEUR V4 », valeur en cm (rouge < 10 cm, « rien devant » > 40 cm), barre 0–40 cm avec zone rouge 0–10,
     curseur blanc), mise à jour par `dsShow` ; plus d'étiquette sur le plateau ; `#dsCard` masquée) : carte « Capteur de distance · V4 » (`#dsCard`, valeur en cm + barre 0–40 cm
     avec les zones de « Suivre la main »). Tant que l'onglet Pilotage est ouvert et le V4 connecté, l'appli envoie `U1` (sinon `U0`) ;
     le V4 imprime `DS <mm>` toutes les 250 ms (`DS -1` = pas de capteur) ; en « Suivre la main », c'est `HD` qui alimente la carte.
     Test : `t_dist.py`.
   - **Main devant le capteur pendant le spectacle** (v1.84, demande de Gilles, remplace Gestes/Statue qui sont passés entre marqueurs
     `#[JEUX`) : réglage retiré de Programme, `SONAR` = 1 toujours (aussi dans le programme idle de la routine). `show_hand` (V4, état
     `sp = [état, début, reprise demandée, prochaine mesure]`) : en lecture/retour seulement (le capteur n'est pas lu à l'arrêt), main
     < 10 cm (hors `MASK` = pas un véhicule) pendant 80 ms → `z` + `SP 1 <w>` et `OBS` remis à None ; l'appli (`spLine`) renvoie
     `O1..O3` (positions en pause, `posAt`) ; dès la pause effective et les positions reçues, le V4 passe en conduite manuelle interne
     (`manual`, `hand`, `h_mode = 2`, `h_lost` = début de la détection → poussée / attaque comme en manuel) ; main partie depuis 2,5 s
     (ou `p` reçu, ex. montre) → `SP 0`, `blend` vers sa place, puis `p` (reprise). Sans positions en 4 s : reprise sans bouger.
     Pendant ce temps `z h n` → BUSY. Appli : `SP` (position du V4 suivie par `POS`, dessinée sur le plateau et pour `drawSensor`).
     Tests : harness (`SMODE=1`, `HARNESS_SONAR`, le harness répond à `SP 1` comme l'appli ; `HARNESS_APP_SP=0` pour couper),
     `t_showpush.py`.
   - **Capteur V4 pendant le spectacle** (v1.56 ; depuis v1.84 le réglage est retiré de Programme (`.edrow` caché) et `SONAR` vaut toujours 1 = Gestes ; avant : option « Capteur V4 » Arrêt / Gestes / Statue, `odv.sonar`,
     intégrée au programme par `%SMODE%`, changeable en direct par `S0|S1|S2`). Uniquement hors conduite manuelle (jeu 0).
     `gesture_tick` (toutes les 40 ms) : **Gestes** — main < 12 cm (sortie > 20 cm) ; passage de 60–900 ms ; 1 passage (puis
     700 ms sans autre) = lecture/pause, 2 passages = `n` chorégraphie suivante, main tenue 2 s = `h` stop et retour.
     **Statue** — main < 25 cm pendant 150 ms en lecture → `z` ; repart (`p`) 1 s après son départ. Les commandes passent par
     `command()` (donc +1 s de `LEAD`). Le V4 imprime `GST 1|2|H|S|R` (toast dans l'appli). `MASK` (`%MASK%`, calculé par
     `ODVGEN.sonarMask` : intervalles où un autre véhicule est devant le capteur, même colonne ±12 pas, à < 35 cm, élargis de
     300 ms) : mesures ignorées, sauf aux limites de chorégraphies (tous au départ). Commande `n` : à une limite, saut au début
     de la suivante et lecture ; au milieu, retour à la limite la plus proche (comme `h`) puis saut (`next_tgt`).
     Harness : `SMODE=1 node mkprogs.js …` + `HARNESS_SONAR`.
   - **Billes et poursuite RETIRÉS de l'appli depuis v1.55** (demande de Gilles) : le bouton `#tiltGo` et la carte `#gameCard`
     sont masqués (`hidden`) ; le code (page + hub) est resté en place, il suffit d'enlever `hidden` pour les remettre.
   - **Jeu de poursuite** (V4 en manuel) : `D<pas/s×100>` vitesse des chasseurs, `J` départ, `K` fin. Le V4
     calcule les chasseurs V1..V3 (vont vers le joueur, jamais < 10 pas, marge 11 entre chasseurs / 10,5 du
     joueur sauf pour s'éloigner ; prise si < 10,8 → `CATCH n ms`, pause 2,5 s où ils reculent), diffuse
     `(t, 7+16·GEN, octets x1 y1 x2 y2 x3 y3 (×8) vitesse)` toutes les 150 ms ; les V1..V3 suivent ces
     cibles. Fin : retour un par un par chemin dégagé (`JOK`, ou `JSTUCK`), puis l'appli ramène le V4 et `Q`.
     Le V4 imprime `JP x1 y1 … x4 y4 phase prises` (×100) toutes les 250 ms.
     **Rôles** (depuis v1.52) : `R<abc>` (chiffres pour V1..V3 : 0 méchant, 1 gentil, 2 fixe ; « retiré » = fixe garé dans un coin
     par l'appli). Gentil = garde du corps : `guard_target` se colle devant le méchant le plus proche du joueur (10,3 pas, côté
     joueur), vitesse ×0,5 (le méchant va bien plus vite), marge 10,2 entre méchant et gentil. Le méchant est plus fort : bloqué
     par un gentil il le bouscule (`push` : devant, de côté ou sur un axe, le gentil s'écarte peu à peu), glisse du côté opposé à
     l'obstacle (`GS`), et s'il ne se rapproche plus du joueur depuis 0,6 s il prend un détour (`detour`, point de passage `GW` 4 s). Seuls les méchants attrapent. LED des suiveurs via un 8ᵉ octet de diffusion `r1+3r2+9r3` (255 = couleur du
     véhicule) : méchant rouge, gentil bleu, fixe couleur atténuée ; sur le plateau de l'appli, pastille M rouge / G bleue / F grise / TOI ambre (`drawPlate`, si `GM.kind === 'chase'`). **Placement au hasard** : `P` (→ `PON`, jeu 2 + `b_ret`,
     `g_placed`) puis `W…`/`Z` comme les billes, puis `J` (accepté depuis le jeu 0 ou 3) ; `K` après un placement → rangement
     par l'appli (`W…`, `Z`). Appli : `gRandomConfig` (joueur au hasard, gentils ≤ 16 pas de lui, méchants ≥ 20, fixes partout,
     retirés dans un coin, écart ≥ 11, doit se ranger par `tidyPlan`), `gMoves`, rôles mémorisés `odv.roles`. Test : `t_game.py`.
   - **Billes** (V4 en manuel, bouton « 📱 Billes » de Pilotage) : `D` vitesse max, `B` départ (`BON`), `T<jx>,<jy>`
     inclinaison −100..100 (gauche/droite, haut/bas de l'écran). Le V4 calcule la physique des 4 billes (élan, frottement,
     rebond amorti sur la clôture, poids/vitesse max différents `BK` pour qu'elles s'étalent) et diffuse V1..V3 comme
     la poursuite (`game = 4`). Sécurité : 11 pas avec la position prévue ET avec celle d'il y a 250–500 ms (retard
     radio des suiveurs), sinon on ne peut que s'éloigner ; simulé : jamais < 10 pas. `K` arrête ; la page planifie le
     rangement (`tidyPlan` : A* `planReturn` + parkings si bloqué) et envoie `W<k><x>,<y>` (un trajet droit, `WOK`)
     puis `Z` (`JOK`), puis rend la main. Page : capteur `deviceorientation` (position au démarrage = à plat,
     zone morte 3°, plein à 20°) ; le joystick fait aussi pencher. Tests : `tests/t_billes.py`, harness (`B`, `T…`).
   - **Matrice lumineuse 3×3 du V4** (v1.77, `ColorLightMatrix` sur le **port D du V4**, seulement le V4 ; `MX`, `mshow(motif, couleur)`
     = 9 caractères ligne par ligne, 'x' allumé, ne renvoie rien si inchangé ; `mtick` toutes les 100 ms) :
     **démarrage** (v1.88, demande de Gilles) : les 9 cases en orange qui clignotent en fondu pendant 3 s (l'arc-en-ciel avant l'envoi du programme vient de la matrice / du firmware, on ne peut pas le changer) ; **calibrage** flèche orange vers la clôture du haut puis de droite (`homing`) ; **tableau de bord** :
     ▶ vert en lecture, ◀ cyan en retour, ❚❚ orange en pause, **au départ (veille, v1.81, choix « A · Comète » de Gilles) = comète
     rouge (violette avant v1.87) avec traînée de 2 pixels qui fait le tour (`RING`, `COMET`, 110 ms par case) et point central orange qui clignote** (plus de batterie),
     ✕ rouge en urgence ; **compte à rebours** : `p` depuis le début d'une chorégraphie (pas en reprise) démarre 3 s plus tard au lieu
     de 1 s (`m_last[5]`), la matrice affiche 3, 2, 1 (les autres suivent l'horloge, donc synchrones) ; **visage** en conduite manuelle :
     yeux qui regardent dans le sens du mouvement, yeux fermés (atténués) après 4 s immobile, orange pendant l'appui de la main,
     magenta + bouche (attaque ; rouge avant v1.87, le V4 étant devenu rouge, LED du hub aussi magenta), jaunes + bouche ronde (poussé). Sans matrice : rien ne change (pas de délai de 3 s).
     Harness : stub `ColorLightMatrix`, motifs dans `harness_out.json` → `matrix`. **Orientation de la matrice sur le véhicule à vérifier.**
     Pour la place : le mode « suivre la main » (H1), `rx_ok`/`v4_ok`/`RXO` et la réception des jeux par les suiveurs sont passés
     entre marqueurs `#[JEUX` (source V4 sans données ≈ 26,6 k, comme avant la matrice).
   - LED du hub = couleur du véhicule (`VCOL` : V1 bleu 215°, V2 orange 28°, V3 vert 140°, V4 **rouge 0° depuis v1.87** (avant violet 270°), `Color(h,100,100)`) ;
     en marche elle pulse couleur pleine / atténuée (`VDIM`, v = 30) ; restent : rouge = urgence, jaune/rouge = batterie faible
     (< 7,0 / 6,5 V), cyan = connexion télécommande.
   - **Reconnexion sans calibrage** (v1.60, demande de Gilles) : au démarrage sans `DO_HOMING`, le hub ne va plus à sa place
     (`run_target` seulement après un calibrage) ; `still` : il reste là où il est (angles moteurs gardés, `reset_angle=False`)
     tant que le spectacle ne démarre pas (horloge en lecture/retour, prise en main ou jeu), puis rejoint la chorégraphie en
     douceur (`blend`, 16 pas/s max). Harness : moteurs sans calibrage créés à la place de départ.
   - Au démarrage, chaque hub imprime `BAT <mV>` (niveau affiché dans Envoi : 6,0 V = 0 %, 8,4 V = 100 %).
   - Le V4 imprime `ST <P|F|B|S> <w> <chor> <attente> <mV> <GEN>` toutes les 400 ms.
4. **`src/page.html`** : F4 Square, 5 onglets dans une barre en haut, qui reste visible au défilement (`nav.tabbar`, sticky, 5 tuiles « briques » graphite à bande orange en bas comme les véhicules, onglet actif tout orange ; après l’écran de démarrage, les 5 tuiles arrivent comme des véhicules : elles descendent au centre puis glissent à leur place, `tabsArrive()` ; (au clic : l’orange monte du bas + l’icône fait un tour, classe `spin` ; les `.card` de l’onglet apparaissent l’une après l’autre, coins orange qui s’écartent puis remplissage, classe `anim` sur la section), icônes + libellés, ordre Setup (= Mise en place) · Programme · Pilotage · Véhicules · Stats ; le dernier ouvert est mémorisé, `odv.tab` ; glisser le doigt à gauche/droite change d’onglet ; appui long 2 s sur un onglet = jeu « TOY » : on le promène, les autres s’écartent, tout revient au relâcher, sauf sur les plateaux, curseurs, joystick, listes défilantes et fenêtres) :
   **Mise en place** (`#setup` : TOUJOURS avec recalage, un véhicule à la fois 1→4, bouton « Calibrer » par véhicule (le mot « recalage » est affiché « calibrage »),
   `sendVehicle(v, true, true, true)` = programme « idle » SANS chorégraphie (une pause de 500 ms, `idleTL()`) :
   les véhicules se recalent puis attendent au départ ; depuis v1.58 : les 4 posés en colonne contre la clôture de droite (V1 dans le
   coin du haut, puis 2, 3, 4) ; après le calibrage, le hub rejoint sa place le long du haut (`track_target`, 10 pas/s) et
   imprime `CLR` dès qu'il a quitté la colonne (x ≥ 12) ; la page reste connectée jusqu'au `CLR` (90 s max) ; bouton « Calibrer »
   de v actif dès que les précédents ont touché la clôture du haut (`HY`, imprimé après le calage en Y) et qu'aucun suivant
   n'est parti (`can(v)` dans `suRender`) ; son programme est envoyé tout de suite mais `sendVehicle(…, gate)` n'envoie la
   commande de démarrage qu'après le `CLR` du précédent (« Prêt : il démarrera dès que… »).
   **Plan en frise** (v1.83, design E puis « B · Frise » de Gilles, en largeur) : `#suPlan` (SVG 320×96 dessiné par `suPlan(next, run)` depuis `suRender`) = 4 petits plateaux côte à côte ; le plateau n montre la situation une fois le 0n calibré (précédents à leur place le long du haut, suivants dans la colonne de droite, le 0n en pointillés à son arrivée tant qu'il n'est pas fait et clignotant dans la colonne si c'est l'étape en cours) ; étape en cours encadrée en orange, étapes faites « en place », suivantes atténuées ; clôtures courtes (une largeur de véhicule) avec picot rouge ; texte de `#suNext` raccourci.
   **Bluetooth indisponible** (v1.83, design 5) : `#nobt.bt1` = une ligne en pointillés « Hors ligne · préparation seulement » + bulle « ? ».
   Le bouton disponible et pas encore fait (`go`) est orange et « respire » (`suPulse`, coupé si réduire les animations ; tests : `click(force=True)`).
   **Éditeur de plateau** (v1.89 ; depuis v1.90 **en haut de Setup, replié par défaut** : `<details id="boardCard">`, résumé `#bdSum`
   « ✓ validé · n blocs » ou « ● modifié, à valider ») : dessiner le plateau tel qu'il est réellement. L'éditeur modifie un **brouillon**
   `BDE` (localStorage `odv.boardDraft`) ; **« ✓ Valider le plateau »** (`#bdOk`) le copie dans le **plateau validé** `BD` (`odv.board`,
   défini juste après `store`) utilisé partout ; « Annuler » (`#bdUndoAll`) revient au validé. Grille **sans limite** (`bdView` : blocs
   + 2 cases libres autour, au moins 8×8 ; figée pendant qu'on dessine, `bdV`), coordonnées négatives permises, blocs de 10 pas (12,25 cm),
   bloc (bx, by) = véhicule centré en (10·bx, 10·by), bx vers la gauche (+X), by vers le bas ; (0,0) = coin du calibrage (ne peut pas
   être enlevé) ; **zone rouge** sur les 2 cases derrière ses clôtures (`BD_RED`) ; modes Blocs / **Décharge** (un bloc, bac cyan) ;
   **zoom à 2 doigts** (`bdPinch`, `bdZoomAt`, `bdZ`), molette, ⤢ `#bdFit` ; bouton « 4×4 ».
   **Utilisation du plateau validé** (v1.90, demande de Gilles) : `bdFits(p, e)` (véhicule entièrement sur des blocs, tolérance e pas,
   1 par défaut car la chorégraphie d'origine déborde de 0,7), `bdBox`, `plateGeo(W)` = repère commun de tous les plateaux canvas
   (`drawPlate`, `drawSensor`, `boardPt`, `edPt`, Atelier ; 4×4 = l'ancien u = W/44) : **Pilotage et Atelier dessinent le plateau validé**
   (blocs, clôtures en haut/à droite du coin, décharge) ; véhicule hors plateau encadré en rouge ; **chorégraphies qui sortent du
   plateau bloquées** dans Programme (`tlFits`, `it.fit`, badge « HORS ZONE » (v1.92, design « 5 · Mini plan » : petit bloc gris + véhicule rouge qui déborde, `.badge.hz`), case désactivée, exclues de `PLAY`) ;
   joystick limité aux blocs (`freeAt` → `bdFits(p, 0.01)`). **Plateau d'une chorégraphie** (v1.98, demande de Gilles) : les chorégraphies créées (Atelier, IA, code collé) enregistrent le plateau validé du moment (`board` dans `odv.custom`, `bdCopy`) ; l'**aperçu** dessine le plateau pour lequel la chorégraphie est prévue (`chorBoard(it)` : son plateau enregistré, sinon le 4×4 d'origine si elle sort du plateau validé ; `withBoard(b, fn)` remplace `BD` le temps du dessin) avec la ligne `#pvBd` « Plateau prévu pour cette chorégraphie (n blocs), pas le plateau validé ». Les anciennes chorégraphies créées n'ont pas de plateau enregistré. Les programmes reçoivent le plateau (`opts.board` = `bdPairs()`,
   marqueur `%BOARD%` → `BOARD = ((bx, by), …)`, défaut 4×4) ; `genId` et `keyNow` en tiennent compte (renvoi nécessaire après
   validation). Hub : `on_board` dans `free_at` (télécommande et poussée restent sur les blocs) ; `G` borné à ±200 (c'est l'appli qui
   garde le V4 sur les blocs). Harness : `BOARD='[[bx,by],…]' node mkprogs.js …`.
   **Aller à la décharge** (v1.90) : en conduite manuelle du V4, toucher le V4 sur le plateau de Pilotage = armer (`dumpArm`, `A1`/`A0`
   → `ARM`, cadre cyan qui tourne autour du V4) ; main devant le capteur 1 s → le hub imprime `DG` au lieu de pousser ; l'appli
   (`dumpGo`) coupe le capteur (`H0`), calcule un chemin sur les blocs qui évite les 3 autres (`bdPlan`, A* au pas de 1, 8 directions,
   sans couper de coin), le suit (`M.auto`, `dumpTick`, pointillés cyan), arrivé à la décharge, fait **1 cm vers la droite** du plateau vu de face (= −X, `DUMP_NUDGE` = 0,82 pas ; v2.01, demande de Gilles ; pas fait sur le bloc du coin (clôture) ni s'il toucherait un autre véhicule), attend 3 s, revient de 1 cm à gauche (place d'arrivée), puis revient par le même chemin ; **depuis v2.02** (Gilles : pas assez net) le petit pas se fait à l'arrêt : phases `go` → `settle` (0,8 s immobile) → `in` (1 cm lent, 1,6 pas/s) → `wait` 3 s → `out` → `rest` 0,5 s → `back` ; sur le plateau virtuel `dumpDraw` montre le déchargement (billes orange qui roulent vers le bord droit du V4 et disparaissent, bord droit allumé, barre cyan de 3 s + « DÉCHARGE » sous ou au-dessus du V4) puis
   remet le capteur (`handStart(2, true)`). Pendant le trajet aller (v1.91, choix « 2 · Gyrophare » de Gilles) l'appli envoie `Y2` : deux lumières orange tournent sur
   le bord de la matrice (`RING`) et la LED du hub clignote orange. Pendant les 3 s (choix « 1 · Cascade » orange) `Y1`, puis `Y0` au retour :
   la matrice montre des billes orange qui tombent dans chaque colonne (`a_arm[1]`, en tête de `mtick`) et la LED du hub clignote orange. « Rendre la main » annule. Test : `t_dump.py` ; aussi `t_board.py`, `t_board_zoom.py`, `t_board_fit.py`.
   **Piloter seulement le V4** (v1.65, carte `#soloCard` sous la Mise en place, bouton `#suSolo` ; depuis v1.82 façon arcade (design C
   de Gilles) : « MODE SOLO », « PLAYER 04 », bouton « ▶ PRESS START » qui pulse (`.solob`, `soloPu`), bulle d'aide en coin) : V1..V3 déjà garés le long du haut,
   V4 posé dans le coin en haut à droite ; calibre le V4 seul (programme idle), ouvre Pilotage et prend la main (`manGo`) ; joystick,
   télécommande, « Suivre la main ». `manGo` accepte le programme idle (`genId(idleTL(), false)` si `R.idle`). Test : `t_solo.py`.
   Test : `t_setup_order.py` ; Lecture/Pause/Retour désactivés tant que `R.idle`), **Programme** (`#choix` : choix/ordre + « Envoyer aux 4 véhicules » = `updateAll` (depuis v1.85 bouton graphique `.sendb` « Brique » choisi par Gilles : carré orange flèche ↑ qui pulse, « ×4 », 4 véhicules `.vbk`, bande orange en bas ; réglages Capteur V4 et boucle cachés par `style=display:none` car `.edrow` écrase `hidden`),
   sans recalage), **Véhicules** (`#envoi` : cartes (nom Bluetooth du hub `#hubn<v>` (localStorage `odv.hub<v>`) dans le menu ⋯ de chaque carte, sous « ↻ Relancer » et « .py » (`#vset<v>`, visible avec `.veh.open`) ; v1.99 : roue dentée, v2.00 : menu ⋯, demande de Gilles ; l'ancien bloc « Noms des hubs » sous les cartes est retiré), « Reconnecter » = renvoi sans recalage / « Déconnecter » par
   véhicule, « Tout reconnecter » = (depuis v1.61) remise à zéro du calibrage et onglet Setup (les 4 véhicules remis en colonne), « Tout déconnecter » ; barre de chargement hachurée animée pendant `updateAll`, dans Programme et Véhicules : `updProg`, étapes 0–22 % puis ≈ 19,5 % par véhicule suivant `setBar`), **Pilotage** (`#tele`).
   Il n'y a plus d'option « Recalage au démarrage » : seul l'onglet Mise en place recale.
   5ᵉ onglet **Statistiques** (`#stats`, sous les 4 autres) : collecte dans `odoTick` (`statAdd`/`statFrame`) — distance,
   temps en mouvement, vitesse max, carte de chaleur 20×20 (cases de 2 pas, emprise 10×10 ; depuis v1.95 un véhicule ne compte que s'il bouge ou pendant une chorégraphie : plus de ligne en haut due aux véhicules garés au départ, `STAT.heatPrev`), rose des directions
   (16 secteurs), plus courte distance entre véhicules, temps par chorégraphie, spectacles joués, mètres au joystick ;
   par session (mémoire) et par jour (localStorage `odv.stDays`, 120 jours max) ; batterie dans le temps (`odv.stBatt`,
   via `setBat`) ; trajectoires et courbes de vitesse : session seulement. Période Session / 7 jours / Depuis le début.
   Maquette sur le canevas Design (artboard Stats). Test : `tests/t_stats.py`. Compile avec
   `@pybricks/mpy-cross-v6@2.0.0` (chargé depuis jsDelivr, ou esm.sh en secours), envoie au hub
   (format multi-mpy6 : taille u32 + `__main__\0` + mpy ; commandes 0 stop, 3 meta, 4 RAM, 1 start,
   6 stdin), service Pybricks `c5f50001-8280-46da-89f4-6d8051e4aeef`.
   Fonctions : choix/ordre des chorégraphies (glisser-déposer par la poignée ⠿ ; corrigé en v1.98 (`chDrag`) : en montant, la ligne était retirée du document et perdait la capture du doigt (une seule place, ligne restée « en glisse ») → on déplace les voisines, plusieurs places par mouvement, suivi sur toute la fenêtre, défilement auto près des bords ; test `t_drag.py`), aperçu animé (bouton radar, icône SVG ambre), recalage (« Jouer en boucle » retiré en v1.84 : `#optLoop` caché, toujours décoché),
   « Mettre à jour les 4 véhicules » (retour au départ → `e` → arrêt V4 → envoi 1,2,3,4 sans recalage ;
   une petite boîte demande un appui par hub inconnu, la fenêtre Bluetooth étant filtrée sur son nom), « Tout déconnecter » (vérifié),
   reconnexion automatique, joystick pour le véhicule 4 uniquement (anti-collision et bornes 0..30) ;
   « Rendre la main » : retour du V4 par le plus court chemin qui contourne les 3 autres (A* + lissage).
   **Mode focus de conduite** (v1.79, design « B · Cockpit » choisi par Gilles) : dès que le V4 est en conduite manuelle au joystick,
   `body.focus` (posé par `manUI`) cache la barre d'onglets, l'en-tête, l'état/boutons du spectacle et tout sauf la 1ʳᵉ carte de Pilotage ;
   la jauge `#dsBar` est juste sous le plateau (v1.94 ; avant : en transparence sur le bas du plateau) ; `#joyBox` devient une console (bande orange) :
   bouton rond `#fRc` à gauche (icône SVG de télécommande LEGO, cyan si connectée, « respire » pendant la recherche → `rcGo`),
   joystick, bouton rond orange `#fBack` « Rendre » à droite (→ `manGo`) ; depuis v1.85 (design « B · Briques » de Gilles) les deux `.fb` sont des blocs graphite 70×190 (hauteur du joystick) avec bande en bas (cyan téléco, orange Rendre), icônes seules. `#fMsg` reprend `manMsg`. Le bouton « Connecter la
   télécommande » et son état sous Conduite manuelle sont masqués (`hidden`). Tests : `t_joy.py`/`t_push.py` cliquent `#fBack`.
   **Joystick carré** (v1.66, design « A · Pavé » choisi par Gilles) : `.joy` carré à coins ambre (`.jc`), manette carrée 64 px ;
   `joyAt` borne chaque axe séparément (−1..1, coins atteignables).
   **Atelier** (« Créer une chorégraphie ») : étapes = poses des 4 véhicules (glisser sur le plateau,
   aimant 1 pas), vitesse et pause par étape, contrôle de collision (pose + trajet, via core.js),
   « Ajouter le retour au départ » (tout droit / X puis Y / Y puis X / un par un, le plus court sûr),
   **solutions automatiques** sous chaque conflit (boutons ✨, `edFixes`, vérifiées par `segOK` = simulation core.js) : chevauchement
   à une étape → décaler l'un des deux véhicules sur la place libre la plus proche ; collision en trajet → « tous de côté puis en
   hauteur » / l'inverse (+1 étape), « un par un » (ordre et trajets droits ou en L), sinon « contourner un par un » (`tidyPlan`) ;
   aperçu (sous le plateau) ; enregistré dans le navigateur (localStorage `odv.custom`, champ `ed` = étapes) et
   réouvrable avec ✏️ ; « Enregistrer » ferme l'Atelier et revient à l'onglet Programme.
   **Inventer avec l'IA** (dans l'Atelier, sous les Étapes ; exemples en pastilles, bouton ✨, clé repliée) : description en français → API Anthropic (`claude-sonnet-5-5`,
   appel direct du navigateur avec `anthropic-dangerous-direct-browser-access`), réponse JSON
   `{name, steps:[{pos,speed,wait}]}` chargée dans l'Atelier ; jusqu'à 3 corrections automatiques en renvoyant
   les collisions ; retour au départ ajouté par ⌂ si c'est le seul manque. **Depuis v1.93** (demande de Gilles) : le prompt système est construit
   par `aiSys()` avec le **plateau validé** (`aiBoardTxt` : carte en texte `#`/`.`/`D`, liste des blocs, règle floor/ceil, coordonnées
   hors 0..30 permises) et la **décharge** (aller y vider les billes un par un, pause 3000) ; `aiParse` borne à `bdBox` ; l'éditeur
   (`edValidate`) signale « HORS ZONE » à l'étape et pendant le trajet (lignes droites échantillonnées), ce qui part aussi dans les
   corrections demandées à l'IA. Test : `t_ai_board.py`. Clé API dans localStorage `odv.aikey`
   uniquement (JAMAIS dans le dépôt). Test : `tests/t_ai.py` (API simulée). Les chorégraphies créées ne sont PAS dans le dépôt : pour les garder pour de
   bon, copier leur code dans `choregraphies/` et `CHORS`.
5. **`simulateur/template.html`** : simulateur visuel (plateau sombre à points, véhicules en blocs sombres
   « 01…04 » d'après la photo du montage), lecture, détection des chevauchements, édition du code.

   **Montre · télécommande** (v1.74, **toujours actif, sans réglage** (demande de Gilles) : la carte `#watchCard` est masquée ;
   au premier toucher de l'écran une fois le V4 connecté, `watchStart()` lance le son — Chrome exige un geste) : les commandes Musique d'une montre
   (Garmin…) pilotent le spectacle via la **Media Session** de Chrome : l'appli joue un WAV silencieux en boucle (`silentWav`),
   handlers `play`/`pause` → lecture/pause (`p`/`z` selon l'état), `nexttrack` → `n`, `previoustrack`/`stop` → `h` (`watchAct`) ;
   titre du « morceau » = état du spectacle (`watchMeta`, chaque seconde). **En conduite manuelle du V4, Lecture/Pause = « Rendre
   la main »** (`manGo`, v1.75) ; Suivant/Précédent ignorés. **Routine spéciale Spirale + Pulsation** (v1.76, demande de Gilles) :
   `choregraphies/routine_spirale_pulsation.py` (la « Vague » est retirée ; 19 s, 0 collision ; « Vague + Spirale + Pulsation » n'est
   plus dans `CHORS`) est injectée par `build.py` (`/*ROUTINE*/`) et forme **le programme sans chorégraphie** (`idleTL()`) : tous les
   programmes de Mise en place la contiennent, à l'arrêt au départ. Sans chorégraphie (`R.idle`), Lecture de la montre la lance (`p`)
   si les 4 véhicules sont calibrés (`SU.done` 1..4), sinon un message ; Précédent = stop et retour ; Suivant ignoré. Test : `t_watch2.py`.
   Test : `t_watch.py` (`WATCH.h`). À vérifier sur le vrai téléphone + montre de Gilles. Étape suivante possible : appli
   Connect IQ + relais Internet (ntfy) pour plus de commandes.

## Langue FR / EN (v1.95, demande de Gilles : « tout doit être traduit »)
- Le français reste la langue du code. **Choix FR | EN en haut à droite, à côté de la version** (`#langSw`, aussi dans le simulateur) ;
  localStorage `odv.lang` (partagé appli/simulateur), sinon langue du téléphone (`navigator.language`) ; changer recharge la page
  (`setLang`, confirmation si des véhicules sont connectés).
- `src/i18n.js` (injecté par `build.py` via `/*I18NJS*/` dans l'appli et le simulateur) : `tr(s)` = dictionnaire exact, puis modèles
  avec variables `{0}` `{1}` (morceaux variables retraduits), puis préfixe de symboles (✨ ⚠ ●…) retiré, puis **remplacement des phrases
  connues** dans le texte (limites de mots, les plus longues d'abord) et décimales `6,5 cm` → `6.5 cm`. `trNode` traduit le DOM au
  chargement puis à chaque changement (MutationObserver) : un élément qui ne contient que du texte + balises de mise en forme est traduit
  d'un bloc (`tr(html, true)` = exact/modèle seulement), sinon nœud par nœud ; attributs `title aria-label placeholder data-tip alt data-t` ;
  textes du canvas (`fillText` enveloppé), `confirm`/`alert`, titre de la montre (`watchMeta`). `data-noi18n` = ne pas traduire (code du
  simulateur, ligne en cours). L'IA de l'Atelier reçoit « name in English » en anglais.
- **Dictionnaire** : `src/i18n/*.txt`, une ligne `français<TAB>anglais` (`#` = commentaire), `{0}`… = modèle. Vocabulaire : Programme →
  Program, Pilotage → Control, pas → steps, Décharge → Unload, Rendre la main → Hand back, Prendre la main → Take control, Stop et
  retour → Stop & return, Atelier → Workshop, HORS ZONE → OUT OF BOUNDS.
- **Vérifier** : en anglais, `window.__i18nMiss` liste les textes encore en français. Scripts de collecte : parcourir tous les onglets et
  états (Setup, Programme, Atelier, Pilotage/cockpit, lignes du hub simulées, décharge, montre, Véhicules, Stats, simulateur) et
  lire `__i18nMiss` (0 à la v1.95). Les tests Playwright ouvrent la page avec `locale='fr-FR'` (sinon la page passerait en anglais).

## Construire, tester, publier
- `python build.py` → régénère `index.html` et `simulateur/index.html` (les chorégraphies sont lues
  dans `choregraphies/`). Les pages générées sont autonomes (un seul fichier).
- Tests (dans `tests/`) :
  - `node mkprogs.js <fichiers.py> <boucle 0|1> <recalage 0|1> <gen>` puis
    `python harness.py progs.json '<script>' <fin_ms>` : 4 hubs simulés (horloges décalées, latence
    radio, paquets perdus) ; `python analyze.py` vérifie synchro, pause, retour, urgence.
  - `t_page2.py`, `t_manual.py`, `t_joy.py` : Playwright + faux Bluetooth (envoi, mise à jour, joystick).
  - `sim_model.py` : modèle Python de référence des mouvements.
- Publier : `python build.py --publier` (augmente la version dans `version.json` et note l'heure
  de Bruxelles, affichées en haut à droite de l'appli et dans le simulateur) ; l'appli relit `version.json` sans cache
  (démarrage, toutes les 2 min, retour dans l'appli) et affiche un bandeau « Nouvelle version disponible » qui recharge avec `?v=N`, puis commit de
  `index.html`, `simulateur/index.html`, `version.json` sur `main` ; en ligne en 1–2 min.
- Écran de démarrage (`#splash`, 5 s, touche pour passer, désactivé si « réduire les animations ») : point orange, (v1.96 a essayé une version « 4 · Matrice » ; Gilles a demandé de remettre celle-ci en v1.97)
- Dessin des véhicules PARTOUT (plateaux canvas `vehDraw` dans la page, `drawVehicle` du simulateur, écran de
  démarrage, étiquettes HTML classe `.vbk` avec `--c` = couleur du véhicule) : bloc sombre #1f2124 hachuré en
  diagonale à la couleur du véhicule, coins « crochets » de sa couleur, ligne orange en bas, numéro en police
  **Tomorrow** 700 (Google Fonts).
- Boutons orange (`.btn.primary`, `.rb.play`) ; « Fermer » = croix orange dans un carré en haut à droite (`.xclose`, Atelier et aperçu) : coins légèrement arrondis (5 px), éclair blanc à l’appui (classe `flash` posée au pointerdown). Tous les `.btn` sont compacts (≈36 px de haut) ; tous les boutons et sélecteurs ont le même arrondi de 5 px.
- Logo : véhicule « 01 » en pixel art (`icons/logo.svg`, PNG dérivés, `manifest.webmanifest`).
- Style visuel de l'appli (depuis v1.22, choix de Gilles parmi 3 maquettes) : **« Holo ambre »**, futuriste
  minimaliste — fond graphite #121314, cartes #1a1c1e, accent ambre #ff9a3c, texte #edeae4, polices Space Grotesk
  + Space Mono (Google Fonts), coins « crochets » ambre sur les cartes, titres `> EN CAPITALES` en mono, plateau
  sombre à points avec règle 0–40. Bloc CSS « Thème Holo ambre » en fin de `<style>` dans `src/page.html`.
  Le simulateur a le même thème (bloc « Thème Holo ambre » en fin de `<style>` de `simulateur/template.html`).
- **Chorégraphie d'origine corrigée** (v1.57) : `choregraphies/7_origine_corrigee.py` (utilisée dans `CHORS` à la place du
  programme d'origine, qui reste en référence) : sans les 3 déplacements de mise en place ; 8 des V1..V3 écrasé en hauteur
  (y' = 10,3 + y × 19,7/30) pour que le V4 garde sa ligne y = 0 ; entrée/sortie du 8 en 3 temps (V1/V2, puis V3 le long du
  haut, puis V3 descend pendant que V4 avance). core.js : 0 collision, écart mini 10 ; hubs simulés : 9,74 dans le tour du
  plateau en convoi (côte à côte, gigue de synchro, comme les autres chorégraphies).
- Nouvelle chorégraphie : fichier de lignes `mvc.*` indentées de 4 espaces dans `choregraphies/`,
  partant de et revenant à (30,0)(20,0)(10,0)(0,0), sans chevauchement ; l'ajouter à `CHORS` dans
  `build.py`. `gen_cinq.py` / `gen_vague_spirale.py` montrent comment les générer et les valider.

## Non vérifié sur le vrai matériel (à surveiller)
- **Taille du programme** : la v1.56 était trop grosse pour le hub (Gilles, 09/11). Depuis v1.57, `ODVGEN.buildProgram` enlève
  les blocs `#[JEUX` … `#]JEUX` de `runtime.py` (poursuite, billes ; `opts.games` pour les garder) et tous les commentaires /
  lignes vides (`stripPy`). Source envoyée au hub (sans les données) : ≈ 26 k caractères (v1.54 qui marchait : ≈ 28,5 k).
  Toute nouvelle fonction du hub doit rester petite ; mettre ce qui n'est plus utilisé entre marqueurs.
  **Ménage v1.91** (≈ 28,3 k → 25,0 k) : passés entre marqueurs `#[JEUX` les restes des jeux (commandes `K`/`W`/`Z` de rangement,
  `b_pos`…`b_snapshot`, `game_tick`, appel des jeux et `JP` dans la boucle, retard radio `BOLD` de `free_at`) et la commande `S0|S1|S2`
  (mode du capteur, plus envoyée par l'appli). Les marqueurs ne s'imbriquent pas (le retrait prend du premier `#[JEUX` au premier `#]JEUX`).
- Paramètre `reset_angle=` de `Motor` (utilisé sans recalage) et taille max du programme par hub.
- Ressenti du joystick (8 envois/s) ; charge radio du V4 connecté + diffusion.
- Perte de liaison V4 au joystick (signalée de nouveau le 09/11, v1.61) : la puce Bluetooth du Technic Hub peut se bloquer si la
  diffusion (`ble.broadcast`) est mise à jour trop souvent pendant une connexion (problème connu de Pybricks) → en conduite manuelle
  le V4 ne diffuse plus que toutes les 3 s (au lieu de 0,5 s). Après une reconnexion, l'appli vérifie que le programme tourne encore
  (sinon : hub redémarré, batterie faible ?) et l'affiche dans Pilotage. À confirmer sur le vrai matériel.
- **Chrome s'est fermé** pendant l'envoi du programme au V4 lors du calibrage (Gilles, 12/11, capteur tout juste branché sur le
  port B). Cause non trouvée (rien côté hub n'utilise le capteur pendant la mise en place : `%SMODE%` = 0 dans le programme idle) ;
  piste : batterie du V4 / hub qui redémarre pendant une écriture Bluetooth (plantage connu de Chrome Android). Depuis v1.64, la
  Mise en place est mémorisée (`odv.su`, 30 min : véhicules faits ou sortis de la colonne) pour reprendre après une fermeture
  (test `t_su_resume.py`).
- « Tout déconnecter » remet aussi la Mise en place à zéro (plus de véhicule en vert, « ○ Déconnecté »).
- Gilles a signalé : « Stop et retour » OK après coup ; perte de liaison V4 pendant le joystick
  (corrigé par allègement radio + reconnexion auto, à confirmer) ; déconnexion difficile (corrigée,
  à confirmer).

## Idées en attente
- Adoucir le demi-tour du « retour au départ » (courte pause avant de repartir en arrière).
- Allonger `LEAD` si un véhicule réagit en retard.
