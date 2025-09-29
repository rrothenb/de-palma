#!/usr/bin/env python3
"""
De Palma Task Scheduler MCP Server

Uses Google OR-Tools for optimal task assignment based on:
- Skill matching
- Workload balancing
- Deadline constraints
- Team member availability
"""

import json
import sys
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
from ortools.sat.python import cp_model
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Task:
    id: str
    description: str
    skills_required: List[str]
    estimated_hours: float
    deadline: Optional[str] = None
    priority: str = 'medium'

@dataclass
class TeamMember:
    name: str
    email: str
    skills: List[str]
    current_workload: float
    availability: str
    max_hours: float = 40.0

@dataclass
class Assignment:
    assignee: str
    confidence: float
    rationale: str

@dataclass
class SchedulerResponse:
    assignment: Assignment
    alternatives: List[Assignment]

class TaskScheduler:
    """
    OR-Tools based task scheduler that optimizes assignments
    """

    def __init__(self):
        self.priority_weights = {
            'low': 1,
            'medium': 2,
            'high': 3,
            'urgent': 4
        }

    def calculate_skill_match_score(self, task: Task, member: TeamMember) -> float:
        """
        Calculate how well a team member's skills match the task requirements
        Returns score between 0.0 and 1.0
        """
        if not task.skills_required:
            return 0.5  # Neutral score for tasks with no specific skill requirements

        required_skills = set(skill.lower() for skill in task.skills_required)
        member_skills = set(skill.lower() for skill in member.skills)

        # Calculate intersection
        matched_skills = required_skills.intersection(member_skills)

        if not matched_skills:
            return 0.1  # Low score but not zero (might have transferable skills)

        # Score based on percentage of required skills matched
        match_ratio = len(matched_skills) / len(required_skills)

        # Bonus for having additional relevant skills
        extra_skills = member_skills - required_skills
        bonus = min(0.2, len(extra_skills) * 0.05)

        return min(1.0, match_ratio + bonus)

    def calculate_workload_score(self, task: Task, member: TeamMember) -> float:
        """
        Calculate workload impact score (higher is better)
        """
        if member.availability != 'available':
            return 0.0

        available_hours = member.max_hours - member.current_workload

        if available_hours <= 0:
            return 0.0

        if task.estimated_hours > available_hours:
            return 0.2  # Can partially handle but will be overloaded

        # Score based on how much capacity they have left
        utilization = member.current_workload / member.max_hours
        return 1.0 - utilization

    def optimize_assignment(self, task: Task, team: List[TeamMember]) -> SchedulerResponse:
        """
        Use OR-Tools to find optimal assignment
        """
        model = cp_model.CpModel()

        # Decision variables: assign[i] = 1 if person i is assigned to task
        assign = {}
        for i, member in enumerate(team):
            assign[i] = model.NewBoolVar(f'assign_{i}')

        # Constraint: exactly one person must be assigned
        model.Add(sum(assign[i] for i in range(len(team))) == 1)

        # Calculate scores for each team member
        scores = []
        for i, member in enumerate(team):
            skill_score = self.calculate_skill_match_score(task, member)
            workload_score = self.calculate_workload_score(task, member)

            # Availability constraint
            if member.availability != 'available':
                workload_score = 0.0

            # Combined score (weighted)
            combined_score = (
                skill_score * 0.6 +  # Skill match is most important
                workload_score * 0.4  # Workload balance is also important
            )

            # Apply priority multiplier
            priority_multiplier = self.priority_weights.get(task.priority, 2)
            final_score = combined_score * priority_multiplier

            scores.append({
                'index': i,
                'member': member,
                'skill_score': skill_score,
                'workload_score': workload_score,
                'combined_score': combined_score,
                'final_score': final_score
            })

        # Objective: maximize the score of the assigned person
        objective_terms = []
        for i, score_data in enumerate(scores):
            # Convert to integer for OR-Tools (multiply by 1000 for precision)
            score_int = int(score_data['final_score'] * 1000)
            objective_terms.append(assign[i] * score_int)

        model.Maximize(sum(objective_terms))

        # Solve
        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            # Find the assigned person
            assigned_index = None
            for i in range(len(team)):
                if solver.Value(assign[i]) == 1:
                    assigned_index = i
                    break

            if assigned_index is not None:
                assigned_member = team[assigned_index]
                assigned_score = scores[assigned_index]

                # Generate rationale
                rationale = self._generate_rationale(task, assigned_member, assigned_score)

                # Create primary assignment
                assignment = Assignment(
                    assignee=assigned_member.name,
                    confidence=assigned_score['combined_score'],
                    rationale=rationale
                )

                # Generate alternatives (top 2 other candidates)
                alternatives = []
                other_scores = [s for s in scores if s['index'] != assigned_index]
                other_scores.sort(key=lambda x: x['combined_score'], reverse=True)

                for alt_score in other_scores[:2]:
                    if alt_score['combined_score'] > 0.1:  # Only include viable alternatives
                        alt_rationale = self._generate_rationale(task, alt_score['member'], alt_score)
                        alternatives.append(Assignment(
                            assignee=alt_score['member'].name,
                            confidence=alt_score['combined_score'],
                            rationale=alt_rationale
                        ))

                return SchedulerResponse(
                    assignment=assignment,
                    alternatives=alternatives
                )

        # Fallback if no solution found
        logger.warning("No optimal solution found, using fallback")
        best_member = max(team, key=lambda m: self.calculate_skill_match_score(task, m))

        return SchedulerResponse(
            assignment=Assignment(
                assignee=best_member.name,
                confidence=0.5,
                rationale="Fallback assignment - best available skill match"
            ),
            alternatives=[]
        )

    def _generate_rationale(self, task: Task, member: TeamMember, score_data: Dict) -> str:
        """Generate human-readable rationale for assignment"""
        reasons = []

        if score_data['skill_score'] > 0.8:
            reasons.append("excellent skill match")
        elif score_data['skill_score'] > 0.6:
            reasons.append("good skill match")
        elif score_data['skill_score'] > 0.3:
            reasons.append("some relevant skills")

        if score_data['workload_score'] > 0.7:
            reasons.append("low current workload")
        elif score_data['workload_score'] > 0.3:
            reasons.append("manageable workload")

        if member.availability == 'available':
            reasons.append("currently available")

        return f"Best choice: {', '.join(reasons)}" if reasons else "Available team member"


