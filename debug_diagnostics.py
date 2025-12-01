import json
from app_with_navigation import app
from scheduler import TimetableGenerator
from models import db


def run_diagnostics():
    with app.app_context():
        gen = TimetableGenerator(db)
        context = gen._load_context()

        # Precompute room capabilities and time_slots
        rooms = context.get('rooms', [])
        room_capabilities = context.get('room_capabilities', {})
        time_slots = context.get('time_slots', [])

        results = []
        sessions = context.get('sessions', [])

        for faculty in context.get('faculty', []):
            faculty_id = faculty.id
            name = faculty.name
            min_h = faculty.min_hours_per_week or 0
            max_h = faculty.max_hours_per_week or 0
            avail_slots = context['faculty_availability'].get(faculty_id, set())
            available_slot_count = len(avail_slots)

            # Count possible sessions faculty could teach (expertise + room + availability)
            possible_session_count = 0
            missing_expertise = set()
            missing_room = set()

            for session in sessions:
                course = context['course_by_id'].get(session.course_id)
                if not course:
                    continue

                # expertise check
                eligible_fac = gen._faculty_for_course(course, [faculty], context.get('faculty_expertise', {}))
                if not eligible_fac:
                    missing_expertise.add(course.code)
                    continue

                # rooms check
                eligible_rooms = gen._rooms_for_course(course, rooms, room_capabilities)
                if not eligible_rooms:
                    missing_room.add(course.code)
                    continue

                # availability check: at least one slot where faculty is available
                if any(slot.id in avail_slots for slot in time_slots):
                    possible_session_count += 1

            results.append({
                'faculty_id': faculty_id,
                'name': name,
                'min_hours_per_week': min_h,
                'max_hours_per_week': max_h,
                'available_slots': available_slot_count,
                'possible_session_count': possible_session_count,
                'missing_expertise_for': sorted(list(missing_expertise))[:5],
                'missing_room_for': sorted(list(missing_room))[:5],
            })

        print(json.dumps({'summary': {
            'total_sessions': len(sessions),
            'faculty_count': len(context.get('faculty', [])),
            'time_slots': len(time_slots)
        }, 'per_faculty': results}, indent=2, default=str))


if __name__ == '__main__':
    run_diagnostics()
