import re
from typing import Dict

def inlineSvg(svg: str, props: Dict[str, str]) -> str:
    m = re.search(r'<svg([^>]*)>', svg)
    if not m:
        return svg
    attrs_str = m.group(1)
    
    attr_dict: Dict[str, str] = {}
    for attr_match in re.finditer(r'([A-Za-z0-9-]+)="([^"]*)"', attrs_str):
        attr_dict[attr_match.group(1)] = attr_match.group(2)
        
    for k, v in props.items():
        if v == "" and k in attr_dict:
            del attr_dict[k]
        elif v != "":
            attr_dict[k] = v
            
    if "width" in attr_dict and "height" in attr_dict and "viewBox" not in attr_dict:
        w = attr_dict["width"].replace("pt", "")
        h = attr_dict["height"].replace("pt", "")
        attr_dict["viewBox"] = f"0 0 {w} {h}"
        
    new_attrs = " ".join(f'{k}="{v}"' for k, v in attr_dict.items())
    return f"<svg {new_attrs}>" + svg[m.end():]
