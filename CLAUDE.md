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
     `G` de l'appli est prioritaire 400 ms ; le V4 imprime `POS x y <bouge>` (×100) et `RC 0|1`.
   - **Jeu de poursuite** (V4 en manuel) : `D<pas/s×100>` vitesse des chasseurs, `J` départ, `K` fin. Le V4
     calcule les chasseurs V1..V3 (vont vers le joueur, jamais < 10 pas, marge 11 entre chasseurs / 10,5 du
     joueur sauf pour s'éloigner ; prise si < 10,8 → `CATCH n ms`, pause 2,5 s où ils reculent), diffuse
     `(t, 7+16·GEN, octets x1 y1 x2 y2 x3 y3 (×8) vitesse)` toutes les 150 ms ; les V1..V3 suivent ces
     cibles. Fin : retour un par un par chemin dégagé (`JOK`, ou `JSTUCK`), puis l'appli ramène le V4 et `Q`.
     Le V4 imprime `JP x1 y1 … x4 y4 phase prises` (×100) toutes les 250 ms.
   - Au démarrage, chaque hub imprime `BAT <mV>` (niveau affiché dans Envoi : 6,0 V = 0 %, 8,4 V = 100 %).
   - Le V4 imprime `ST <P|F|B|S> <w> <chor> <attente> <mV> <GEN>` toutes les 400 ms.
4. **`src/page.html`** : Pilote ODV, 4 onglets (le dernier ouvert est mémorisé, `odv.tab`) :
   **Mise en place** (`#setup` : TOUJOURS avec recalage, un véhicule à la fois 1→4, bouton « Recaler » par véhicule,
   `sendVehicle(v, true, true, true)` = programme « idle » SANS chorégraphie (une pause de 500 ms, `idleTL()`) :
   les véhicules se recalent puis attendent au départ ; Lecture/Pause/Retour désactivés tant que `R.idle`), **Programme** (`#choix` : choix/ordre + « Envoyer aux 4 véhicules » = `updateAll`,
   sans recalage), **Véhicules** (`#envoi` : cartes, « Reconnecter » = renvoi sans recalage / « Déconnecter » par
   véhicule, « Reconnecter les 4 » = `updateAll`, « Tout déconnecter »), **Pilotage** (`#tele`).
   Il n'y a plus d'option « Recalage au démarrage » : seul l'onglet Mise en place recale.
   5ᵉ onglet **Statistiques** (`#stats`, sous les 4 autres) : collecte dans `odoTick` (`statAdd`/`statFrame`) — distance,
   temps en mouvement, vitesse max, carte de chaleur 20×20 (cases de 2 pas, emprise 10×10), rose des directions
   (16 secteurs), plus courte distance entre véhicules, temps par chorégraphie, spectacles joués, mètres au joystick ;
   par session (mémoire) et par jour (localStorage `odv.stDays`, 120 jours max) ; batterie dans le temps (`odv.stBatt`,
   via `setBat`) ; trajectoires et courbes de vitesse : session seulement. Période Session / 7 jours / Depuis le début.
   Maquette sur le canevas Design (artboard Stats). Test : `tests/t_stats.py`. Compile avec
   `@pybricks/mpy-cross-v6@2.0.0` (chargé depuis jsDelivr, ou esm.sh en secours), envoie au hub
   (format multi-mpy6 : taille u32 + `__main__\0` + mpy ; commandes 0 stop, 3 meta, 4 RAM, 1 start,
   6 stdin), service Pybricks `c5f50001-8280-46da-89f4-6d8051e4aeef`.
   Fonctions : choix/ordre des chorégraphies (glisser-déposer par la poignée ⠿), aperçu animé (bouton 👁), boucle, recalage,
   « Mettre à jour les 4 véhicules » (retour au départ → `e` → arrêt V4 → envoi 1,2,3,4 sans recalage ;
   une petite boîte demande un appui par hub inconnu, la fenêtre Bluetooth étant filtrée sur son nom), « Tout déconnecter » (vérifié),
   reconnexion automatique, joystick pour le véhicule 4 uniquement (anti-collision et bornes 0..30) ;
   « Rendre la main » : retour du V4 par le plus court chemin qui contourne les 3 autres (A* + lissage).
   **Atelier** (« Créer une chorégraphie ») : étapes = poses des 4 véhicules (glisser sur le plateau,
   aimant 1 pas), vitesse et pause par étape, contrôle de collision (pose + trajet, via core.js),
   « Ajouter le retour au départ » (tout droit / X puis Y / Y puis X / un par un, le plus court sûr),
   aperçu (sous le plateau) ; enregistré dans le navigateur (localStorage `odv.custom`, champ `ed` = étapes) et
   réouvrable avec ✏️.
   **Inventer avec l'IA** (dans l'Atelier, sous les Étapes ; exemples en pastilles, bouton ✨, clé repliée) : description en français → API Anthropic (`claude-sonnet-5-5`,
   appel direct du navigateur avec `anthropic-dangerous-direct-browser-access`), réponse JSON
   `{name, steps:[{pos,speed,wait}]}` chargée dans l'Atelier ; jusqu'à 3 corrections automatiques en renvoyant
   les collisions ; retour au départ ajouté par ⌂ si c'est le seul manque. Clé API dans localStorage `odv.aikey`
   uniquement (JAMAIS dans le dépôt). Test : `tests/t_ai.py` (API simulée). Les chorégraphies créées ne sont PAS dans le dépôt : pour les garder pour de
   bon, copier leur code dans `choregraphies/` et `CHORS`.
5. **`simulateur/template.html`** : simulateur visuel (plateau sombre à points, véhicules en blocs sombres
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
- Publier : `python build.py --publier` (augmente la version dans `version.json` et note l'heure
  de Bruxelles, affichées en haut à droite de l'appli et dans le simulateur) ; l'appli relit `version.json` sans cache
  (démarrage, toutes les 2 min, retour dans l'appli) et affiche un bandeau « Nouvelle version disponible » qui recharge avec `?v=N`, puis commit de
  `index.html`, `simulateur/index.html`, `version.json` sur `main` ; en ligne en 1–2 min.
- Logo : véhicule « 01 » en pixel art (`icons/logo.svg`, PNG dérivés, `manifest.webmanifest`).
- Style visuel de l'appli (depuis v1.22, choix de Gilles parmi 3 maquettes) : **« Holo ambre »**, futuriste
  minimaliste — fond graphite #121314, cartes #1a1c1e, accent ambre #ff9a3c, texte #edeae4, polices Space Grotesk
  + Space Mono (Google Fonts), coins « crochets » ambre sur les cartes, titres `> EN CAPITALES` en mono, plateau
  sombre à points avec règle 0–40. Bloc CSS « Thème Holo ambre » en fin de `<style>` dans `src/page.html`.
  Le simulateur a le même thème (bloc « Thème Holo ambre » en fin de `<style>` de `simulateur/template.html`).
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
