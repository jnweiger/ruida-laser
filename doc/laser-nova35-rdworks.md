                        jw, Sa 25. Nov 20:14:04 CET 2017

Importieren nach RDworks
========================

inkscape -> (Speichern unter) -> PDF
        -> [x] Texte in Pfade wandeln

PDF -> CorelDraw X7 
   -> PDF importieren
   -> Text importieren als
      (*) Kurven) -> OK

-> rechts oben grüngrauer Kreis mit Rechtspfeil
   "DRWorks V8 Laser Working" 
   -> Klick!

# evtl. passiert nicht, dann versteckt sich der Requester mit der Fehlermeldung 
hinter allen Fenstern.

   -> Fehlermeldung RDWorks. ....
       ..tmp enthält eine ungültige Pfadangabe -> OK

Einstellungen in RDworks
========================

# Falls nicht alle Teile sichtbar sind: 
#  gefüllte Flächen ohne Randlinien funktionieren nicht!
#  
# Falls im RDworks eine Farbe mit 'BMP' markiert ist:
#  Zurück ins CorelDraw, Objekt wählen, 'Objekt' -> 'in Kurven Umwandeln (Ctrl-Q)'
#  (Ursache kann sein: Deckkraft oder Alpha settings war nicht auf 100%)

   -> rechts oben Farben
      Doppelklick auf jede Farben
      -> Auswählen was zu tun ist:
      Speed, MinPower1, MaxPower1 siehe https://wiki.fablab-nuernberg.de/w/Nova_35#Notwendige_Einstellungen

# Beispiel:
# - CUT Birke 4mm: Mode Cut, Speed -> 35mm/s, MaxPower1 65 %, MinPower1 50 %
# - MARK: Mode: Cut, Speed: 9999, MaxPower1 20 %, MinPower1 7 %
# - IGNORE: Mode: Cut, Output: No

# Man kann Materialeinstellungen theoretisch in der Software hinterlegen. Das
# hat bei mir aber nie funktioniert. Die Liste ist immer leer. (Admin-Rechte?)

Bei jedem Neustart von RDworks verstellt sich die X-Achse, so dass alles
seitenverkehrt ist. Prüfen:
-> Config(S) -> System Setting
   -> [ ] Axis X Mirror (*) ( ) ( )              # kein Häkchen bei X!
                        ( ) ( ) ( ) 
   -> [X] Axis Y Mirror ( ) ( ) ( )              # Häkchen bei Y!
   -> Close

# Damit wird genau so gelasert, wie am Bildschirm sichtbar.  Wenn Schriften im
# RD-Works verkehrt herum sind, dann die Häkchen anders setzen und probieren.

Transport via USB-Stick
=======================

 -> rechts unten (Laser work) [  SavetoUFile  ] 
   -> *.rd      (7 oder 8 Buchstaben sind später sichtbar)
   -> auf USB Stick im Wurzelverzeichnis(!).
   -> Success ->  
   -> (Ein Requester mit unleserlicher Fehlermeldung ist okay.)


USB-Stick
 -> Am Laser: 2.Stecker von unten beschriftet mit "USB-Stick"

Tastenfeld
  unten blau: "Datei" drücken.
  Cursor-Taste-rechts (hoch / runter) "[  Udisk+  ]" auswählen, [Enter]

-> [  UDisk  ] [Enter]
Read UDisk File -> Enter... dauert.
  -> Wähle Datei
 XWING.-~
[Read UDisk File] -> [Enter]
  -> Wähle Datei
 02 XWING.-~
-> Cursor-Taste-rechts -> Copy to mem -> Enter
 -> Copy Successfull [Enter]

# Falls "Name overlap" erscheint:
#   es darf noch keine gleichnamige Datei im internen 'mem' geben, sonst kann
#   nicht kopiert werden. Eine alte Datei mit gleichem Namen muss vorher 
#   händisch# gelöscht werden.

Bedienung am Laser
==================

Taste [Datei]
 -> links im Display erscheint die Liste der im Laser gespeicherten Dateien.
  -> Mit den Cursor-Tasten die richtige auswählen, -> [Enter]

 39 XWINF.-~
   -> Der Dateiname erscheint ganz oben rechts im Display.

