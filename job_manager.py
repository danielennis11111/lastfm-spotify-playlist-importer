import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import threading
import uuid

class JobManager:
    """Manages import jobs and their statuses with persistent storage"""
    
    def __init__(self, storage_file: str = "job_status.json"):
        self.storage_file = storage_file
        self.jobs: Dict[str, Dict] = {}
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
    
    def create_job(self, user_id: str, job_type: str, params: Dict) -> str:
        """Create a new job and return its ID"""
        with self.lock:
            job_id = str(uuid.uuid4())
            self.jobs[job_id] = {
                'user_id': user_id,
                'type': job_type,
                'params': params,
                'status': 'pending',
                'progress': 0,
                'message': 'Initializing...',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'result': None,
                'error': None
            }
            self._save_jobs()
            return job_id
    
    def update_job(self, job_id: str, **kwargs) -> bool:
        """Update job status and other fields"""
        with self.lock:
            if job_id not in self.jobs:
                return False
            
            job = self.jobs[job_id]
            job.update(kwargs)
            job['updated_at'] = datetime.now().isoformat()
            self._save_jobs()
            return True
    
    def get_job(self, job_id: str) -> Optional[Dict]:
        """Get job details"""
        return self.jobs.get(job_id)
    
    def get_user_jobs(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get recent jobs for a user"""
        user_jobs = [
            job for job in self.jobs.values()
            if job['user_id'] == user_id
        ]
        # Sort by creation date, newest first
        user_jobs.sort(key=lambda x: x['created_at'], reverse=True)
        return user_jobs[:limit]
    
    def cleanup_old_jobs(self, days: int = 30):
        """Remove jobs older than specified days"""
        cutoff = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff.isoformat()
        
        with self.lock:
            self.jobs = {
                job_id: job for job_id, job in self.jobs.items()
                if job['created_at'] > cutoff_str
            }
            self._save_jobs() 