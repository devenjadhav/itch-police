#!/usr/bin/env python3
"""
Game Validator Script for Itch.io Links
Checks if itch.io games are playable in browser and updates Airtable status
"""

import os
import requests
import logging
from bs4 import BeautifulSoup
from pyairtable import Api
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ItchioChecker:
    """Checks if itch.io games are playable in browser"""
    
    @staticmethod
    def is_playable(url):
        """
        Check if an itch.io game is playable in browser
        Returns True if the game has a .game_frame element (browser playable)
        """
        if not url or not url.strip():
            return False
            
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; GameValidator/1.0)'
            }
            
            response = requests.get(url, timeout=10, headers=headers)
            
            if response.status_code != 200:
                logger.warning(f"HTTP {response.status_code} for {url}")
                return False
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for itch.io's game frame - indicates browser playable game
            game_frames = soup.select('.game_frame')
            is_playable = len(game_frames) > 0
            
            logger.info(f"URL {url} - Playable: {is_playable}")
            return is_playable
            
        except Exception as e:
            logger.error(f"Error checking {url}: {str(e)}")
            return False

class AirtableGameValidator:
    """Handles Airtable operations for game validation"""
    
    def __init__(self):
        self.api_key = os.getenv('AIRTABLE_API_KEY')
        self.base_id = os.getenv('AIRTABLE_BASE_ID')
        
        if not self.api_key or not self.base_id:
            raise ValueError("AIRTABLE_API_KEY and AIRTABLE_BASE_ID must be set in environment")
            
        self.api = Api(self.api_key)
        self.table = self.api.table(self.base_id, 'projects')
    
    def get_projects_to_validate(self):
        """Get all projects that need validation from specific view"""
        try:
            # Get records from specific view
            records = self.table.all(view='viwTShFXBXjhP4w9s')
            projects_to_check = []
            
            for record in records:
                fields = record.get('fields', {})
                gameplay_url = fields.get('gameplay_url')
                ysws_status = fields.get('ysws_status')
                
                # Only check if there's a URL and status is not already processed
                if gameplay_url and ysws_status not in ['Ready', 'Invalid']:
                    projects_to_check.append({
                        'id': record['id'],
                        'url': gameplay_url,
                        'current_status': ysws_status
                    })
            
            logger.info(f"Found {len(projects_to_check)} projects to validate")
            return projects_to_check
            
        except Exception as e:
            logger.error(f"Error fetching projects: {str(e)}")
            return []
    
    def update_status(self, record_id, status='Ready'):
        """Update the ysws_status field for a record"""
        try:
            self.table.update(record_id, {'ysws_status': status})
            logger.info(f"Updated record {record_id} to status: {status}")
            return True
        except Exception as e:
            logger.error(f"Error updating record {record_id}: {str(e)}")
            return False

def main():
    """Main validation process"""
    try:
        validator = AirtableGameValidator()
        checker = ItchioChecker()
        
        projects = validator.get_projects_to_validate()
        
        if not projects:
            logger.info("No projects to validate")
            return
        
        ready_count = 0
        invalid_count = 0
        
        for project in projects:
            logger.info(f"Checking project {project['id']}: {project['url']}")
            
            if checker.is_playable(project['url']):
                if validator.update_status(project['id'], 'Ready'):
                    ready_count += 1
            else:
                logger.info(f"Game not playable in browser: {project['url']}")
                if validator.update_status(project['id'], 'Invalid'):
                    invalid_count += 1
            
            # Rate limiting - be nice to itch.io
            time.sleep(1)
        
        logger.info(f"Validation complete. {ready_count} games set to 'Ready', {invalid_count} games set to 'Invalid'")
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")

if __name__ == "__main__":
    main()
