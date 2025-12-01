"""
Comprehensive Constraint Fixer for Timetable Generation
Resolves "Bound analysis failed" errors by adjusting system constraints
"""

from app_with_navigation import app
from models import db, Faculty, Course, StudentGroup
from scheduler import TimetableGenerator
import json


def analyze_current_state():
    """Analyze the current state and provide recommendations"""
    with app.app_context():
        gen = TimetableGenerator(db)
        context = gen._load_context()
        
        total_sessions = len(context['sessions'])
        faculty_count = len(context['faculty'])
        
        total_capacity = sum(f.max_hours_per_week for f in context['faculty'])
        total_minimum = sum(f.min_hours_per_week for f in context['faculty'])
        
        print("=" * 70)
        print("📊 TIMETABLE CONSTRAINT ANALYSIS")
        print("=" * 70)
        print(f"\n📚 Sessions: {total_sessions} total hours needed")
        print(f"👥 Faculty: {faculty_count} members")
        print(f"   - Total capacity: {total_capacity} hours/week")
        print(f"   - Total minimum: {total_minimum} hours/week")
        print(f"   - Gap: {total_sessions - total_capacity} hours SHORT")
        
        # Calculate what's needed
        avg_needed = total_sessions / faculty_count if faculty_count > 0 else 0
        
        print(f"\n💡 Analysis:")
        if total_sessions > total_capacity:
            print(f"   ❌ CRITICAL: Not enough faculty capacity!")
            print(f"   📊 Average hours needed per faculty: {avg_needed:.1f}")
            print(f"   📊 Current average max capacity: {total_capacity/faculty_count:.1f}")
            print(f"\n🔧 Recommended fixes:")
            print(f"   1. Increase faculty max_hours_per_week to ~{int(avg_needed)+2}")
            print(f"   2. Reduce course hours_per_week")
            print(f"   3. Add more faculty members")
            print(f"   4. Reduce number of student groups")
        else:
            print(f"   ✅ Capacity is sufficient")
        
        # Check course distribution
        courses = context['courses']
        groups = context['student_groups']
        
        print(f"\n📖 Courses: {len(courses)}")
        total_course_hours = sum(c.hours_per_week for c in courses)
        print(f"   - Total hours per course: {total_course_hours}")
        print(f"   - Sessions = {total_course_hours} × {len(groups)} groups = {total_sessions}")
        
        print(f"\n👨‍🎓 Student Groups: {len(groups)}")
        for g in groups[:5]:
            print(f"   - {g.name}")
        if len(groups) > 5:
            print(f"   ... and {len(groups) - 5} more")
        
        return {
            'total_sessions': total_sessions,
            'total_capacity': total_capacity,
            'faculty_count': faculty_count,
            'avg_needed': avg_needed,
            'shortage': total_sessions - total_capacity
        }


def fix_faculty_capacity(target_hours=None):
    """Increase faculty max_hours_per_week to meet demand"""
    with app.app_context():
        gen = TimetableGenerator(db)
        context = gen._load_context()
        
        total_sessions = len(context['sessions'])
        faculty_count = len(context['faculty'])
        
        if target_hours is None:
            target_hours = int((total_sessions / faculty_count) * 1.2)  # 20% buffer
        
        print(f"\n🔧 Fixing faculty capacity...")
        print(f"   Setting all faculty max_hours_per_week to: {target_hours}")
        
        updated = 0
        for faculty in Faculty.query.all():
            # Increase max hours
            faculty.max_hours_per_week = target_hours
            
            # Adjust min hours to be reasonable (not more than max)
            if faculty.min_hours_per_week > target_hours:
                faculty.min_hours_per_week = max(4, target_hours // 2)
            
            updated += 1
        
        db.session.commit()
        print(f"   ✅ Updated {updated} faculty members")
        
        # Verify
        total_capacity = sum(f.max_hours_per_week for f in Faculty.query.all())
        print(f"   📊 New total capacity: {total_capacity} hours")
        print(f"   📊 Sessions needed: {total_sessions} hours")
        
        if total_capacity >= total_sessions:
            print(f"   ✅ Capacity is now sufficient!")
            return True
        else:
            print(f"   ⚠️  Still short by {total_sessions - total_capacity} hours")
            return False


def reduce_course_hours():
    """Reduce hours_per_week for all courses"""
    with app.app_context():
        courses = Course.query.all()
        
        print(f"\n🔧 Reducing course hours...")
        print(f"   Current average: {sum(c.hours_per_week for c in courses) / len(courses):.1f} hours/week")
        
        updated = 0
        for course in courses:
            # Reduce by 20% but keep minimum of 1
            course.hours_per_week = max(1, int(course.hours_per_week * 0.8))
            updated += 1
        
        db.session.commit()
        print(f"   ✅ Reduced hours for {updated} courses")
        print(f"   📊 New average: {sum(c.hours_per_week for c in Course.query.all()) / len(courses):.1f} hours/week")


def ensure_faculty_expertise():
    """Make sure all faculty can teach some courses"""
    with app.app_context():
        courses = Course.query.all()
        faculty_list = Faculty.query.all()
        
        course_codes = [c.code for c in courses]
        all_codes = ','.join(course_codes)
        
        print(f"\n🔧 Ensuring faculty expertise...")
        
        updated = 0
        for faculty in faculty_list:
            if not faculty.expertise or len(faculty.expertise.split(',')) < 5:
                faculty.expertise = all_codes
                updated += 1
        
        db.session.commit()
        print(f"   ✅ Updated {updated} faculty members with all {len(course_codes)} courses")


def main():
    print("\n" + "=" * 70)
    print("🔧 TIMETABLE CONSTRAINT FIXER")
    print("=" * 70)
    
    # Step 1: Analyze
    stats = analyze_current_state()
    
    print("\n" + "=" * 70)
    print("🛠️  RECOMMENDED ACTIONS")
    print("=" * 70)
    
    print("\n1. Fix faculty capacity (increase max_hours_per_week)")
    print("2. Ensure faculty expertise (assign course codes)")
    print("3. Reduce course hours (reduce hours_per_week)")
    print("4. Run all fixes automatically")
    print("5. Exit")
    
    choice = input("\nEnter choice (1-5): ").strip()
    
    if choice == "1":
        target = input(f"Enter target hours per faculty (recommended: {int(stats['avg_needed'])+2}): ").strip()
        target = int(target) if target else None
        fix_faculty_capacity(target)
        
    elif choice == "2":
        ensure_faculty_expertise()
        
    elif choice == "3":
        reduce_course_hours()
        
    elif choice == "4":
        print("\n🚀 Running all fixes...")
        ensure_faculty_expertise()
        success = fix_faculty_capacity()
        
        if not success:
            print("\n⚠️  Still short on capacity, reducing course hours...")
            reduce_course_hours()
            fix_faculty_capacity()
        
        # Final verification
        print("\n" + "=" * 70)
        print("🔍 FINAL VERIFICATION")
        print("=" * 70)
        
        with app.app_context():
            gen = TimetableGenerator(db)
            context = gen._load_context()
            result = gen._run_bound_analyzer(context)
            
            if result['feasible']:
                print("\n✅ SUCCESS! Constraints are now satisfied!")
                print("💡 You can now generate the timetable.")
            else:
                print("\n⚠️  Issues remain:")
                for warning in result['warnings']:
                    print(f"   {warning}")
    
    elif choice == "5":
        print("\nExiting...")
        return
    
    else:
        print("❌ Invalid choice")


if __name__ == '__main__':
    main()
