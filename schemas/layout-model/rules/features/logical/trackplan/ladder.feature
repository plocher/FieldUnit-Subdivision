Feature: A ladder and the selector that serves it
  A yard ladder is worked from a rotary knob: NX by track selection (the owner, 2026-11-13; issue #145, a POC). A
  ladder marker, a policy sign of Kind LADDER with a Name, stands on the ladder's start leg. A ladder is every
  facing-point switch the dispatcher controls, from its start leg up to a trailing point: the walk goes from the
  marker both ways along the track, across every joint; one way meets the start switch trailing, the other meets the
  first ladder switch at C, so the direction needs no orientation. It continues through each switch entered at C and
  stops where the next switch on a path is met at N or R, at an end of track, or where the dispatcher no longer
  controls the track (the owner, 2026-11-14): a facing switch or a derail the dispatcher does not control. A derail
  the dispatcher controls is a ladder member, and every choice through it sets it to REVERSE, its clear position.
  The choices come in a fixed order. At each ladder switch the spine is the leg that leads to the next ladder switch,
  N or R; the other leg is the next choice; the last switch gives R, then N. Where both legs lead to ladder switches,
  N's sub-ladder comes before R's. Each choice is its leg with its alignment, written here `17R: 15N 17R`. Detent 1
  is nearest the start.
  A selector serves the ladder of its Name, qualified like a lever, and derives its choices and its range, 1 to the
  number of choices. Each ladder switch derives its ladder and its control source, the selector. A selector's controls
  are switch-position demands, not tokens (the owner, 2026-11-14): each switch of a choice's alignment with the
  position the choice asks of it, and the station receives them. The field unit lines and locks as for any lever. Nothing here implements locking (ADR 0012 §5.2).

  Background:
    Given interlocking "X" has house "East"
    And interlocking "X" has these ends:
      | Id | Kind   |
      | E1 | BUMPER |
      | E2 | BUMPER |
      | E3 | BUMPER |
      | E4 | BUMPER |

  Scenario: the spine changes legs and the last switch gives R, then N
    Given interlocking "X" has these appliances:
      | Name | Appliance | Style   | TC  |
      | 9    | switch    | powered | 9T1 |
      | 1    | switch    | powered | 1T1 |
      | 3    | switch    | powered | 3T1 |
      | 5    | switch    | powered | 5T1 |
    And interlocking "X" has these joints:
      | Id | Kind |
      | J1 | IRJ  |
    And interlocking "X" has these policies:
      | Id | Name | Kind   |
      | M  | Yard | LADDER |
    And interlocking "X" has these wires:
      | Pins                  |
      | 9.R Yard.track J1.A   |
      | J1.B 1.C              |
      | 1.R E1.EoT            |
      | 1.N 3.C               |
      | 3.N E2.EoT            |
      | 3.R 5.C               |
      | 5.R E3.EoT            |
      | 5.N E4.EoT            |
    And interlocking "X" has these devices:
      | Name | Appliance |
      | Yard | selector  |
    When the layout is derived
    Then selector "Yard" offers "1R: 1R; 3N: 1N 3N; 5R: 1N 3R 5R; 5N: 1N 3R 5N"
    And selector "Yard" ranges from 1 to 4
    And ladder "M" starts at "X:9.R" with switches "X:1, X:3, X:5"
    And "3" has derived ladder "X:Yard"
    And "3" has derived selector "X:Yard"
    And "9" has no derived ladder

  @switch.lever
  Scenario: a ladder switch a selector serves needs no switch lever
    Given interlocking "X" has these appliances:
      | Name | Appliance | Style   | TC  |
      | 9    | switch    | powered | 9T1 |
      | 1    | switch    | powered | 1T1 |
    And interlocking "X" has these policies:
      | Id | Name | Kind   |
      | M  | Yard | LADDER |
    And interlocking "X" has these wires:
      | Pins               |
      | 9.R Yard.track 1.C |
      | 1.R E1.EoT         |
      | 1.N E2.EoT         |
    And interlocking "X" has these devices:
      | Name | Appliance |
      | Yard | selector  |
    And the desk has these levers for interlocking "X":
      | Name | Style  |
      | 9    | switch |
    When the layout is derived
    Then selector "Yard" offers "1R: 1R; 1N: 1N"
    And it is not reported

  Scenario: where both legs lead to ladder switches, N's sub-ladder comes first
    Given interlocking "X" has these appliances:
      | Name | Appliance | Style   | TC  |
      | 9    | switch    | powered | 9T1 |
      | 1    | switch    | powered | 1T1 |
      | 3    | switch    | powered | 3T1 |
      | 5    | switch    | powered | 5T1 |
    And interlocking "X" has these policies:
      | Id | Name | Kind   |
      | M  | Yard | LADDER |
    And interlocking "X" has these wires:
      | Pins               |
      | 9.R Yard.track 1.C |
      | 1.N 3.C            |
      | 1.R 5.C            |
      | 3.R E1.EoT         |
      | 3.N E2.EoT         |
      | 5.R E3.EoT         |
      | 5.N E4.EoT         |
    And interlocking "X" has these devices:
      | Name | Appliance |
      | Yard | selector  |
    When the layout is derived
    Then selector "Yard" offers "3R: 1N 3R; 3N: 1N 3N; 5R: 1R 5R; 5N: 1R 5N"

  Scenario: a leg that meets another switch trailing ends there
    Given interlocking "X" has these appliances:
      | Name | Appliance | Style   | TC  |
      | 9    | switch    | powered | 9T1 |
      | 1    | switch    | powered | 1T1 |
      | 7    | switch    | powered | 7T1 |
    And interlocking "X" has these policies:
      | Id | Name | Kind   |
      | M  | Yard | LADDER |
    And interlocking "X" has these wires:
      | Pins               |
      | 9.R Yard.track 1.C |
      | 1.R 7.N            |
      | 1.N E1.EoT         |
    And interlocking "X" has these devices:
      | Name | Appliance |
      | Yard | selector  |
    When the layout is derived
    Then selector "Yard" offers "1R: 1R; 1N: 1N"
    And ladder "M" starts at "X:9.R" with switches "X:1"

  @ladder.name
  Scenario: a ladder marker with no Name
    Given interlocking "X" has these appliances:
      | Name | Appliance | Style   | TC  |
      | 1    | switch    | powered | 1T1 |
    And interlocking "X" has these policies:
      | Id | Kind   |
      | M  | LADDER |
    And interlocking "X" has these wires:
      | Pins       |
      | M.track 1.C |
    When the layout is derived
    Then it is reported as missing on "M"

  @ladder.start
  Scenario: a marker from which no way meets a switch at its points
    Given interlocking "X" has these policies:
      | Id | Name | Kind   |
      | M  | Yard | LADDER |
    And interlocking "X" has these wires:
      | Pins                     |
      | E1.EoT Yard.track E2.EoT |
    When the layout is derived
    Then it is reported as missing on "M"

  @ladder.direction
  Scenario: a marker with a switch at its points both ways
    Given interlocking "X" has these appliances:
      | Name | Appliance | Style   | TC  |
      | 1    | switch    | powered | 1T1 |
      | 3    | switch    | powered | 3T1 |
    And interlocking "X" has these policies:
      | Id | Name | Kind   |
      | M  | Yard | LADDER |
    And interlocking "X" has these wires:
      | Pins               |
      | 1.C Yard.track 3.C |
    When the layout is derived
    Then it is reported as an error on "M"

  @ladder.leg
  Scenario: a leg that reaches neither a trailing point nor an end of track
    Given interlocking "X" has these appliances:
      | Name | Appliance | Style   | TC  |
      | 9    | switch    | powered | 9T1 |
      | 1    | switch    | powered | 1T1 |
    And interlocking "X" has these policies:
      | Id | Name | Kind   |
      | M  | Yard | LADDER |
    And interlocking "X" has these wires:
      | Pins               |
      | 9.R Yard.track 1.C |
      | 1.N E1.EoT         |
    And interlocking "X" has these devices:
      | Name | Appliance |
      | Yard | selector  |
    When the layout is derived
    Then it is reported as missing on "M"
    And selector "Yard" offers "1R: 1R; 1N: 1N"

  @ladder.shared
  Scenario: two ladders that share a switch
    Given interlocking "X" has these appliances:
      | Name | Appliance | Style   | TC  |
      | 9    | switch    | powered | 9T1 |
      | 1    | switch    | powered | 1T1 |
    And interlocking "X" has these policies:
      | Id | Name   | Kind   |
      | M  | Yard   | LADDER |
      | P  | Lead   | LADDER |
    And interlocking "X" has these wires:
      | Pins                          |
      | 9.R Yard.track Lead.track 1.C |
      | 1.R E1.EoT                    |
      | 1.N E2.EoT                    |
    When the layout is derived
    Then it is reported as an error on "1"
    And "1" has no derived ladder

  @ladder.selector
  Scenario: a ladder no selector serves
    Given interlocking "X" has these appliances:
      | Name | Appliance | Style   | TC  |
      | 9    | switch    | powered | 9T1 |
      | 1    | switch    | powered | 1T1 |
    And interlocking "X" has these policies:
      | Id | Name | Kind   |
      | M  | Yard | LADDER |
    And interlocking "X" has these wires:
      | Pins               |
      | 9.R Yard.track 1.C |
      | 1.R E1.EoT         |
      | 1.N E2.EoT         |
    When the layout is derived
    Then it is reported as information on "M"
    And "1" has derived ladder "X:Yard"
    And "1" has no derived selector

  @selector.ladder
  Scenario: a selector whose Name names no ladder
    Given interlocking "X" has these devices:
      | Name    | Appliance |
      | Nowhere | selector  |
    When the layout is derived
    Then it is reported as an error on "0"
    And selector "Nowhere" offers no choices

  # Who sends a selector's choice (the owner, 2026-11-13). A selector is in no column. Its choice goes to the station
  # that owns its ladder's switches; that station's CODE button sends it, with the levers of its column, as ordinary
  # controls. VAL shows the choice, PRESS locks it in, CODE sends the locked choice.

  @selector.code
  Scenario: the station's CODE button sends the choice the selector's PRESS locks in
    Given interlocking "X" is on an AAR token code line
    And interlocking "X" has these appliances:
      | Name | Appliance | Style   | TC  | CP Name |
      | 9    | switch    | powered | 9T1 | East    |
      | 1    | switch    | powered | 1T1 | East    |
    And interlocking "X" has these policies:
      | Id | Name | Kind   |
      | M  | Yard | LADDER |
    And interlocking "X" has these wires:
      | Pins               |
      | 9.R Yard.track 1.C |
      | 1.R E1.EoT         |
      | 1.N E2.EoT         |
    And interlocking "X" has these devices:
      | Name | Appliance |
      | Yard | selector  |
    And selector "Yard" binds VAL to "Desk/0x50/ENC" and PRESS to "Desk/0x50/Press"
    And the desk has these columns:
      | Column | CP Name | Interlocking |
      | 13     | East    | X            |
    And the desk has a CODE button on column "13" bound to "Desk/0x2D/B5"
    When the layout is derived
    Then selector "Yard" goes to station "X"
    And selector "Yard" is sent by the CODE button of column "Desk:13"
    And selector "Yard" shows its choice on "Desk/0x50/ENC", locks it in on "Desk/0x50/Press" and sends it on "Desk/0x2D/B5"
    And it is not reported

  @selector.code
  Scenario: a station with no CODE button
    Given interlocking "X" is on an AAR token code line
    And interlocking "X" has these appliances:
      | Name | Appliance | Style   | TC  |
      | 9    | switch    | powered | 9T1 |
      | 1    | switch    | powered | 1T1 |
    And interlocking "X" has these policies:
      | Id | Name | Kind   |
      | M  | Yard | LADDER |
    And interlocking "X" has these wires:
      | Pins               |
      | 9.R Yard.track 1.C |
      | 1.R E1.EoT         |
      | 1.N E2.EoT         |
    And interlocking "X" has these devices:
      | Name | Appliance |
      | Yard | selector  |
    And selector "Yard" binds VAL to "Desk/0x50/ENC" and PRESS to "Desk/0x50/Press"
    When the layout is derived
    Then it is reported as missing on "0"
    And selector "Yard" goes to station "X"
    And selector "Yard" is sent by no CODE button

  @selector.codes
  Scenario: a station with two CODE buttons
    Which button sends the choice is not stated, so none is chosen.
    Given interlocking "X" is on an AAR token code line
    And interlocking "X" has these appliances:
      | Name | Appliance | Style   | TC  |
      | 9    | switch    | powered | 9T1 |
      | 1    | switch    | powered | 1T1 |
    And interlocking "X" has these policies:
      | Id | Name | Kind   |
      | M  | Yard | LADDER |
    And interlocking "X" has these wires:
      | Pins               |
      | 9.R Yard.track 1.C |
      | 1.R E1.EoT         |
      | 1.N E2.EoT         |
    And interlocking "X" has these devices:
      | Name | Appliance |
      | Yard | selector  |
    And selector "Yard" binds VAL to "Desk/0x50/ENC" and PRESS to "Desk/0x50/Press"
    And the desk has these columns:
      | Column | CP Name | Interlocking |
      | 13     | X       | X            |
      | 14     | X       | X            |
    And the desk has a CODE button on column "13" bound to "Desk/0x2C/B5"
    And the desk has a CODE button on column "14" bound to "Desk/0x2D/B5"
    When the layout is derived
    Then it is reported as a warning on "0"
    And selector "Yard" is sent by no CODE button

  @selector.input
  Scenario: a selector whose PRESS is wired to nothing
    Given interlocking "X" has these appliances:
      | Name | Appliance | Style   | TC  |
      | 9    | switch    | powered | 9T1 |
      | 1    | switch    | powered | 1T1 |
    And interlocking "X" has these policies:
      | Id | Name | Kind   |
      | M  | Yard | LADDER |
    And interlocking "X" has these wires:
      | Pins               |
      | 9.R Yard.track 1.C |
      | 1.R E1.EoT         |
      | 1.N E2.EoT         |
    And interlocking "X" has these devices:
      | Name | Appliance |
      | Yard | selector  |
    And selector "Yard" binds VAL to "Desk/0x50/ENC"
    When the layout is derived
    Then it is reported as missing on "0"

  @selector.station
  Scenario: a ladder whose switches are in two stations
    On a US&S 506 line each house is a station; one station receives a choice.
    Given interlocking "X" has houses "East, West"
    And interlocking "X" is on a US&S 506 code line
    And interlocking "X" has these appliances:
      | Name | Appliance | Style   | TC  | CP Name |
      | 9    | switch    | powered | 9T1 | East    |
      | 1    | switch    | powered | 1T1 | East    |
      | 3    | switch    | powered | 3T1 | West    |
    And interlocking "X" has these policies:
      | Id | Name | Kind   |
      | M  | Yard | LADDER |
    And interlocking "X" has these wires:
      | Pins               |
      | 9.R Yard.track 1.C |
      | 1.R E1.EoT         |
      | 1.N 3.C            |
      | 3.N E2.EoT         |
      | 3.R E3.EoT         |
    And interlocking "X" has these devices:
      | Name | Appliance |
      | Yard | selector  |
    And selector "Yard" binds VAL to "Desk/0x50/ENC" and PRESS to "Desk/0x50/Press"
    When the layout is derived
    Then it is reported as an error on "0"
    And selector "Yard" goes to no station

  # Where the dispatcher's control ends, the ladder ends (the owner, 2026-11-14). The dispatcher controls a switch
  # whose regime is powered or dual; a local, hand-throw, spring or electrically locked switch is not the dispatcher's.

  Scenario Outline: a facing switch the dispatcher does not control ends the ladder
    Given interlocking "X" has these appliances:
      | Name | Appliance | Style    | TC  |
      | 9    | switch    | powered  | 9T1 |
      | 1    | switch    | powered  | 1T1 |
      | 3    | switch    | <regime> | 3T1 |
    And interlocking "X" has these policies:
      | Id | Name | Kind   |
      | M  | Yard | LADDER |
    And interlocking "X" has these wires:
      | Pins               |
      | 9.R Yard.track 1.C |
      | 1.R E1.EoT         |
      | 1.N 3.C            |
      | 3.N E2.EoT         |
      | 3.R E3.EoT         |
    And interlocking "X" has these devices:
      | Name | Appliance |
      | Yard | selector  |
    When the layout is derived
    Then selector "Yard" offers "<choices>"

    Examples: powered and dual are the dispatcher's
      | regime  | choices                     |
      | powered | 1R: 1R; 3R: 1N 3R; 3N: 1N 3N |
      | dual    | 1R: 1R; 3R: 1N 3R; 3N: 1N 3N |

    Examples: every other regime ends the ladder at the switch
      | regime        | choices        |
      | local         | 1R: 1R; 1N: 1N |
      | manual        | 1R: 1R; 1N: 1N |
      | manual_sensed | 1R: 1R; 1N: 1N |
      | spring        | 1R: 1R; 1N: 1N |
      | lock          | 1R: 1R; 1N: 1N |

  @ladder.start
  Scenario: a ladder whose first facing switch the dispatcher does not control
    Given interlocking "X" has these appliances:
      | Name | Appliance | Style   | TC  |
      | 9    | switch    | powered | 9T1 |
      | 1    | switch    | manual  | 1T1 |
    And interlocking "X" has these policies:
      | Id | Name | Kind   |
      | M  | Yard | LADDER |
    And interlocking "X" has these wires:
      | Pins               |
      | 9.R Yard.track 1.C |
      | 1.R E1.EoT         |
      | 1.N E2.EoT         |
    When the layout is derived
    Then it is reported as missing on "M"

  Scenario: a derail the dispatcher controls is a ladder member, set to REVERSE by every choice through it
    Given interlocking "X" has these appliances:
      | Name | Appliance | Style          | TC  |
      | 9    | switch    | powered        | 9T1 |
      | 1    | switch    | powered        | 1T1 |
      | 3    | switch    | powered        | 3T1 |
      | 27   | switch    | derail,powered |     |
      | 29   | switch    | derail,dual    |     |
    And interlocking "X" has these policies:
      | Id | Name | Kind   |
      | M  | Yard | LADDER |
    And interlocking "X" has these wires:
      | Pins               |
      | 9.R Yard.track 1.C |
      | 1.R 29.C           |
      | 29.R E1.EoT        |
      | 1.N 27.C           |
      | 27.R 3.C           |
      | 3.N E2.EoT         |
      | 3.R E3.EoT         |
    And interlocking "X" has these devices:
      | Name | Appliance |
      | Yard | selector  |
    When the layout is derived
    Then selector "Yard" offers "1R: 1R 29R; 3R: 1N 27R 3R; 3N: 1N 27R 3N"
    And ladder "M" starts at "X:9.R" with switches "X:1, X:29, X:27, X:3"
    And "27" has derived selector "X:Yard"

  Scenario: a derail the dispatcher does not control ends the ladder
    Given interlocking "X" has these appliances:
      | Name | Appliance | Style         | TC  |
      | 9    | switch    | powered       | 9T1 |
      | 1    | switch    | powered       | 1T1 |
      | 3    | switch    | powered       | 3T1 |
      | 27   | switch    | derail,manual |     |
    And interlocking "X" has these policies:
      | Id | Name | Kind   |
      | M  | Yard | LADDER |
    And interlocking "X" has these wires:
      | Pins               |
      | 9.R Yard.track 1.C |
      | 1.R E1.EoT         |
      | 1.N 27.C           |
      | 27.R 3.C           |
      | 3.N E2.EoT         |
      | 3.R E3.EoT         |
    And interlocking "X" has these devices:
      | Name | Appliance |
      | Yard | selector  |
    When the layout is derived
    Then selector "Yard" offers "1R: 1R; 1N: 1N"
    And ladder "M" starts at "X:9.R" with switches "X:1"

  # The choice's controls (the owner, 2026-11-14): switch-position demands, not tokens.

  Scenario: the station receives each choice's switch-position demands
    A selector spells no token; the station's lever controls are unchanged.
    Given interlocking "X" is on an AAR token code line
    And interlocking "X" has these appliances:
      | Name | Appliance | Style   | TC  | CP Name |
      | 9    | switch    | powered | 9T1 | East    |
      | 1    | switch    | powered | 1T1 | East    |
      | 3    | switch    | powered | 3T1 | East    |
    And interlocking "X" has these policies:
      | Id | Name | Kind   |
      | M  | Yard | LADDER |
    And interlocking "X" has these wires:
      | Pins               |
      | 9.R Yard.track 1.C |
      | 1.R E1.EoT         |
      | 1.N 3.C            |
      | 3.N E2.EoT         |
      | 3.R E3.EoT         |
    And interlocking "X" has these devices:
      | Name | Appliance |
      | Yard | selector  |
    And selector "Yard" binds VAL to "Desk/0x50/ENC" and PRESS to "Desk/0x50/Press"
    And the desk has these columns:
      | Column | CP Name | Interlocking |
      | 13     | X       | X            |
    And the desk has a CODE button on column "13" bound to "Desk/0x2D/B5"
    When the layout is derived
    Then selector "Yard" offers "1R: 1R; 3R: 1N 3R; 3N: 1N 3N"
    And the demands station "X" receives are "1 NORMAL, 1 REVERSE, 3 NORMAL, 3 REVERSE"
    And station "X" receives nothing

  @switch.lever.selector
  Scenario: a ladder switch a desk lever also works
    One control source works a switch.
    Given interlocking "X" has these appliances:
      | Name | Appliance | Style   | TC  |
      | 9    | switch    | powered | 9T1 |
      | 1    | switch    | powered | 1T1 |
    And interlocking "X" has these policies:
      | Id | Name | Kind   |
      | M  | Yard | LADDER |
    And interlocking "X" has these wires:
      | Pins               |
      | 9.R Yard.track 1.C |
      | 1.R E1.EoT         |
      | 1.N E2.EoT         |
    And interlocking "X" has these devices:
      | Name | Appliance |
      | Yard | selector  |
    And the desk has these levers for interlocking "X":
      | Name | Style  |
      | 1    | switch |
    When the layout is derived
    Then it is reported as an error on "1"
