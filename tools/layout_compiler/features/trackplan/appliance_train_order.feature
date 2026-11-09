Feature: A train order board is not on the track
  A train order board is drawn beside the track at its station.
  It has no pins. A pin of it on a track net is an error.
  Its faces are the pins of its field mast device.

  Background:
    Given this drawing of interlocking "X":
      | Ref | Symbol                                     | Role      | Kind    | Appliance     | Style  | Name   | Station | Interlocking |
      | ST1 | Railroad-Trackplan:Station                 | STRUCTURE | STATION |               |        | Gilroy |         |              |
      | TC1 | Railroad-Trackplan:Track Circuit           | APPLIANCE |         | track_circuit |        | 1NAT   |         |              |
      | NX1 | Railroad-Trackplan:NextCP                  | TRACK     | NEXT_CP |               |        |        |         | Lick         |
      | TO1 | Railroad-Trackplan:Train Order Mast Double | APPLIANCE |         | train_order   | double | Gilroy | Gilroy  |              |

  @train_order.track
  Scenario: a board with a pin on the track
    Given these nets:
      | Net | Pins                |
      | w   | TC1.TC NX1.To TO1.H |
    When the drawing is imported
    Then it is reported as an error on "TO1"

  @train_order.track
  Scenario: a board beside the track
    Given these nets:
      | Net | Pins          |
      | w   | TC1.TC NX1.To |
    When the drawing is imported
    Then it is not reported
    And "Gilroy" states the relation station "Gilroy"
