"""
Monday.com Board Import Utility
Handles importing projects and tasks from Monday.com CSV/Excel exports
"""

import pandas as pd
import io
from datetime import datetime
from typing import Dict, List, Tuple


class MondayImporter:
    """Handle Monday.com board imports"""

    # Common Monday.com column mappings
    COLUMN_MAPPINGS = {
        'project': ['Board', 'Project', 'board', 'project'],
        'name': ['Name', 'Item', 'Task', 'name', 'item', 'task'],
        'status': ['Status', 'status', 'Stage', 'stage'],
        'owner': ['Owner', 'Person', 'owner', 'person', 'assigned_to', 'Assigned To'],
        'description': ['Description', 'description', 'Notes', 'notes', 'Summary', 'summary'],
        'priority': ['Priority', 'priority'],
        'due_date': ['Due Date', 'due_date', 'Deadline', 'deadline', 'Date', 'date'],
    }

    # Status mapping from Monday.com to dashboard stages
    STATUS_MAPPING = {
        'backlog': 'seed',
        'research': 'validation',
        'in progress': 'mvp',
        'testing': 'pilot',
        'production': 'scale',
        'done': 'exit',
        'completed': 'exit',
        'todo': 'seed',
        'doing': 'mvp',
        'stuck': 'validation',
    }

    def __init__(self):
        self.errors = []
        self.warnings = []

    def parse_file(self, file_content: bytes, file_type: str = 'csv') -> pd.DataFrame:
        """Parse uploaded file into DataFrame"""
        try:
            if file_type == 'csv':
                df = pd.read_csv(io.BytesIO(file_content))
            elif file_type in ['xlsx', 'xls']:
                df = pd.read_excel(io.BytesIO(file_content))
            else:
                raise ValueError(f"Unsupported file type: {file_type}")

            return df
        except Exception as e:
            self.errors.append(f"Error parsing file: {str(e)}")
            return None

    def detect_columns(self, df: pd.DataFrame) -> Dict[str, str]:
        """Detect which columns map to our schema"""
        detected = {}

        for field, possible_names in self.COLUMN_MAPPINGS.items():
            for col in df.columns:
                if col.strip() in possible_names:
                    detected[field] = col
                    break

        return detected

    def normalize_status(self, status: str) -> str:
        """Map Monday.com status to dashboard stage"""
        if pd.isna(status):
            return 'seed'

        status_lower = str(status).lower().strip()

        # Direct mapping
        if status_lower in self.STATUS_MAPPING:
            return self.STATUS_MAPPING[status_lower]

        # Partial matching
        for key, value in self.STATUS_MAPPING.items():
            if key in status_lower:
                return value

        # Default to seed if unknown
        self.warnings.append(f"Unknown status '{status}' mapped to 'seed'")
        return 'seed'

    def extract_ideas(self, df: pd.DataFrame, columns: Dict[str, str]) -> List[Dict]:
        """Extract ideas (projects) from DataFrame"""
        ideas = []

        # Group by project if available
        if 'project' in columns:
            project_col = columns['project']
            projects = df[project_col].unique()

            for project_name in projects:
                if pd.isna(project_name):
                    continue

                project_df = df[df[project_col] == project_name]

                # Get project details from first row
                first_row = project_df.iloc[0]

                idea = {
                    'name': str(project_name),
                    'description': self._get_value(first_row, columns, 'description', f"Imported from Monday.com on {datetime.now().strftime('%Y-%m-%d')}"),
                    'stage': self.normalize_status(self._get_value(first_row, columns, 'status', 'seed')),
                    'owner': self._get_value(first_row, columns, 'owner', 'Unassigned'),
                    'next_steps': f"Review {len(project_df)} imported tasks",
                    'risk_flags': '',
                    'tasks': project_df.to_dict('records')  # Keep tasks for milestone extraction
                }

                ideas.append(idea)

        else:
            # No project grouping - treat each row as an idea
            for idx, row in df.iterrows():
                name = self._get_value(row, columns, 'name', f'Imported Item {idx+1}')

                if pd.isna(name) or str(name).strip() == '':
                    continue

                idea = {
                    'name': str(name),
                    'description': self._get_value(row, columns, 'description', 'Imported from Monday.com'),
                    'stage': self.normalize_status(self._get_value(row, columns, 'status', 'seed')),
                    'owner': self._get_value(row, columns, 'owner', 'Unassigned'),
                    'next_steps': '',
                    'risk_flags': '',
                    'tasks': []
                }

                ideas.append(idea)

        return ideas

    def extract_milestones(self, tasks: List[Dict], columns: Dict[str, str]) -> List[Dict]:
        """Extract milestones from project tasks"""
        milestones = []

        for idx, task in enumerate(tasks):
            name = self._get_value(task, columns, 'name', f'Task {idx+1}')

            if pd.isna(name) or str(name).strip() == '':
                continue

            status = self._get_value(task, columns, 'status', 'pending')
            status_lower = str(status).lower().strip()

            # Map Monday status to milestone status
            milestone_status = 'completed' if status_lower in ['done', 'completed', 'finished'] else 'in_progress' if status_lower in ['in progress', 'doing', 'working'] else 'pending'

            milestone = {
                'name': str(name),
                'status': milestone_status,
                'weight': 10,  # Default weight
                'due_date': self._get_value(task, columns, 'due_date', None),
            }

            milestones.append(milestone)

        return milestones

    def _get_value(self, row, columns: Dict[str, str], field: str, default=None):
        """Safely get value from row"""
        if field in columns:
            col_name = columns[field]
            if col_name in row:
                value = row[col_name]
                if pd.isna(value):
                    return default
                return value
        return default

    def import_from_dataframe(self, df: pd.DataFrame) -> Tuple[List[Dict], List[str], List[str]]:
        """
        Import data from DataFrame

        Returns:
            Tuple of (ideas_list, errors_list, warnings_list)
        """
        self.errors = []
        self.warnings = []

        if df is None or df.empty:
            self.errors.append("DataFrame is empty")
            return [], self.errors, self.warnings

        # Detect columns
        columns = self.detect_columns(df)

        if 'name' not in columns:
            self.errors.append("Could not find name/item column in the file")
            return [], self.errors, self.warnings

        # Extract ideas
        ideas = self.extract_ideas(df, columns)

        # Extract milestones for each idea that has tasks
        for idea in ideas:
            if 'tasks' in idea and idea['tasks']:
                idea['milestones'] = self.extract_milestones(idea['tasks'], columns)
                del idea['tasks']  # Remove temporary tasks field
            else:
                idea['milestones'] = []

        return ideas, self.errors, self.warnings

    def generate_preview(self, ideas: List[Dict]) -> str:
        """Generate preview text for import"""
        preview = f"### Import Preview\n\n"
        preview += f"**Total Projects/Ideas:** {len(ideas)}\n\n"

        for idea in ideas[:5]:  # Show first 5
            milestone_count = len(idea.get('milestones', []))
            preview += f"- **{idea['name']}** ({idea['stage']})\n"
            preview += f"  - Owner: {idea['owner']}\n"
            preview += f"  - Milestones: {milestone_count}\n"

        if len(ideas) > 5:
            preview += f"\n*...and {len(ideas) - 5} more*\n"

        return preview


def create_sample_monday_csv() -> str:
    """Create a sample Monday.com CSV format for reference"""
    sample = """Board,Item,Status,Owner,Description,Due Date
Studio Alpha,Blockchain MVP,In Progress,John Doe,Building decentralized platform,2024-03-15
Studio Alpha,User Testing,Testing,Jane Smith,Beta testing with 10 users,2024-03-20
Studio Alpha,Marketing Launch,Todo,John Doe,Prepare marketing materials,2024-04-01
Cohort Beta,Course Curriculum,Done,Sarah Johnson,Complete course outline,2024-02-28
Cohort Beta,Student Recruitment,In Progress,Mike Chen,Reach 50 students,2024-03-10
"""
    return sample
