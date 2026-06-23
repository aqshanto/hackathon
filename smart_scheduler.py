import random
import json
import time
import os

# --- 1. SIMULATION SETUP ---
def generate_cluster_nodes():
    return [
        {"node_id": "Node-1", "max_cpu": 32, "current_cpu": random.uniform(5.0, 15.0), "temp": random.uniform(40.0, 50.0), "tasks": []},
        {"node_id": "Node-2", "max_cpu": 64, "current_cpu": random.uniform(10.0, 30.0), "temp": random.uniform(45.0, 55.0), "tasks": []},
        {"node_id": "Node-3", "max_cpu": 16, "current_cpu": random.uniform(2.0, 10.0), "temp": random.uniform(35.0, 40.0), "tasks": []},
    ]

def generate_incoming_workloads():
    tasks = []
    # Increased volume: Now generates between 5 and 10 tasks per cycle to simulate heavy load
    for i in range(random.randint(5, 10)):
        tasks.append({
            "task_id": f"T-{random.randint(1000, 9999)}",
            "req_cpu": random.randint(2, 8) # Lowered max CPU slightly to allow better bin-packing
        })
    return tasks

# --- 2. THE SCHEDULING ALGORITHM ---
def run_scheduler():
    print("🚀 Starting Smart Scheduler Simulation...")
    nodes = generate_cluster_nodes()
    
    # Ensure the frontend directory exists for the JSON export
    export_dir = '../frontend_web'
    os.makedirs(export_dir, exist_ok=True)
    
    try:
        while True:
            # Step A: Cool down nodes and finish OLD tasks from the previous cycle
            for node in nodes:
                node['temp'] = max(35.0, node['temp'] - 5.0) # Cool down
                
                # Clear out tasks from the last 30-second window
                while len(node['tasks']) > 0 and random.random() > 0.2:
                    node['tasks'].pop(0) 
                    node['current_cpu'] = max(2.0, node['current_cpu'] - random.uniform(4.0, 10.0))

            # Step B: Generate new tasks
            new_tasks = generate_incoming_workloads()
            decision_logs = []
            
            # Sort tasks by highest CPU requirement first (Greedy approach)
            new_tasks.sort(key=lambda x: x['req_cpu'], reverse=True)
            
            # Step C: Assign NEW tasks to the best available node
            for task in new_tasks:
                best_node = None
                max_available_cpu = -1
                decision_reason = "No available nodes"
                
                for node in nodes:
                    available_cpu = node['max_cpu'] - node['current_cpu']
                    
                    # Check constraints: Node must have enough CPU and Temp must be < 80°C
                    if available_cpu >= task['req_cpu'] and node['temp'] < 80.0:
                        if available_cpu > max_available_cpu:
                            max_available_cpu = available_cpu
                            best_node = node
                            decision_reason = f"Optimal Node: Most free CPU ({available_cpu:.1f} cores) & Safe Temp."
                
                # Update the node state and log the decision
                if best_node:
                    best_node['tasks'].append(task['task_id'])
                    best_node['current_cpu'] += task['req_cpu']
                    best_node['temp'] += (task['req_cpu'] * 0.5)
                    
                    decision_logs.append({
                        "task_id": task['task_id'],
                        "req_cpu": task['req_cpu'],
                        "status": "Assigned",
                        "node": best_node['node_id'],
                        "reason": decision_reason
                    })
                else:
                    decision_logs.append({
                        "task_id": task['task_id'],
                        "req_cpu": task['req_cpu'],
                        "status": "Queued",
                        "node": "None",
                        "reason": "Cluster overloaded or all nodes > 80.0°C."
                    })
                
            # --- 3. EXPORT TO FRONTEND ---
            payload = {
                "nodes": nodes,
                "latest_logs": decision_logs
            }
            
            # Write to the JSON file
            export_path = os.path.join(export_dir, 'data.json')
            with open(export_path, 'w') as f:
                json.dump(payload, f)
                
            print("✅ Processed batch, logged decisions, and updated dashboard data.")
            time.sleep(30) # Wait 30 seconds so the dashboard displays the data
            
    except KeyboardInterrupt:
        print("\n🛑 Scheduler Stopped.")

if __name__ == "__main__":
    run_scheduler()