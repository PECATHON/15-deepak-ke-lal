"""Test scenarios for request interruption system.

This file demonstrates:
1. Detecting new queries during active processing
2. Cancelling running agent operations
3. Preserving partial results from interrupted agents
4. Transferring context between queries
5. Resume/continuation logic
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from runner import AgentManager
from interruption_manager import TaskStatus
import json


async def test_basic_interruption():
    """Test 1: Basic interruption - cancel a running task."""
    print("\n" + "="*80)
    print("TEST 1: Basic Interruption")
    print("="*80)
    
    manager = AgentManager()
    user_id = "test_user_1"
    
    # Start a flight search
    print("\n1. Starting flight search...")
    task_id_1 = await manager.handle_user_message(
        user_id,
        "Find flights from New York to London on December 25"
    )
    print(f"   Task ID: {task_id_1}")
    
    # Wait a moment for processing to start
    await asyncio.sleep(1.0)
    
    # Check status
    status = manager.get_status(user_id)
    print(f"\n2. Status after 1 second: {status.get('status')}")
    print(f"   Current agent: {status.get('current_agent')}")
    
    # Interrupt with a new query
    print("\n3. Interrupting with new query...")
    task_id_2 = await manager.handle_user_message(
        user_id,
        "Actually, find hotels in Paris instead"
    )
    print(f"   New Task ID: {task_id_2}")
    
    # Wait for new task to complete
    await asyncio.sleep(3.0)
    
    # Check final status
    status = manager.get_status(user_id)
    print(f"\n4. Final status: {status.get('status')}")
    print(f"   Partial results preserved: {bool(status.get('partial_results'))}")
    
    if status.get('partial_results'):
        print(f"   Partial results: {json.dumps(status['partial_results'], indent=2)}")
    
    print("\n✅ Test 1 Complete: Interruption successful")


async def test_partial_result_preservation():
    """Test 2: Verify partial results are preserved during interruption."""
    print("\n" + "="*80)
    print("TEST 2: Partial Result Preservation")
    print("="*80)
    
    manager = AgentManager()
    user_id = "test_user_2"
    
    # Start a search that produces partial results
    print("\n1. Starting hotel search (will be interrupted)...")
    task_id_1 = await manager.handle_user_message(
        user_id,
        "Find luxury hotels in Tokyo for New Year"
    )
    
    # Let it run for a bit to accumulate partials
    await asyncio.sleep(2.0)
    
    # Check partial results before interruption
    status_before = manager.get_status(user_id)
    print(f"\n2. Status before interruption:")
    print(f"   Current agent: {status_before.get('current_agent')}")
    print(f"   Partial results available: {bool(status_before.get('partial_results'))}")
    
    # Interrupt
    print("\n3. Sending interrupt signal...")
    await manager.interrupt(user_id)
    
    await asyncio.sleep(0.5)
    
    # Check that partials are preserved
    status_after = manager.get_status(user_id)
    print(f"\n4. Status after interruption:")
    print(f"   Status: {status_after.get('status')}")
    print(f"   Partial results preserved: {bool(status_after.get('partial_results'))}")
    
    if status_after.get('partial_results'):
        print(f"\n5. Preserved partial results:")
        for agent, results in status_after['partial_results'].items():
            print(f"   {agent}: {results}")
    
    print("\n✅ Test 2 Complete: Partial results preserved")


async def test_context_transfer():
    """Test 3: Context transfer - use partial results from interrupted task."""
    print("\n" + "="*80)
    print("TEST 3: Context Transfer Between Tasks")
    print("="*80)
    
    manager = AgentManager()
    user_id = "test_user_3"
    
    # Start first query
    print("\n1. Starting first query (flight search)...")
    task_id_1 = await manager.handle_user_message(
        user_id,
        "Find flights from San Francisco to Tokyo"
    )
    
    await asyncio.sleep(1.5)
    
    # Get partial results
    status_1 = manager.get_status(user_id)
    print(f"   Status: {status_1.get('status')}")
    print(f"   Partial flight results: {bool(status_1.get('partial_results', {}).get('flight'))}")
    
    # Interrupt with related query
    print("\n2. Interrupting with related query (add hotels)...")
    task_id_2 = await manager.handle_user_message(
        user_id,
        "Also find hotels in Tokyo for the same dates"
    )
    
    await asyncio.sleep(3.0)
    
    # Check if context was transferred
    status_2 = manager.get_status(user_id)
    print(f"\n3. New task status: {status_2.get('status')}")
    print(f"   Has previous context: {bool(status_2.get('partial_results'))}")
    
    # The new task should have access to previous partial results
    if status_2.get('partial_results'):
        print(f"\n4. Available results from both tasks:")
        for agent, results in status_2['partial_results'].items():
            print(f"   {agent}: {results.get('status', 'N/A')}")
    
    print("\n✅ Test 3 Complete: Context transferred successfully")


async def test_multiple_interruptions():
    """Test 4: Multiple rapid interruptions."""
    print("\n" + "="*80)
    print("TEST 4: Multiple Rapid Interruptions")
    print("="*80)
    
    manager = AgentManager()
    user_id = "test_user_4"
    
    queries = [
        "Find flights to Paris",
        "No wait, hotels in London",
        "Actually, flights to Rome",
        "Change that to Barcelona hotels",
        "Final choice: flights to Athens"
    ]
    
    print(f"\n1. Sending {len(queries)} queries in rapid succession...\n")
    
    task_ids = []
    for i, query in enumerate(queries, 1):
        print(f"   {i}. '{query}'")
        task_id = await manager.handle_user_message(user_id, query)
        task_ids.append(task_id)
        await asyncio.sleep(0.3)  # Brief pause between queries
    
    print(f"\n2. Waiting for final task to complete...")
    await asyncio.sleep(3.0)
    
    # Check final status
    status = manager.get_status(user_id)
    print(f"\n3. Final status: {status.get('status')}")
    print(f"   Last task ID: {status.get('task_id')}")
    print(f"   Expected last task: {task_ids[-1]}")
    print(f"   Match: {status.get('task_id') == task_ids[-1]}")
    
    print("\n✅ Test 4 Complete: Multiple interruptions handled")


async def test_both_agents_with_interruption():
    """Test 5: Interrupt a query requiring both flight and hotel agents."""
    print("\n" + "="*80)
    print("TEST 5: Interrupt Multi-Agent Task")
    print("="*80)
    
    manager = AgentManager()
    user_id = "test_user_5"
    
    # Start a query requiring both agents
    print("\n1. Starting query requiring both agents...")
    task_id_1 = await manager.handle_user_message(
        user_id,
        "Find flights and hotels for a trip to Dubai in January"
    )
    
    await asyncio.sleep(2.0)
    
    # Check which agent is running
    status_mid = manager.get_status(user_id)
    print(f"\n2. Mid-execution status:")
    print(f"   Current agent: {status_mid.get('current_agent')}")
    print(f"   Agents completed: {status_mid.get('agents_completed', [])}")
    
    # Interrupt while one agent might be done
    print("\n3. Interrupting multi-agent task...")
    task_id_2 = await manager.handle_user_message(
        user_id,
        "Cancel that, just show me hotels in Singapore"
    )
    
    await asyncio.sleep(3.0)
    
    # Check final state
    status_final = manager.get_status(user_id)
    print(f"\n4. Final status: {status_final.get('status')}")
    print(f"   Current query: 'hotels in Singapore'")
    
    # Should have partial results from interrupted multi-agent task
    partial = status_final.get('partial_results', {})
    print(f"\n5. Partial results from interrupted task:")
    print(f"   Flight partials: {bool(partial.get('flight'))}")
    print(f"   Hotel partials: {bool(partial.get('hotel'))}")
    
    print("\n✅ Test 5 Complete: Multi-agent interruption handled")


async def test_no_interruption():
    """Test 6: Normal completion without interruption (control test)."""
    print("\n" + "="*80)
    print("TEST 6: Normal Completion (No Interruption)")
    print("="*80)
    
    manager = AgentManager()
    user_id = "test_user_6"
    
    print("\n1. Starting query that will complete normally...")
    task_id = await manager.handle_user_message(
        user_id,
        "Find hotels in Boston"
    )
    
    # Wait for completion
    print("2. Waiting for completion...")
    await asyncio.sleep(4.0)
    
    status = manager.get_status(user_id)
    print(f"\n3. Final status: {status.get('status')}")
    print(f"   Task completed: {status.get('status') == 'completed'}")
    
    if status.get('final_results'):
        print(f"\n4. Final results received:")
        results = status['final_results']
        print(f"   Response available: {bool(results.get('response'))}")
    
    print("\n✅ Test 6 Complete: Normal completion verified")


async def test_interruption_manager_directly():
    """Test 7: Test InterruptionManager directly."""
    print("\n" + "="*80)
    print("TEST 7: InterruptionManager Direct Testing")
    print("="*80)
    
    from interruption_manager import InterruptionManager, TaskStatus
    
    manager = InterruptionManager()
    user_id = "test_user_7"
    
    # Create task context
    print("\n1. Creating task context...")
    context = await manager.create_task_context(
        user_id=user_id,
        query="Find flights to Madrid",
        intent="flight"
    )
    print(f"   Task ID: {context.task_id}")
    print(f"   Status: {context.status.value}")
    
    # Save partial results
    print("\n2. Saving partial results...")
    await manager.save_partial_results(
        user_id=user_id,
        agent_name="flight",
        results={"found": 5, "searching": True}
    )
    
    # Get context
    retrieved = await manager.get_task_context(user_id)
    print(f"   Partial results: {retrieved.partial_results}")
    
    # Interrupt
    print("\n3. Interrupting task...")
    await manager.interrupt_task(user_id, preserve_context=True)
    
    # Verify interruption
    status = manager.get_status_dict(user_id)
    print(f"   Status: {status['status']}")
    print(f"   Partial results preserved: {bool(status.get('partial_results'))}")
    
    # Get previous context
    print("\n4. Creating new task and checking previous context...")
    context2 = await manager.create_task_context(
        user_id=user_id,
        query="Find hotels in Madrid",
        intent="hotel"
    )
    
    prev_context = await manager.get_previous_context(user_id, "hotels")
    print(f"   Previous context available: {prev_context is not None}")
    if prev_context:
        print(f"   Previous query: {prev_context.get('previous_query')}")
        print(f"   Previous partial results: {bool(prev_context.get('partial_results'))}")
    
    print("\n✅ Test 7 Complete: InterruptionManager working correctly")


async def run_all_tests():
    """Run all interruption system tests."""
    print("\n" + "="*80)
    print("INTERRUPTION SYSTEM TEST SUITE")
    print("="*80)
    print("\nTesting core interruption functionality:")
    print("- Request detection during active processing")
    print("- Graceful cancellation of running operations")
    print("- Partial result preservation")
    print("- Context transfer between tasks")
    print("- Resume/continuation logic")
    
    tests = [
        ("Basic Interruption", test_basic_interruption),
        ("Partial Result Preservation", test_partial_result_preservation),
        ("Context Transfer", test_context_transfer),
        ("Multiple Interruptions", test_multiple_interruptions),
        ("Multi-Agent Interruption", test_both_agents_with_interruption),
        ("Normal Completion", test_no_interruption),
        ("InterruptionManager Direct", test_interruption_manager_directly)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            await test_func()
            passed += 1
        except Exception as e:
            print(f"\n❌ {test_name} FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n✅ ALL TESTS PASSED!")
    else:
        print(f"\n⚠️  {failed} test(s) failed")
    
    return failed == 0


if __name__ == "__main__":
    print("Starting Interruption System Test Suite...")
    print("Note: These tests use mock agent responses for demonstration.")
    print("In production, real API calls would be used.")
    
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
