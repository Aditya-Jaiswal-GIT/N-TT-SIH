"""
Reduce Student Groups to Fix Constraint Issue
The main problem is having 50 student groups × 359 hours = 2224 sessions
"""

from app_with_navigation import app
from models import db, StudentGroup
from scheduler import TimetableGenerator


def reduce_student_groups():
    with app.app_context():
        groups = StudentGroup.query.all()
        
        print(f"📊 Current State:")
        print(f"   - Student groups: {len(groups)}\n")
        
        print("Student groups found:")
        for i, group in enumerate(groups[:10], 1):
            print(f"   {i}. {group.name}")
        if len(groups) > 10:
            print(f"   ... and {len(groups) - 10} more\n")
        
        print("\nOptions:")
        print("1. Keep only first 10 groups (recommended for testing)")
        print("2. Keep only first 15 groups")
        print("3. Keep only first 20 groups")
        print("4. Delete all groups and recreate 5 groups")
        print("5. Show current sessions impact")
        print("6. Exit")
        
        choice = input("\nEnter choice (1-6): ").strip()
        
        if choice == "5":
            gen = TimetableGenerator(db)
            context = gen._load_context()
            total_sessions = len(context['sessions'])
            faculty_capacity = sum(f.max_hours_per_week for f in context['faculty'])
            
            print(f"\n📊 Impact Analysis:")
            print(f"   - Current groups: {len(groups)}")
            print(f"   - Total sessions: {total_sessions}")
            print(f"   - Faculty capacity: {faculty_capacity}")
            print(f"   - Shortage: {total_sessions - faculty_capacity} hours")
            
            # Calculate scenarios
            for keep_count in [5, 10, 15, 20]:
                estimated_sessions = int(total_sessions * (keep_count / len(groups)))
                print(f"\n   With {keep_count} groups:")
                print(f"      - Estimated sessions: {estimated_sessions}")
                print(f"      - Status: {'✅ Feasible' if estimated_sessions <= faculty_capacity else '❌ Still short'}")
            return
        
        elif choice == "6":
            print("Exiting...")
            return
        
        # Determine how many to keep
        keep_count = {
            "1": 10,
            "2": 15,
            "3": 20
        }.get(choice)
        
        if choice == "4":
            # Delete all and recreate
            print("\n🗑️ Deleting all student groups...")
            StudentGroup.query.delete()
            db.session.commit()
            
            print("✨ Creating 5 new groups...")
            default_groups = ["CSE-A", "CSE-B", "IT-A", "ECE-A", "ME-A"]
            for name in default_groups:
                group = StudentGroup(
                    name=name,
                    description=f"Default group {name}",
                    total_students=60
                )
                db.session.add(group)
            
            db.session.commit()
            keep_count = 5
            groups = StudentGroup.query.all()
            
        elif keep_count:
            # Keep first N groups
            groups_to_delete = groups[keep_count:]
            print(f"\n🗑️ Deleting {len(groups_to_delete)} groups...")
            
            for group in groups_to_delete:
                db.session.delete(group)
            
            db.session.commit()
            groups = StudentGroup.query.all()
            
        else:
            print("❌ Invalid choice")
            return
        
        # Verify result
        gen = TimetableGenerator(db)
        context = gen._load_context()
        total_sessions = len(context['sessions'])
        faculty_capacity = sum(f.max_hours_per_week for f in context['faculty'])
        
        print(f"\n✅ Groups reduced to: {len(groups)}")
        print(f"\n📊 New State:")
        print(f"   - Student groups: {len(groups)}")
        print(f"   - Total sessions: {total_sessions}")
        print(f"   - Faculty capacity: {faculty_capacity}")
        
        if total_sessions <= faculty_capacity:
            print(f"   - ✅ Feasible! Surplus: {faculty_capacity - total_sessions} hours")
            
            # Run bound analysis
            print(f"\n🔍 Running bound analysis...")
            result = gen._run_bound_analyzer(context)
            
            if result['feasible']:
                print("✅ SUCCESS! All constraints satisfied!")
                print("\n💡 You can now generate the timetable!")
            else:
                print("⚠️ Some warnings:")
                for warning in result['warnings'][:5]:
                    print(f"   {warning}")
        else:
            print(f"   - ⚠️ Still short: {total_sessions - faculty_capacity} hours")
            print("\n💡 Try reducing to fewer groups or increase faculty capacity")


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("🔧 STUDENT GROUP REDUCER")
    print("=" * 70 + "\n")
    
    reduce_student_groups()
