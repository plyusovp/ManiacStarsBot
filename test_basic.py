"""
Basic test for withdrawal system without JSON output.
"""

import asyncio
import hmac
import hashlib
from database import db


async def test_basic():
    """Basic test of the withdrawal system."""
    print("Testing withdrawal system...")
    
    # Test parameters
    user_id = 123456789
    amount = 100
    app_transaction_id = "test_tx_001"
    
    print(f"User ID: {user_id}")
    print(f"Amount: {amount}")
    print(f"Transaction ID: {app_transaction_id}")
    
    # Test database connection
    try:
        # Try to create a withdrawal request
        result = await db.create_app_withdrawal(
            user_id=user_id,
            amount=amount,
            app_transaction_id=app_transaction_id,
            notes="Test withdrawal"
        )
        
        if result["success"]:
            print("SUCCESS: Withdrawal request created!")
            print(f"Withdrawal ID: {result['withdrawal_id']}")
            
            # Test getting withdrawal details
            details = await db.get_app_withdrawal_details(result['withdrawal_id'])
            if details["success"]:
                print("SUCCESS: Withdrawal details retrieved!")
                print(f"Status: {details['withdrawal']['status']}")
            else:
                print("ERROR: Could not get withdrawal details")
        else:
            print("ERROR: Could not create withdrawal request")
            print(f"Reason: {result.get('reason', 'Unknown')}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Starting basic withdrawal test...")
    asyncio.run(test_basic())
