VALID_SKILLS = ["home", "pick", "place"]

def validate_plan(plan_json, scene_config):
    if "plan" not in plan_json:
        return False, "Thiếu key 'plan' trong chuỗi JSON."
    
    valid_objects = list(scene_config.get('objects', {}).keys())
    valid_zones = list(scene_config.get('zones', {}).keys())
    
    for step in plan_json["plan"]:
        skill = step.get("skill")
        if skill not in VALID_SKILLS:
            return False, f"Skill không hợp lệ: '{skill}'"
            
        if skill in ["pick", "place"]:
            obj = step.get("object")
            if obj not in valid_objects:
                return False, f"Vật thể không tồn tại trong scene: '{obj}'"
                
        if skill == "place":
            zone = step.get("zone")
            if zone not in valid_zones:
                return False, f"Vùng (zone) không tồn tại trong scene: '{zone}'"
                
    return True, "Kế hoạch hợp lệ."