import asyncio
from typing import Dict, List, Optional, Any
from ai_employee import AIEmployee
from database import DatabaseManager
from config import Config

class EmployeeManager:
    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = DatabaseManager()
        if db is not None:
            self.db = db
        self.active_employees: Dict[str, AIEmployee] = {}
        # Note: load_existing_employees will be called from setup_hook

    async def load_existing_employees(self):
        """Load existing employees from database"""
        employees = await self.db.get_all_ai_employees()
        self.active_employees.clear()
        for emp_data in employees:
            employee = AIEmployee(
                emp_data['name'],
                emp_data['employee_type'],
                emp_data['parameters'],
                employee_id=emp_data.get('id'),
                db=self.db,
            )
            self.active_employees[emp_data['name']] = employee
    
    async def create_employee(self, name: str, employee_type: str, 
                             parameters: Optional[Dict[str, Any]] = None) -> bool:
        """Create a new AI employee"""
        try:
            # Check if employee already exists
            if name in self.active_employees:
                return False
            
            # Use default parameters if none provided
            if parameters is None:
                parameters = Config.DEFAULT_AI_PARAMS.copy()
            
            # Create employee in database
            success = await self.db.create_ai_employee(name, employee_type, parameters)
            if not success:
                return False
            
            # Create employee instance
            created_row = await self.db.get_ai_employee(name)
            employee = AIEmployee(
                name,
                employee_type,
                parameters,
                employee_id=(created_row or {}).get('id'),
                db=self.db,
            )
            self.active_employees[name] = employee
            
            return True
        except Exception as e:
            print(f"Error creating employee: {e}")
            return False
    
    async def get_employee(self, name: str) -> Optional[AIEmployee]:
        """Get an AI employee by name"""
        return self.active_employees.get(name)
    
    async def get_all_employees(self) -> List[Dict[str, Any]]:
        """Get status of all active employees"""
        employees = []
        for name, employee in self.active_employees.items():
            employees.append(employee.get_status())
        return employees
    
    async def update_employee_parameters(self, name: str, 
                                       new_parameters: Dict[str, Any]) -> bool:
        """Update employee parameters"""
        try:
            employee = self.active_employees.get(name)
            if not employee:
                return False
            
            success = await employee.update_parameters(new_parameters)
            return success
        except Exception as e:
            print(f"Error updating employee parameters: {e}")
            return False
    
    async def deactivate_employee(self, name: str) -> bool:
        """Deactivate an AI employee"""
        try:
            # Remove from active employees
            if name in self.active_employees:
                del self.active_employees[name]
            
            # Update database
            success = await self.db.deactivate_ai_employee(name)
            return success
        except Exception as e:
            print(f"Error deactivating employee: {e}")
            return False
    
    async def send_message_as_employee(self, employee_name: str, message: str, 
                                     context: str = "") -> Optional[str]:
        """Send a message as a specific AI employee"""
        try:
            employee = self.active_employees.get(employee_name)
            if not employee:
                return None
            
            response = await employee.generate_response(message, context)
            return response
        except Exception as e:
            print(f"Error sending message as employee: {e}")
            return None
    
    async def get_employee_types(self) -> Dict[str, str]:
        """Get available employee types"""
        return Config.EMPLOYEE_TYPES
    
    async def get_employee_stats(self) -> Dict[str, Any]:
        """Get overall statistics about employees"""
        total_employees = len(self.active_employees)
        total_conversations = sum(
            len(emp.conversation_history) for emp in self.active_employees.values()
        )
        
        type_counts = {}
        for emp in self.active_employees.values():
            emp_type = emp.employee_type
            type_counts[emp_type] = type_counts.get(emp_type, 0) + 1
        
        return {
            "total_employees": total_employees,
            "total_conversations": total_conversations,
            "employees_by_type": type_counts,
            "active_employees": list(self.active_employees.keys())
        }
    
    async def reset_employee_conversation(self, name: str) -> bool:
        """Reset conversation history for an employee"""
        try:
            employee = self.active_employees.get(name)
            if not employee:
                return False
            
            await employee.reset_conversation()
            return True
        except Exception as e:
            print(f"Error resetting employee conversation: {e}")
            return False
    
    async def get_employee_conversation_summary(self, name: str) -> Optional[str]:
        """Get conversation summary for an employee"""
        try:
            employee = self.active_employees.get(name)
            if not employee:
                return None
            
            return await employee.get_conversation_summary()
        except Exception as e:
            print(f"Error getting conversation summary: {e}")
            return None
    
    async def bulk_create_employees(self, employee_configs: List[Dict[str, Any]]) -> Dict[str, bool]:
        """Create multiple employees at once"""
        results = {}
        for config in employee_configs:
            name = config.get('name')
            emp_type = config.get('type')
            params = config.get('parameters')
            
            if name and emp_type:
                success = await self.create_employee(name, emp_type, params)
                results[name] = success
        
        return results
    
    async def export_employee_configs(self) -> List[Dict[str, Any]]:
        """Export all employee configurations"""
        configs = []
        for name, employee in self.active_employees.items():
            configs.append({
                'name': name,
                'type': employee.employee_type,
                'parameters': employee.parameters
            })
        return configs
