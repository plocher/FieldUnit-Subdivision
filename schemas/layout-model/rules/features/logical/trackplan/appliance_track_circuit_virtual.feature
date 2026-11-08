Feature: The block's one indication, a virtual track circuit
  A station-to-station block reaches the office as one indication: a virtual track circuit
  (Style virtual) whose Members are the block's circuits. The model states the members. A
  consumer qualifies it with the station that sends it; that the station is at one end of the
  block, and the token it puts on the code line, are the blocks and codeline libraries'. A
  block with no virtual circuit drawn has no name. (ADR 0013 §7.2, §9)

  Background: the block from Corporal to Sargent, drawn as X
    Given interlocking "X" has house "East"
    And interlocking "X" has these appliances:
      | Name | Appliance     |
      | 832T | track_circuit |
      | 834T | track_circuit |

  Scenario: a virtual circuit lists the block's circuits
    Given interlocking "X" has these appliances:
      | Name | Appliance     | Style   | Members   |
      | 831T | track_circuit | virtual | 832T,834T |
    When the layout is derived
    Then "831T" has members "X:832T, X:834T"

  @circuit.members
  Scenario: a virtual circuit that lists no members
    Given interlocking "X" has these appliances:
      | Name | Appliance     | Style   | Members |
      | 831T | track_circuit | virtual |         |
    When the layout is derived
    Then it is reported as missing on "831T"

  @circuit.member
  Scenario: a member that is no circuit of the interlocking
    Given interlocking "X" has these appliances:
      | Name | Appliance     | Style   | Members   |
      | 831T | track_circuit | virtual | 832T,999T |
    When the layout is derived
    Then it is reported as an error on "831T"

  Scenario: a member drawn in the next interlocking
    Given interlocking "Y" has these appliances:
      | Name | Appliance     |
      | 836T | track_circuit |
    And interlocking "X" has these appliances:
      | Name | Appliance     | Style   | Members          |
      | 831T | track_circuit | virtual | 832T,834T,Y:836T |
    When the layout is derived
    Then "831T" has members "X:832T, X:834T, Y:836T"

  @reference.unresolved
  Scenario: a member that the other interlocking does not have
    Given interlocking "Y" has these appliances:
      | Name | Appliance     |
      | 836T | track_circuit |
    And interlocking "X" has these appliances:
      | Name | Appliance     | Style   | Members     |
      | 831T | track_circuit | virtual | 832T,Y:999T |
    When the layout is derived
    Then it is reported as an error on "831T"

  @reference.interlocking
  Scenario: a member of an interlocking that is not in this file
    Given interlocking "X" has these appliances:
      | Name | Appliance     | Style   | Members         |
      | 831T | track_circuit | virtual | 832T,Lick:999T  |
    When the layout is derived
    Then it is reported as a warning on "831T"
