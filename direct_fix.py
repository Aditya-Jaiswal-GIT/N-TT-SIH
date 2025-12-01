"""
Direct fix for faculty capacity - increase max_hours_per_week for all faculty
"""

from app_with_navigation import app
from models import db, Faculty, Course
from scheduler import TimetableGenerator


def direct_fix():
    with app.app_context():
        # Calculate what we need
        gen = TimetableGenerator(db)
        context = gen._load_context()
        
        total_sessions = len(context['sessions'])
        faculty_count = len(context['faculty'])
        
        target_hours = int((total_sessions / faculty_count) + 5)  # Add buffer
        
        print(f"📊 Current State:")
        print(f"   - Total sessions needed: {total_sessions}")
        print(f"   - Faculty count: {faculty_count}")
        print(f"   - Hours per faculty needed: {total_sessions / faculty_count:.1f}")
        print(f"   - Target max_hours: {target_hours}\n")
        
        # Update all faculty
        faculty_list = Faculty.query.all()
        
        for faculty in faculty_list:
            # Set max hours high enough
            faculty.max_hours_per_week = target_hours
            
            # Set min hours to reasonable value
            faculty.min_hours_per_week = min(4, target_hours // 3)
            
            # Ensure they have expertise
            if not faculty.expertise or not faculty.expertise.strip():
                courses = Course.query.all()
                course_codes = [c.code for c in courses]
                faculty.expertise = ','.join(course_codes[:20])  # Give them 20 courses
        
        # Commit changes
        try:
            db.session.commit()
            print("✅ Database updated successfully!")
        except Exception as e:
            print(f"❌ Error: {e}")
            db.session.rollback()
            return False
        
        # Verify
        faculty_list = Faculty.query.all()
        total_capacity = sum(f.max_hours_per_week for f in faculty_list)
        total_minimum = sum(f.min_hours_per_week for f in faculty_list)
        
        print(f"\n📊 Updated State:")
        print(f"   - Total capacity: {total_capacity} hours")
        print(f"   - Total minimum: {total_minimum} hours")
        print(f"   - Sessions needed: {total_sessions} hours")
        
        if total_capacity >= total_sessions:
            print(f"\n✅ SUCCESS! Capacity is now sufficient!")
            print(f"   Surplus: {total_capacity - total_sessions} hours\n")
            
            # Run bound analyzer
            print("🔍 Running bound analysis...")
            result = gen._run_bound_analyzer(context)
            
            if result['feasible']:
                print("✅ Bound analysis PASSED!")
                print("\n💡 You can now generate the timetable from the web interface!")
                return True
            else:
                print("⚠️ Bound analysis still has warnings:")
                for warning in result['warnings']:
                    print(f"   {warning}")
                return False
        else:
            print(f"\n⚠️ Still short by {total_sessions - total_capacity} hours")
            print("\n💡 You may need to:")
            print("   1. Reduce number of student groups")
            print("   2. Reduce course hours_per_week")
            print("   3. Add more faculty")
            return False


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("🔧 DIRECT FACULTY CAPACITY FIX")
    print("=" * 70 + "\n")
    
    direct_fix()
