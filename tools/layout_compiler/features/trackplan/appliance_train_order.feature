Feature: A train order board is not on the track
  A train order board is drawn beside the track at its station.
  It has no track pin. A pin of it on a track net is an error.
  It has no head pin. A trackplan head wired to it is the retired drawing: its faces are its field device's units.

  Background:
    Given this drawing of interlocking "X":
      | Ref | Symbol                              | Role      | Kind    | Appliance     | Name   | Station | Interlocking |
      | ST1 | Railroad-Trackplan:Station          | STRUCTURE | STATION |               | Gilroy |         |              |
      | TC1 | Railroad-Trackplan:Track Circuit    | APPLIANCE |         | track_circuit | 1NAT   |         |              |
      | NX1 | Railroad-Trackplan:NextCP           | TRACK     | NEXT_CP |               |        |         | Lick         |
      | TO1 | Railroad-Trackplan:Train Order Mast | APPLIANCE |         | train_order   | Gilroy | Gilroy  |              |

  @train_order.track
  Scenario: a board with a pin on the track
    Given these nets:
      | Net | Pins                  |
      | w   | TC1.TC NX1.To TO1.H   |
    When the drawing is imported
    Then it is reported as an error on "TO1"

  @train_order.track
  Scenario: a board beside the track
    Given these nets:
      | Net | Pins            |
      | w   | TC1.TC NX1.To   |
    When the drawing is imported
    Then it is not reported
    And "Gilroy" states the relation station "Gilroy"

  @train_order.heads
  Scenario: a board drawn with trackplan heads
    Given these symbols too:
      | Ref | Symbol                                     | Role      | Appliance | Style | Name |
      | HN  | Railroad-Trackplan:Signal Head - Semaphore-LQ | APPLIANCE | head   | LQ    | N    |
    And these nets:
      | Net | Pins            |
      | w   | TC1.TC NX1.To   |
      | h   | TO1.H HN.M      |
    When the drawing is imported
    Then it is reported as a warning on "TO1"
