Feature: A derail
  A derail is a switch with the word derail in its Style, ports C and R. The switch words name its regime:
  derail,powered; derail,dual; derail,local; derail,manual_sensed; derail,manual. It is worked as a switch of
  that word is: a powered derail by a desk lever, a dual one by the desk lever and the crew's Local-Lock and
  Local-Switch, a local one by a Local-Switch alone, a manual one by hand. A derail lever is a switch lever named
  for the derail; there is no derail lever word.
  A derail is dependent when its gang id names a switch or lock gang of the interlocking (ADR 0003 D8): it takes
  that switch's regime whatever its own word, and is worked through it. One drawn local or manual is a finding.
  A derail owns no OS circuit: no <name>T1, no TC. It lies in the circuit of the track its ports are on, as a
  lamp or contact does; a track circuit marker on that track names it. (The owner, 2026-11-09; GLOSSARY: derail)

  Background:
    Given interlocking "X" has house "East"
    And interlocking "X" has these appliances:
      | Name | Appliance     |
      | 1T   | track_circuit |
    And interlocking "X" has these joints:
      | Id | Kind |
      | J1 | IRJ  |

  Scenario: a dispatcher-controlled derail
    Given interlocking "X" has these appliances:
      | Name | Appliance | Style          |
      | 5    | switch    | derail,powered |
    And interlocking "X" has these wires:
      | Pins      |
      | 5.C 1T.TC |
    And the desk has these levers for interlocking "X":
      | Name | Style  |
      | 5    | switch |
    When the layout is derived
    Then "5" is powered
    And "5" follows no switch
    And nothing is reported on "5"

  Scenario: a dual-control derail
    Given interlocking "X" has these appliances:
      | Name | Appliance | Style       |
      | 5    | switch    | derail,dual |
    And interlocking "X" has these wires:
      | Pins      |
      | 5.C 1T.TC |
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

  Scenario: a local derail, worked from its Local-Derail alone
    Given interlocking "X" has these appliances:
      | Name | Appliance | Style        |
      | 5    | switch    | derail,local |
    And interlocking "X" has these wires:
      | Pins      |
      | 5.C 1T.TC |
    And interlocking "X" has these devices:
      | Name | Appliance | Style  |
      | 5    | lever     | switch |
    When the layout is derived
    Then "5" is powered
    And nothing is reported on "5"

  Scenario Outline: a hand-thrown derail, sensed or not
    Given interlocking "X" has these appliances:
      | Name | Appliance | Style   |
      | 5    | switch    | <style> |
    And interlocking "X" has these wires:
      | Pins      |
      | 5.C 1T.TC |
    When the layout is derived
    Then "5" is not powered
    And nothing is reported on "5"

    Examples:
      | style                |
      | derail,manual_sensed |
      | derail,manual        |

  Scenario: a dependent derail takes its switch's regime, an electric lock
    Given interlocking "X" has these appliances:
      | Name | Appliance | Style          | TC    |
      | 795  | switch    | lock           | 795T1 |
      | 795D | switch    | derail,powered |       |
    And interlocking "X" has these wires:
      | Pins        |
      | 1T.TC J1.A  |
      | J1.B 795.N  |
      | 795.R 795D.R |
    And the desk has these levers for interlocking "X":
      | Name | Style |
      | 795  | lock  |
    And interlocking "X" has these devices:
      | Name | Appliance | Style |
      | 795  | lever     | lock  |
    When the layout is derived
    Then "795D" follows switch "795"
    And "795D" is not powered
    And "795D" is on circuit "X:795T1"
    And "795D" has no derived osCircuit
    And nothing is reported on "795D"

  Scenario: a dependent derail takes its switch's regime, a powered switch
    Given interlocking "X" has these appliances:
      | Name | Appliance | Style         | TC    |
      | 783  | switch    | powered       | 783T1 |
      | 783D | switch    | derail,manual_sensed |  |
    And interlocking "X" has these wires:
      | Pins         |
      | 1T.TC J1.A   |
      | J1.B 783.N   |
      | 783.R 783D.R |
    And the desk has these levers for interlocking "X":
      | Name | Style  |
      | 783  | switch |
    When the layout is derived
    Then "783D" follows switch "783"
    And "783D" is powered
    And nothing is reported on "783D"

  Scenario: a derail of a gang with no bare member
    Given interlocking "X" has these appliances:
      | Name | Appliance | Style          | TC    |
      | 815A | switch    | powered        | 815T1 |
      | 815B | switch    | powered        | 815T1 |
      | 815D | switch    | derail,powered |       |
    And interlocking "X" has these wires:
      | Pins           |
      | 1T.TC J1.A     |
      | J1.B 815A.N     |
      | 815A.R 815B.R  |
      | 815B.N 815D.R  |
    And the desk has these levers for interlocking "X":
      | Name | Style  |
      | 815A | switch |
    When the layout is derived
    Then "815D" follows switch "815A"
    And "815D" is powered

  @derail.regime
  Scenario Outline: a dependent derail drawn as if worked on its own
    Given interlocking "X" has these appliances:
      | Name | Appliance | Style   | TC    |
      | 795  | switch    | lock    | 795T1 |
      | 795D | switch    | <style> |       |
    And interlocking "X" has these wires:
      | Pins         |
      | 1T.TC J1.A   |
      | J1.B 795.N   |
      | 795.R 795D.R |
    And the desk has these levers for interlocking "X":
      | Name | Style |
      | 795  | lock  |
    And interlocking "X" has these devices:
      | Name | Appliance | Style |
      | 795  | lever     | lock  |
    When the layout is derived
    Then it is reported as an error on "795D"

    Examples:
      | style         |
      | derail,local  |
      | derail,manual |

  Scenario: a derail lies in the circuit its ports are on
    Given interlocking "X" has these appliances:
      | Name | Appliance | Style          |
      | 5    | switch    | derail,powered |
    And interlocking "X" has these wires:
      | Pins      |
      | 5.C 1T.TC |
    And the desk has these levers for interlocking "X":
      | Name | Style  |
      | 5    | switch |
    When the layout is derived
    Then "5" stands on "X:1T"
    And "5" is on circuit "X:1T"
    And "5" has no derived osCircuit

  Scenario: a derail's TC is not read
    Given interlocking "X" has these appliances:
      | Name | Appliance | Style          | TC  |
      | 5    | switch    | derail,powered | 5T1 |
    And interlocking "X" has these wires:
      | Pins      |
      | 5.C 1T.TC |
    And the desk has these levers for interlocking "X":
      | Name | Style  |
      | 5    | switch |
    When the layout is derived
    Then "5" is on circuit "X:1T"
    And "5" has no derived osCircuit

  @switch.lever
  Scenario: an independent powered derail that no lever works
    Given interlocking "X" has these appliances:
      | Name | Appliance | Style          |
      | 5    | switch    | derail,powered |
    And interlocking "X" has these wires:
      | Pins      |
      | 5.C 1T.TC |
    When the layout is derived
    Then it is reported as missing on "5"
