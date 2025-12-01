"""
Fix Faculty Expertise Issue - Assign course codes to faculty members
This script will help resolve the "Bound analysis failed" error by ensuring
faculty members have the necessary expertise to teach available courses.
"""

from app_with_navigation import app
from models import db, Faculty, Course


def fix_faculty_expertise():
    with app.app_context():
        # Get all courses
        courses = Course.query.all()
        faculty_list = Faculty.query.all()
        
        if not courses:
            print("❌ No courses found in database. Please add courses first.")
            return
        
        if not faculty_list:
            print("❌ No faculty found in database. Please add faculty first.")
            return
        
        # Get all course codes
        course_codes = [c.code for c in courses]
        print(f"📚 Found {len(courses)} courses: {', '.join(course_codes[:10])}...")
        print(f"👥 Found {len(faculty_list)} faculty members\n")
        
        print("Choose an option:")
        print("1. Assign ALL course codes to ALL faculty (allows any faculty to teach any course)")
        print("2. Distribute courses evenly among faculty (each faculty gets subset of courses)")
        print("3. Assign courses to faculty who have empty expertise only")
        print("4. Show current expertise status and exit")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == "1":
            # Option 1: Give all faculty all courses
            updated = 0
            all_codes = ','.join(course_codes)
            
            for faculty in faculty_list:
                faculty.expertise = all_codes
                updated += 1
            
            db.session.commit()
            print(f"\n✅ Updated {updated} faculty members with all {len(course_codes)} course codes")
            
        elif choice == "2":
            # Option 2: Distribute evenly
            import math
            courses_per_faculty = max(3, math.ceil(len(courses) / len(faculty_list)))
            
            updated = 0
            for i, faculty in enumerate(faculty_list):
                start_idx = (i * courses_per_faculty) % len(course_codes)
                end_idx = start_idx + courses_per_faculty
                assigned_codes = course_codes[start_idx:end_idx]
                
                # Wrap around if needed
                if len(assigned_codes) < courses_per_faculty:
                    assigned_codes += course_codes[:courses_per_faculty - len(assigned_codes)]
                
                faculty.expertise = ','.join(assigned_codes)
                updated += 1
            
            db.session.commit()
            print(f"\n✅ Updated {updated} faculty members with ~{courses_per_faculty} courses each")
            
        elif choice == "3":
            # Option 3: Only update faculty with empty expertise
            all_codes = ','.join(course_codes)
            updated = 0
            
            for faculty in faculty_list:
                if not faculty.expertise or faculty.expertise.strip() == '':
                    faculty.expertise = all_codes
                    updated += 1
            
            db.session.commit()
            print(f"\n✅ Updated {updated} faculty members with empty expertise")
            print(f"ℹ️  {len(faculty_list) - updated} faculty already had expertise defined")
            
        elif choice == "4":
            # Option 4: Show status
            print("\n📊 Current Faculty Expertise Status:\n")
            empty_expertise = 0
            has_expertise = 0
            
            for faculty in faculty_list[:20]:  # Show first 20
                if not faculty.expertise or faculty.expertise.strip() == '':
                    print(f"❌ {faculty.name}: (empty)")
                    empty_expertise += 1
                else:
                    codes = faculty.expertise.split(',')
                    print(f"✅ {faculty.name}: {len(codes)} courses ({', '.join(codes[:3])}...)")
                    has_expertise += 1
            
            if len(faculty_list) > 20:
                print(f"\n... and {len(faculty_list) - 20} more faculty members")
            
            print(f"\n📊 Summary:")
            print(f"   - Faculty with expertise: {has_expertise}")
            print(f"   - Faculty without expertise: {empty_expertise}")
            return
        
        else:
            print("❌ Invalid choice")
            return
        
        # Verify the fix
        print("\n🔍 Verification:")
        faculty_with_expertise = sum(1 for f in Faculty.query.all() if f.expertise and f.expertise.strip())
        print(f"   ✅ {faculty_with_expertise}/{len(faculty_list)} faculty now have expertise")
        print("\n💡 Try generating the timetable again!")


if __name__ == '__main__':
    fix_faculty_expertise()
