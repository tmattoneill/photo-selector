import os
import hashlib
import concurrent.futures
from typing import Dict, Optional, List, Set
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import select, text
from ..models.app_state import AppState
from ..models.image import Image


class DirectoryService:
    """Directory service with SHA-256 caching as per algo-update.yaml spec."""
    
    def __init__(self, db: Session):
        self.db = db
        self.cache: Dict[str, Dict[str, any]] = {}  # sha256 -> {path, size, mtime}
        self.root_directory: Optional[str] = None
        self.supported_extensions = [".jpg", ".jpeg", ".png", ".webp", ".gif"]
        self.max_workers = 4
        self.chunk_size = 1048576  # 1 MB chunks
        self.max_total_files = 200_000
        self.max_file_size_mb = 250
    
    def set_root_directory(self, root: str) -> Dict[str, any]:
        """Validate and set root directory, then scan for images."""
        if not os.path.exists(root):
            raise ValueError(f"Directory does not exist: {root}")
        
        if not os.path.isdir(root):
            raise ValueError(f"Path is not a directory: {root}")
        
        if not os.access(root, os.R_OK):
            raise ValueError(f"Directory not readable: {root}")
        
        self.root_directory = os.path.abspath(root)
        discovered = self.scan_and_sync()
        
        return {"ok": True, "discovered": discovered}
    
    def scan_and_sync(self) -> int:
        """Scan directory recursively and sync with database."""
        if not self.root_directory:
            return 0
        
        # Find all image files
        image_files = self._find_image_files()
        
        if len(image_files) > self.max_total_files:
            raise ValueError(f"Too many files: {len(image_files)} > {self.max_total_files}")
        
        # Hash files in parallel
        new_cache = self._hash_files_parallel(image_files)
        
        # Update cache (invalidate changed files)
        self._update_cache(new_cache)
        
        # Sync new SHA256s to database
        discovered = self._sync_to_database()
        
        return discovered
    
    def _find_image_files(self) -> List[str]:
        """Recursively find all supported image files."""
        image_files = []
        
        for root, dirs, files in os.walk(self.root_directory):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                if file.startswith('.'):  # Skip hidden files
                    continue
                    
                # Check extension
                file_lower = file.lower()
                if not any(file_lower.endswith(ext) for ext in self.supported_extensions):
                    continue
                
                file_path = os.path.join(root, file)
                
                # Check if it's a regular file and not a symlink
                if not os.path.isfile(file_path) or os.path.islink(file_path):
                    continue
                
                # Check file size
                try:
                    size = os.path.getsize(file_path)
                    if size > self.max_file_size_mb * 1024 * 1024:
                        continue
                except OSError:
                    continue
                
                image_files.append(file_path)
        
        return image_files
    
    def _hash_files_parallel(self, files: List[str]) -> Dict[str, Dict[str, any]]:
        """Hash files in parallel, reusing cache where possible."""
        new_cache = {}
        files_to_hash = []
        
        for file_path in files:
            try:
                stat = os.stat(file_path)
                size = stat.st_size
                mtime = stat.st_mtime
                
                # Check if we can reuse cached hash
                cached_entry = None
                for sha256, cache_data in self.cache.items():
                    if (cache_data["path"] == file_path and 
                        cache_data["size"] == size and 
                        cache_data["mtime"] == mtime):
                        cached_entry = sha256
                        break
                
                if cached_entry:
                    # Reuse cached hash
                    new_cache[cached_entry] = {
                        "path": file_path,
                        "size": size,
                        "mtime": mtime
                    }
                else:
                    # Need to hash this file
                    files_to_hash.append((file_path, size, mtime))
                    
            except OSError:
                continue
        
        # Hash files that need hashing
        if files_to_hash:
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                hash_futures = {
                    executor.submit(self._hash_file, file_path): (file_path, size, mtime)
                    for file_path, size, mtime in files_to_hash
                }
                
                for future in concurrent.futures.as_completed(hash_futures):
                    file_path, size, mtime = hash_futures[future]
                    try:
                        sha256 = future.result()
                        if sha256:
                            new_cache[sha256] = {
                                "path": file_path,
                                "size": size,
                                "mtime": mtime
                            }
                    except Exception:
                        # Skip files that failed to hash
                        continue
        
        return new_cache
    
    def _hash_file(self, file_path: str) -> Optional[str]:
        """Compute SHA-256 hash of a file."""
        try:
            hasher = hashlib.sha256()
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(self.chunk_size)
                    if not chunk:
                        break
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception:
            return None
    
    def _update_cache(self, new_cache: Dict[str, Dict[str, any]]):
        """Update the in-memory cache."""
        # Remove entries for files no longer present
        old_paths = {data["path"] for data in self.cache.values()}
        new_paths = {data["path"] for data in new_cache.values()}
        removed_paths = old_paths - new_paths
        
        if removed_paths:
            # Remove cache entries for deleted files
            to_remove = []
            for sha256, data in self.cache.items():
                if data["path"] in removed_paths:
                    to_remove.append(sha256)
            
            for sha256 in to_remove:
                del self.cache[sha256]
        
        # Update cache with new data
        self.cache = new_cache
    
    def _sync_to_database(self) -> int:
        """Sync new SHA256s to database."""
        existing_sha256s = set()
        stmt = select(Image.sha256)
        for row in self.db.execute(stmt):
            existing_sha256s.add(row[0])
        
        new_sha256s = set(self.cache.keys()) - existing_sha256s
        
        if new_sha256s:
            # Insert new images with proper defaults
            for sha256 in new_sha256s:
                self.db.execute(
                    text("""
                        INSERT INTO images 
                        (sha256, mu, sigma, exposures, likes, unlikes, skips, is_archived_hard_no) 
                        VALUES (:sha256, 1500.0, 350.0, 0, 0, 0, 0, false)
                        ON CONFLICT (sha256) DO NOTHING
                    """),
                    {"sha256": sha256}
                )
            
            self.db.commit()
        
        return len(new_sha256s)
    
    def get_path_by_sha256(self, sha256: str) -> Optional[str]:
        """Get file path by SHA256 from cache."""
        cache_entry = self.cache.get(sha256)
        if cache_entry:
            # Verify file still exists
            path = cache_entry["path"]
            if os.path.exists(path):
                return path
        return None
    
    def get_all_sha256s(self) -> Set[str]:
        """Get all SHA256s currently in cache."""
        return set(self.cache.keys())
    
    def get_cache_info(self) -> Dict[str, any]:
        """Get information about the current cache state."""
        return {
            "root_directory": self.root_directory,
            "total_images": len(self.cache),
            "cache_entries": len(self.cache)
        }