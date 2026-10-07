## Electric Lock Protocol

Operating an electrically locked hand switch using Association of American Railroads (AAR) standard nomenclature and Centralized Traffic Control (CTC) codeline protocols involves a strict sequence of transmission tokens (control and indication bits), vital logic, and physical operations. [1, 2, 3] 
------------------------------
### Step 1: Crew Request & Local Initialization

   1. Radio Request: The train crew contacts the train dispatcher via radio or wayside phone to request permission to unlock a specific hand-throw switch. [4, 5] 
   2. Opening the Lock Box: Upon verbal permission, a crew member removes the padlock and opens the door of the electric lock box. [6] 
   3. Signal Tumbledown: Opening the door triggers a local mechanical circuit breaker. This forces all absolute signals governing movement over the switch to immediately "tumble down" to their most restrictive aspect (Stop). [5, 7] 

### Step 2: Field-to-Office Indication Code (Field Token Transmission)
Once the signals are verified at Stop, the wayside field station initiates an indication cycle to send data back to the dispatching office over the physical code line: [1, 2] 

* Station Selection Steps: The field unit transmits its unique identification pulse sequence to grab the line.
* Signal Status Tokens: Sends the Stop Indication Bit (RGK), confirming that protecting signals are red. [3, 5, 7] 
* Track Circuit Tokens: Sends track occupancy states (TK/AK bits), indicating if a train is closely approaching or already occupying the circuit. [3, 8, 9] 
* Unlock Request Token: Transmits the active request bit (NWK/LPK variants), visually alerting the dispatcher's system that the field box is open and awaiting a command. [2, 6] 

### Step 3: Dispatcher Approval & Office-to-Field Control Code (Office Token Transmission)
The dispatcher observes the flashing unlock request light on their computer-aided dispatch (CAD) or physical CTC machine. To approve the request: [1, 2] 

   1. Lever Positioning: The dispatcher moves the corresponding switch lever from Normal to Reverse (Unlocked). [2, 3, 10] 
   2. Code Execution: The dispatcher presses the "Code Start" button. [2] 
   3. Control Code Transmission: The office system packetizes and transmits a control code down the line containing:
   * Station Code: Targets the precise field station hosting the switch.
      * Unlock Control Token (WZ/WL code bit): A specific vital bit programmed to change the state of the wayside lock relay. [1, 2, 4] 
   
### Step 4: Vital Logic Validation & Final Execution
When the field station receives the Unlock Control Token, it routes the request through local vital safety relays: [2, 4] 

* Approach/Time Locking Verification: If the track circuits are clear, the unlock is granted immediately. If a train is approaching, a vital time-locking relay (TE) starts a countdown timer (typically 5 to 10 minutes) to prevent a sudden derailment. [3, 8, 9] 
* Relay Energization: Once safety parameters are validated or the timer expires, the Switch Lock Relay (WL) energizes. [4, 5, 11] 
* Physical Release: An internal armature drops inside the lock box, causing the physical indicator to move from "Locked" to "Unlocked". The crew member can now safely throw the hand switch lever to line the track for their route. [2, 6, 10] 


[1] [https://www.researchgate.net](https://www.researchgate.net/publication/360816207_CIXL_Moving_Block_Research_Project)
[2] [https://ctcparts.com](http://ctcparts.com/?page_id=322)
[3] [https://www.scribd.com](https://www.scribd.com/document/913441464/AAR-Signal-Section-Circuit-nomenclature-written-circuits-and-graphical-symbols-1946-10)
[4] [https://www.scribd.com](https://www.scribd.com/document/259938916/Chapter-7-Communication-and-Signals)
[5] [https://www.scribd.com](https://www.scribd.com/document/259938916/Chapter-7-Communication-and-Signals)
[6] [https://www.arcinfra.com](https://www.arcinfra.com/ARCInfrastructure/media/documents/NetworkSafeworking/9024-Operation-of-Switchlocks-version-1-0.pdf)
[7] [https://www.law.cornell.edu](https://www.law.cornell.edu/cfr/text/49/236.314)
[8] [https://www.law.cornell.edu](https://www.law.cornell.edu/cfr/text/49/236.410)
[9] [https://www.law.cornell.edu](https://www.law.cornell.edu/cfr/text/49/236.207)
[10] [https://ctcparts.com](http://ctcparts.com/?page_id=322)
[11] [https://quizlet.com](https://quizlet.com/1191352500)

