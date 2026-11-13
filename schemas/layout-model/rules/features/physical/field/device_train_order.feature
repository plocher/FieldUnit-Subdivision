Feature: The faces of a train order board
  A train order board's field mast has one pin for each face: N and S, or E and W, on a double board; one pin on a single board.
  A face is a pin something is wired to: its head, and the fascia lever that serves it.
  A double board's face pin names the direction the face serves. A single board faces the way its glyph is turned.
  The lever has the inputs STOP and SLOW. Nothing asserted is CLEAR. SLOW is APPROACH. STOP is STOP.
  The most restrictive asserted input wins: STOP before SLOW.
  The control is local. No code line carries it.
  A face can show CLEAR and the word of each input its lever wires.

  Background:
    Given the timetable has station "Gilroy"
    And interlocking "Gilroy" has these appliances:
      | Name   | Appliance   | Style  | Station | relations.station |
      | Gilroy | train_order | double | Gilroy  | Gilroy            |

  Scenario: a double board with two faces
    Given train order mast "Gilroy" has a head on face "N"
    And train order mast "Gilroy" has a lever on face "N" wiring "STOP, SLOW"
    And train order mast "Gilroy" has a head on face "S"
    And train order mast "Gilroy" has a lever on face "S" wiring "STOP, SLOW"
    When the layout is derived
    Then "Gilroy" has faces "N, S"
    And the "N" face of "Gilroy" serves the direction "LEFT"
    And the "S" face of "Gilroy" serves the direction "RIGHT"

  Scenario: a single board faces the way it is drawn
    Given interlocking "Gilroy" has these appliances:
      | Name  | Appliance   | Style  | Station | relations.station | relations.facing |
      | North | train_order | single | Gilroy  | Gilroy            | RIGHT            |
    And train order mast "North" has a head on face "TO"
    And train order mast "North" has a lever on face "TO" wiring "STOP"
    When the layout is derived
    Then "North" has faces "TO"
    And the "TO" face of "North" serves the direction "RIGHT"

  @train_order.device
  Scenario: a board with no field mast device
    When the layout is derived
    Then it is reported as missing on "Gilroy"

  @train_order.device
  Scenario: a field mast with no face wired
    Given train order mast device "Gilroy" exists
    When the layout is derived
    Then it is reported as missing on "Gilroy"

  @train_order.lever
  Scenario: a face with no lever
    Given train order mast "Gilroy" has a head on face "N"
    When the layout is derived
    Then it is reported as missing on "Gilroy"

  @train_order.face
  Scenario: a double board's face that names no direction
    Given train order mast "Gilroy" has a lever on face "A" wiring "STOP"
    When the layout is derived
    Then it is reported as an error on "Gilroy"

  @train_order.face
  Scenario: a single board turned a quarter
    Given interlocking "Gilroy" has these appliances:
      | Name  | Appliance   | Style  | Station | relations.station |
      | North | train_order | single | Gilroy  | Gilroy            |
    And train order mast "North" has a lever on face "TO" wiring "STOP"
    When the layout is derived
    Then it is reported as an error on "North"

  @train_order.face
  Scenario: a single board with two faces wired
    Given interlocking "Gilroy" has these appliances:
      | Name  | Appliance   | Style  | Station | relations.station | relations.facing |
      | North | train_order | single | Gilroy  | Gilroy            | LEFT             |
    And train order mast "North" has a lever on face "E" wiring "STOP"
    And train order mast "North" has a lever on face "W" wiring "STOP"
    When the layout is derived
    Then it is reported as an error on "North"

  @train_order.face
  Scenario: a face two levers serve
    Given train order mast "Gilroy" has a lever on face "N" wiring "STOP"
    And train order mast "Gilroy" has a lever on face "N" wiring "SLOW"
    When the layout is derived
    Then it is reported as an error on "Gilroy"

  Scenario: a face shows what its lever's wired inputs can ask for
    Given train order mast "Gilroy" has a lever on face "N" wiring "STOP, SLOW"
    When the layout is derived
    Then the "N" face of "Gilroy" can show "APPROACH, CLEAR, STOP"

  Scenario: a face whose lever wires no input shows CLEAR
    Given train order mast "Gilroy" has a lever on face "N" wiring "nothing"
    When the layout is derived
    Then the "N" face of "Gilroy" can show "CLEAR"

  Scenario Outline: what a face shows
    Given the "N" face of "Gilroy" has <inputs> asserted
    Then the "N" face of "Gilroy" shows "<indication>"

    Examples:
      | inputs        | indication |
      | nothing       | CLEAR      |
      | SLOW          | APPROACH   |
      | STOP          | STOP       |
      | STOP and SLOW | STOP       |

  Scenario: a face's inputs are ranked from the most restrictive, with the rest word
    Given train order mast "Gilroy" has a lever on face "N" wiring "SLOW, STOP"
    When the layout is derived
    Then the "N" face of "Gilroy" ranks "STOP=STOP, SLOW=APPROACH" and rests at "CLEAR"

  Scenario: a face whose lever wires one input ranks that one
    Given train order mast "Gilroy" has a lever on face "N" wiring "SLOW"
    When the layout is derived
    Then the "N" face of "Gilroy" ranks "SLOW=APPROACH" and rests at "CLEAR"

  Scenario: the layout's rulebook selects the words
    Given the user's train order inputs for rulebook "SP" rank "STOP=STOP, SLOW=RESTRICTING" and rest "CLEAR"
    And the layout states Rulebook "SP"
    And train order mast "Gilroy" has a lever on face "N" wiring "STOP, SLOW"
    When the layout is derived
    Then the "N" face of "Gilroy" ranks "STOP=STOP, SLOW=RESTRICTING" and rests at "CLEAR"
    And the "N" face of "Gilroy" can show "CLEAR, RESTRICTING, STOP"

  Scenario: the board's own Rest and Shows.<input> override the table, beside the item
    Given interlocking "Gilroy" has these appliances:
      | Name  | Appliance   | Style  | Station | relations.station | Rest     | Shows.SLOW  |
      | North | train_order | double | Gilroy  | Gilroy            | APPROACH | RESTRICTING |
    And train order mast "North" has a lever on face "N" wiring "STOP, SLOW"
    When the layout is derived
    Then the "N" face of "North" ranks "STOP=STOP, SLOW=RESTRICTING" and rests at "APPROACH"
    And the "N" face of "North" can show "APPROACH, RESTRICTING, STOP"