#  Falls mehr als 99 Dateien im internen 'mem' gespeichert sind, werden nur 
#  die ersten 99 angezeigt. -> Fleissiges löschen.


 Deckel auf. Warnleuchte beginnt zu blitzen, Reset leuchtet rot.

 Material in die Mitte. Die Links-Hinten-Anschlagleisten die es beim Zing gab, gibt es hier nicht.

Focus Einstellung
-----------------

  Taste Z/U -> [z move] -> erst Cursor-Taste-rechts drücken. (= nach unten)
  -> zwischen blauer Spitze und Materialoberkante: [  20mm  ] Abstand
     Mit Schlüssellochförmigem Acryl-Teil prüfen.
  -> ESC

Deckel zu, Reset drücken. Warnleuchte wird wieder grün.

Startpunkt Einstellung
----------------------

  -> mit Cursor-Tasten hinfahren
  -> Startposition Taste
Achtung: Fährt sehr schnell, Blaue Düse ist [  20mm  ] über dem Material.
Sicher stellen, dass das nirgends kollidiert! 
Keine Beschwerungseisen für krumme Holzplatten! 
Es gibt statt dessen 3 runde Magnete, die vorne links innen im Laser gelagert werden.
 -> Taste [Box]
   -> Der rote Laserpunkt zeigt, ob alles draufpasst.

# Farben: Sollte über RDworks schon gemacht sein!!!
#  -> Enter, [Rote Farbe]
#    Z/U rein
# 
#    Acryl 3mm: Speed -> 25mm/s, MaxPower1 70 %  MinPower1 55%
#    Birke 3mm: Speed -> 40mm/s, MaxPower1 65 %, MinPower1 50%
#    Birke 4mm: Speed -> 35mm/s, MaxPower1 65 %, MinPower1 50%
# 
#    (Kleinere Teile wenn durch sind: MinPower stimmt.,
#    Grössere Sachen wenn durch: Maxpower stimmt.)
#    -> Enter
#    Z/U 
#  -> [grüne Farbe]
#    Speed 9999 mm/s, MaxPower1 20%, MinPoer1 8%
# 

-> Air Assist ist eingebaut, läuft immer.
-> Aussengebläse "Elmo" muss an sein. Schalter an der Wand. Schlauf muss gesteckt sein.

-> "Start/Pause" Taste drücken. 
 -> Laser beginnt.
 -> Uhr läuft inten links im Display mit.
 -> Nach dem Lasern ca. 30 sec warten, bis sich der Rauch verzogen hat.
 
Anmerkungen
===========

Wartung
-------
Siehe http://www.thunderlaser.com/download/down/User's_manual_for_NOVA35.pdf

DAILY CHECK LIST
① Check Mirrors and lens for condens ation and make sure it is clean after work
② Check exhaust grille to ensure there is no blockage for exhaust fan
③ Check coolant water level
④ Check air filter on compressor
⑤ Ensure cooling fans on sides are free from debris
⑥ The air blower must be checking and cleaning if required.

WEEKLY CHECK LIST
① Clean filters on water chiller
② Clean debris from under laser bed
③ Clean X & Y & Z axis rails and lubricate as required
④ Clean Acrylic /Tempered glass covers in lid
⑤ The beam combiner must be checking every weekly, and cleaning if required.


Schnittleistung
---------------
 Beispiel 10 Bieberschweine ganze Platte 40cm x 30cm, 4mm
 13 Minuten. (Beim Zing waren es 35 Minuten)

Prüfungsfragen
--------------
 - Was muss man überprüfen, bevor man die Starttaste drückt?
 - Wo steht der Feuerlöscher? Welche Type Feuerlöscher ist das?
 - Wie kann man sich die Finger quetschen?
 - Wie kann die Düse beschädigt werden?
   * Beim Fokus einstellen?
   * Beim lasern?
 - Wer darf lasern? (Namensliste? Wer Einweisung hatte und eine Kopie dieser Anleitung hat, ...)
 - Was tun, wenn
   * Ecken oder Kleinteile nicht durch sind?
   * Lange Linien in der Mitte nicht durch sind?
   * Wenn man eine neue Einstellung gefunden hat?
   * Unbekannte Meldungen erscheinen?

