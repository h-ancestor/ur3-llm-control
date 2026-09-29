# UR3 LLM Control – Bài thực hành 02

## 1. Giới thiệu

Hệ thống điều khiển robot UR3/UR3e bằng lệnh ngôn ngữ tự nhiên thông qua LLM và skill-based planning.

Luồng xử lý:

Natural Language Command
→ LLM Planner
→ Structured JSON Plan
→ Task Validator
→ Skill Executor
→ Robot Skills
→ MoveIt 2
→ UR3/UR3e

## 2. Robot Skills

Các skill được sử dụng:

- `home()`
- `pick(object)`
- `place(object, zone)`

## 3. Cấu trúc package

```text
ur3_llm_control/
├── config/
│   ├── scene.yaml
│   └── student_config.yaml
├── ur3_llm_control/
│   ├── llm_planner.py
│   ├── planning_scene.py
│   ├── robot_skills.py
│   ├── skill_executor.py
│   └── task_validator.py
├── resource/
├── test/
├── package.xml
├── setup.py
└── setup.cfg
