Feature: A lever's controls go to its desk column's station
  A code line addresses stations. What a station is depends on the line's encoding (ADR 0009 §3.12 "House is a
  station", "506 station address"; the owner, 2026-10-27 and 2026-10-28): on a US&S 506 line each house is a station,
  with its column number as its address, so a column must name a house; on an AAR token line the interlocking is the
  one station, and a house a column names is location only. A desk lever's controls, and the indications it consumes,
  go to the station of the column it sits in, never to the station of the appliance it works: that station does all
  the code line work for the lever, and its field unit drives appliances in other houses internally, unseen by the
  office. A lamp has nothing to do with columns: its token belongs to the station of the appliance that reports it.
  Stations are computed on demand from the derived file (tools/railroad/codeline.py); nothing is stored per station.

  Background: Luchessa, three houses, a switch in each of two and a signal
    Given interlocking "Luchessa" has houses "Luchessa, Gilroy, Carnadero"
    And interlocking "Luchessa" has these appliances:
      | Name   | Appliance     | Style   | Kind       | TC    | CP Name   | signal | heads | relations.facing | Indication |
      | 783    | switch        | powered | CONTROLLED | 783T1 | Luchessa  |        |       |                  | 783T1K     |
      | 795    | switch        | lock    |            | 795T1 | Gilroy    |        |       |                  | 795T1K     |
      | 784EAB | mast          | double  | CONTROLLED |       | Luchessa  | 784    | A,B   | RIGHT            |            |
      | 1T     | track_circuit |         |            |       | Carnadero |        |       |                  | 1TK        |
    And the desk has these columns:
      | Column | CP Name   | Interlocking |
      | 1      | Luchessa  | Luchessa     |
      | 2      | Gilroy    | Luchessa     |
      | 3      | Carnadero | Luchessa     |

  Scenario: on a US&S 506 line each house is a station and a lever's controls go to its column's house
    Given interlocking "Luchessa" is on a US&S 506 code line
    And the desk has these levers:
      | Name | Style  | Column | Controls       | Indications   |
      | 783  | switch | 1      | 783NWS, 783RWS | 783NWK, 783RWK |
      | 784  | signal | 1      | 784NGS, 784SGS | 784NGK, 784SGK |
      | 795  | lock   | 2      | 795WLS         | 795WLK         |
    When the layout is derived
    Then the stations of "Luchessa" are "Luchessa:Luchessa, Luchessa:Gilroy, Luchessa:Carnadero"
    And station "Luchessa:Luchessa" receives "783NWS, 783RWS, 784NGS, 784SGS"
    And station "Luchessa:Luchessa" must send "783NWK, 783RWK, 784NGK, 784SGK"
    And station "Luchessa:Gilroy" receives "795WLS"
    And station "Luchessa:Gilroy" must send "795WLK"
    And station "Luchessa:Carnadero" receives nothing

  Scenario: on an AAR token line the interlocking is the one station, whatever house a column names
    Given interlocking "Luchessa" is on an AAR token code line
    And the desk has these levers:
      | Name | Style  | Column | Controls       | Indications |
      | 783  | switch | 1      | 783NWS, 783RWS | 783NWK      |
      | 795  | lock   | 2      | 795WLS         | 795WLK      |
    When the layout is derived
    Then the stations of "Luchessa" are "Luchessa"
    And station "Luchessa" receives "783NWS, 783RWS, 795WLS"
    And station "Luchessa" must send "783NWK, 795WLK"

  Scenario: the station is the lever's column, not the house of the appliance it works
    Given interlocking "Luchessa" is on a US&S 506 code line
    And the desk has these levers:
      | Name | Style | Column | Controls | Indications |
      | 795  | lock  | 1      | 795WLS   | 795WLK      |
    When the layout is derived
    Then station "Luchessa:Luchessa" receives "795WLS"
    And station "Luchessa:Luchessa" must send "795WLK"
    And station "Luchessa:Gilroy" receives nothing

  Scenario: a lamp's token belongs to the station of the appliance that reports it, whatever column
    Given interlocking "Luchessa" is on a US&S 506 code line
    And the desk has these lamps for interlocking "Luchessa":
      | Name | Indication     |
      | 1TL  | 1TK            |
      | 795L | 795T1K \| 1TK  |
    When the layout is derived
    Then station "Luchessa:Carnadero" must send "1TK"
    And station "Luchessa:Gilroy" must send "795T1K"
    And station "Luchessa:Luchessa" must send nothing

  @column.cp_name
  Scenario: a column with no CP Name on a US&S 506 line
    Given interlocking "Luchessa" is on a US&S 506 code line
    And the desk has these columns:
      | Column | CP Name | Interlocking |
      | 4      |         | Luchessa     |
    When the layout is derived
    Then it is reported as missing on "4"

  @column.house
  Scenario: a column naming the interlocking on a US&S 506 line
    Given interlocking "Sargent" has house "Sargent East"
    And interlocking "Sargent" is on a US&S 506 code line
    And the desk has these columns:
      | Column | CP Name | Interlocking |
      | 4      | Sargent | Sargent      |
    When the layout is derived
    Then it is reported as an error on "4"

  @column.house
  Scenario: a column naming the interlocking on an AAR token line is location only
    Given interlocking "Sargent" has house "Sargent East"
    And interlocking "Sargent" is on an AAR token code line
    And the desk has these columns:
      | Column | CP Name | Interlocking |
      | 4      | Sargent | Sargent      |
    When the layout is derived
    Then it is not reported

  @station.columns
  Scenario: one house on two columns of a US&S 506 line
    Given interlocking "Luchessa" is on a US&S 506 code line
    And the desk has these columns:
      | Column | CP Name | Interlocking |
      | 4      | Gilroy  | Luchessa     |
    When the layout is derived
    Then it is reported as an error on "Gilroy"

  @reference.station
  Scenario: a lamp token that appliances of two houses report on a US&S 506 line
    Given interlocking "Luchessa" is on a US&S 506 code line
    And interlocking "Luchessa" has these appliances:
      | Name | Appliance     | CP Name  | Indication |
      | 2T   | track_circuit | Luchessa | 2TK        |
      | 3T   | track_circuit | Gilroy   | 2TK        |
    And the desk has these lamps for interlocking "Luchessa":
      | Name | Indication |
      | 2TL  | 2TK        |
    When the layout is derived
    Then it is reported as a warning on "0"
