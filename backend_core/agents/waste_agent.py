# # waste_agent.py - Complete Waste Management Agent
# import asyncio
# import json
# import os
# import re
# import smtplib
# from datetime import datetime, timedelta
# from email.message import EmailMessage
# from openai import AsyncOpenAI
# from agents import Agent, Runner, OpenAIChatCompletionsModel
# from agents.mcp import MCPServerStdio
# import random
#
# # ===== LOAD ENV =====
# from dotenv import load_dotenv
# load_dotenv()
# # ===== GEMINI SETUP =====
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
#
# if not GEMINI_API_KEY:
#     raise ValueError("❌ GEMINI_API_KEY not found in .env file!")
#
# client = AsyncOpenAI(
#     api_key=GEMINI_API_KEY,
#     base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
# )
#
# gemini_model = OpenAIChatCompletionsModel(
#     model="gemini-2.0-flash",
#     openai_client=client
# )
#
# # ===== EMAIL CONFIG =====
# SENDER_EMAIL = "nooreasal786@gmail.com"
# APP_PASSWORD = "irph tole tuqr vfmi"
#
# def send_email_notification(receiver_email, subject, body):
#     """📧 Email notification"""
#     try:
#         msg = EmailMessage()
#         msg['Subject'] = subject
#         msg['From'] = SENDER_EMAIL
#         msg['To'] = receiver_email
#         msg.set_content(body)
#
#         with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
#             smtp.starttls()
#             smtp.login(SENDER_EMAIL, APP_PASSWORD)
#             smtp.send_message(msg)
#
#         print(f"✉️ Email sent to {receiver_email}")
#         return True
#     except Exception as e:
#         print(f"❌ Email failed: {e}")
#         return False
#
# # ===== AUDIT LOGS =====
# AUDIT_LOG_FILE = "waste_audit.json"
# audit_logs = []
#
# def log_decision(agent_name, action, reasoning, data=None):
#     """🧠 Audit logging"""
#     entry = {
#         "timestamp": datetime.now().isoformat(),
#         "agent": agent_name,
#         "action": action,
#         "reasoning": reasoning,
#         "data": data or {}
#     }
#     audit_logs.append(entry)
#     with open(AUDIT_LOG_FILE, "w") as f:
#         json.dump(audit_logs, f, indent=2)
#     print(f"📝 [AUDIT] {agent_name} → {action}")
#
# # ===== LOCAL WASTE DATABASE =====
# CONTAINERS_FILE = "waste_containers.json"
# PICKUPS_FILE = "waste_pickups.json"
# ROUTES_FILE = "waste_routes.json"
#
# def load_containers():
#     if os.path.exists(CONTAINERS_FILE):
#         with open(CONTAINERS_FILE, "r") as f:
#             return json.load(f)
#
#     # Default IoT-enabled containers
#     return {
#         "CONT-001": {
#             "container_id": "CONT-001",
#             "location": "Services Hospital - Emergency Wing",
#             "hospital_id": "H001",
#             "waste_type": "bio_medical",
#             "capacity_liters": 240,
#             "current_level_percent": 45.0,
#             "last_updated": datetime.now().isoformat(),
#             "sensor_status": "active",
#             "lat": 31.5103,
#             "lon": 74.3221
#         },
#         "CONT-002": {
#             "container_id": "CONT-002",
#             "location": "Mayo Hospital - Surgery Ward",
#             "hospital_id": "H002",
#             "waste_type": "bio_medical",
#             "capacity_liters": 240,
#             "current_level_percent": 85.0,
#             "last_updated": datetime.now().isoformat(),
#             "sensor_status": "active",
#             "lat": 31.5820,
#             "lon": 74.3090
#         },
#         "CONT-003": {
#             "container_id": "CONT-003",
#             "location": "Jinnah Hospital - ICU",
#             "hospital_id": "H003",
#             "waste_type": "bio_medical",
#             "capacity_liters": 240,
#             "current_level_percent": 92.0,
#             "last_updated": datetime.now().isoformat(),
#             "sensor_status": "active",
#             "lat": 31.4752,
#             "lon": 74.3053
#         },
#         "CONT-004": {
#             "container_id": "CONT-004",
#             "location": "Services Hospital - Pharmacy",
#             "hospital_id": "H001",
#             "waste_type": "pharmaceutical",
#             "capacity_liters": 120,
#             "current_level_percent": 65.0,
#             "last_updated": datetime.now().isoformat(),
#             "sensor_status": "active",
#             "lat": 31.5103,
#             "lon": 74.3221
#         }
#     }
#
# def save_containers(containers):
#     with open(CONTAINERS_FILE, "w") as f:
#         json.dump(containers, f, indent=2)
#
# def load_pickups():
#     if os.path.exists(PICKUPS_FILE):
#         with open(PICKUPS_FILE, "r") as f:
#             return json.load(f)
#     return []
#
# def save_pickups(pickups):
#     with open(PICKUPS_FILE, "w") as f:
#         json.dump(pickups, f, indent=2)
#
# def load_routes():
#     if os.path.exists(ROUTES_FILE):
#         with open(ROUTES_FILE, "r") as f:
#             return json.load(f)
#     return []
#
# def save_routes(routes):
#     with open(ROUTES_FILE, "w") as f:
#         json.dump(routes, f, indent=2)
#
# # ===== IoT SIMULATION =====
# def simulate_iot_update(container_id, level_change=None):
#     """Simulate IoT sensor update"""
#     containers = load_containers()
#
#     if container_id not in containers:
#         return {"error": "Container not found"}
#
#     container = containers[container_id]
#
#     # Update level
#     if level_change:
#         container["current_level_percent"] += level_change
#         container["current_level_percent"] = max(0, min(100, container["current_level_percent"]))
#     else:
#         # Random fluctuation
#         container["current_level_percent"] += random.uniform(2, 8)
#         container["current_level_percent"] = min(100, container["current_level_percent"])
#
#     container["last_updated"] = datetime.now().isoformat()
#
#     save_containers(containers)
#     return container
#
# # # ===== MCP SERVER =====
# # mcp_server = MCPServerStdio(
# #     params={
# #         "command": "python",
# #         "args": ["agents_mcp.py"]
# #     },
# #     cache_tools_list=True,
# #     name="WasteMCP"
# # )
#
# # ===== MCP SERVERS (2 servers for inter-agent communication) =====
#
# # 1. Orchestrator MCP (for handoffs)
# orchestrator_mcp = MCPServerStdio(
#     params={
#         "command": "python",
#         "args": ["agent_orchestrator_mcp.py"]
#     },
#     cache_tools_list=True,
#     name="OrchestratorMCP"
# )
#
# # 2. Domain MCP (for actual work)
# domain_mcp = MCPServerStdio(
#     params={
#         "command": "python",
#         "args": ["agents_mcp.py"]
#     },
#     cache_tools_list=True,
#     name="DomainMCP"
# )
# #
# # # ===== WASTE AGENT =====
# # waste_agent = Agent(
# #     name="WasteManagementAgent",
# #     model=gemini_model,
# #     instructions=(
# #         "You are an autonomous waste management agent for hospital bio-waste and pharmaceutical waste.\n\n"
# #         "Your role is to monitor IoT-enabled waste containers, schedule pickups before overflow, "
# #         "optimize collection routes, and coordinate special pharmaceutical waste disposal.\n\n"
# #         "🧠 Available capabilities (tools via MCP):\n"
# #         "- Monitor container levels via IoT sensors\n"
# #         "- Schedule automatic pickups when containers reach threshold (75%)\n"
# #         "- Optimize routing for garbage collection trucks\n"
# #         "- Handle pharmaceutical waste disposal (special protocol)\n"
# #         "- Sync with LWMC (Lahore Waste Management Company)\n"
# #         "- Send email alerts to hospitals and LWMC\n\n"
# #         "🚨 AUTO-SCHEDULE TRIGGERS:\n"
# #         "- Container >= 90% → URGENT priority pickup (1-3 hours)\n"
# #         "- Container >= 75% → HIGH priority pickup (3-6 hours)\n"
# #         "- Container >= 60% → NORMAL priority pickup (6-12 hours)\n"
# #         "- Pharmaceutical waste → Special disposal protocol\n\n"
# #         "🌐 Language: Respond in Urdu or English.\n"
# #         "📧 Notifications: Alert hospitals and LWMC about pickups.\n\n"
# #         "💡 Decision Flow:\n"
# #         "1. Monitor all containers → identify critical levels\n"
# #         "2. If >= 75% → schedule pickup with appropriate priority\n"
# #         "3. If pharmaceutical waste → use special disposal protocol\n"
# #         "4. Optimize routes for multiple pickups\n"
# #         "5. Sync with LWMC systems\n\n"
# #         "📋 Response Format:\n"
# #         "1) Reasoning: Why this action was taken\n"
# #         "2) Action: What was done\n"
# #         "3) Next Steps: Recommendations"
# #     ),
# #     mcp_servers=[mcp_server]
# # )
#
# # ===== WASTE AGENT =====
# waste_agent = Agent(
#     name="WasteManagementAgent",
#     model=gemini_model,
#     instructions=(
#         "You are a waste management agent for hospital bio-waste.\n\n"
#
#         "🤝 ORCHESTRATOR TOOLS (inter-agent communication):\n"
#         "- handoff_to_agent(from_agent='waste', to_agent, task_type, context, priority)\n"
#         "  → Emergency waste overflow? → handoff to 'tracking' for urgent transport\n"
#         "  → Pharmaceutical waste? → Can handle yourself OR handoff to 'pharmacy' for verification\n"
#         "- check_my_tasks(agent_name='waste')\n"
#         "  → Check for pharmaceutical disposal requests from pharmacy agent\n"
#         "- complete_task(handoff_id, result, completed_by='waste')\n"
#         "  → Complete tasks\n"
#         "- query_agent_capabilities(agent_name)\n"
#         "  → Check capabilities\n\n"
#
#         "⚡ WORKFLOW:\n"
#         "1. Start: check_my_tasks('waste')\n"
#         "2. Monitor containers → if >=75% → schedule_pickup()\n"
#         "3. Multiple pickups? → optimize_collection_route()\n"
#         "4. Pharmaceutical waste? → handle_pharmaceutical_waste()\n\n"
#
#         "🗑️ YOUR DOMAIN TOOLS:\n"
#         "- monitor_container_levels()\n"
#         "- schedule_pickup(container_id, priority)\n"
#         "- optimize_collection_route(depot_location)\n"
#         "- handle_pharmaceutical_waste(container_id)\n"
#         "- sync_with_lwmc(data_type)\n"
#         "- get_container_details(container_id)\n"
#         "- update_container_level(container_id, new_level_percent)\n"
#         "- notify_hospital_pickup(hospital_id, pickup_id, pickup_details)\n\n"
#
#         "🚨 AUTO-SCHEDULE TRIGGERS:\n"
#         "- Container >= 90% → URGENT (1-3 hours)\n"
#         "- Container >= 75% → HIGH (3-6 hours)\n"
#         "- Container >= 60% → NORMAL (6-12 hours)\n"
#         "- Pharmaceutical → Special protocol\n\n"
#
#         "🌐 Language: Urdu or English\n"
#         "📧 Notifications: Alert hospitals and LWMC\n\n"
#
#         "💡 Decision Flow:\n"
#         "1. Monitor containers → identify critical\n"
#         "2. If >= 75% → schedule pickup\n"
#         "3. Pharmaceutical? → special disposal\n"
#         "4. Optimize routes for multiple pickups\n"
#         "5. Sync with LWMC\n\n"
#
#         "📋 Format: 1) Reasoning 2) Action 3) Next Steps"
#     ),
#     mcp_servers=[orchestrator_mcp, domain_mcp]
# )
#
# # ===== RETRY LOGIC =====
# async def run_with_retry(agent, query, max_retries=3):
#     """🔄 Retry with fallback"""
#     for attempt in range(max_retries):
#         try:
#             result = await Runner.run(agent, query)
#             return result
#         except Exception as e:
#             print(f"⚠️ Attempt {attempt + 1} failed: {e}")
#             if attempt == max_retries - 1:
#                 return {"final_output": "System offline. Manual waste management required."}
#             await asyncio.sleep(1)
#
# # ===== DEMO (LLM-DRIVEN) =====
# async def run_demo():
#     async with orchestrator_mcp, domain_mcp:
#     # async with mcp_server:
#         try:
#             await orchestrator_mcp.connect()
#             await domain_mcp.connect()
#             print("✅ Both MCP servers connected\n")
#             # await mcp_server.connect()
#             # print("✅ MCP Connected\n")
#         except Exception as e:
#             print(f"⚠️ MCP failed: {e}\n")
#
#         print("🗑️ Waste Management Agent Started - LLM Autonomous Decision Testing!\n")
#         print("=" * 70)
#
#         # Test 1: Monitor containers and schedule pickups
#         print("=" * 70)
#         print("TEST 1: Monitor Containers - LLM Auto-Schedules Pickups")
#         print("-" * 70)
#
#         query1 = (
#             "Hospital waste containers ki monitoring karo. "
#             "Jo containers 75% ya zyada full hain unke liye pickup schedule karo. "
#             "Priority set karo based on fill level. "
#             "Container details check karo aur batao kaunse urgent hain."
#         )
#
#         print(f"📝 User Query:\n{query1}\n")
#
#         result1 = await run_with_retry(waste_agent, query1)
#         output1 = result1.final_output if hasattr(result1, "final_output") else str(result1)
#
#         print("✅ [LLM RESPONSE]")
#         print(output1)
#         print()
#
#         # Test 2: Route optimization
#         print("=" * 70)
#         print("TEST 2: Route Optimization - LLM Optimizes Collection Route")
#         print("-" * 70)
#
#         query2 = (
#             "Multiple containers pickup ke liye ready hain. "
#             "Garbage collection truck ke liye optimal route banao jo:\n"
#             "1. Sabse zyada full container pehle collect kare\n"
#             "2. Total distance minimize ho\n"
#             "3. Time estimation de\n"
#             "Lahore Depot se start karke sab containers cover karo."
#         )
#
#         print(f"📝 User Query:\n{query2}\n")
#
#         result2 = await run_with_retry(waste_agent, query2)
#         output2 = result2.final_output if hasattr(result2, "final_output") else str(result2)
#
#         print("✅ [LLM RESPONSE]")
#         print(output2)
#         print()
#
#         # Test 3: Pharmaceutical waste handling
#         print("=" * 70)
#         print("TEST 3: Pharmaceutical Waste - LLM Applies Special Protocol")
#         print("-" * 70)
#
#         query3 = (
#             "Container CONT-004 mein pharmaceutical waste hai jo 65% full hai. "
#             "Ye expired medicines aur contaminated drugs hain. "
#             "Special disposal protocol use karo kyunki ye normal waste nahi hai. "
#             "Kya karna chahiye?"
#         )
#
#         print(f"📝 User Query:\n{query3}\n")
#
#         result3 = await run_with_retry(waste_agent, query3)
#         output3 = result3.final_output if hasattr(result3, "final_output") else str(result3)
#
#         print("✅ [LLM RESPONSE]")
#         print(output3)
#         print()
#
#         # Test 4: IoT sensor alert
#         print("=" * 70)
#         print("TEST 4: IoT Alert - LLM Responds to Sensor Data")
#         print("-" * 70)
#
#         # Simulate IoT update
#         updated_container = simulate_iot_update("CONT-002", level_change=8)
#
#         query4 = (
#             f"IoT sensor alert! Container CONT-002 (Mayo Hospital - Surgery Ward) "
#             f"ka level suddenly {updated_container['current_level_percent']:.1f}% ho gaya hai. "
#             f"Ye bio-medical waste hai. Immediate action chahiye? "
#             f"Pickup schedule karni chahiye ya wait karna theek hai?"
#         )
#
#         print(f"📝 User Query:\n{query4}\n")
#
#         result4 = await run_with_retry(waste_agent, query4)
#         output4 = result4.final_output if hasattr(result4, "final_output") else str(result4)
#
#         print("✅ [LLM RESPONSE]")
#         print(output4)
#         print()
#
#         # Test 5: LWMC sync
#         print("=" * 70)
#         print("TEST 5: LWMC Sync - LLM Syncs with Municipal Systems")
#         print("-" * 70)
#
#         query5 = (
#             "Lahore Waste Management Company (LWMC) ke saath data sync karna hai. "
#             "Containers, pickups, aur routes ka latest data unhe bhejo. "
#             "Sync karo aur confirm karo ke sab data successfully transfer ho gaya."
#         )
#
#         print(f"📝 User Query:\n{query5}\n")
#
#         result5 = await run_with_retry(waste_agent, query5)
#         output5 = result5.final_output if hasattr(result5, "final_output") else str(result5)
#
#         print("✅ [LLM RESPONSE]")
#         print(output5)
#         print()
#
#         # Test 6: Complex multi-container scenario
#         print("=" * 70)
#         print("TEST 6: Complex Scenario - LLM Multi-Step Decision")
#         print("-" * 70)
#
#         query6 = (
#             "Emergency situation:\n"
#             "- CONT-003 (Jinnah Hospital ICU): 92% full - bio-medical waste\n"
#             "- CONT-002 (Mayo Hospital Surgery): 93% full - bio-medical waste\n"
#             "- CONT-004 (Services Pharmacy): 65% full - pharmaceutical waste\n"
#             "\nTumhe kya karna chahiye? Step by step batao:\n"
#             "1. Kaunse containers urgent hain?\n"
#             "2. Kis order mein pickup schedule karni chahiye?\n"
#             "3. Pharmaceutical waste ka kya karna hai?\n"
#             "4. Route optimization zaruri hai?\n"
#             "5. LWMC ko inform karna chahiye?"
#         )
#
#         print(f"📝 User Query:\n{query6}\n")
#
#         result6 = await run_with_retry(waste_agent, query6)
#         output6 = result6.final_output if hasattr(result6, "final_output") else str(result6)
#
#         print("✅ [LLM RESPONSE - FULL AUTONOMOUS WORKFLOW]")
#         print(output6)
#         print()
#
#         # Summary
#         print("=" * 70)
#         print("\n📊 DEMO SUMMARY")
#         print("-" * 70)
#         print(f"✅ Total tests run: 6")
#         print(f"📝 Total audit logs: {len(audit_logs)}")
#         print(f"💾 Logs saved to: {AUDIT_LOG_FILE}")
#         print(f"📦 Container data: {CONTAINERS_FILE}")
#         print(f"🚛 Pickup data: {PICKUPS_FILE}")
#         print(f"🗺️ Route data: {ROUTES_FILE}")
#
#         # Stats
#         containers = load_containers()
#         pickups = load_pickups()
#         routes = load_routes()
#
#         print(f"\n📈 Statistics:")
#         print(f"   Total Containers: {len(containers)}")
#         print(f"   Scheduled Pickups: {len(pickups)}")
#         print(f"   Optimized Routes: {len(routes)}")
#         print(f"   Critical Containers: {len([c for c in containers.values() if c['current_level_percent'] >= 90])}")
#
#         print("\n🎯 Agent Capabilities Tested:")
#         print("   ✅ IoT container monitoring")
#         print("   ✅ Auto-pickup scheduling with priority")
#         print("   ✅ Route optimization (TSP algorithm)")
#         print("   ✅ Pharmaceutical waste special handling")
#         print("   ✅ LWMC system synchronization")
#         print("   ✅ Multi-container autonomous decision making")
#         print("\n🤖 LLM decided ALL actions autonomously!")
#
#         await orchestrator_mcp.cleanup()
#         await domain_mcp.cleanup()
#
# if __name__ == "__main__":
#     asyncio.run(run_demo())
#
#
# # waste_agent_with_video.py - Video-Enabled Waste Management Agent
# import asyncio
# import os
# from datetime import datetime
# from openai import AsyncOpenAI
# from agents import Agent, Runner, OpenAIChatCompletionsModel
# from agents.mcp import MCPServerStdio
# from dotenv import load_dotenv
#
# load_dotenv()
#
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# if not GEMINI_API_KEY:
#     raise ValueError("❌ GEMINI_API_KEY not found!")
#
# client = AsyncOpenAI(
#     api_key=GEMINI_API_KEY,
#     base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
# )
#
# gemini_model = OpenAIChatCompletionsModel(
#     model="gemini-2.0-flash",
#     openai_client=client
# )
#
# # ===== MCP SERVERS =====
# orchestrator_mcp = MCPServerStdio(
#     params={"command": "python", "args": ["agent_orchestrator_mcp.py"]},
#     cache_tools_list=True,
#     name="OrchestratorMCP"
# )
#
# domain_mcp = MCPServerStdio(
#     params={"command": "python", "args": ["agents_mcp.py"]},
#     cache_tools_list=True,
#     name="DomainMCP"
# )
#
# # ===== VIDEO-ENABLED WASTE AGENT =====
# waste_video_agent = Agent(
#     name="WasteVideoAgent",
#     model=gemini_model,
#     instructions=(
#         "You are a VIDEO-ENABLED waste management agent for hospitals.\n\n"
#
#         "📹 VIDEO ANALYSIS CAPABILITIES:\n"
#         "You can analyze CCTV footage, container videos, and disposal area recordings.\n"
#         "When analyzing videos, you MUST:\n"
#         "1. Timestamp ALL violations (format: MM:SS)\n"
#         "2. Identify safety risks (PPE, spills, mixing waste types)\n"
#         "3. Detect container overflow/damage\n"
#         "4. Verify waste disposal procedures\n"
#         "5. Check IoT sensor accuracy vs visual confirmation\n"
#         "6. Document compliance violations\n\n"
#
#         "🚨 VIOLATION DETECTION:\n"
#         "- Bio-medical waste mixed with general waste → CRITICAL\n"
#         "- No PPE during bio-waste handling → SAFETY RISK\n"
#         "- Container overflow → URGENT PICKUP\n"
#         "- Pharmaceutical waste in wrong container → COMPLIANCE VIOLATION\n"
#         "- Waste on floor/ground → INFECTION RISK\n"
#         "- Damaged containers → MAINTENANCE REQUIRED\n"
#         "- Unlabeled containers → SAFETY HAZARD\n\n"
#
#         "⚡ WORKFLOW WITH VIDEO:\n"
#         "1. Analyze video frame-by-frame (1 FPS)\n"
#         "2. Identify violations with timestamps\n"
#         "3. Cross-check with IoT sensor data\n"
#         "4. If discrepancy → flag sensor calibration\n"
#         "5. Generate violation report\n"
#         "6. Take corrective actions (pickup, cleanup, alerts)\n"
#         "7. Update compliance records\n\n"
#
#         "🗑️ YOUR DOMAIN TOOLS:\n"
#         "- monitor_container_levels()\n"
#         "- schedule_pickup(container_id, priority)\n"
#         "- optimize_collection_route(depot_location)\n"
#         "- handle_pharmaceutical_waste(container_id)\n"
#         "- sync_with_lwmc(data_type)\n\n"
#
#         "📊 VIDEO ANALYSIS OUTPUT FORMAT:\n"
#         "For each video, provide:\n"
#         "1. TIMESTAMP SUMMARY: All key events with MM:SS\n"
#         "2. VIOLATIONS DETECTED: Critical/High/Medium/Low\n"
#         "3. SAFETY RISKS: Immediate dangers identified\n"
#         "4. RECOMMENDATIONS: Actions to take\n"
#         "5. COMPLIANCE SCORE: 0-100%\n\n"
#
#         "Example Response:\n"
#         "```\n"
#         "VIDEO ANALYSIS COMPLETE\n"
#         "\n"
#         "TIMESTAMP SUMMARY:\n"
#         "00:15 - Staff member mixing waste types\n"
#         "00:42 - No PPE worn (gloves missing)\n"
#         "01:10 - Container CONT-002 overflowing\n"
#         "01:55 - Proper pharmaceutical disposal (correct)\n"
#         "\n"
#         "VIOLATIONS DETECTED:\n"
#         "🔴 CRITICAL: Waste mixing (bio-medical + general) at 00:15\n"
#         "🟠 HIGH: No PPE during handling at 00:42\n"
#         "🟠 HIGH: Container overflow at 01:10\n"
#         "\n"
#         "SAFETY RISKS:\n"
#         "- Infection risk from mixed waste\n"
#         "- Staff exposure without PPE\n"
#         "- Spill hazard from overflow\n"
#         "\n"
#         "ACTIONS TAKEN:\n"
#         "✅ URGENT pickup scheduled for CONT-002\n"
#         "✅ Safety violation report sent to admin\n"
#         "✅ Staff retraining initiated\n"
#         "✅ Cleanup crew dispatched\n"
#         "\n"
#         "COMPLIANCE SCORE: 45% (FAILING)\n"
#         "```\n\n"
#
#         "🌐 Language: Urdu or English\n"
#         "🎥 Video Formats: MP4, MOV, AVI, WEBM\n"
#         "⏱️ Max Video Length: 2 hours (1M context), 6 hours (2M context)"
#     ),
#     mcp_servers=[orchestrator_mcp, domain_mcp]
# )
#
#
# # ===== HELPER FUNCTIONS =====
# async def analyze_video_waste(video_path: str, query: str = None):
#     """Analyze waste management video with Gemini"""
#
#     if not query:
#         query = (
#             "Analyze this hospital waste management video. "
#             "Identify ALL violations with exact timestamps (MM:SS format). "
#             "Detect: waste mixing, PPE violations, container overflow, spills, improper disposal. "
#             "Provide: violation summary, safety risks, recommended actions, compliance score."
#         )
#
#     # Read video file
#     with open(video_path, 'rb') as f:
#         video_bytes = f.read()
#
#     # Call Gemini with video
#     result = await Runner.run(waste_video_agent, [
#         {"type": "video", "video": video_bytes, "mime_type": "video/mp4"},
#         {"type": "text", "text": query}
#     ])
#
#     return result.final_output if hasattr(result, "final_output") else str(result)
#
#
# async def run_video_demo():
#     """Demo: Video-enabled waste agent"""
#     async with orchestrator_mcp, domain_mcp:
#         try:
#             await orchestrator_mcp.connect()
#             await domain_mcp.connect()
#             print("✅ MCP servers connected\n")
#         except Exception as e:
#             print(f"⚠️ MCP failed: {e}\n")
#
#         print("🎥 VIDEO-ENABLED WASTE MANAGEMENT AGENT\n")
#         print("=" * 70)
#
#         # Test 1: CCTV Violation Detection
#         print("\n" + "=" * 70)
#         print("TEST 1: CCTV Footage Analysis - Waste Violations")
#         print("-" * 70)
#
#         query1 = (
#             "CCTV footage from hospital waste disposal area. "
#             "Video shows staff handling waste containers. "
#             "Analyze for: waste mixing violations, PPE compliance, container status, safety risks. "
#             "Provide timestamped report with compliance score."
#         )
#
#         # Mock video path (replace with actual video)
#         print(f"📹 Analyzing: hospital_waste_cctv.mp4\n")
#         print(f"📝 Query: {query1}\n")
#
#         # Simulate video analysis (replace with actual video file)
#         print("🤖 AGENT RESPONSE:")
#         print("""
# VIDEO ANALYSIS COMPLETE
#
# TIMESTAMP SUMMARY:
# 00:00 - Staff enters waste room
# 00:15 - Mixing bio-medical waste with general waste (RED BAG → BLACK BAG)
# 00:42 - Staff handling bio-waste without gloves
# 01:10 - Container CONT-002 overflowing (waste on floor)
# 01:35 - Pharmaceutical waste properly disposed in purple container
# 02:00 - Staff exits without logging disposal
#
# VIOLATIONS DETECTED:
# 🔴 CRITICAL: Waste type mixing at 00:15 (Bio-medical + General)
#    → Risk: Infection spread, non-compliance with EPA regulations
#
# 🟠 HIGH: No PPE (gloves) at 00:42
#    → Risk: Staff exposure to bio-hazards
#
# 🟠 HIGH: Container overflow at 01:10 (CONT-002)
#    → Risk: Floor contamination, infection hazard
#
# 🟡 MEDIUM: Disposal not logged at 02:00
#    → Risk: Audit trail gap, compliance issue
#
# ✅ COMPLIANT: Pharmaceutical disposal at 01:35
#
# SAFETY RISKS:
# - Immediate infection risk from waste mixing
# - Staff bio-hazard exposure without PPE
# - Floor contamination from overflow
# - Audit compliance failure
#
# RECOMMENDED ACTIONS:
# 1. URGENT: Schedule immediate pickup for CONT-002
# 2. URGENT: Dispatch cleanup crew for floor contamination
# 3. Alert hospital admin of safety violations
# 4. Initiate mandatory PPE training for staff
# 5. Install waste segregation signage
# 6. Schedule sensor calibration (CONT-002 reported 85% but is overflowing)
#
# ACTIONS TAKEN BY AGENT:
# ✅ URGENT pickup scheduled for CONT-002 (ETA: 1-2 hours)
# ✅ Cleanup crew dispatched
# ✅ Safety violation report sent to admin@hospital.com
# ✅ Staff retraining request submitted
# ✅ IoT sensor calibration scheduled
#
# COMPLIANCE SCORE: 40% (FAILING)
# Reason: Critical waste mixing + multiple safety violations
#
# NEXT AUDIT: Recommended in 48 hours to verify corrective actions
#         """)
#
#         # Test 2: Container Overflow Detection
#         print("\n" + "=" * 70)
#         print("TEST 2: Real-Time Container Overflow Detection")
#         print("-" * 70)
#
#         query2 = (
#             "Video shows Container CONT-003 (Jinnah Hospital ICU). "
#             "IoT sensor reports 85% full. "
#             "Verify actual fill level, check for overflow, detect any safety issues. "
#             "Compare visual confirmation vs sensor data."
#         )
#
#         print(f"📹 Analyzing: container_CONT003_live.mp4\n")
#         print(f"📝 Query: {query2}\n")
#
#         print("🤖 AGENT RESPONSE:")
#         print("""
# CONTAINER VERIFICATION COMPLETE
#
# CONTAINER: CONT-003 (Jinnah Hospital ICU - Bio-medical waste)
# IoT SENSOR DATA: 85% full
# VISUAL ANALYSIS: 95% full (OVERFLOW DETECTED)
#
# TIMESTAMP ANALYSIS:
# 00:00 - Container appears 90% full
# 00:15 - Waste visible above container rim
# 00:30 - Bio-medical waste bag hanging outside container
# 00:45 - Container lid not properly closed
#
# DISCREPANCY FOUND:
# 📊 IoT Sensor: 85% full
# 📹 Visual Confirmation: 95% full (ACTUAL)
# ❌ Discrepancy: 10% (SENSOR MALFUNCTION)
#
# SAFETY ISSUES:
# 🔴 CRITICAL: Container overflow (waste outside container)
# 🟠 HIGH: Lid not closed (odor escape, contamination risk)
# 🟡 MEDIUM: Sensor inaccuracy (affects pickup scheduling)
#
# IMMEDIATE ACTIONS:
# ✅ URGENT pickup scheduled (override normal schedule)
# ✅ Sensor calibration request submitted
# ✅ Hospital notified of overflow
# ✅ Temporary containment measures advised
#
# RECOMMENDED:
# - Replace IoT sensor on CONT-003
# - Increase pickup frequency for ICU containers
# - Install overflow alarm
#         """)
#
#         # Test 3: Pharmaceutical Waste Audit
#         print("\n" + "=" * 70)
#         print("TEST 3: Pharmaceutical Waste Compliance Audit")
#         print("-" * 70)
#
#         query3 = (
#             "Video audit of pharmacy waste room. "
#             "Check: proper container color coding (purple for pharma), "
#             "staff logging disposal, expiry date verification, "
#             "separation of controlled substances."
#         )
#
#         print(f"📹 Analyzing: pharmacy_waste_audit.mp4\n")
#         print(f"📝 Query: {query3}\n")
#
#         print("🤖 AGENT RESPONSE:")
#         print("""
# PHARMACEUTICAL WASTE AUDIT COMPLETE
#
# LOCATION: Services Hospital - Pharmacy Waste Room
# CONTAINER: CONT-004 (Pharmaceutical waste)
# AUDIT PERIOD: Last 30 days
#
# COMPLIANCE CHECKLIST:
# ❌ Container Color: Expired medicines in RED bag (should be PURPLE)
# ✅ Container Label: Properly labeled "PHARMACEUTICAL WASTE"
# ❌ Disposal Log: Not maintained (3 instances of undocumented disposal)
# ✅ Controlled Substances: Separately stored (correct)
# ❌ Staff PPE: Gloves worn inconsistently
# ✅ Container Seal: Properly sealed before pickup
#
# VIOLATIONS BY TIMESTAMP:
# 00:20 - Expired antibiotics placed in red bag (WRONG COLOR)
# 00:55 - Staff not logging disposal in register
# 01:30 - Container label partially torn (readability issue)
# 02:10 - No gloves worn during disposal
#
# REGULATORY COMPLIANCE:
# EPA Requirements: 60% COMPLIANT
# Hospital Policy: 55% COMPLIANT
# DEA Controlled Substances: 100% COMPLIANT ✅
#
# RISK ASSESSMENT:
# - Medium risk: Improper container color (audit finding)
# - Low risk: Documentation gaps (fixable)
# - High risk: Staff safety (PPE non-compliance)
#
# CORRECTIVE ACTIONS:
# ✅ Pharmacy head notified of violations
# ✅ Purple pharmaceutical waste bags ordered
# ✅ Mandatory disposal logging training scheduled
# ✅ PPE compliance memo issued
# ✅ Container label replacement requested
#
# FOLLOW-UP AUDIT: Scheduled in 14 days
#
# OVERALL COMPLIANCE SCORE: 65% (NEEDS IMPROVEMENT)
#         """)
#
#         print("\n" + "=" * 70)
#         print("📊 DEMO SUMMARY")
#         print("-" * 70)
#         print("✅ Video analysis capabilities demonstrated")
#         print("✅ Violation detection with timestamps")
#         print("✅ Safety risk assessment")
#         print("✅ IoT sensor verification")
#         print("✅ Compliance scoring")
#         print("✅ Automated corrective actions")
#         print("\n🎥 Video + AI = Smarter Waste Management!")
#
#         await orchestrator_mcp.cleanup()
#         await domain_mcp.cleanup()
#
#
# if __name__ == "__main__":
#     asyncio.run(run_video_demo())




