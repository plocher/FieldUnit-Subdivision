# Part C Reference Models

## Purpose

This research informs vocabulary selection. It does not establish SPCoast plant facts, topology, or operating rules.

## JMRI PanelPro

JMRI Layout Editor is the relevant panel model because it captures drawn connectivity. Its documented primitives include track segments, anchors, end bumpers, edge connectors, turnouts, crossovers, slips, level crossings, turntables, and traversers. Segments reference typed connection points through stable identifiers.

PanelPro persistence is deliberately not adopted as the interchange format. Its `layout-config` XML combines panel data with global NamedBean managers, blocks, sensors, signals, and other JMRI configuration.

Part C adopts only the portable lessons: stable local identifiers, typed ports, node-edge-junction structure, explicit sheet seams, optional block/circuit references, and independently layered annotations.

Primary sources:

- [JMRI Layout Editor](https://www.jmri.org/help/en/package/jmri/jmrit/display/LayoutEditor.shtml)
- [JMRI Panel Editor](https://www.jmri.org/help/en/package/jmri/jmrit/display/PanelEditor.shtml)
- [JMRI Control Panel Editor](https://www.jmri.org/help/en/package/jmri/jmrit/display/ControlPanelEditor.shtml)
- [JMRI layout schema](https://github.com/JMRI/JMRI/blob/master/xml/schema/layout.xsd)
- [JMRI editor primitive schema](https://github.com/JMRI/JMRI/blob/master/xml/schema/types/editors.xsd)
- [JMRI block schemas](https://github.com/JMRI/JMRI/tree/master/xml/schema/types)

## JMRI OperationsPro

OperationsPro models an operating session around locations, tracks at locations, rolling stock, routes, trains, manifests, and location switch lists. Its location track categories include spur, yard, classification/interchange, and staging. An industry is normally represented through a spur and its load/schedule rules, rather than as an unrelated topology primitive.

Part C uses this as evidence for a later functional-intent vocabulary. It does not import OperationsPro's model, and its operational route is called a `TrainRoute` to prevent collision with the vital `SignalRoute` term.

Primary sources:

- [OperationsPro overview](https://www.jmri.org/help/en/package/jmri/jmrit/operations/Operations.shtml)
- [OperationsPro user guide](https://webserver.jmri.org/help/en/manual/JMRI_OPS_UsersGuide/Ops_Start.shtml)
- [Locations](https://webserver.jmri.org/help/en/manual/JMRI_OPS_UsersGuide/Ops_Locations_List.shtml)
- [Location track types](https://webserver.jmri.org/help/en/manual/JMRI_OPS_UsersGuide/Ops_AddLocations.shtml)
- [Spurs and industries](https://webserver.jmri.org/help/en/manual/JMRI_OPS_UsersGuide/Ops_AddSiding.shtml)
- [Yards](https://webserver.jmri.org/help/en/manual/JMRI_OPS_UsersGuide/Ops_AddYard.shtml)
- [Train building and manifests](https://webserver.jmri.org/help/en/manual/JMRI_OPS_UsersGuide/Ops_TrainsBuild.shtml)

## CATS and TrainCrew

CATS provides dispatch/session roles such as dispatcher, trainmaster, yardmaster, train crew, jobs, and crew assignments. It can exchange selected train information with JMRI Operations. This is useful prior art for keeping dispatch control and operations workflow adjacent but separate.

TrainCrew supplies browser-based tasks such as handbrake, air-brake, inspection, and switching procedures. It is useful prior art for a future `CrewTask` vocabulary, not for car routing or topology.

Primary sources:

- [CATS project](http://cats4ctc.wikidot.com/)
- [CATS and JMRI](https://www.jmri.org/community/connections/CATS/index.shtml)
- [CATS technical integration](https://www.jmri.org/help/en/html/doc/Technical/CATS.shtml)
- [TrainCrew](https://traincrew.conrail1285.com/)
- [TrainCrew source](https://github.com/ekapus/TrainCrew)
- [TrainCrew and JMRI](https://www.jmri.org/community/connections/TrainCrew/index.shtml)

## Adopted scope limit

Part C.A uses only the vocabulary needed to review plant diagrams and run deterministic through-train progression. Operations locations, car intent, manifests, crew assignments, and crew tasks are Part C.B inputs. They must not be used to infer topology or alter vital behavior.
