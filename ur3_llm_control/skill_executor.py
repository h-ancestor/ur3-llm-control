def execute_plan(plan_json, robot_skills):
    print("\nEXECUTION:")
    plan = plan_json.get("plan", [])
    
    for step in plan:
        skill = step.get("skill")
        
        if skill == "home":
            status = robot_skills.home()
            print(f"home() ................. {status}")
            
        elif skill == "pick":
            obj = step.get("object")
            status = robot_skills.pick(obj)
            print(f"pick({obj}) ........ {status}")
            
        elif skill == "place":
            obj = step.get("object")
            zone = step.get("zone")
            status = robot_skills.place(obj, zone)
            print(f"place({obj}, {zone}) {status}")
            
        if status != "SUCCESS":
            print(f"\nTASK FAILED AT STEP: {step}")
            return False
            
    print("\nTASK SUCCESS")
    return True