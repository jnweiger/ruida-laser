                        jw, Fr 16. Jun 10:39:54 CEST 2017
                        jw, Mo 12. Jun 21:38:39 CEST 2017
                        jw, Mi 7. Jun 21:47:55 CEST 2017

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

 -> rechts unten (Laser work) SavetoUFile 
   -> *.rd      (7 oder 8 Buchstaben sind später sichtbar)
   -> auf USB Stick im Wurzelverzeichnis(!).
   -> Success ->  
   -> (Ein Requester mit unleserlicher Fehlermeldung ist okay.)


USB-Stick
 -> Am Laser: 2.Stecker von unten beschriftet mit "USB-Stick"

Tastenfeld
  unten blau: "Datei" drücken.
  Cursor-Taste-rechts (hoch / runter) "+Udisk" auswählen, [Enter]

-> +UDisk [Enter]
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
  -> zwischen blauer Spitze und Materialoberkante: 6mm Abstand
     Mit Schlüssellochförmigem Acryl-Teil prüfen.
  -> ESC

Deckel zu, mit beiden Händen.  Reset leuchtet noch rot.
 -> Reset drücken, dann kann man wieder bedienen.

Startpunkt Einstellung
----------------------

  -> mit Cursor-Tasten hinfahren
  -> Startposition Taste
Achtung: Fährt sehr schnell, Blaue Düse ist nur 6mm über dem Material.
Sicher stellen, dass das nirgends kollidiert! 
Keine Beschwerungseisen für krumme Holzplatten! 
Es gibt statt dessen 2 flache Magnete, die unter der Düse durchpassen.
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

-> Air Assist muss laufen! Schalter am Stecker. Immer prüfen! Sonst kaputt!
   Die Linse darf nie schmutzig werden!
-> Aussengebläse "Elmo" muss an sein. Schalter an der Wand

-> "Start/Pause" Taste drücken. 
 -> Laser beginnt.
 -> Uhr läuft inten links im Display mit.

Anmerkungen
===========

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
 - Wer darf lasern? (Namensliste!)
 - Was tun, wenn 
   * Ecken oder Kleinteile nicht durch sind?
   * Lange Linien in der Mitte nicht durch sind?
   * Wenn man eine neue Einstellung gefunden hat?
   * Unbekannte Meldungen erscheinen?
 - Man kann händisch bei offener Klappe positionieren. Wie?


