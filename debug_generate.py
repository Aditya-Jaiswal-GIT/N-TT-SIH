import json
from app_with_navigation import app
from scheduler import TimetableGenerator
from models import db

if __name__ == '__main__':
    with app.app_context():
        # Enable maximize_fill so ILP will try to fill as many timetable cells as possible
        gen = TimetableGenerator(db, config={"maximize_fill": True, "assign_reward": 20, "min_violation_penalty": 1000})
        res = gen.generate()
        print(json.dumps(res, indent=2, default=str))
