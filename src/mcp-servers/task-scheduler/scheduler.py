"""
Core task scheduling logic using Google OR-Tools

This module contains the optimization algorithms for task assignment
separate from the MCP server protocol handling.
"""

from typing import List, Dict, Tuple, Optional
from ortools.sat.python import cp_model
import logging

logger = logging.getLogger(__name__)

class TaskSchedulingModel:
    """
    Advanced task scheduling model with multiple constraints and objectives
    """

    def __init__(self):
        self.skill_weight = 0.6
        self.workload_weight = 0.3
        self.availability_weight = 0.1

    def solve_assignment(
        self,
        task_requirements: Dict,
        team_members: List[Dict],
        constraints: Optional[Dict] = None
    ) -> Dict:
        """
        Solve task assignment optimization problem

        Args:
            task_requirements: Task details including skills, hours, priority
            team_members: List of team member details
            constraints: Additional constraints (deadlines, exclusions, etc.)

        Returns:
            Assignment solution with scores and alternatives
        """
        model = cp_model.CpModel()

        # Decision variables
        num_members = len(team_members)
        assignment_vars = [
            model.NewBoolVar(f'assign_member_{i}')
            for i in range(num_members)
        ]

        # Constraint: exactly one assignment
        model.Add(sum(assignment_vars) == 1)

        # Calculate scores for objective function
        member_scores = []
        for i, member in enumerate(team_members):
            score = self._calculate_member_score(task_requirements, member)
            member_scores.append(score)

            # Hard constraints
            if not self._is_member_eligible(task_requirements, member, constraints):
                model.Add(assignment_vars[i] == 0)

        # Objective: maximize assignment score
        objective_terms = []
        for i, score in enumerate(member_scores):
            # Convert float score to integer for OR-Tools
            score_int = int(score * 10000)
            objective_terms.append(assignment_vars[i] * score_int)

        model.Maximize(sum(objective_terms))

        # Solve the model
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 10.0  # 10 second timeout

        status = solver.Solve(model)

        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            return self._extract_solution(
                solver, assignment_vars, team_members, member_scores, task_requirements
            )
        else:
            logger.warning(f"Solver status: {status}")
            return self._fallback_solution(team_members, member_scores, task_requirements)

    def _calculate_member_score(self, task: Dict, member: Dict) -> float:
        """Calculate composite score for a team member"""
        skill_score = self._skill_match_score(task, member)
        workload_score = self._workload_score(task, member)
        availability_score = self._availability_score(member)

        return (
            skill_score * self.skill_weight +
            workload_score * self.workload_weight +
            availability_score * self.availability_weight
        )

    def _skill_match_score(self, task: Dict, member: Dict) -> float:
        """Calculate skill matching score (0.0 to 1.0)"""
        required_skills = set(skill.lower() for skill in task.get('skills_required', []))
        member_skills = set(skill.lower() for skill in member.get('skills', []))

        if not required_skills:
            return 0.7  # Neutral score for tasks with no specific requirements

        if not member_skills:
            return 0.1  # Low score for members with no listed skills

        # Direct skill matches
        matches = required_skills & member_skills
        if not matches:
            return 0.2  # Some potential for learning

        match_ratio = len(matches) / len(required_skills)

        # Bonus for additional relevant skills
        additional_skills = len(member_skills - required_skills)
        versatility_bonus = min(0.2, additional_skills * 0.05)

        # Experience modifier based on total skills
        experience_modifier = min(1.2, 1.0 + len(member_skills) * 0.02)

        return min(1.0, (match_ratio + versatility_bonus) * experience_modifier)

    def _workload_score(self, task: Dict, member: Dict) -> float:
        """Calculate workload impact score (0.0 to 1.0, higher is better)"""
        current_workload = member.get('current_workload', 0)
        max_capacity = member.get('max_hours', 40)
        task_hours = task.get('estimated_hours', 8)

        available_capacity = max_capacity - current_workload

        if available_capacity <= 0:
            return 0.0  # No capacity available

        if task_hours > available_capacity:
            # Can partially handle but will be overloaded
            return 0.3 * (available_capacity / task_hours)

        # Score based on remaining capacity after assignment
        utilization_after = (current_workload + task_hours) / max_capacity

        if utilization_after <= 0.7:
            return 1.0  # Ideal utilization
        elif utilization_after <= 0.85:
            return 0.8  # Good utilization
        elif utilization_after <= 1.0:
            return 0.5  # High but manageable
        else:
            return 0.2  # Overloaded

    def _availability_score(self, member: Dict) -> float:
        """Calculate availability score"""
        availability = member.get('availability', 'available')

        availability_scores = {
            'available': 1.0,
            'busy': 0.3,
            'out_of_office': 0.0,
            'vacation': 0.0,
        }

        return availability_scores.get(availability, 0.5)

    def _is_member_eligible(self, task: Dict, member: Dict, constraints: Optional[Dict]) -> bool:
        """Check if member meets hard constraints"""
        # Basic availability check
        if member.get('availability') in ['out_of_office', 'vacation']:
            return False

        # Custom constraints
        if constraints:
            # Exclusion list
            excluded = constraints.get('excluded_members', [])
            if member.get('name') in excluded or member.get('email') in excluded:
                return False

            # Required skills (must have at least one)
            required_skills = constraints.get('required_skills', [])
            if required_skills:
                member_skills = set(skill.lower() for skill in member.get('skills', []))
                required_skills_lower = set(skill.lower() for skill in required_skills)
                if not (member_skills & required_skills_lower):
                    return False

        return True

    def _extract_solution(
        self,
        solver: cp_model.CpSolver,
        assignment_vars: List,
        team_members: List[Dict],
        member_scores: List[float],
        task: Dict
    ) -> Dict:
        """Extract and format the solution"""
        # Find assigned member
        assigned_index = None
        for i, var in enumerate(assignment_vars):
            if solver.Value(var) == 1:
                assigned_index = i
                break

        if assigned_index is None:
            return self._fallback_solution(team_members, member_scores, task)

        assigned_member = team_members[assigned_index]
        assigned_score = member_scores[assigned_index]

        # Generate alternatives
        alternatives = []
        for i, (member, score) in enumerate(zip(team_members, member_scores)):
            if i != assigned_index and score > 0.3:  # Only viable alternatives
                alternatives.append({
                    'member': member,
                    'score': score,
                    'rationale': self._generate_rationale(task, member, score)
                })

        # Sort alternatives by score
        alternatives.sort(key=lambda x: x['score'], reverse=True)

        return {
            'assignment': {
                'assignee': assigned_member.get('name'),
                'confidence': assigned_score,
                'rationale': self._generate_rationale(task, assigned_member, assigned_score)
            },
            'alternatives': [
                {
                    'assignee': alt['member'].get('name'),
                    'confidence': alt['score'],
                    'rationale': alt['rationale']
                }
                for alt in alternatives[:3]  # Top 3 alternatives
            ],
            'optimization_details': {
                'solver_status': 'OPTIMAL',
                'solve_time': solver.WallTime(),
                'total_candidates': len(team_members),
                'viable_candidates': sum(1 for s in member_scores if s > 0.3)
            }
        }

    def _fallback_solution(self, team_members: List[Dict], member_scores: List[float], task: Dict) -> Dict:
        """Provide fallback solution when optimization fails"""
        if not team_members:
            return {'error': 'No team members available'}

        # Simple fallback: choose member with highest score
        best_index = max(range(len(member_scores)), key=lambda i: member_scores[i])
        best_member = team_members[best_index]
        best_score = member_scores[best_index]

        return {
            'assignment': {
                'assignee': best_member.get('name'),
                'confidence': max(0.3, best_score),  # Minimum confidence for fallback
                'rationale': f"Fallback assignment: {self._generate_rationale(task, best_member, best_score)}"
            },
            'alternatives': [],
            'optimization_details': {
                'solver_status': 'FALLBACK',
                'message': 'Used fallback algorithm due to solver issues'
            }
        }

    def _generate_rationale(self, task: Dict, member: Dict, score: float) -> str:
        """Generate human-readable rationale"""
        skill_score = self._skill_match_score(task, member)
        workload_score = self._workload_score(task, member)

        reasons = []

        # Skill assessment
        if skill_score > 0.8:
            reasons.append("excellent skill match")
        elif skill_score > 0.6:
            reasons.append("good skill match")
        elif skill_score > 0.4:
            reasons.append("adequate skills")
        else:
            reasons.append("can learn required skills")

        # Workload assessment
        if workload_score > 0.8:
            reasons.append("low current workload")
        elif workload_score > 0.5:
            reasons.append("manageable workload")
        elif workload_score > 0.3:
            reasons.append("busy but can accommodate")
        else:
            reasons.append("high workload")

        # Availability
        availability = member.get('availability', 'available')
        if availability == 'available':
            reasons.append("currently available")
        elif availability == 'busy':
            reasons.append("somewhat busy")

        return f"{', '.join(reasons[:3])}"  # Limit to top 3 reasons