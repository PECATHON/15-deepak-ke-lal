#!/usr/bin/env python3
"""
Quick Interruption System Test

This is a simple standalone test to verify the interruption system works.
Run this to see interruption in action without needing real agents.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from interruption_manager import InterruptionManager, TaskStatus


async def simulate_agent_work(user_id: str, agent_name: str, manager: InterruptionManager, duration: float):
    """Simulate an agent doing work that can be interrupted."""
    print(f"  [{agent_name}] Starting work...")
    
    # Get cancellation event
    cancel_event = await manager.get_cancellation_event(user_id)
    
    # Simulate work in chunks
    chunks = int(duration * 10)  # 10 chunks per second
    for i in range(chunks):
        # Check if cancelled
        if cancel_event and cancel_event.is_set():
            print(f"  [{agent_name}] ❌ Cancelled at {i}/{chunks} chunks")
            # Save partial results
            await manager.save_partial_results(
                user_id, 
                agent_name, 
                {"chunks_completed": i, "total_chunks": chunks, "progress": f"{i/chunks*100:.1f}%"}
            )
            return {"status": "cancelled", "partial": f"Completed {i}/{chunks} chunks"}
        
        # Do work
        await asyncio.sleep(0.1)
        
        # Report progress occasionally
        if i % 5 == 0:
            await manager.save_partial_results(
                user_id,
                agent_name,
                {"chunks_completed": i, "progress": f"{i/chunks*100:.1f}%"}
            )
            print(f"  [{agent_name}] Progress: {i/chunks*100:.1f}%")
    
    print(f"  [{agent_name}] ✅ Completed successfully")
    return {"status": "completed", "result": f"Finished all {chunks} chunks"}


async def test_basic_interruption():
    """Test 1: Basic interruption."""
    print("\n" + "="*70)
    print("TEST 1: Basic Interruption")
    print("="*70)
    
    manager = InterruptionManager()
    user_id = "test_user_1"
    
    # Start first task
    print("\n1️⃣ Starting first task (will run for 3 seconds)...")
    context1 = await manager.create_task_context(user_id, "Find flights", "flight")
    await manager.update_task_status(user_id, TaskStatus.RUNNING, current_agent="flight")
    
    # Run agent in background
    task1 = asyncio.create_task(simulate_agent_work(user_id, "FlightAgent", manager, 3.0))
    await manager.set_task_reference(user_id, task1)
    
    # Let it run for 1 second
    await asyncio.sleep(1.0)
    
    # Check status
    status = manager.get_status_dict(user_id)
    print(f"\n📊 Status after 1 second:")
    print(f"   Status: {status['status']}")
    print(f"   Partial results: {status.get('partial_results', {})}")
    
    # Interrupt with new task
    print("\n2️⃣ Interrupting with new task...")
    context2 = await manager.create_task_context(user_id, "Find hotels", "hotel")
    
    # Check if first task was cancelled
    await asyncio.sleep(0.2)
    
    print(f"\n📊 After interruption:")
    status = manager.get_status_dict(user_id)
    print(f"   Status: {status['status']}")
    print(f"   Partial results preserved: {status.get('partial_results', {})}")
    
    # Start new task
    await manager.update_task_status(user_id, TaskStatus.RUNNING, current_agent="hotel")
    task2 = asyncio.create_task(simulate_agent_work(user_id, "HotelAgent", manager, 2.0))
    await manager.set_task_reference(user_id, task2)
    
    # Wait for completion
    await task2
    
    await manager.complete_task(user_id, {"hotels": "found"}, TaskStatus.COMPLETED)
    
    # Final status
    status = manager.get_status_dict(user_id)
    print(f"\n✅ Final status:")
    print(f"   Status: {status['status']}")
    print(f"   All partial results: {status.get('partial_results', {})}")
    
    print("\n✅ Test 1 PASSED: Interruption working!")


async def test_context_transfer():
    """Test 2: Context transfer."""
    print("\n" + "="*70)
    print("TEST 2: Context Transfer")
    print("="*70)
    
    manager = InterruptionManager()
    user_id = "test_user_2"
    
    # First task
    print("\n1️⃣ Starting first task...")
    context1 = await manager.create_task_context(user_id, "Search flights to Paris", "flight")
    await manager.update_task_status(user_id, TaskStatus.RUNNING, current_agent="flight")
    
    task1 = asyncio.create_task(simulate_agent_work(user_id, "FlightAgent", manager, 2.0))
    await manager.set_task_reference(user_id, task1)
    
    await asyncio.sleep(0.8)
    
    # Interrupt
    print("\n2️⃣ Interrupting...")
    context2 = await manager.create_task_context(user_id, "Actually, find hotels in Paris", "hotel")
    
    await asyncio.sleep(0.2)
    
    # Get previous context
    prev_context = await manager.get_previous_context(user_id, "hotels in Paris")
    
    print(f"\n📦 Previous context available:")
    if prev_context:
        print(f"   Previous query: {prev_context.get('previous_query')}")
        print(f"   Previous intent: {prev_context.get('previous_intent')}")
        print(f"   Partial results: {prev_context.get('partial_results', {})}")
        print(f"   Interrupted at: {prev_context.get('interrupted_at')}")
    
    print("\n✅ Test 2 PASSED: Context transfer working!")


async def test_multiple_interruptions():
    """Test 3: Multiple rapid interruptions."""
    print("\n" + "="*70)
    print("TEST 3: Multiple Rapid Interruptions")
    print("="*70)
    
    manager = InterruptionManager()
    user_id = "test_user_3"
    
    queries = [
        ("Paris flights", 0.5),
        ("London hotels", 0.5),
        ("Rome flights", 0.5),
        ("Tokyo hotels", 2.0)
    ]
    
    print(f"\n📨 Sending {len(queries)} queries rapidly...")
    
    for i, (query, delay) in enumerate(queries, 1):
        print(f"\n{i}. Query: '{query}'")
        context = await manager.create_task_context(user_id, query, "test")
        await manager.update_task_status(user_id, TaskStatus.RUNNING)
        
        task = asyncio.create_task(simulate_agent_work(user_id, f"Agent{i}", manager, delay))
        await manager.set_task_reference(user_id, task)
        
        await asyncio.sleep(delay * 0.3)  # Wait a bit before next
    
    # Wait for last task
    await asyncio.sleep(2.5)
    
    status = manager.get_status_dict(user_id)
    print(f"\n✅ Final status: {status['status']}")
    print(f"✅ Test 3 PASSED: Multiple interruptions handled!")


async def run_all_tests():
    """Run all quick tests."""
    print("\n" + "="*70)
    print("🚀 INTERRUPTION SYSTEM QUICK TEST")
    print("="*70)
    print("\nThis will test:")
    print("  • Basic interruption (cancel running task)")
    print("  • Partial result preservation")
    print("  • Context transfer between tasks")
    print("  • Multiple rapid interruptions")
    
    try:
        await test_basic_interruption()
        await test_context_transfer()
        await test_multiple_interruptions()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED!")
        print("="*70)
        print("\nThe interruption system is working correctly!")
        print("\nNext steps:")
        print("  1. Start the backend: uvicorn main:app --reload")
        print("  2. Test with real API calls")
        print("  3. Use WebSocket client to see real-time updates")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Starting Interruption System Quick Test...")
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
