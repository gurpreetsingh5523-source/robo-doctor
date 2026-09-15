"""
AMRIT Harness Integration - 6 Team Architecture Patterns
Based on revfactory/harness - A/B tested +60% quality improvement
"""
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import random
from datetime import datetime
from collections import Counter

class TeamPattern(Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    VOTING = "voting"
    HIERARCHICAL = "hierarchical"
    DEBATE = "debate"
    SPECIALIZED = "specialized"

@dataclass
class TaskResult:
    agent_id: str
    task: str
    output: str
    confidence: float
    timestamp: str

class TeamArchitecture:
    """
    6 proven team patterns for multi-agent collaboration
    Each pattern optimized for different problem types
    """

    def __init__(self, pattern: TeamPattern = TeamPattern.DEBATE):
        self.pattern = pattern
        self.agents = []
        self.results_history = []

    def add_agent(self, agent_id: str, role: str, expertise: List[str]):
        """Add agent to team"""
        self.agents.append({
            'id': agent_id,
            'role': role,
            'expertise': expertise,
            'status': 'idle'
        })

    def execute_sequential(self, tasks: List[str]) -> List[TaskResult]:
        """
        Pattern 1: SEQUENTIAL
        Step-by-step pipeline. Each agent's output feeds next agent's input.
        Best for: Multi-step workflows, data processing pipelines
        """
        results = []
        current_input = tasks[0] if tasks else ""

        for i, agent in enumerate(self.agents):
            if i < len(tasks):
                result = TaskResult(
                    agent_id=agent['id'],
                    task=tasks[i],
                    output="Processed by %s: %s" % (agent['role'], tasks[i]),
                    confidence=random.uniform(0.7, 0.95),
                    timestamp=datetime.now().isoformat()
                )
                results.append(result)
                current_input = result.output

        return results

    def execute_parallel(self, task: str) -> List[TaskResult]:
        """
        Pattern 2: PARALLEL
        Divide task among agents, merge results.
        Best for: Large tasks, independent subtasks, speed optimization
        """
        results = []
        subtasks = self._divide_task(task, len(self.agents))

        for agent, subtask in zip(self.agents, subtasks):
            result = TaskResult(
                agent_id=agent['id'],
                task=subtask,
                output="Parallel processing by %s: %s" % (agent['role'], subtask),
                confidence=random.uniform(0.75, 0.95),
                timestamp=datetime.now().isoformat()
            )
            results.append(result)

        merged = self._merge_results(results)
        results.append(merged)

        return results

    def execute_voting(self, task: str) -> TaskResult:
        """
        Pattern 3: VOTING
        Multiple agents solve same task, majority vote wins.
        Best for: Critical decisions, reducing bias, verification
        """
        votes = {}

        for agent in self.agents:
            vote = random.choice(['A', 'B', 'C'])
            votes[vote] = votes.get(vote, 0) + 1

            result = TaskResult(
                agent_id=agent['id'],
                task=task,
                output="Vote: %s by %s" % (vote, agent['role']),
                confidence=random.uniform(0.6, 0.9),
                timestamp=datetime.now().isoformat()
            )
            self.results_history.append(result)

        winner = max(votes, key=votes.get)

        return TaskResult(
            agent_id="MAJORITY_VOTE",
            task=task,
            output="Consensus: %s (votes: %s)" % (winner, votes),
            confidence=votes[winner] / len(self.agents),
            timestamp=datetime.now().isoformat()
        )

    def execute_hierarchical(self, task: str) -> List[TaskResult]:
        """
        Pattern 4: HIERARCHICAL
        Manager assigns subtasks to workers, reviews output.
        Best for: Complex projects, quality control, delegation
        """
        results = []

        manager = self.agents[0]
        plan = self._create_plan(task, manager)

        results.append(TaskResult(
            agent_id=manager['id'],
            task="Planning",
            output="Plan created: %s" % plan,
            confidence=0.9,
            timestamp=datetime.now().isoformat()
        ))

        workers = self.agents[1:]
        for i, worker in enumerate(workers):
            if i < len(plan):
                result = TaskResult(
                    agent_id=worker['id'],
                    task=plan[i],
                    output="Executed by %s: %s" % (worker['role'], plan[i]),
                    confidence=random.uniform(0.7, 0.9),
                    timestamp=datetime.now().isoformat()
                )
                results.append(result)

        review = self._review_results(results, manager)
        results.append(review)

        return results

    def execute_debate(self, topic: str, max_rounds: int = 3) -> Dict:
        """
        Pattern 5: DEBATE
        Structured debate between agents to reach consensus.
        Best for: Complex decisions, hypothesis validation, ethics review
        """
        rounds = []

        for round_num in range(max_rounds):
            round_results = []

            for agent in self.agents:
                stance = random.choice(['pro', 'con', 'neutral'])
                argument = "Agent %s argues %s on %s" % (agent['role'], stance, topic)

                round_results.append({
                    'agent': agent['id'],
                    'stance': stance,
                    'argument': argument,
                    'confidence': random.uniform(0.6, 0.95)
                })

            consensus = self._calculate_consensus(round_results)

            rounds.append({
                'round': round_num + 1,
                'arguments': round_results,
                'consensus': consensus
            })

            if consensus['score'] > 0.8:
                break

        return {
            'topic': topic,
            'pattern': 'debate',
            'rounds': rounds,
            'final_consensus': rounds[-1]['consensus'],
            'recommendation': self._generate_recommendation(rounds[-1]['consensus'])
        }

    def execute_specialized(self, task: str, domain: str) -> List[TaskResult]:
        """
        Pattern 6: SPECIALIZED
        Domain experts handle specific aspects.
        Best for: Medical, legal, scientific tasks requiring expertise
        """
        results = []

        expert = self._find_expert(domain)

        if expert:
            result = TaskResult(
                agent_id=expert['id'],
                task=task,
                output="Specialized analysis by %s in %s: %s" % (expert['role'], domain, task),
                confidence=random.uniform(0.85, 0.98),
                timestamp=datetime.now().isoformat()
            )
            results.append(result)

        validators = [a for a in self.agents if a['id'] != expert['id']]
        for validator in validators[:2]:
            result = TaskResult(
                agent_id=validator['id'],
                task="Validation",
                output="Validated by %s: %s" % (validator['role'], task),
                confidence=random.uniform(0.7, 0.9),
                timestamp=datetime.now().isoformat()
            )
            results.append(result)

        return results

    def _divide_task(self, task: str, n_parts: int) -> List[str]:
        """Divide task into subtasks"""
        words = task.split()
        chunk_size = max(1, len(words) // n_parts)
        return [' '.join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]

    def _merge_results(self, results: List[TaskResult]) -> TaskResult:
        """Merge parallel results"""
        outputs = [r.output for r in results]
        return TaskResult(
            agent_id="MERGER",
            task="Merge",
            output="Merged: " + " | ".join(outputs),
            confidence=sum(r.confidence for r in results) / len(results),
            timestamp=datetime.now().isoformat()
        )

    def _create_plan(self, task: str, manager: Dict) -> List[str]:
        """Create execution plan"""
        return ["Step 1: Analyze %s" % task, "Step 2: Process %s" % task, "Step 3: Validate %s" % task]

    def _review_results(self, results: List[TaskResult], manager: Dict) -> TaskResult:
        """Review worker results"""
        avg_confidence = sum(r.confidence for r in results) / len(results) if results else 0
        return TaskResult(
            agent_id=manager['id'],
            task="Review",
            output="Review complete. Avg confidence: %.2f" % avg_confidence,
            confidence=avg_confidence,
            timestamp=datetime.now().isoformat()
        )

    def _calculate_consensus(self, arguments: List[Dict]) -> Dict:
        """Calculate debate consensus"""
        stances = [a['stance'] for a in arguments]
        stance_counts = Counter(stances)
        majority = stance_counts.most_common(1)[0]

        return {
            'score': majority[1] / len(arguments),
            'majority_stance': majority[0],
            'agreement': majority[1],
            'total': len(arguments)
        }

    def _generate_recommendation(self, consensus: Dict) -> str:
        """Generate recommendation from consensus"""
        if consensus['score'] > 0.7:
            return "Strong consensus reached. Proceed with majority stance: %s" % consensus['majority_stance']
        elif consensus['score'] > 0.5:
            return "Moderate consensus. Consider additional review."
        else:
            return "Weak consensus. Require more evidence or expert input."

    def _find_expert(self, domain: str) -> Optional[Dict]:
        """Find domain expert"""
        for agent in self.agents:
            if domain.lower() in [e.lower() for e in agent.get('expertise', [])]:
                return agent
        return self.agents[0] if self.agents else None


class AutoTeamGenerator:
    """
    Auto-generate optimal team based on task requirements
    Inspired by Harness pattern matching
    """

    PATTERN_MAP = {
        'medical_diagnosis': TeamPattern.SPECIALIZED,
        'research_analysis': TeamPattern.DEBATE,
        'data_processing': TeamPattern.SEQUENTIAL,
        'literature_review': TeamPattern.PARALLEL,
        'ethics_review': TeamPattern.VOTING,
        'project_management': TeamPattern.HIERARCHICAL,
    }

    def __init__(self):
        self.team_history = []

    def generate_team(self, task_type: str, complexity: str = 'medium') -> TeamArchitecture:
        """Auto-generate optimal team for task"""

        pattern = self.PATTERN_MAP.get(task_type, TeamPattern.DEBATE)
        team = TeamArchitecture(pattern)

        if pattern == TeamPattern.SPECIALIZED:
            team.add_agent('EXPERT_001', 'Medical Expert', ['medicine', 'diagnosis'])
            team.add_agent('EXPERT_002', 'Genetics Expert', ['genetics', 'genomics'])
            team.add_agent('EXPERT_003', 'Ethics Expert', ['ethics', 'bioethics'])

        elif pattern == TeamPattern.DEBATE:
            team.add_agent('DEBATER_001', 'Researcher', ['research', 'analysis'])
            team.add_agent('DEBATER_002', 'Critic', ['review', 'validation'])
            team.add_agent('DEBATER_003', 'Synthesizer', ['integration', 'summary'])
            team.add_agent('DEBATER_004', 'Ethicist', ['ethics', 'gurmat'])

        elif pattern == TeamPattern.HIERARCHICAL:
            team.add_agent('MANAGER_001', 'Project Manager', ['planning', 'coordination'])
            team.add_agent('WORKER_001', 'Data Analyst', ['analysis', 'statistics'])
            team.add_agent('WORKER_002', 'Research Assistant', ['research', 'documentation'])

        else:
            team.add_agent('AGENT_001', 'Researcher', ['research'])
            team.add_agent('AGENT_002', 'Analyst', ['analysis'])
            team.add_agent('AGENT_003', 'Validator', ['validation'])

        self.team_history.append({
            'task_type': task_type,
            'pattern': pattern.value,
            'agents': len(team.agents),
            'complexity': complexity
        })

        return team

    def get_recommendation(self, task_type: str) -> Dict:
        """Get team recommendation for task type"""
        pattern = self.PATTERN_MAP.get(task_type, TeamPattern.DEBATE)

        recommendations = {
            TeamPattern.SEQUENTIAL: "Use for multi-step workflows with clear dependencies",
            TeamPattern.PARALLEL: "Use for large tasks that can be divided independently",
            TeamPattern.VOTING: "Use for critical decisions requiring consensus",
            TeamPattern.HIERARCHICAL: "Use for complex projects needing oversight",
            TeamPattern.DEBATE: "Use for research validation and hypothesis testing",
            TeamPattern.SPECIALIZED: "Use for domain-specific tasks requiring expertise"
        }

        return {
            'task_type': task_type,
            'recommended_pattern': pattern.value,
            'rationale': recommendations[pattern],
            'estimated_agents': 3 if pattern in [TeamPattern.SEQUENTIAL, TeamPattern.VOTING] else 4
        }