class MCPServer:
    """MCP Server for task scheduling"""

    def __init__(self):
        self.scheduler = TaskScheduler()

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP request"""
        try:
            method = request.get('method')
            params = request.get('params', {})

            if method == 'tools/list':
                return self._list_tools()
            elif method == 'tools/call':
                return self._call_tool(params)
            else:
                return self._error_response(f"Unknown method: {method}")

        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return self._error_response(str(e))

    def _list_tools(self) -> Dict[str, Any]:
        """List available tools"""
        return {
            'tools': [
                {
                    'name': 'schedule_task',
                    'description': 'Optimize task assignment using OR-Tools',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'task': {
                                'type': 'object',
                                'properties': {
                                    'id': {'type': 'string'},
                                    'description': {'type': 'string'},
                                    'skills_required': {'type': 'array', 'items': {'type': 'string'}},
                                    'estimated_hours': {'type': 'number'},
                                    'priority': {'type': 'string', 'enum': ['low', 'medium', 'high', 'urgent']}
                                }
                            },
                            'team': {
                                'type': 'array',
                                'items': {
                                    'type': 'object',
                                    'properties': {
                                        'name': {'type': 'string'},
                                        'email': {'type': 'string'},
                                        'skills': {'type': 'array', 'items': {'type': 'string'}},
                                        'current_workload': {'type': 'number'},
                                        'availability': {'type': 'string'}
                                    }
                                }
                            }
                        }
                    }
                }
            ]
        }

    def _call_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific tool"""
        tool_name = params.get('name')
        arguments = params.get('arguments', {})

        if tool_name == 'schedule_task':
            return self._schedule_task(arguments)
        else:
            return self._error_response(f"Unknown tool: {tool_name}")

    def _schedule_task(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule a task using OR-Tools optimization"""
        try:
            # Parse task
            task_data = args.get('task', {})
            task = Task(
                id=task_data.get('id', ''),
                description=task_data.get('description', ''),
                skills_required=task_data.get('skills_required', []),
                estimated_hours=task_data.get('estimated_hours', 8.0),
                priority=task_data.get('priority', 'medium')
            )

            # Parse team
            team_data = args.get('team', [])
            team = []
            for member_data in team_data:
                member = TeamMember(
                    name=member_data.get('name', ''),
                    email=member_data.get('email', ''),
                    skills=member_data.get('skills', []),
                    current_workload=member_data.get('current_workload', 0),
                    availability=member_data.get('availability', 'available')
                )
                team.append(member)

            # Run optimization
            result = self.scheduler.optimize_assignment(task, team)

            return {
                'content': [
                    {
                        'type': 'text',
                        'text': json.dumps(asdict(result), indent=2)
                    }
                ]
            }

        except Exception as e:
            logger.error(f"Error in schedule_task: {e}")
            return self._error_response(str(e))

    def _error_response(self, message: str) -> Dict[str, Any]:
        """Create error response"""
        return {
            'content': [
                {
                    'type': 'text',
                    'text': json.dumps({'error': message})
                }
            ],
            'isError': True
        }


def main():
    """Main MCP server loop"""
    server = MCPServer()

    try:
        while True:
            line = sys.stdin.readline()
            if not line:
                break

            try:
                request = json.loads(line.strip())
                response = server.handle_request(request)
                print(json.dumps(response))
                sys.stdout.flush()
            except json.JSONDecodeError:
                error_response = server._error_response("Invalid JSON request")
                print(json.dumps(error_response))
                sys.stdout.flush()

    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")


if __name__ == '__main__':
    main()