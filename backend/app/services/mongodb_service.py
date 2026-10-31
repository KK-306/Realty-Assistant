import logging
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from bson import ObjectId

logger = logging.getLogger(__name__)

class MongoDBService:
    """
    MongoDB Atlas integration service with GridFS for binary storage.
    Includes thread-safe client, robust error handling, and graceful fallback
    if MongoDB is unconfigured or unreachable.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBService, cls).__new__(cls)
            cls._instance._client = None
            cls._instance._db = None
            cls._instance._fs = None
            cls._instance._initialized = False
            cls._instance._retry_after = 0.0
            cls._instance._connected_cache = False
            cls._instance._init_connection()
        return cls._instance

    def _init_connection(self):
        from app.config import settings
        
        uri = settings.MONGODB_URI
        db_name = settings.MONGODB_DB_NAME
        
        if not uri:
            logger.info("MongoDB Atlas URI not configured (MONGODB_URI is empty). Falling back to local storage.")
            self._client = None
            self._db = None
            self._fs = None
            self._connected_cache = False
            self._initialized = True
            return

        try:
            from pymongo import MongoClient
            import gridfs
            
            # Keep the client after transient DNS/network failures so later calls
            # can reconnect instead of permanently switching this process to local storage.
            client = MongoClient(
                uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=10000,
                appname="RAPropertyStudioAI"
            )
            self._client = client
            self._db = client[db_name]
            
            if settings.MONGODB_GRIDFS_ENABLED:
                self._fs = gridfs.GridFS(self._db)
            else:
                self._fs = None

            # Ping verifies startup connectivity; on failure, preserve the client
            # and schedule a retry from is_connected().
            client.admin.command("ping")
            self._retry_after = time.monotonic() + 5
            self._connected_cache = True
            self._initialized = True
            logger.info(f"Successfully connected to MongoDB Atlas database: '{db_name}'")
        except Exception as e:
            logger.warning(
                "Could not connect to MongoDB Atlas (%s). Using local fallback for now; the service will retry.",
                e,
            )
            self._retry_after = time.monotonic() + 5
            self._connected_cache = False
            self._initialized = True

    def is_connected(self) -> bool:
        from app.config import settings

        if not settings.MONGODB_URI:
            return False
        if time.monotonic() < self._retry_after:
            return self._connected_cache
        if self._client is None or self._db is None:
            self._init_connection()
            if self._client is None or self._db is None:
                return False
        was_connected = self._connected_cache
        try:
            self._client.admin.command("ping")
            self._retry_after = time.monotonic() + 5
            self._connected_cache = True
            if not was_connected:
                logger.info("MongoDB Atlas connection restored.")
            return True
        except Exception:
            self._retry_after = time.monotonic() + 5
            self._connected_cache = False
            return False

    def get_status(self) -> Dict[str, Any]:
        from app.config import settings
        configured = bool(settings.MONGODB_URI)
        connected = self.is_connected()
        collections = []
        if connected and self._db is not None:
            try:
                collections = self._db.list_collection_names()
            except Exception:
                pass

        return {
            "configured": configured,
            "connected": connected,
            "database": settings.MONGODB_DB_NAME if configured else None,
            "gridfs_enabled": settings.MONGODB_GRIDFS_ENABLED and self._fs is not None,
            "collections": collections
        }

    # =========================================================================
    # Job Persistence
    # =========================================================================
    def save_job(self, job_dict: Dict[str, Any]) -> bool:
        if not self.is_connected() or self._db is None:
            return False
        try:
            doc = dict(job_dict)
            job_id = doc.get("job_id")
            if not job_id:
                return False
            
            # Convert enums / datetimes if present
            if hasattr(doc.get("status"), "value"):
                doc["status"] = doc["status"].value
            if isinstance(doc.get("created_at"), datetime):
                doc["created_at"] = doc["created_at"].isoformat()
            if isinstance(doc.get("updated_at"), datetime):
                doc["updated_at"] = doc["updated_at"].isoformat()

            self._db["jobs"].update_one(
                {"job_id": job_id},
                {"$set": doc},
                upsert=True
            )
            return True
        except Exception as e:
            logger.warning(f"Failed to save job {job_dict.get('job_id')} to MongoDB: {e}")
            return False

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        if not self.is_connected() or self._db is None:
            return None
        try:
            doc = self._db["jobs"].find_one({"job_id": job_id})
            if doc:
                doc.pop("_id", None)
            return doc
        except Exception as e:
            logger.warning(f"Failed to get job {job_id} from MongoDB: {e}")
            return None

    # =========================================================================
    # Property Input Persistence
    # =========================================================================
    def save_property(self, job_id: str, property_dict: Dict[str, Any]) -> bool:
        if not self.is_connected() or self._db is None:
            return False
        try:
            doc = {
                "job_id": job_id,
                "property": property_dict,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            self._db["properties"].update_one(
                {"job_id": job_id},
                {"$set": doc},
                upsert=True
            )
            return True
        except Exception as e:
            logger.warning(f"Failed to save property input for job {job_id} in MongoDB: {e}")
            return False

    # =========================================================================
    # Storyboard Persistence
    # =========================================================================
    def save_storyboard(self, job_id: str, storyboard_dict: Dict[str, Any]) -> bool:
        if not self.is_connected() or self._db is None:
            return False
        try:
            doc = {
                "job_id": job_id,
                "storyboard": storyboard_dict,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            self._db["storyboards"].update_one(
                {"job_id": job_id},
                {"$set": doc},
                upsert=True
            )
            return True
        except Exception as e:
            logger.warning(f"Failed to save storyboard for job {job_id} in MongoDB: {e}")
            return False

    # =========================================================================
    # Video Library Persistence
    # =========================================================================
    def save_video_record(self, video_record: Dict[str, Any]) -> bool:
        if not self.is_connected() or self._db is None:
            return False
        try:
            doc = dict(video_record)
            video_id = doc.get("video_id")
            if not video_id:
                return False
            self._db["videos"].update_one(
                {"video_id": video_id},
                {"$set": doc},
                upsert=True
            )
            return True
        except Exception as e:
            logger.warning(f"Failed to save video record {video_record.get('video_id')} in MongoDB: {e}")
            return False

    def list_videos(self) -> List[Dict[str, Any]]:
        if not self.is_connected() or self._db is None:
            return []
        try:
            cursor = self._db["videos"].find({}, {"_id": 0}).sort("created_at", -1)
            return list(cursor)
        except Exception as e:
            logger.warning(f"Failed to list videos from MongoDB: {e}")
            return []

    def get_video_record(self, video_id: str) -> Optional[Dict[str, Any]]:
        if not self.is_connected() or self._db is None:
            return None
        try:
            return self._db["videos"].find_one({"video_id": video_id}, {"_id": 0})
        except Exception as e:
            logger.warning(f"Failed to get video record {video_id} from MongoDB: {e}")
            return None

    # =========================================================================
    # GridFS Binary File Storage (Images & Videos)
    # =========================================================================
    def save_file_to_gridfs(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Stores binary data (MP4, image) directly into MongoDB Atlas GridFS.
        Returns the GridFS file ID string, or None if offline.
        """
        if not self.is_connected() or self._fs is None:
            return None
        try:
            file_meta = metadata or {}
            file_meta["content_type"] = content_type
            file_meta["uploaded_at"] = datetime.now(timezone.utc).isoformat()
            
            # Remove any existing file with identical filename to keep it clean
            try:
                existing = self._fs.find_one({"filename": filename})
                if existing:
                    self._fs.delete(existing._id)
            except Exception:
                pass

            grid_in = self._fs.put(
                file_bytes,
                filename=filename,
                metadata=file_meta
            )
            return str(grid_in)
        except Exception as e:
            logger.warning(f"Failed to save file '{filename}' to MongoDB GridFS: {e}")
            return None

    def get_file_from_gridfs(self, filename_or_id: str) -> Optional[bytes]:
        """
        Retrieves file binary bytes from MongoDB Atlas GridFS by filename or string ObjectId.
        """
        if not self.is_connected() or self._fs is None:
            return None
        try:
            # 1. Try finding by ObjectId
            if ObjectId.is_valid(filename_or_id):
                try:
                    grid_out = self._fs.get(ObjectId(filename_or_id))
                    if grid_out:
                        return grid_out.read()
                except Exception:
                    pass
            
            # 2. Try finding by filename
            grid_out = self._fs.find_one({"filename": filename_or_id})
            if grid_out:
                return grid_out.read()
                
            return None
        except Exception as e:
            logger.warning(f"Failed to get file '{filename_or_id}' from GridFS: {e}")
            return None

    def exists_in_gridfs(self, filename: str) -> bool:
        if not self.is_connected() or self._fs is None:
            return False
        try:
            return self._fs.exists({"filename": filename})
        except Exception:
            return False

mongodb_service = MongoDBService()