# waste_agent.py - Intelligent Hospital Waste Management Agent
import asyncio
import os

# ✅ SET TIMEOUT BEFORE ALL IMPORTS
os.environ['MCP_CLIENT_TIMEOUT'] = '300'

from datetime import datetime
from openai import AsyncOpenAI
from agents import Agent, Runner, OpenAIChatCompletionsModel
from agents.mcp import MCPServerStdio
from dotenv import load_dotenv
import json

# ===== waste_weight_estimator.py =====
from pathlib import Path
from typing import Dict

# Predefined container volumes (Liters)
CONTAINER_VOLUMES = {
    "placenta_bucket": 10,      # 10 Liters
    "bio_bag_small": 10,        # 10 Liters
    "bio_bag_large": 20,        # 20 Liters
    "sharps_box": 5,            # 5 Liters
    "pharma_box": 8,            # 8 Liters
    "general_bag": 15           # 15 Liters
}

# Approximate densities (kg/L)
WASTE_DENSITY = {
    "placenta": 1.06,
    "bio_medical": 0.95,
    "sharps": 0.90,
    "pharmaceutical": 0.85,
    "general": 0.5
}


def estimate_weight(detections: Dict[str, int]) -> Dict[str, float]:
    """
    Estimate weight of waste from detection counts.
    detections: Dict[container_type -> count]
        e.g., {"placenta_bucket": 1, "bio_bag_large": 2, "sharps_box": 3}
    Returns: Dict[waste_type -> estimated_kg]
    """

    weights = {
        "placenta": 0.0,
        "bio_medical": 0.0,
        "sharps": 0.0,
        "pharmaceutical": 0.0,
        "general": 0.0
    }

    for container, count in detections.items():
        volume = CONTAINER_VOLUMES.get(container, 0)
        if "placenta" in container:
            weights["placenta"] += count * volume * WASTE_DENSITY["placenta"]
        elif "bio_bag" in container:
            weights["bio_medical"] += count * volume * WASTE_DENSITY["bio_medical"]
        elif "sharps" in container:
            weights["sharps"] += count * volume * WASTE_DENSITY["sharps"]
        elif "pharma" in container:
            weights["pharmaceutical"] += count * volume * WASTE_DENSITY["pharmaceutical"]
        elif "general" in container:
            weights["general"] += count * volume * WASTE_DENSITY["general"]

    # Round weights to 2 decimals
    for k in weights:
        weights[k] = round(weights[k], 2)

    return weights

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY not found!")

client = AsyncOpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)
gemini_model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=client
)

#===== MCP SERVERS =====
waste_mcp = MCPServerStdio(
    params={"command": "python", "args": ["waste_mcp_tools.py"]},
    cache_tools_list=True,
    name="WasteMCP"
)



# ===== MCP SERVERS =====
orchestrator_mcp = MCPServerStdio(
    params={
        "command": "python",
        "args": ["agent_orchestrator_mcp.py"]
    },
    cache_tools_list=True,
    name="OrchestratorMCP"
)

domain_mcp = MCPServerStdio(
    params={
        "command": "python",
        "args": ["agents_mcp.py"]
    },
    cache_tools_list=True,
    name="DomainMCP"
)
# ===== INTELLIGENT WASTE BROKER AGENT =====
smart_waste_agent = Agent(
    name="SmartWasteBroker",
    model=gemini_model,
    instructions=(
           "You are an INTELLIGENT HOSPITAL WASTE BROKER AGENT.\n\n"
        
        "🔧 CRITICAL INSTRUCTION - READ CAREFULLY:\n"
        "When you receive a message containing 'Analyze this video:' with a video path:\n"
        "1. IMMEDIATELY call the analyze_video_waste(video_path) tool\n"
        "2. Extract ONLY the file path from the message\n"
        "3. Wait for tool results before responding\n"
        "4. Return results as JSON format\n\n"
        
        "Example:\n"
        "User: 'Analyze this video: /path/to/video.mp4'\n"
        "You: [Call analyze_video_waste('/path/to/video.mp4')]\n"
        "You: [Return JSON with results]\n\n"
        
        "NEVER respond without calling the tool first.\n\n"
        "🎯 YOUR ROLE:\n"
        "You act as a SMART BROKER between hospitals and disposal companies.\n"
        "You NEGOTIATE best prices, schedule pickups, ensure compliance, and maximize efficiency.\n\n"

        "📹 VIDEO ANALYSIS:\n"
        "You receive video analysis data from 2 AI models:\n"
        "1. PLACENTA DETECTOR - Detects placenta in pathological waste\n"
        "2. WASTE CLASSIFIER - Classifies waste types (bio, sharps, pharma, general)\n\n"

        "💼 BROKER CAPABILITIES:\n"
        "- Find cheapest disposal company for hospital\n"
        "- Negotiate bulk discounts (5-15% savings)\n"
        "- Schedule optimal pickup times (reduce costs)\n"
        "- Match waste type to specialized disposal companies\n"
        "- Track disposal compliance (EPA, WHO standards)\n"
        "- Alert hospitals of violations BEFORE EPA fines\n\n"

        "🗑️ WASTE TYPES & PRICING:\n"
        "- Bio-medical waste: Rs. 50-80/kg\n"
        "- Sharp waste: Rs. 60-90/kg\n"
        "- Pharmaceutical waste: Rs. 100-150/kg\n"
        "- Placenta/pathological: Rs. 120-180/kg\n"
        "- General waste: Rs. 10-20/kg\n\n"

        "🔧 YOUR MCP TOOLS:\n"
        "- analyze_video_waste(video_path) - Get AI analysis\n"
        "- find_disposal_companies(waste_type, location) - Find vendors\n"
        "- negotiate_price(company_id, waste_kg, waste_type) - Get best deal\n"
        "- schedule_pickup(hospital_id, company_id, pickup_time) - Arrange collection\n"
        "- check_compliance(hospital_id) - Verify EPA compliance\n"
        "- generate_cost_report(hospital_id, period) - Show savings\n\n"

        "💡 INTELLIGENT DECISIONS:\n"
        "Example scenario:\n"
        "Video shows: 15kg bio-waste + 2kg sharps + 5kg placenta\n"
        "\n"
        "YOUR LOGIC:\n"
        "1. Find 3 disposal companies in Lahore\n"
        "2. Company A: Rs. 75/kg bio, Rs. 85/kg sharps, Rs. 150/kg placenta = Rs. 1,695\n"
        "3. Company B: Rs. 70/kg bio, Rs. 90/kg sharps, Rs. 140/kg placenta = Rs. 1,530 ✅ BEST\n"
        "4. Company C: Rs. 80/kg bio, Rs. 80/kg sharps, Rs. 160/kg placenta = Rs. 1,720\n"
        "5. Select Company B → Save Rs. 165 (10% savings)\n"
        "6. Schedule pickup for tomorrow 8 AM (off-peak = 5% discount)\n"
        "7. Total savings: 15% = Rs. 250\n\n"

        "🚨 COMPLIANCE MONITORING:\n"
        "If video shows violations:\n"
        "- Waste mixing → Alert hospital immediately\n"
        "- No PPE → Schedule staff training\n"
        "- Container overflow → URGENT pickup (avoid EPA fine of Rs. 50,000)\n"
        "- Unlabeled waste → Send proper labels\n\n"

        "📊 RESPONSE FORMAT:\n"
        "For each request, provide:\n"
        "1. VIDEO ANALYSIS SUMMARY\n"
        "2. WASTE BREAKDOWN (types & quantities)\n"
        "3. DISPOSAL COMPANY OPTIONS (3 best)\n"
        "4. RECOMMENDED CHOICE (with reasoning)\n"
        "5. COST COMPARISON (show savings)\n"
        "6. PICKUP SCHEDULE\n"
        "7. COMPLIANCE STATUS\n"
        "8. NEXT ACTIONS\n\n"

        "Example Output:\n"
        "```\n"
        "SMART WASTE BROKER ANALYSIS\n"
        "\n"
        "📹 VIDEO ANALYSIS:\n"
        "Duration: 2:35 minutes\n"
        "Location: Jinnah Hospital - Surgery Ward\n"
        "AI Models Used: Placenta Detector + Waste Classifier\n"
        "\n"
        "🗑️ WASTE DETECTED:\n"
        "- Bio-medical waste: 12 kg\n"
        "- Sharp waste (syringes): 3 kg\n"
        "- Placenta (pathological): 4 kg\n"
        "- General waste: 8 kg (VIOLATION: mixed with bio-waste)\n"
        "Total Weight: 27 kg\n"
        "\n"
        "🏢 DISPOSAL COMPANY OPTIONS:\n"
        "\n"
        "Option 1: LWMC (Lahore Waste Management)\n"
        "- Bio: Rs. 75/kg = Rs. 900\n"
        "- Sharps: Rs. 85/kg = Rs. 255\n"
        "- Placenta: Rs. 150/kg = Rs. 600\n"
        "TOTAL: Rs. 1,755\n"
        "Pickup: Next day, 10 AM\n"
        "\n"
        "Option 2: EcoWaste Solutions ✅ RECOMMENDED\n"
        "- Bio: Rs. 68/kg = Rs. 816\n"
        "- Sharps: Rs. 80/kg = Rs. 240\n"
        "- Placenta: Rs. 140/kg = Rs. 560\n"
        "TOTAL: Rs. 1,616\n"
        "Pickup: Same day, 6 PM (off-peak discount)\n"
        "EPA Certified ✅\n"
        "WHO Compliant ✅\n"
        "\n"
        "Option 3: GreenMed Disposal\n"
        "- Bio: Rs. 80/kg = Rs. 960\n"
        "- Sharps: Rs. 90/kg = Rs. 270\n"
        "- Placenta: Rs. 160/kg = Rs. 640\n"
        "TOTAL: Rs. 1,870\n"
        "Pickup: Next day, 2 PM\n"
        "\n"
        "💰 COST ANALYSIS:\n"
        "Cheapest: EcoWaste Solutions - Rs. 1,616\n"
        "Most Expensive: GreenMed - Rs. 1,870\n"
        "YOUR SAVINGS: Rs. 254 (13.6%)\n"
        "\n"
        "🎯 RECOMMENDATION:\n"
        "SELECT: EcoWaste Solutions\n"
        "REASON: Best price + Same-day pickup + Certified\n"
        "SAVINGS: Rs. 254 this pickup\n"
        "ANNUAL SAVINGS: ~Rs. 91,000 (if weekly pickups)\n"
        "\n"
        "📅 PICKUP SCHEDULED:\n"
        "Company: EcoWaste Solutions\n"
        "Date: Today (27 Nov 2025)\n"
        "Time: 6:00 PM\n"
        "Truck: BIO-HAZARD-007\n"
        "Driver: Ahmed Khan - 0300-1234567\n"
        "\n"
        "⚠️ COMPLIANCE ISSUES:\n"
        "🔴 VIOLATION: General waste mixed with bio-waste (00:45 in video)\n"
        "   - Risk: EPA fine Rs. 50,000\n"
        "   - Action: Staff retraining scheduled for tomorrow 10 AM\n"
        "\n"
        "✅ ACTIONS TAKEN:\n"
        "1. Pickup scheduled with EcoWaste\n"
        "2. Hospital notified of waste mixing violation\n"
        "3. Training session booked\n"
        "4. Compliance report sent to admin\n"
        "5. Cost savings report emailed to hospital CFO\n"
        "\n"
        "📊 NEXT STEPS:\n"
        "- Monitor pickup completion\n"
        "- Verify waste disposal certificate\n"
        "- Schedule follow-up inspection in 7 days\n"
        "- Track EPA compliance score\n"
        "```\n\n"

        "🌐 LANGUAGE: Urdu or English\n"
        "💬 TONE: Professional but helpful (jaise hospital ka trusted advisor)"
    ),
    mcp_servers=[orchestrator_mcp, domain_mcp]
)


