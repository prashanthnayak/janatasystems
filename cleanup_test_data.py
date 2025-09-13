#!/usr/bin/env python3
"""
Cleanup script to remove test data from the database
"""

from database_setup import DatabaseManager

def cleanup_test_data():
    """Remove test cases from the database"""
    db = DatabaseManager()
    
    try:
        # Get all cases
        cases = db.get_all_cases()
        
        print(f"Found {len(cases)} cases in database")
        
        # List of test case patterns to remove
        test_patterns = [
            'smith vs johnson',
            'smith v johnson', 
            'test case',
            'sample case',
            'demo case',
            'johnson vs smith',
            'johnson v smith',
            'simulated case',
            'simulated'
        ]
        
        cases_to_delete = []
        
        for case in cases:
            case_title = case.get('case_title', '').lower()
            client_name = case.get('client_name', '').lower()
            
            # Check if this looks like test data
            is_test_case = False
            for pattern in test_patterns:
                if pattern in case_title or pattern in client_name:
                    is_test_case = True
                    break
            
            if is_test_case:
                cases_to_delete.append(case['cnr_number'])
                print(f"Found test case: {case.get('case_title')} (CNR: {case['cnr_number']})")
        
        if cases_to_delete:
            print(f"\nDeleting {len(cases_to_delete)} test cases...")
            
            for cnr in cases_to_delete:
                # Delete case history first (due to foreign key constraint)
                db.delete_case_history(cnr)
                # Then delete the case
                db.delete_case(cnr)
                print(f"Deleted case: {cnr}")
            
            print(f"✅ Successfully deleted {len(cases_to_delete)} test cases")
        else:
            print("✅ No test cases found to delete")
            
        # Show remaining cases
        remaining_cases = db.get_all_cases()
        print(f"\nRemaining cases: {len(remaining_cases)}")
        for case in remaining_cases:
            print(f"- {case.get('case_title')} (CNR: {case['cnr_number']})")
            
    except Exception as e:
        print(f"❌ Error cleaning up test data: {e}")

if __name__ == "__main__":
    cleanup_test_data() 