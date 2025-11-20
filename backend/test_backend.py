"""Quick test script to verify backend functionality."""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from runner import AgentManager


async def test_basic_workflow():
    """Test basic agent workflow without interruption."""
    print("=== Testing Basic Workflow ===\n")
    
    manager = AgentManager()
    
    # Test 1: Flight query
    print("Test 1: Flight search")
    task_id = await manager.handle_user_message("test_user_1", "Find flights from NYC to LAX")
    print(f"Task ID: {task_id}")
    
    # Wait for completion
    await asyncio.sleep(3)
    status = manager.get_status("test_user_1")
    print(f"Status: {status}\n")
    
    # Test 2: Hotel query
    print("Test 2: Hotel search")
    task_id = await manager.handle_user_message("test_user_2", "Find hotels in Paris")
    print(f"Task ID: {task_id}")
    
    await asyncio.sleep(3)
    status = manager.get_status("test_user_2")
    print(f"Status: {status}\n")
    
    # Test 3: Combined query
    print("Test 3: Combined search")
    task_id = await manager.handle_user_message("test_user_3", "I need flights and hotels for Miami")
    print(f"Task ID: {task_id}")
    
    await asyncio.sleep(4)
    status = manager.get_status("test_user_3")
    print(f"Status: {status}\n")


async def test_interruption():
    """Test workflow interruption and partial result preservation."""
    print("=== Testing Interruption Flow ===\n")
    
    manager = AgentManager()
    
    # Start a workflow
    print("Starting workflow...")
    task_id = await manager.handle_user_message("test_user_interrupt", "Find flights and hotels for Tokyo")
    print(f"Task ID: {task_id}")
    
    # Interrupt after 1 second
    await asyncio.sleep(1)
    print("\nInterrupting workflow...")
    await manager.interrupt("test_user_interrupt")
    
    # Check status
    await asyncio.sleep(0.5)
    status = manager.get_status("test_user_interrupt")
    print(f"Status after interruption: {status}\n")


async def main():
    """Run all tests."""
    try:
        await test_basic_workflow()
        print("\n" + "="*50 + "\n")
        await test_interruption()
        print("\n✅ All tests completed!")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
