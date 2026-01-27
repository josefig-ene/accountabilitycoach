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
        'project': ['Board', 'Project', 'board', 'project', 'Group', 'group'],
        'name': ['Name', 'Item', 'Task', 'name', 'item', 'task', 'Title', 'title', 'Item Name', 'item name'],
        'status': ['Status', 'status', 'Stage', 'stage', 'State', 'state'],
        'owner': ['Owner', 'Person', 'owner', 'person', 'assigned_to', 'Assigned To', 'People', 'people'],
        'description': ['Description', 'description', 'Notes', 'notes', 'Summary', 'summary', 'Text', 'text'],
        'priority': ['Priority', 'priority'],
        'due_date': ['Due Date', 'due_date', 'Deadline', 'deadline', 'Date', 'date', 'Timeline', 'timeline'],
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

        # Fallback: if no name column found, use the first column
        if 'name' not in detected and len(df.columns) > 0:
            first_col = df.columns[0]
            detected['name'] = first_col
            self.warnings.append(f"No standard name column found. Using '{first_col}' as name column.")

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
        """Extract ideas (projects) from DataFrame - handles nested subitems"""
        ideas = []
        current_idea = None
        current_subitems = []
        in_subitems_section = False
        subitem_columns = {}

        name_col = columns.get('name', df.columns[0])

        for idx, row in df.iterrows():
            # Check if this is a "Subitems" header row
            first_val = str(row[name_col]).strip().lower() if pd.notna(row[name_col]) else ''

            if first_val == 'subitems':
                in_subitems_section = True
                # Next row after "Subitems" has the subitem column headers
                # We'll detect them dynamically as we parse
                continue

            # If we see a new main item (has data in project column or non-empty name)
            if not in_subitems_section:
                # Save previous idea if exists
                if current_idea is not None:
                    current_idea['tasks'] = current_subitems
                    ideas.append(current_idea)
                    current_subitems = []

                # Start new idea
                name = self._get_value(row, columns, 'name', '')
                if pd.isna(name) or str(name).strip() == '':
                    continue

                current_idea = {
                    'name': str(name),
                    'description': self._get_value(row, columns, 'description', 'Imported from Monday.com'),
                    'stage': self.normalize_status(self._get_value(row, columns, 'status', 'seed')),
                    'owner': self._get_value(row, columns, 'owner', 'Unassigned'),
                    'next_steps': '',
                    'risk_flags': '',
                }

            else:
                # We're in subitems section - parse as milestone
                # Look for "Name" column in the row (subitems have their own Name column)
                subitem_name = None
                subitem_status = None

                # Try to find the subitem data
                for col in df.columns:
                    val = row[col]
                    if pd.notna(val) and str(val).strip():
                        col_lower = str(col).lower().strip()
                        # First non-empty column is usually the subitem name
                        if subitem_name is None and 'name' in col_lower:
                            subitem_name = str(val).strip()
                        elif 'status' in col_lower or 'state' in col_lower:
                            subitem_status = str(val).strip()

                # If we found a subitem name, add it
                if subitem_name and subitem_name.lower() not in ['name', 'owner', 'status', 'date', 'text']:
                    current_subitems.append({
                        'name': subitem_name,
                        'status': self._map_subitem_status(subitem_status),
                        'weight': 10
                    })
                else:
                    # No more subitems, back to main items
                    in_subitems_section = False
                    # This row might be a new main item, process it
                    name = row[name_col]
                    if pd.notna(name) and str(name).strip():
                        # Save previous idea
                        if current_idea is not None:
                            current_idea['tasks'] = current_subitems
                            ideas.append(current_idea)
                            current_subitems = []

                        # Start new idea
                        current_idea = {
                            'name': str(name),
                            'description': self._get_value(row, columns, 'description', 'Imported from Monday.com'),
                            'stage': self.normalize_status(self._get_value(row, columns, 'status', 'seed')),
                            'owner': self._get_value(row, columns, 'owner', 'Unassigned'),
                            'next_steps': '',
                            'risk_flags': '',
                        }

        # Don't forget the last idea
        if current_idea is not None:
            current_idea['tasks'] = current_subitems
            ideas.append(current_idea)

        return ideas

    def _map_subitem_status(self, status):
        """Map subitem status to milestone status"""
        if not status:
            return 'pending'

        status_lower = str(status).lower().strip()

        if 'done' in status_lower or 'complete' in status_lower:
            return 'completed'
        elif 'working' in status_lower or 'progress' in status_lower:
            return 'in_progress'
        elif 'stuck' in status_lower or 'blocked' in status_lower:
            return 'in_progress'  # Mark as in progress but could add flag
        else:
            return 'pending'

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
            self.errors.append(f"Could not find name/item column in the file. Available columns: {', '.join(df.columns.tolist())}")
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
