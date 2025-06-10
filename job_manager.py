import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import threading
import uuid
import time
import logging
from flask import session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JobManager:
    """Manages import jobs and their statuses with persistent storage"""
    
    def __init__(self, storage_file: str = "job_status.json"):
        self.storage_file = storage_file
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()
        self._load_jobs()
    
    def _load_jobs(self):
        """Load jobs from storage file"""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r') as f:
                    self.jobs = json.load(f)
            except json.JSONDecodeError:
                print("Error loading jobs file, starting fresh")
                self.jobs = {}
    
    def _save_jobs(self):
        """Save jobs to storage file"""
        with open(self.storage_file, 'w') as f:
            json.dump(self.jobs, f, indent=2)
    
    def _get_user_id(self) -> str:
        """Get the current user's ID from session"""
        return session.get('spotify_user_id', 'anonymous')
    
    def create_job(self, job_type: str, params: Dict[str, Any]) -> str:
        """Create a new job with user-specific tracking"""
        user_id = self._get_user_id()
        job_id = f"{user_id}_{int(time.time())}"
        
        self.jobs[job_id] = {
            'id': job_id,
            'user_id': user_id,
            'type': job_type,
            'params': params,
            'status': 'pending',
            'progress': 0,
            'message': 'Job created',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'error': None,
            'result': None
        }
        
        logger.info(f"Created job {job_id} for user {user_id}: {job_type}")
        self._save_jobs()
        return job_id
    
    def update_job(self, job_id: str, status: str, progress: int = None, 
                  message: str = None, error: str = None, result: Any = None) -> None:
        """Update job status with logging"""
        with self.lock:
            if job_id not in self.jobs:
                logger.error(f"Job {job_id} not found")
                return
            
            job = self.jobs[job_id]
            job['status'] = status
            job['updated_at'] = datetime.now().isoformat()
            
            if progress is not None:
                job['progress'] = progress
            if message is not None:
                job['message'] = message
            if error is not None:
                job['error'] = error
                logger.error(f"Job {job_id} error: {error}")
            if result is not None:
                job['result'] = result
                # Add detailed statistics if available
                if isinstance(result, dict):
                    if 'total_tracks' in result:
                        job['stats'] = {
                            'total_tracks': result['total_tracks'],
                            'matched_tracks': result['matched_tracks'],
                            'failed_tracks': result['failed_tracks']
                        }
                        if result.get('failed_tracks', 0) > 0:
                            logger.warning(f"Job {job_id}: {result['failed_tracks']} tracks failed to match")
            
            logger.info(f"Updated job {job_id}: {status} - {message}")
            self._save_jobs()
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job details with user verification"""
        with self.lock:
            if job_id not in self.jobs:
                return None
            
            job = self.jobs[job_id]
            user_id = self._get_user_id()
            
            # Only return job if it belongs to the current user
            if job['user_id'] != user_id:
                logger.warning(f"User {user_id} attempted to access job {job_id} belonging to {job['user_id']}")
                return None
            
            return job
    
    def get_user_jobs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent jobs for a user"""
        user_id = self._get_user_id()
        user_jobs = [
            job for job in self.jobs.values()
            if job['user_id'] == user_id
        ]
        # Sort by creation date, newest first
        user_jobs.sort(key=lambda x: x['created_at'], reverse=True)
        return user_jobs[:limit]
    
    def cleanup_old_jobs(self, max_age_hours: int = 24) -> None:
        """Clean up old completed jobs"""
        current_time = datetime.now()
        jobs_to_remove = []
        
        with self.lock:
            for job_id, job in self.jobs.items():
                if job['status'] in ['completed', 'failed']:
                    job_time = datetime.fromisoformat(job['updated_at'])
                    age_hours = (current_time - job_time).total_seconds() / 3600
                    
                    if age_hours > max_age_hours:
                        jobs_to_remove.append(job_id)
            
            for job_id in jobs_to_remove:
                del self.jobs[job_id]
                logger.info(f"Cleaned up old job {job_id}")
            self._save_jobs()

# Global job manager instance
job_manager = JobManager() 