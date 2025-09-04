import requests
from typing import Dict, Any, Optional
from functools import lru_cache
from app.ui.logger import logger
from app.agents.followup_questions import handle_errors

class APIService:
    """Service to manage external API connections and requests"""
    
    def __init__(self):
        self.api_configs: Dict[str, Dict[str, str]] = {}
        self.session = requests.Session()
    
    def add_api_config(self, api_name: str, config: Dict[str, str]):
        """
        Add a new API configuration
        config should include:
        - base_url: Base URL of the API
        - api_key: API key if required
        - headers: Additional headers if needed
        """
        self.api_configs[api_name] = config
        if config.get('api_key'):
            self.api_configs[api_name]['headers'] = {
                'Authorization': f"Bearer {config['api_key']}",
                **(config.get('headers', {}))
            }
    
    # @handle_errors("API request failed")
    # async def make_request(
    #     self,
    #     api_name: str,
    #     endpoint: str,
    #     method: str = 'GET',
    #     data: Optional[Dict] = None,
    #     params: Optional[Dict] = None
    # ) -> Dict[str, Any]:
    #     """
    #     Make an API request to the specified endpoint
    #     """
    #     if api_name not in self.api_configs:
    #         raise ValueError(f"API configuration for {api_name} not found")
        
    #     config = self.api_configs[api_name]
    #     url = f"{config['base_url'].rstrip('/')}/{endpoint.lstrip('/')}"
        
    #     try:
    #         response = self.session.request(
    #             method=method,
    #             url=url,
    #             headers=config.get('headers', {}),
    #             json=data if method in ['POST', 'PUT', 'PATCH'] else None,
    #             params=params if method == 'GET' else None
    #         )
    #         response.raise_for_status()
    #         return response.json()
    #     except requests.exceptions.RequestException as e:
    #         logger.error(f"API request failed: {str(e)}")
    #         raise
    
    @lru_cache(maxsize=100)
    async def cached_request(self, api_name: str, endpoint: str, cache_key: str) -> Dict[str, Any]:
        """
        Make a cached API request - useful for frequently accessed endpoints
        """
        return await self.make_request(api_name, endpoint)

# Initialize the API service
api_service = APIService()
