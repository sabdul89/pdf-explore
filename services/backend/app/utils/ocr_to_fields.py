
import re
from collections import defaultdict
try:
    import spacy
    _nlp = None
    try:
        _nlp = spacy.load("en_core_web_sm")
    except Exception:
        # model may not be installed; handle gracefully
        _nlp = None
except Exception:
    _nlp = None

def extract_entities_with_spacy(text):
    if not _nlp:
        return []
    doc = _nlp(text)
    ents = [{"text": ent.text, "label": ent.label_} for ent in doc.ents]
    return ents

def parse_ocr_to_fields(ocr_text: str):
    norm = ocr_text.replace("’","'").replace("\u2013","-").replace("\u2014","-")
    fields = []
    props = {}
    used = set()

    # 1) repeated-block detection example for the fence form
    anchor = "who resides at"
    lines = [ln.strip() for ln in norm.splitlines() if ln.strip()!='']
    anchors_idx = [i for i,ln in enumerate(lines) if anchor in ln.lower()]
    counter = 0
    for idx in anchors_idx:
        counter += 1
        name = ""
        addr = ""
        if idx-1 >=0:
            candidate = lines[idx-1]
            if candidate.lower()!='x':
                name = candidate
        # gather address lines until 'will allow' or next anchor
        j = idx+1
        while j < len(lines) and "will allow" not in lines[j].lower() and "x" not in lines[j].lower():
            addr = (addr + " " + lines[j]).strip()
            j += 1
        k1 = f"neighbor_{counter}_name"
        k2 = f"neighbor_{counter}_address"
        fields.append({"key":k1,"label":f"Neighbor {counter} - Name","sample_value":name})
        fields.append({"key":k2,"label":f"Neighbor {counter} - Address","sample_value":addr})
        props[k1] = {"type":"string","title":f"Neighbor {counter} - Name","default":name}
        props[k2] = {"type":"string","title":f"Neighbor {counter} - Address","default":addr}

    # 2) generic label:value capture
    for m in re.finditer(r'([\w \/\-]{2,40}):\s*(.+)', norm):
        label = m.group(1).strip()
        val = m.group(2).strip()
        key = re.sub(r'[^a-z0-9_]+', '_', label.lower()).strip('_')
        if key in used:
            i = 2
            while f"{key}_{i}" in used:
                i += 1
            key = f"{key}_{i}"
        used.add(key)
        fields.append({"key":key,"label":label,"sample_value":val})
        props[key] = {"type":"string","title":label,"default":val}

    # 3) spaCy NER enrichment if available
    ents = extract_entities_with_spacy(norm)
    # Map PERSON -> possible name fields, GPE/LOC -> address
    person_idx = 0
    for ent in ents:
        if ent["label"] in ("PERSON",):
            person_idx += 1
            key = f"person_{person_idx}_name"
            if key not in props:
                props[key] = {"type":"string","title":f"Person {person_idx} - Name","default":ent["text"]}
                fields.append({"key":key,"label":f"Person {person_idx} - Name","sample_value":ent["text"]})
        if ent["label"] in ("GPE","LOC","FAC","ADDRESS"):
            key = f"place_{len(props)+1}"
            props[key] = {"type":"string","title":"Location","default":ent["text"]}
            fields.append({"key":key,"label":"Location","sample_value":ent["text"]})

    # 4) fallback raw_text if nothing found
    if not fields:
        props["raw_text"] = {"type":"string","title":"Scanned Text","default":norm}
        fields.append({"key":"raw_text","label":"Scanned Text","sample_value":norm})

    schema = {"title":"Extracted Form","type":"object","properties": props}
    return {"fields": fields, "json_schema": schema}
