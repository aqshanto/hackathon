import random
from models.schemas import NodeStatus
from ml.real_ai_engine import real_ai

class MFSOrchestrator:
    def __init__(self):
        self.ai_enabled = True
        self.surge_active = False
        self.anomaly_active = False
        self.uptime = 100.0
        self.latency = 5.0
        self.sim_seconds = 0.0
        self.total_heavy = 0
        self.total_light = 0
        self.failed_tasks = 0
        self.legacy_cost = 0.0
        self.optimized_cost = 0.0
        self.latest_ai_decision = "System Normal. AI Smart Scheduling active."
        
        self.nodes = [
            NodeStatus(id=0, name="Node 1 (Heavy GPU)", type="heavy", load=0.0, temp=35.0, assigned=0, status="healthy", costActive=2.5, costStandby=0.0),
            NodeStatus(id=1, name="Node 2 (Light CPU)", type="light", load=0.0, temp=30.0, assigned=0, status="healthy", costActive=0.4, costStandby=0.0),
            NodeStatus(id=2, name="Node 3 (Scaler)", type="dynamic", load=0.0, temp=25.0, assigned=0, status="standby", costActive=1.2, costStandby=0.0)
        ]

    def update_simulation(self, dt_ms: float):
        sim_speed_multiplier = 600
        sim_dt_seconds = (dt_ms / 1000.0) * sim_speed_multiplier
        self.sim_seconds += sim_dt_seconds
        sim_dt_hours = sim_dt_seconds / 3600.0

        # ১. আসল MFS ট্রানজেকশন ডেটা জেনারেট করা হচ্ছে
        spawn_chance = 0.7 if self.surge_active else 0.15
        if random.random() < spawn_chance:
            # একটি আসল MFS ট্রানজেকশন পেলোড তৈরি হচ্ছে
            amount = random.choice([500, 1200, 2500, 5000, 15000, 48000, 50000])
            tx_type = random.choice([0, 1, 2]) # 0:Send, 1:Pay, 2:Cashout
            account_age = random.randint(0, 60)
            
            # ২. আসল Scikit-Learn ML মডেল দিয়ে প্রেডিক্ট করা হচ্ছে এটা Heavy নাকি Light
            ai_analysis = real_ai.predict_task_complexity(amount, tx_type, account_age)
            is_heavy = ai_analysis["is_heavy"]
            load_to_add = ai_analysis["cpu_load_required"]
            
            if is_heavy:
                self.total_heavy += 1
            else:
                self.total_light += 1
            self.route_task(is_heavy, load_to_add)

        active_count = 0
        current_latency_sum = 0.0

        for i, n in enumerate(self.nodes):
            if n.load > 0:
                decay = 1.5 if self.ai_enabled else 0.6
                n.load = max(0.0, n.load - decay)

            if i == 0 and self.anomaly_active:
                n.temp += 0.5
                # ৩. যখনই নোড ১ ওভারহিট করবে, সাথে সাথে আসল LLM API কল করে লাইভ ডিসিশন নেবে!
                if n.temp > 75 and random.random() < 0.1:
                    self.latest_ai_decision = real_ai.analyze_anomaly_with_llm(n.name, n.temp, n.load, self.total_heavy)
            else:
                if n.load > 75: n.temp += 0.15
                elif n.temp > 25: n.temp -= 0.2

            if n.temp > 95:
                n.status = "crashed"
                n.load = 0.0
            elif n.temp > 75 and n.status != "crashed":
                n.status = "warning" if self.ai_enabled else "healthy"
            elif n.temp <= 75 and n.status == "warning":
                n.status = "healthy"
            elif n.temp < 50 and n.status == "crashed":
                n.status = "healthy"

            if self.ai_enabled and i == 2 and n.status != "crashed":
                if not self.surge_active and n.load == 0 and self.nodes[0].load < 60 and self.nodes[1].load < 60:
                    n.status = "standby"
            elif not self.ai_enabled and i == 2 and n.status == "standby":
                n.status = "healthy"

            if n.status not in ["standby", "crashed"]:
                active_count += 1
            current_latency_sum += n.load * 0.4

        base_latency = 5.0
        fail_penalty = min(500.0, self.failed_tasks * 10.0) if self.failed_tasks > 0 else 0.0
        target_latency = base_latency + (current_latency_sum / (active_count or 1)) + fail_penalty
        self.latency = (self.latency * 0.9) + (target_latency * 0.1)

        total_processed = self.total_heavy + self.total_light
        target_uptime = 100.0
        if total_processed > 0:
            target_uptime = 100.0 - (self.failed_tasks / total_processed) * 100.0
        self.uptime = (self.uptime * 0.95) + (target_uptime * 0.05)

        current_legacy_rate = sum(n.costActive for n in self.nodes)
        current_optimized_rate = sum(n.costStandby if n.status == "standby" else n.costActive for n in self.nodes)

        self.legacy_cost += current_legacy_rate * sim_dt_hours
        self.optimized_cost += current_optimized_rate * sim_dt_hours

    def route_task(self, is_heavy: bool, load_amt: float):
        dest_idx = 0
        if self.ai_enabled:
            if is_heavy:
                dest_idx = 0 if (self.nodes[0].status == "healthy" and self.nodes[0].load < 85) else 2
            else:
                dest_idx = 1 if (self.nodes[1].status == "healthy" and self.nodes[1].load < 85) else 2
        else:
            total = self.total_heavy + self.total_light
            dest_idx = total % 3

        if self.nodes[dest_idx].status == "standby":
            self.nodes[dest_idx].status = "healthy"
        
        self.nodes[dest_idx].assigned += 1
        if self.nodes[dest_idx].status == "crashed":
            self.failed_tasks += 1
        else:
            self.nodes[dest_idx].load = min(100.0, self.nodes[dest_idx].load + load_amt)

    def format_time(self, secs: float) -> str:
        h = int(secs // 3600)
        m = int((secs % 3600) // 60)
        s = int(secs % 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    def get_telemetry(self) -> dict:
        active_nodes_count = sum(1 for n in self.nodes if n.status not in ["standby", "crashed"])
        return {
            "uptime": round(self.uptime, 2),
            "latency": round(self.latency, 1),
            "active_nodes": f"{active_nodes_count}/3",
            "sim_time": self.format_time(self.sim_seconds),
            "total_heavy": self.total_heavy,
            "total_light": self.total_light,
            "saved_cost": round(self.legacy_cost - self.optimized_cost, 2),
            "nodes": [n.model_dump() for n in self.nodes],
            "ai_enabled": self.ai_enabled,
            "surge_active": self.surge_active,
            "anomaly_active": self.anomaly_active,
            "ai_decision": self.latest_ai_decision  # নতুন লাইভ এআই ডিসিশন পাঠানো হচ্ছে
        }

orchestrator = MFSOrchestrator()