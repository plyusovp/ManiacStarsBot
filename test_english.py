"""
Simple test for withdrawal system without Cyrillic characters.
"""

import asyncio
import hmac
import hashlib
import json
from typing import Dict, Any

from api_withdrawal import create_app_withdrawal_api, get_app_withdrawal_status


async def test_withdrawal_system():
    """Test the withdrawal system."""
    print("Testing withdrawal system from app to bot")
    print("=" * 60)
    
    # Test parameters
    user_id = 123456789
    amount = 100
    app_transaction_id = "test_tx_001"
    secret_key = "test_secret_key_123"
    
    print(f"Test parameters:")
    print(f"   User ID: {user_id}")
    print(f"   Amount: {amount} stars")
    print(f"   App Transaction ID: {app_transaction_id}")
    print()
    
    # Generate signature
    message = f"{user_id}:{amount}:{app_transaction_id}"
    signature = hmac.new(
        secret_key.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    print(f"Signature: {signature}")
    print()
    
    # Test 1: Create withdrawal request
    print("1. Testing withdrawal request creation...")
    result = await create_app_withdrawal_api(
        user_id=user_id,
        amount=amount,
        app_transaction_id=app_transaction_id,
        signature=signature,
        secret_key=secret_key,
        notes="Test withdrawal request"
    )
    
    print(f"   Result: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    if result["success"]:
        withdrawal_id = result["withdrawal_id"]
        print(f"   SUCCESS: Withdrawal request created with ID: {withdrawal_id}")
        print()
        
        # Test 2: Check withdrawal status
        print("2. Testing withdrawal status check...")
        status_result = await get_app_withdrawal_status(withdrawal_id)
        print(f"   Result: {json.dumps(status_result, ensure_ascii=False, indent=2)}")
        
        if status_result["success"]:
            print(f"   SUCCESS: Withdrawal status: {status_result['status']}")
        else:
            print(f"   ERROR: {status_result['message']}")
    else:
        print(f"   ERROR: {result['message']}")
    
    print()
    print("=" * 60)
    print("Testing completed")


async def main():
    """Main function to run tests."""
    try:
        await test_withdrawal_system()
    except Exception as e:
        print(f"ERROR during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Starting withdrawal system test")
    print("Note: Make sure database is initialized!")
    print()
    
    # Run tests
    asyncio.run(main())
