import re
from collections import defaultdict

def parse_ocr_to_fields(ocr_text: str):
    """
    Convert OCR text into a list of candidate fields and a JSON Schema.
    Returns: dict { fields: [...], json_schema: {...} }
    """
    fields = []
    schema_props = {}
    used_keys = set()
    text = ocr_text
    norm = text.replace("’","'").replace("\u2013","-").replace("\u2014","-")

    # 1) Label: value patterns
    for m in re.finditer(r'([A-Za-z0-9 \-/]{2,40}):\s*(.+)', norm):
        label = m.group(1).strip()
        val = m.group(2).strip()
        key = re.sub(r'[^a-z0-9_]+', '_', label.lower()).strip('_')
        if not key:
            continue
        if key in used_keys:
            i = 2
            while f"{key}_{i}" in used_keys:
                i += 1
            key = f"{key}_{i}"
        used_keys.add(key)
        fields.append({"key": key, "label": label, "hint": "", "sample_value": val})
        schema_props[key] = {"type":"string","title":label,"default":val}

    # 2) Repeated anchor detection (e.g., "who resides at")
    anchor_phrase = "who resides at"
    occurrences = [m.start() for m in re.finditer(re.escape(anchor_phrase), norm, flags=re.IGNORECASE)]
    if occurrences:
        lines = [ln.strip() for ln in norm.splitlines() if ln.strip()!='']
        anchor_lines_idx = []
        for i, ln in enumerate(lines):
            if anchor_phrase in ln.lower():
                anchor_lines_idx.append(i)
        idx_counter = defaultdict(int)
        for idx in anchor_lines_idx:
            name_candidate = ""
            if idx-1 >= 0:
                prev = lines[idx-1]
                if prev.lower() != 'x':
                    name_candidate = prev
            address_candidate = ""
            j = idx+1
            while j < len(lines) and "will allow" not in lines[j].lower() and "x" not in lines[j].lower():
                address_candidate += ((" " + lines[j]) if address_candidate else lines[j])
                j += 1
            base = "neighbor"
            idx_counter[base] += 1
            i_num = idx_counter[base]
            name_key = f"neighbor_{i_num}_name"
            addr_key = f"neighbor_{i_num}_address"
            name_sample = name_candidate if name_candidate else ""
            addr_sample = address_candidate if address_candidate else ""
            fields.append({"key": name_key, "label": f"Neighbor {i_num} - Name", "hint":"As written on form", "sample_value": name_sample})
            fields.append({"key": addr_key, "label": f"Neighbor {i_num} - Address", "hint":"Full address", "sample_value": addr_sample})
            schema_props[name_key] = {"type":"string","title":f"Neighbor {i_num} - Name","default":name_sample}
            schema_props[addr_key] = {"type":"string","title":f"Neighbor {i_num} - Address","default":addr_sample}

    # 3) Common single-line field patterns
    lines = norm.splitlines()
    for ln in lines:
        ln_stripped = ln.strip()
        if len(ln_stripped) < 3:
            continue
        low = ln_stripped.lower()
        if ('name' in low or 'owner' in low) and ':' in ln_stripped:
            parts = ln_stripped.split(':',1)
            label = parts[0].strip()
            val = parts[1].strip()
            key = re.sub(r'[^a-z0-9_]+', '_', label.lower()).strip('_')
            if key and key not in used_keys:
                used_keys.add(key)
                fields.append({"key": key, "label": label, "hint": "", "sample_value": val})
                schema_props[key] = {"type":"string","title":label,"default":val}

    # 4) Fallback raw_text
    if not fields:
        fields.append({"key":"raw_text","label":"Scanned Text","hint":"Full OCR text — edit to extract fields","sample_value": norm})
        schema_props["raw_text"] = {"type":"string","title":"Scanned Text","default":norm}
    else:
        schema_props["__raw_ocr_text"] = {"type":"string","title":"__raw_ocr_text","default":norm}

    json_schema = {"title":"Extracted Form","type":"object","properties": schema_props}
    return {"fields": fields, "json_schema": json_schema}