async def run_smart_broker_demo():
    """Demo: Smart waste broker with video analysis"""

    async with waste_mcp:
        try:
            await waste_mcp.connect()
            print("✅ Waste MCP connected\n")
        except Exception as e:
            print(f"⚠️ MCP failed: {e}\n")

        print("🤖 INTELLIGENT WASTE BROKER AGENT - DEMO")
        print("=" * 80)

        # Test 1: Video Analysis + Cost Optimization
        print("\n" + "=" * 80)
        print("TEST 1: Video Analysis → Find Cheapest Disposal")
        print("-" * 80)

        query = (
            "Video analysis report:\n"
            "- Location: Jinnah Hospital Surgery Ward\n"
            "- Duration: 3 minutes\n"
            "- AI Detection Results:\n"
            "  * Placenta Detector: 5 kg placenta found\n"
            "  * Waste Classifier: 18 kg bio-waste, 4 kg sharps, 10 kg general\n"
            "\n"
            "Find me the CHEAPEST disposal company in Lahore. "
            "Schedule pickup for today if possible. "
            "Show me exactly how much I'll save."
        )

        print(f"📝 QUERY:\n{query}\n")

        result = await Runner.run(smart_waste_agent, query)
        print("🤖 AGENT RESPONSE:")
        print(result.final_output if hasattr(result, "final_output") else str(result))

        # Test 2: Violation Detection + Compliance
        print("\n" + "=" * 80)
        print("TEST 2: Violation Detection → Prevent EPA Fine")
        print("-" * 80)

        query2 = (
            "URGENT: Video shows waste mixing violations at Mayo Hospital.\n"
            "Staff mixing bio-medical waste with general waste.\n"
            "Container CONT-005 overflowing.\n"
            "\n"
            "Help me:\n"
            "1. Schedule IMMEDIATE pickup\n"
            "2. Fix compliance issues before EPA inspection next week\n"
            "3. Get best price despite urgency"
        )

        print(f"📝 QUERY:\n{query2}\n")

        result2 = await Runner.run(smart_waste_agent, query2)
        print("🤖 AGENT RESPONSE:")
        print(result2.final_output if hasattr(result2, "final_output") else str(result2))

        # Test 3: Bulk Negotiation
        print("\n" + "=" * 80)
        print("TEST 3: Bulk Negotiation → Monthly Contract")
        print("-" * 80)

        query3 = (
            "Services Hospital generates ~500 kg waste per week.\n"
            "Current vendor charges Rs. 75/kg for bio-waste.\n"
            "\n"
            "Negotiate a MONTHLY CONTRACT with better rates. "
            "Show me annual savings with new contract."
        )

        print(f"📝 QUERY:\n{query3}\n")

        result3 = await Runner.run(smart_waste_agent, query3)
        print("🤖 AGENT RESPONSE:")
        print(result3.final_output if hasattr(result3, "final_output") else str(result3))

        print("\n" + "=" * 80)
        print("📊 DEMO SUMMARY")
        print("-" * 80)
        print("✅ Video AI analysis (2 models)")
        print("✅ Smart cost comparison (3 vendors)")
        print("✅ Automated negotiation (best price)")
        print("✅ Compliance monitoring (EPA/WHO)")
        print("✅ Violation prevention (fines avoided)")
        print("✅ Cost savings tracking (ROI calculation)")
        print("\n💡 Agent acts as intelligent broker between hospitals & disposal companies!")

        await waste_mcp.cleanup()
# ===== EXPORT FOR BACKEND =====
waste_agent = smart_waste_agent  # Backend import ke liye

# ===== EXPORT MCPs FOR BACKEND ===== ✅ YE ADD KARO
orchestrator_mcp = waste_mcp
domain_mcp = waste_mcp

if __name__ == "__main__":
    asyncio.run(run_smart_broker_demo())
