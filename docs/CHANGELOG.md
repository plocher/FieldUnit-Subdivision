# Changelog
## Unreleased
- Added KiCad harvest support for one-pin Track Circuit markers, one-pin Rule 251/261/6.28 policy markers, NextCP terminals, Main House, Maintainer Call, Route, and E/W mast suffixes.
- Made Track Circuit Value the authoritative controlled-segment name and added warning-level CP allocation validation against Main House Values.
- Added `dark_exit` routes at the IRJ before Rule 6.28 dark track; dark track and its bumper no longer enter route traversal or route-clear requirements.
- Added mast-head attachment validation from the netlist and route-level attached-head output without duplicating structural routes.
- Expanded the route table with heads, normalized LEFT/RIGHT demand, circuit roles, natural ordering, and updated Luchessa validation coverage.
- Added static route-indication evaluation with per-switch Normal/Reverse overrides, dark-exit caps, and fail-closed demand, correspondence, lock, occupancy, and circuit-health gates.
- Documented the signal-system glossary and the locally captured JMRI definition catalogue used to select future aspect profiles.
- Added the documented MVP indication vocabulary, including `ADVANCED_APPROACH` and diverging indication variants, to switch-property validation.
- Normalized switch indication input across case and space, hyphen, or underscore word separators.
