Feature: What works a switch
  A switch states how it is worked in its Style, one switch word: powered, dual, local, lock, manual_sensed, manual.
  Powered is ADR 0013 §4's seam word: the field unit knows the position and may move the points. Powered, dual and
  local are powered; lock, manual_sensed, manual and spring are not. A CP Name makes nothing powered.
  What works it is read from the lever devices named for it, on the desk or in the field, never assumed:
  a powered switch has a desk lever; a dual switch has the desk lever and, for the crew's release and throw by
  hand, a Local-Lock and a Local-Switch; a local switch has a Local-Switch alone, no desk lever and no lock;
  an electrically locked switch has the dispatcher's lock lever and the same field pair: a Local-Lock asking the
  release and a Local-Switch throwing the model's points, the switch device reporting the position (Christopher
  813 and 817 are the reference drawing); a sensed or plain manual switch has no lever at all.
  A powered, dual or local switch no switch lever works, and a locked switch with no Local-Switch, is missing its
  control source. A local switch with a desk lever, a dual or locked switch without a Local-Lock, and a hand-throw
  switch with any lever are findings. (The owner, 2026-11-09; GLOSSARY: powered switch, dual-control switch,
  electric lock)

  Background:
    Given interlocking "X" has house "East"
    And interlocking "X" has these appliances:
      | Name | Appliance     | TC   |
      | 1T   | track_circuit |      |

  Scenario: a powered switch, worked from the desk
    Given interlocking "X" has these appliances:
      | Name | Appliance | Style   | TC  |
      | 5    | switch    | powered | 5T1 |
    And interlocking "X" has these wires:
      | Pins      |
      | 5.N 1T.TC |
    And the desk has these levers for interlocking "X":
      | Name | Style  |
      | 5    | switch |
    When the layout is derived
    Then "5" is powered
    And nothing is reported on "5"

  Scenario: a dual-control switch, worked from the desk and by hand under a release
    Given interlocking "X" has these appliances:
      | Name | Appliance | Style | TC  |
      | 5    | switch    | dual  | 5T1 |
    And interlocking "X" has these wires:
      | Pins      |
      | 5.N 1T.TC |
    And the desk has these levers for interlocking "X":
      | Name | Style  |
      | 5    | switch |
    And interlocking "X" has these devices:
      | Name | Appliance | Style  |
      | 5    | lever     | lock   |
      | 5    | lever     | switch |
    When the layout is derived
    Then "5" is powered
    And nothing is reported on "5"

  Scenario: a local switch, worked from its Local-Switch alone
    Given interlocking "X" has these appliances:
      | Name | Appliance | Style | TC  |
      | 5    | switch    | local | 5T1 |
    And interlocking "X" has these wires:
      | Pins      |
      | 5.N 1T.TC |
    And interlocking "X" has these devices:
      | Name | Appliance | Style  |
      | 5    | lever     | switch |
    When the layout is derived
    Then "5" is powered
    And nothing is reported on "5"

  Scenario: an electrically locked switch, as Christopher's 813
    Given interlocking "X" has these appliances:
      | Name | Appliance | Style | TC    |
      | 813  | switch    | lock  | 813T1 |
    And interlocking "X" has these wires:
      | Pins        |
      | 813.N 1T.TC |
    And the desk has these levers for interlocking "X":
      | Name | Style |
      | 813  | lock  |
    And interlocking "X" has these devices:
      | Name | Appliance | Style  |
      | 813  | lever     | lock   |
      | 813  | lever     | switch |
    When the layout is derived
    Then "813" is not powered
    And nothing is reported on "813"

  @switch.lever
  Scenario: a locked switch with no Local-Switch
    Given interlocking "X" has these appliances:
      | Name | Appliance | Style | TC    |
      | 813  | switch    | lock  | 813T1 |
    And interlocking "X" has these wires:
      | Pins        |
      | 813.N 1T.TC |
    And the desk has these levers for interlocking "X":
      | Name | Style |
      | 813  | lock  |
    And interlocking "X" has these devices:
      | Name | Appliance | Style |
      | 813  | lever     | lock  |
    When the layout is derived
    Then it is reported as missing on "813"

  @switch.lock.local
  Scenario: a locked switch with no Local-Lock
    Given interlocking "X" has these appliances:
      | Name | Appliance | Style | TC    |
      | 813  | switch    | lock  | 813T1 |
    And interlocking "X" has these wires:
      | Pins        |
      | 813.N 1T.TC |
    And the desk has these levers for interlocking "X":
      | Name | Style |
      | 813  | lock  |
    And interlocking "X" has these devices:
      | Name | Appliance | Style  |
      | 813  | lever     | switch |
    When the layout is derived
    Then it is reported as missing on "813"

  Scenario Outline: a hand-throw switch, sensed or not, with no lever
    Given interlocking "X" has these appliances:
      | Name | Appliance | Style   |
      | 5    | switch    | <style> |
    And interlocking "X" has these wires:
      | Pins      |
      | 5.N 1T.TC |
    When the layout is derived
    Then "5" is not powered
    And nothing is reported on "5"

    Examples:
      | style         |
      | manual_sensed |
      | manual        |

  Scenario: a CP Name makes nothing powered
    Given interlocking "X" has these appliances:
      | Name | Appliance | Style  | CP Name |
      | 5    | switch    | manual | East    |
    And interlocking "X" has these wires:
      | Pins      |
      | 5.N 1T.TC |
    When the layout is derived
    Then "5" is not powered
    And nothing is reported on "5"

  @switch.lever
  Scenario Outline: a powered switch that no lever works
    Given interlocking "X" has these appliances:
      | Name | Appliance | Style   |
      | 5    | switch    | <style> |
    And interlocking "X" has these wires:
      | Pins      |
      | 5.N 1T.TC |
    When the layout is derived
    Then it is reported as missing on "5"

    Examples: the three powered regimes
      | style   |
      | powered |
      | dual    |
      | local   |

  @switch.lever
  Scenario: a lock lever alone does not work a powered switch
    Given interlocking "X" has these appliances:
      | Name | Appliance | Style   |
      | 5    | switch    | powered |
    And interlocking "X" has these wires:
      | Pins      |
      | 5.N 1T.TC |
    And the desk has these levers for interlocking "X":
      | Name | Style |
      | 5    | lock  |
    When the layout is derived
    Then it is reported as missing on "5"

  @switch.lever.desk
  Scenario: a local switch with a desk lever
    Given interlocking "X" has these appliances:
      | Name | Appliance | Style |
      | 5    | switch    | local |
    And interlocking "X" has these wires:
      | Pins      |
      | 5.N 1T.TC |
    And the desk has these levers for interlocking "X":
      | Name | Style  |
      | 5    | switch |
    And interlocking "X" has these devices:
      | Name | Appliance | Style  |
      | 5    | lever     | switch |
    When the layout is derived
    Then it is reported as an error on "5"

  @switch.lock.local
  Scenario: a dual switch with no Local-Lock
    Given interlocking "X" has these appliances:
      | Name | Appliance | Style |
      | 5    | switch    | dual  |
    And interlocking "X" has these wires:
      | Pins      |
      | 5.N 1T.TC |
    And the desk has these levers for interlocking "X":
      | Name | Style  |
      | 5    | switch |
    And interlocking "X" has these devices:
      | Name | Appliance | Style  |
      | 5    | lever     | switch |
    When the layout is derived
    Then it is reported as missing on "5"

  @switch.lever.hand
  Scenario Outline: a hand-throw switch with a lever
    Given interlocking "X" has these appliances:
      | Name | Appliance | Style   |
      | 5    | switch    | <style> |
    And interlocking "X" has these wires:
      | Pins      |
      | 5.N 1T.TC |
    And the desk has these levers for interlocking "X":
      | Name | Style  |
      | 5    | switch |
    When the layout is derived
    Then it is reported as an error on "5"

    Examples:
      | style         |
      | manual_sensed |
      | manual        |

  Scenario: a gang follower is worked through its lead
    Given interlocking "X" has these appliances:
      | Name | Appliance | Style   | TC    |
      | 815  | switch    | powered | 815T1 |
      | 815A | switch    | powered | 815T1 |
    And interlocking "X" has these wires:
      | Pins          |
      | 815.N 1T.TC   |
      | 815.R 815A.R  |
    And the desk has these levers for interlocking "X":
      | Name | Style  |
      | 815  | switch |
    When the layout is derived
    Then nothing is reported on "815A"
