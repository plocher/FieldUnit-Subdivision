Feature: The units of a train order device
  The field device of a train order board has one unit for each face: N or W, S or E.
  The board has the faces whose units are placed.
  Each unit's IND is wired to the head of its face.

  @pending
  Scenario: a device with two units placed
    Given this drawing of interlocking "X":
      | Ref | Symbol                                   | Role      | Appliance   | Style | Name   | Station | Unit |
      | TO1 | Railroad-Trackplan:Train Order Mast      | APPLIANCE | train_order |       | Gilroy | Gilroy  |      |
      | D1  | Railroad-Field-Signals:Device-TrainOrder | DEVICE    | train_order |       | Gilroy |         | N    |
      | D1  | Railroad-Field-Signals:Device-TrainOrder | DEVICE    | train_order |       | Gilroy |         | S    |
    When the drawing is imported
    Then "Gilroy" has faces "N, S"

  @pending
  Scenario: a device with one unit placed
    Given this drawing of interlocking "X":
      | Ref | Symbol                                   | Role      | Appliance   | Style | Name   | Station | Unit |
      | TO1 | Railroad-Trackplan:Train Order Mast      | APPLIANCE | train_order |       | Gilroy | Gilroy  |      |
      | D1  | Railroad-Field-Signals:Device-TrainOrder | DEVICE    | train_order |       | Gilroy |         | W    |
    When the drawing is imported
    Then "Gilroy" has faces "W"
