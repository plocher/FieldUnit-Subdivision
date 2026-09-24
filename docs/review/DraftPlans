We've taken the original spcoast-ctc sketch in
    /Users/jplocher/Dropbox/Arduino/libraries/FieldUnit/examples/spcoast_ctc
that was built using historical XML files as "truth", and updated it to use the latest CP Luchessa json/kicad-derived "truth":
    /Users/jplocher/Dropbox/workspace/FieldUnit-Subdivision/runtime/ctc_desk/spcoast_ctc
The logic in the FieldUnit-Subdevision version has diverged so much from the original, both in the handling of the code button one-shot and the I2C expander interface that the sketch no longer works. The restoration/addition of the OLED display confirms that the I2C bits are not being handled correctly and the MQTT topic monotoring shows that nothing is being sent.
Worse, with so many changes, the new version is unusable as a before/after test of the CP Luchessa changes.

Time for a reset and a refocus:

The Goal:
Long term: We are creating a design provinance chain that starts with a KiCad schematic set that is compiled into a functional data model.
Among the uses for this data model are
  Use it for the creation of a functional field unit that represents the plant's appliances and devices
     - in the field, as a sketch that can control a microcontroller and its I/O capabilities to manage physical devices on a layout (i.e, an Arduino Sketch that uses I2C etc for I/O)
     - in the office, as an application that itself connects to microcontroller(s) in the field that manage the physical devices on a layout (i.e., a CMRInet Host that uses CMRI Nodes for I/O)
     - in a simulation, where users (or NPC autotomata) control the moving trains (FieldUnit-Studio holds the germ of this unrealized idea...)
     - in an emulation where the physical appliances are represented and introspected, allowing test vectors, debugging and replay of dynamic operations ( ./spcoast_virtual_plant is a simple version of this)

Meduim term: 
  - collect all the historical Control Point / Interlocking plant XML and Graffle docs and definitions for the "SPCoast Model Railroas layout", 
  - use that data to mechanically seed new KiCad Schematics with the appliance symbols
  - allow the user to curate / update them into high quality representations of theie data models.
  - identify and create "missing" data concepts:  the ctc machine itself, the structure of a field unit sketch, the scope of a dispatcher terratory, etc
     Concept: Identify every piece of data needed by that sketch to represent the plant and map them to the compiled data in the json data model -or- flag it as missing

Short term:

  - Prove that the KiCad/json work being done in FieldUnit-Subdicision is sufficient to generate a minimal viable subset on an already working ctc-machine sketch.
  - The spcoast-ctc sketch interacts via MQTT with the plant simulator ./spcoast_virtual_plant, and the two need to share the same protocol definitions.
  - Identify and fill gaps in the data model
  - Identify and build a plan for those that are not filled.  (I2C and bit mappings in the ctc machine, I2C / CMRI mappings in the field unit sketches, ...)

The Methodology:
Deal with the short term milestone spike:
Fork the existing FieldUnit spcoast-ctc example sketch 
Restore/add/create-new an OLED display mechanism to support debugging
prove it still works
Change the cp luchessa plant content to match the data coming from the KiCad/json work in FieldUnit-Subdivision.
prove it still works

Look back on what was done in this spike and address the systemic issues: the repo structures and content of fieldunit and subdivision leak abstractions everywhere - ctc internal details are hardcoded in general fieldunit library code, sketch behaviors and MQTT protocols are hidden in python programs...  DRY violations, design issues and unevolvable code issues abound.  Step back and help define a better structure that aligns with the long term goals above.  This may require eliminating/refactoring/renaming/... the fieldunit, fieldunit-subdivision and fieldunit-studio repos...

Done:
Initial: Baseline: does the current original fieldunit still work?
Operational: the new CP Luchessa definition slots in and works
complete: we have a solid foundation and plan to continue into the middle term activities