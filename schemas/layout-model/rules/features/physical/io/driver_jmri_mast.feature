Feature: A JMRI signal mast driver publishes a mast's indication
  A JMRI signal mast driver is a whole-mast consumer: it takes the mast's indication for the positions on its net.
  A mast device's position pins are passive. What is wired to a pin says what it takes: a head its position's head word, the driver the mast's indication.
  Mixed wiring is allowed: a position wired to a head and the others to the driver.
  A head's own driver takes the indication for that head's position.
  We publish; JMRI does not run the mast. The topic is the channel prefix on the JMRI encoding and the driver's Address as its tail.
  The JMRI signal system (JMRI.SignalSystem, the signal system folder under JMRI's xml/signals) is a fact about each installation: the encoding names the usual one, a driver states its own when its appliance is of another era.
  The aspect name the driver sends is the translation table's row for the signal system, the indication and the mast's Kind.

  Background:
    Given the layout has these I/O encodings:
      | Name | Kind | Topic         | JMRI.SignalSystem | relations.transport | relations.processor |
      | JMRI | JMRI | jmri_channel/ | basic             | MQTT                | Field               |
    And interlocking "X" has these appliances:
      | Name   | Appliance | Kind       | Style  |
      | 778NAB | mast      | CONTROLLED | double |

  Scenario: a whole-mast consumer on every position
    Given processor "Field" has these drivers:
      | Key               | IC        | Kind       |
      | SIGNALMAST.778NAB | MQTT-JMRI | SIGNALMAST |
    And field mast device "778NAB" of interlocking "X" binds "A, B" to "Field/SIGNALMAST.778NAB/IND"
    When the layout is derived
    Then the driver "SIGNALMAST.778NAB" on "Field" stands in for positions "A, B" of "X:778NAB"

  Scenario: mixed wiring, one position to the driver and the other to a head
    Given processor "Field" has these drivers:
      | Key                 | IC        | Kind       |
      | SIGNALMAST.778NAB.B | MQTT-JMRI | SIGNALMAST |
    And field mast device "778NAB" of interlocking "X" binds "B" to "Field/SIGNALMAST.778NAB.B/IND"
    When the layout is derived
    Then the driver "SIGNALMAST.778NAB.B" on "Field" stands in for positions "B" of "X:778NAB"

  Scenario: a train order face's head has its own driver
    Given the timetable has station "Gilroy"
    And interlocking "X" has these appliances:
      | Name   | Appliance   | Style  | Station | relations.station |
      | Gilroy | train_order | double | Gilroy  | Gilroy            |
    And processor "Field" has these drivers:
      | Key                 | IC        | Kind       |
      | SIGNALMAST.Gilroy.E | MQTT-JMRI | SIGNALMAST |
    And train order mast "Gilroy" has a head on face "E"
    And train order mast "Gilroy" has a lever on face "E" wiring "STOP, SLOW"
    And the head on face "E" of "Gilroy" binds "APP" to "Field/SIGNALMAST.Gilroy.E/IND"
    When the layout is derived
    Then the driver "SIGNALMAST.Gilroy.E" on "Field" stands in for positions "E" of "X:Gilroy"

  Scenario: the topic is the channel prefix and the Address
    Given processor "Field" has these drivers:
      | Key               | Address | IC        | Kind       |
      | SIGNALMAST.778NAB | SM778   | MQTT-JMRI | SIGNALMAST |
    When the layout is derived
    Then the driver "SIGNALMAST.778NAB" on "Field" publishes to the topic "jmri_channel/SM778"

  Scenario: the encoding names the usual signal system
    Given processor "Field" has these drivers:
      | Key               | IC        | Kind       |
      | SIGNALMAST.778NAB | MQTT-JMRI | SIGNALMAST |
    When the layout is derived
    Then the driver "SIGNALMAST.778NAB" on "Field" uses the signal system "basic"

  Scenario: a driver of another era states its own signal system
    Given processor "Field" has these drivers:
      | Key               | IC        | Kind       | JMRI.SignalSystem |
      | SIGNALMAST.778NAB | MQTT-JMRI | SIGNALMAST | SPTCO-1969        |
    When the layout is derived
    Then the driver "SIGNALMAST.778NAB" on "Field" uses the signal system "SPTCO-1969"

  @driver.jmri.signal_system
  Scenario: no JMRI signal system stated anywhere
    Given the layout has these I/O encodings:
      | Name | Kind | Topic         | relations.transport | relations.processor |
      | JMRI | JMRI | jmri_channel/ | MQTT                | Field               |
    And processor "Field" has these drivers:
      | Key               | IC        | Kind       |
      | SIGNALMAST.778NAB | MQTT-JMRI | SIGNALMAST |
    When the layout is derived
    Then it is reported as missing on "SIGNALMAST.778NAB"

  @driver.signal_system.unknown
  Scenario: a signal system no table names
    Given processor "Field" has these drivers:
      | Key               | IC        | Kind       | JMRI.SignalSystem |
      | SIGNALMAST.778NAB | MQTT-JMRI | SIGNALMAST | SP-1890           |
    When the layout is derived
    Then it is reported as an error on "SIGNALMAST.778NAB"

  @pending @driver.aspect_name
  Scenario: a mast demands a word its signal system has no name for
    Given interlocking "X" has these appliances:
      | Name   | Appliance | Kind       | Style  | Indications                    |
      | 778NAB | mast      | CONTROLLED | double | STOP, ADVANCE_APPROACH, CLEAR  |
    And processor "Field" has these drivers:
      | Key               | IC        | Kind       | JMRI.SignalSystem |
      | SIGNALMAST.778NAB | MQTT-JMRI | SIGNALMAST | SPTCO-1969        |
    And field mast device "778NAB" of interlocking "X" binds "A, B" to "Field/SIGNALMAST.778NAB/IND"
    When the layout is derived
    Then it is reported as an error on "SIGNALMAST.778NAB"

  Scenario: the driver derives the aspect names it publishes, for its system and its mast's Kind
    Given processor "Field" has these drivers:
      | Key               | IC        | Kind       |
      | SIGNALMAST.778NAB | MQTT-JMRI | SIGNALMAST |
    And field mast device "778NAB" of interlocking "X" binds "A, B" to "Field/SIGNALMAST.778NAB/IND"
    When the layout is derived
    Then the driver "SIGNALMAST.778NAB" on "Field" publishes the aspect names "CLEAR=Clear, APPROACH=Approach, STOP=Stop, DIVERGING_CLEAR=Diverging Clear, DIVERGING_APPROACH=Diverging Approach, RESTRICTING=Restricting"
