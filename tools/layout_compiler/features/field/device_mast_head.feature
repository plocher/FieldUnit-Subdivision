Feature: A head's position is the mast pin its IND is wired to
  A field mast device has one pin for each head position: A, B, C, top down.
  A head has no name and no Head letter. The pin its IND is wired to is its position on that mast.
  Any number of heads may share a pin; one head is one position's.

  Scenario: two heads on a double mast
    Given this drawing of interlocking "X":
      | Ref | Symbol                            | Role   | Appliance | Style | Name   |
      | DM1 | Railroad-Field:Device-Mast-Double | DEVICE | mast      |       | 784EAB |
      | HD1 | Railroad-Field:Device-Head-TypeD  | DEVICE | head      | TypeD |        |
      | HD2 | Railroad-Field:Device-Head-SA     | DEVICE | head      | SA    |        |
    And these nets:
      | Net | Pins           |
      | a   | DM1.A HD1.IND  |
      | b   | DM1.B HD2.IND  |
    When the drawing is imported
    Then the head "HD1" is position "A" of "784EAB"
    And the head "HD2" is position "B" of "784EAB"

  Scenario: an anonymous head is not asked for a Name or a Head letter
    Given this drawing of interlocking "X":
      | Ref | Symbol                            | Role   | Appliance | Style | Name   |
      | DM1 | Railroad-Field:Device-Mast-Single | DEVICE | mast      |       | 784EA  |
      | HD1 | Railroad-Field:Device-Head-TypeD  | DEVICE | head      | TypeD |        |
    And these nets:
      | Net | Pins           |
      | a   | DM1.A HD1.IND  |
    When the drawing is imported
    Then nothing is reported on "HD1"

  @head.mast
  Scenario: a head wired to no mast
    Given this drawing of interlocking "X":
      | Ref | Symbol                           | Role   | Appliance | Style |
      | HD1 | Railroad-Field:Device-Head-TypeD | DEVICE | head      | TypeD |
    When the drawing is imported
    Then it is reported as missing on "HD1"

  @head.masts
  Scenario: two heads wired to one mast pin are both that position
    Given this drawing of interlocking "X":
      | Ref | Symbol                            | Role   | Appliance | Style | Name   |
      | DM1 | Railroad-Field:Device-Mast-Single | DEVICE | mast      |       | 784EA  |
      | HD1 | Railroad-Field:Device-Head-TypeD  | DEVICE | head      | TypeD |        |
      | HD2 | Railroad-Field:Device-Head-SA     | DEVICE | head      | SA    |        |
    And these nets:
      | Net | Pins                   |
      | a   | DM1.A HD1.IND HD2.IND  |
    When the drawing is imported
    Then the head "HD1" is position "A" of "784EA"
    And the head "HD2" is position "A" of "784EA"
    And it is not reported

  @head.masts
  Scenario: a head wired to two positions of one mast
    Given this drawing of interlocking "X":
      | Ref | Symbol                            | Role   | Appliance | Style | Name   |
      | DM1 | Railroad-Field:Device-Mast-Double | DEVICE | mast      |       | 784EAB |
      | HD1 | Railroad-Field:Device-Head-TypeD  | DEVICE | head      | TypeD |        |
    And these nets:
      | Net | Pins                 |
      | a   | DM1.A DM1.B HD1.IND  |
    When the drawing is imported
    Then it is reported as an error on "HD1"
