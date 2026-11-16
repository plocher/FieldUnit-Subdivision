import sys, uuid
variant = sys.argv[1]          # "pinless" or "pinned"
U = lambda: str(uuid.uuid4())
root = U()
def prop(n, v, x, y, hide=False):
    return f'''(property "{n}" "{v}" (at {x} {y} 0) {'(hide yes)' if hide else ''} (show_name yes) (effects (font (size 1.27 1.27))))'''
def pin(name, num, x, y):
    return f'(pin passive line (at {x} {y} 180) (length 2.54) (name "{name}" (effects (font (size 1.27 1.27)))) (number "{num}" (effects (font (size 1.27 1.27)))))'
def unit(n, label, pins):
    return f'''(symbol "TOFace_{n}_1"
      (rectangle (start -5.08 2.54) (end 5.08 -2.54) (stroke (width 0.254) (type default)) (fill (type none)))
      (text "{label}" (at 0 0 0) (effects (font (size 1.27 1.27))))
      {" ".join(pins)})'''
pins_b = [pin("STOP", "2", 7.62, 0)] if variant == "pinned" else []
pins_c = [pin("SLOW", "3", 7.62, 0)] if variant == "pinned" else []
lib = f'''(symbol "Spike:TOFace" (exclude_from_sim no) (in_bom yes) (on_board yes)
    {prop("Reference","TOF",0,5.08)} {prop("Value","",0,-5.08)}
    {prop("Footprint","",0,0,True)} {prop("Datasheet","",0,0,True)} {prop("Description","spike",0,0,True)}
    {prop("Name","${{Value}}",0,0,True)} {prop("Address.MAST","",0,0,True)} {prop("Address.STOP","",0,0,True)} {prop("Address.SLOW","",0,0,True)}
    {unit(1,"MAST" if variant!="single" else "TO FACE",[pin("IOBus","1",7.62,0)])}
    {"" if variant=="single" else unit(2,"STOP",pins_b)}
    {"" if variant=="single" else unit(3,"SLOW",pins_c)})'''
def inst(u, x, addr):
    pins = {1: ['(pin "1" (uuid "%s"))' % U()], 2: ['(pin "2" (uuid "%s"))' % U()] if variant=="pinned" else [], 3: ['(pin "3" (uuid "%s"))' % U()] if variant=="pinned" else []}[u]
    fields = "".join(prop(k, v, x, 60 + 2.54*i) for i, (k, v) in enumerate(addr.items()))
    return f'''(symbol (lib_id "Spike:TOFace") (at {x} 50 0) (unit {u}) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid "{U()}")
    {prop("Reference","TOF1",x,45)} {prop("Value","Gilroy.E",x,55)} {prop("Footprint","",x,50,True)} {prop("Datasheet","",x,50,True)}
    {prop("Description","spike",x,50,True)} {prop("Name","${Value}",x,50,True)} {fields}
    {" ".join(pins)}
    (instances (project "spike" (path "/{root}" (reference "TOF1") (unit {u})))))'''
# each unit gets ONLY its own Address field set; the others empty
units = [inst(1, 50, {"Address.MAST": "101", "Address.STOP": "202", "Address.SLOW": "303"})] if variant=="single" else [inst(1, 50, {"Address.MAST": "101", "Address.STOP": "", "Address.SLOW": ""}),
         inst(2, 90, {"Address.MAST": "", "Address.STOP": "202", "Address.SLOW": ""}),
         inst(3, 130, {"Address.MAST": "", "Address.STOP": "", "Address.SLOW": "303"})]
label = '(label "IOBus" (at 57.62 50 0) (effects (font (size 1.27 1.27))) (uuid "%s"))' % U()
wire = '(wire (pts (xy 57.62 50) (xy 62.7 50)) (stroke (width 0) (type default)) (uuid "%s"))' % U()
nc = "".join('(no_connect (at %s 50) (uuid "%s"))' % (x, U()) for x in ((97.62, 137.62) if variant == "pinned" else ()))
print(f'''(kicad_sch (version 20260306) (generator "eeschema") (generator_version "10.0") (uuid "{root}") (paper "A4")
  (lib_symbols {lib})
  {label} {wire} {nc}
  {" ".join(units)}
  (sheet_instances (path "/" (page "1"))))''')
