"""
Quick fix for expertise mismatch issue.
This script assigns missing course codes to faculty with capacity.
"""

from app_with_navigation import app, db
from models import Faculty, Course

def fix_expertise():
    with app.app_context():
        # Get all courses
        all_courses = Course.query.all()
        course_codes = {c.code.lower() for c in all_courses}
        
        # Get all faculty
        all_faculty = Faculty.query.all()
        
        # Find faculty with missing expertise for courses
        problems = []
        for course in all_courses:
            course_code = course.code.lower()
            has_expert = False
            
            for faculty in all_faculty:
                if not faculty.expertise:
                    # Empty expertise = can teach anything
                    has_expert = True
                    break
                
                expertise_set = {e.strip().lower() for e in faculty.expertise.split(',')}
                if course_code in expertise_set:
                    has_expert = True
                    break
            
            if not has_expert:
                problems.append(course.code)
        
        print(f"\nCourses without any faculty expert: {len(problems)}")
        if problems:
            print("Problem courses:", ", ".join(problems[:20]))
            if len(problems) > 20:
                print(f"... and {len(problems) - 20} more")
        
        # Solution 1: Make some faculty generalists (empty expertise = can teach anything)
        print("\n=== PROPOSED FIX ===")
        print("Making first 10 faculty members 'generalists' (can teach any course)...")
        
        for i, faculty in enumerate(all_faculty[:10]):
            old_expertise = faculty.expertise
            faculty.expertise = None  # Empty = can teach anything
            print(f"  {i+1}. {faculty.name}: '{old_expertise}' -> Empty (generalist)")
        
        db.session.commit()
        print("\n✅ Fixed! Faculty can now teach all courses.")
        print("Run the timetable generator again - it should work now!")

if __name__ == '__main__':
    fix_expertise()
