import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
import httpx
from config import Config

class DatabaseManager:
    def __init__(self):
        if not Config.SUPABASE_URL or not Config.SUPABASE_ANON_KEY:
            raise ValueError("Supabase URL and anon key must be configured")
        
        self.supabase_url = Config.SUPABASE_URL.rstrip('/')
        self.supabase_key = Config.SUPABASE_ANON_KEY
        self.headers = {
            'apikey': self.supabase_key,
            'Authorization': f'Bearer {self.supabase_key}',
            'Content-Type': 'application/json'
        }
        # Note: init_database is not needed for Supabase as tables are created via migrations
    
    def init_database(self):
        """Initialize the database with required tables"""
        # Note: In Supabase, tables are typically created via migrations or the dashboard
        # This method can be used to ensure tables exist or create them if needed
        # For now, we'll assume tables are already created in Supabase
        
        # You can add table creation logic here if needed
        # Example SQL for Supabase:
        """
        CREATE TABLE IF NOT EXISTS ai_employees (
            id BIGSERIAL PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            employee_type TEXT NOT NULL,
            parameters JSONB NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            last_used TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE TABLE IF NOT EXISTS user_permissions (
            user_id BIGINT PRIMARY KEY,
            permission_level INTEGER DEFAULT 1,
            granted_by BIGINT,
            granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE TABLE IF NOT EXISTS conversations (
            id BIGSERIAL PRIMARY KEY,
            employee_id BIGINT,
            user_id BIGINT,
            channel_id BIGINT,
            message TEXT,
            response TEXT,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        pass
    
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict]:
        """Make HTTP request to Supabase"""
        url = f"{self.supabase_url}/rest/v1/{endpoint}"
        
        async with httpx.AsyncClient() as client:
            try:
                if method.upper() == 'GET':
                    response = await client.get(url, headers=self.headers)
                elif method.upper() == 'POST':
                    response = await client.post(url, headers=self.headers, json=data)
                elif method.upper() == 'PUT':
                    response = await client.put(url, headers=self.headers, json=data)
                elif method.upper() == 'PATCH':
                    response = await client.patch(url, headers=self.headers, json=data)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response.raise_for_status()
                return response.json() if response.content else None
                
            except httpx.HTTPStatusError as e:
                print(f"HTTP error {e.response.status_code}: {e.response.text}")
                return None
            except Exception as e:
                print(f"Request error: {e}")
                return None
    
    async def create_ai_employee(self, name: str, employee_type: str, parameters: Dict[str, Any]) -> bool:
        """Create a new AI employee"""
        try:
            data = {
                'name': name,
                'employee_type': employee_type,
                'parameters': parameters,
                'is_active': True,
                'created_at': datetime.utcnow().isoformat(),
                'last_used': datetime.utcnow().isoformat()
            }
            
            result = await self._make_request('POST', 'ai_employees', data)
            return result is not None
            
        except Exception as e:
            print(f"Error creating AI employee: {e}")
            return False
    
    async def get_ai_employee(self, name: str) -> Optional[Dict[str, Any]]:
        """Get AI employee by name"""
        try:
            # Use Supabase's filter syntax
            url = f"{self.supabase_url}/rest/v1/ai_employees?name=eq.{name}&is_active=eq.true"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                result = response.json()
            
            if result and len(result) > 0:
                row = result[0]
                return {
                    'id': row['id'],
                    'name': row['name'],
                    'employee_type': row['employee_type'],
                    'parameters': row['parameters'],
                    'is_active': row['is_active'],
                    'created_at': row['created_at'],
                    'last_used': row['last_used']
                }
            return None
            
        except Exception as e:
            print(f"Error getting AI employee: {e}")
            return None
    
    async def get_all_ai_employees(self) -> List[Dict[str, Any]]:
        """Get all active AI employees"""
        try:
            url = f"{self.supabase_url}/rest/v1/ai_employees?is_active=eq.true"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                result = response.json()
            
            employees = []
            for row in result:
                employees.append({
                    'id': row['id'],
                    'name': row['name'],
                    'employee_type': row['employee_type'],
                    'parameters': row['parameters'],
                    'is_active': row['is_active'],
                    'created_at': row['created_at'],
                    'last_used': row['last_used']
                })
            
            return employees
            
        except Exception as e:
            print(f"Error getting AI employees: {e}")
            return []
    
    async def update_ai_employee(self, name: str, parameters: Dict[str, Any]) -> bool:
        """Update AI employee parameters"""
        try:
            data = {
                'parameters': parameters,
                'last_used': datetime.utcnow().isoformat()
            }
            
            # Use Supabase's filter syntax for update
            url = f"{self.supabase_url}/rest/v1/ai_employees?name=eq.{name}"
            
            async with httpx.AsyncClient() as client:
                response = await client.patch(url, headers=self.headers, json=data)
                response.raise_for_status()
                result = response.json()
            
            return result is not None
            
        except Exception as e:
            print(f"Error updating AI employee: {e}")
            return False
    
    async def deactivate_ai_employee(self, name: str) -> bool:
        """Deactivate an AI employee"""
        try:
            data = {
                'is_active': False
            }
            
            # Use Supabase's filter syntax for update
            url = f"{self.supabase_url}/rest/v1/ai_employees?name=eq.{name}"
            
            async with httpx.AsyncClient() as client:
                response = await client.patch(url, headers=self.headers, json=data)
                response.raise_for_status()
                result = response.json()
            
            return result is not None
            
        except Exception as e:
            print(f"Error deactivating AI employee: {e}")
            return False
    
    async def get_user_permission(self, user_id: int) -> int:
        """Get user permission level"""
        try:
            url = f"{self.supabase_url}/rest/v1/user_permissions?user_id=eq.{user_id}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                result = response.json()
            
            if result and len(result) > 0:
                return result[0]['permission_level']
            return 1  # Default to USER level
            
        except Exception as e:
            print(f"Error getting user permission: {e}")
            return 1
    
    async def set_user_permission(self, user_id: int, permission_level: int, granted_by: int) -> bool:
        """Set user permission level"""
        try:
            data = {
                'user_id': user_id,
                'permission_level': permission_level,
                'granted_by': granted_by,
                'granted_at': datetime.utcnow().isoformat()
            }
            
            # Use upsert endpoint
            url = f"{self.supabase_url}/rest/v1/user_permissions"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=self.headers, json=data)
                response.raise_for_status()
                result = response.json()
            
            return result is not None
            
        except Exception as e:
            print(f"Error setting user permission: {e}")
            return False
    
    async def log_conversation(self, employee_id: int, user_id: int, channel_id: int, 
                              message: str, response: str) -> bool:
        """Log a conversation for analytics"""
        try:
            data = {
                'employee_id': employee_id,
                'user_id': user_id,
                'channel_id': channel_id,
                'message': message,
                'response': response,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            result = await self._make_request('POST', 'conversations', data)
            return result is not None
            
        except Exception as e:
            print(f"Error logging conversation: {e}")
            return False
