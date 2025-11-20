#!/usr/bin/env python3
"""
Interactive Demo: Request Interruption System

This script demonstrates the interruption system in action with
a simulated conversation showing:
- Automatic interruption when new queries arrive
- Partial result preservation
- Context transfer between queries
"""

import asyncio
import sys
import os
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from runner import AgentManager
import json


class InteractiveDemo:
    """Interactive demonstration of the interruption system."""
    
    def __init__(self):
        self.manager = AgentManager()
        self.user_id = "demo_user"
    
    def print_header(self, text):
        """Print a formatted header."""
        print("\n" + "="*70)
        print(f"  {text}")
        print("="*70)
    
    def print_status(self, status_dict):
        """Print formatted status information."""
        print(f"\n📊 Current Status:")
        print(f"   • Status: {status_dict.get('status', 'N/A')}")
        print(f"   • Task ID: {status_dict.get('task_id', 'N/A')}")
        
        if status_dict.get('current_agent'):
            print(f"   • Current Agent: {status_dict['current_agent']}")
        
        if status_dict.get('partial_results'):
            print(f"\n💾 Partial Results Available:")
            for agent, results in status_dict['partial_results'].items():
                print(f"   • {agent}: {results}")
        
        if status_dict.get('final_results'):
            print(f"\n✅ Final Results:")
            results = status_dict['final_results']
            if isinstance(results, dict) and 'response' in results:
                try:
                    response_data = json.loads(results['response'])
                    print(json.dumps(response_data, indent=6))
                except:
                    print(f"   {results['response']}")
    
    async def demo_scenario_1(self):
        """Scenario 1: Basic interruption during flight search."""
        self.print_header("SCENARIO 1: Basic Interruption")
        
        print("\n🎭 Story: User starts searching for flights, then changes mind")
        print("\n👤 User: 'Find flights from New York to London on December 25'")
        
        task_id_1 = await self.manager.handle_user_message(
            self.user_id,
            "Find flights from New York to London on December 25"
        )
        print(f"✓ Task {task_id_1[:8]}... started")
        
        print("\n⏳ Processing... (simulating 1.5 seconds)")
        await asyncio.sleep(1.5)
        
        status = self.manager.get_status(self.user_id)
        self.print_status(status)
        
        print("\n👤 User: 'Actually, find hotels in Paris instead'")
        print("💡 (This will interrupt the flight search)")
        
        task_id_2 = await self.manager.handle_user_message(
            self.user_id,
            "Actually, find hotels in Paris instead"
        )
        print(f"✓ Task {task_id_2[:8]}... started (previous task interrupted)")
        
        print("\n⏳ Waiting for completion...")
        await asyncio.sleep(3.0)
        
        status = self.manager.get_status(self.user_id)
        self.print_status(status)
        
        print("\n✨ Result: Flight search was interrupted, partial results preserved")
        print("   New hotel search completed successfully")
    
    async def demo_scenario_2(self):
        """Scenario 2: Multiple rapid interruptions."""
        self.print_header("SCENARIO 2: Rapid-Fire Query Changes")
        
        print("\n🎭 Story: User keeps changing their mind rapidly")
        
        queries = [
            ("Find flights to Paris", 0.5),
            ("No, hotels in London", 0.5),
            ("Actually, flights to Rome", 0.5),
            ("Wait, Barcelona hotels", 0.5),
            ("Final answer: Tokyo flights", 3.0)
        ]
        
        for i, (query, wait_time) in enumerate(queries, 1):
            print(f"\n👤 User ({i}/5): '{query}'")
            task_id = await self.manager.handle_user_message(self.user_id, query)
            print(f"   ✓ Task started: {task_id[:8]}...")
            
            if i < len(queries):
                print(f"   ⏳ Brief pause ({wait_time}s)...")
            else:
                print(f"   ⏳ Waiting for completion ({wait_time}s)...")
            
            await asyncio.sleep(wait_time)
        
        status = self.manager.get_status(self.user_id)
        self.print_status(status)
        
        print("\n✨ Result: All previous queries interrupted, final query completed")
        print("   System handled rapid changes gracefully")
    
    async def demo_scenario_3(self):
        """Scenario 3: Context transfer between related queries."""
        self.print_header("SCENARIO 3: Context Transfer")
        
        print("\n🎭 Story: User adds to initial query with a follow-up")
        
        print("\n👤 User: 'Find flights from San Francisco to Tokyo in March'")
        task_id_1 = await self.manager.handle_user_message(
            self.user_id,
            "Find flights from San Francisco to Tokyo in March"
        )
        print(f"✓ Task {task_id_1[:8]}... started")
        
        print("\n⏳ Processing... (1.5 seconds)")
        await asyncio.sleep(1.5)
        
        status_1 = self.manager.get_status(self.user_id)
        print(f"\n📊 Mid-execution:")
        print(f"   • Agent: {status_1.get('current_agent', 'N/A')}")
        if status_1.get('partial_results'):
            print(f"   • Partial flight results accumulated")
        
        print("\n👤 User: 'Also find hotels in Tokyo for those dates'")
        print("💡 (This is related to the previous query)")
        
        task_id_2 = await self.manager.handle_user_message(
            self.user_id,
            "Also find hotels in Tokyo for those dates"
        )
        print(f"✓ Task {task_id_2[:8]}... started")
        print("   Previous context and partial results are available")
        
        print("\n⏳ Waiting for completion...")
        await asyncio.sleep(3.0)
        
        status_2 = self.manager.get_status(self.user_id)
        self.print_status(status_2)
        
        print("\n✨ Result: Hotel search has access to previous flight context")
        print("   Could potentially combine results intelligently")
    
    async def demo_scenario_4(self):
        """Scenario 4: Multi-agent task interruption."""
        self.print_header("SCENARIO 4: Multi-Agent Task Interruption")
        
        print("\n🎭 Story: Interrupt a query that needs both flight AND hotel agents")
        
        print("\n👤 User: 'Plan a complete trip to Dubai - flights and hotels'")
        task_id_1 = await self.manager.handle_user_message(
            self.user_id,
            "Find flights and hotels for a trip to Dubai in January"
        )
        print(f"✓ Task {task_id_1[:8]}... started (requires both agents)")
        
        print("\n⏳ Processing... (2 seconds)")
        await asyncio.sleep(2.0)
        
        status_mid = self.manager.get_status(self.user_id)
        print(f"\n📊 Progress check:")
        print(f"   • Current agent: {status_mid.get('current_agent', 'N/A')}")
        print(f"   • Completed agents: {status_mid.get('agents_completed', [])}")
        
        print("\n👤 User: 'Cancel that, just show hotels in Singapore'")
        print("💡 (Interrupting multi-agent workflow)")
        
        task_id_2 = await self.manager.handle_user_message(
            self.user_id,
            "Cancel that, just show me hotels in Singapore"
        )
        print(f"✓ Task {task_id_2[:8]}... started")
        
        print("\n⏳ Waiting for completion...")
        await asyncio.sleep(3.0)
        
        status_final = self.manager.get_status(self.user_id)
        self.print_status(status_final)
        
        print("\n✨ Result: Multi-agent task interrupted mid-execution")
        print("   Partial results from both agents preserved")
    
    async def run_all_scenarios(self):
        """Run all demonstration scenarios."""
        self.print_header("REQUEST INTERRUPTION SYSTEM - INTERACTIVE DEMO")
        
        print("\n📖 This demo shows how the system handles:")
        print("   • New queries arriving during processing")
        print("   • Graceful cancellation of running operations")
        print("   • Preservation of partial results")
        print("   • Context transfer between queries")
        print("\n⚠️  Note: Using simulated agents for demonstration")
        
        input("\nPress Enter to start...")
        
        scenarios = [
            self.demo_scenario_1,
            self.demo_scenario_2,
            self.demo_scenario_3,
            self.demo_scenario_4
        ]
        
        for scenario in scenarios:
            await scenario()
            print("\n" + "-"*70)
            input("Press Enter for next scenario...")
        
        self.print_header("DEMO COMPLETE")
        print("\n✅ All scenarios demonstrated successfully!")
        print("\n📚 Key Takeaways:")
        print("   1. New queries automatically interrupt running tasks")
        print("   2. Partial results are always preserved")
        print("   3. Context is available to subsequent queries")
        print("   4. System handles rapid changes gracefully")
        print("   5. Multi-agent workflows are interrupted cleanly")
        print("\n💡 Try it yourself:")
        print("   • Start the backend: uvicorn main:app --reload")
        print("   • Send queries via API or WebSocket")
        print("   • Observe real-time interruption handling")


async def main():
    """Run the interactive demo."""
    demo = InteractiveDemo()
    
    try:
        await demo.run_all_scenarios()
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("="*70)
    print("  REQUEST INTERRUPTION SYSTEM - INTERACTIVE DEMO")
    print("="*70)
    
    asyncio.run(main())
