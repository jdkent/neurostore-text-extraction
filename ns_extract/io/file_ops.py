"""File operation utilities with proper error handling and thread safety.

This module provides a thread-safe interface for file operations with atomic
writing, proper locking, and error handling.
"""
import fcntl
import json
import os
import shutil
from contextlib import contextmanager
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Iterator, Union

from ..pipelines.utils.errors import FileOperationError

# Global lock for thread synchronization
_file_locks: Dict[str, Lock] = {}
_lock_creation_lock = Lock()


def get_file_lock(path: Union[str, Path]) -> Lock:
    """Get or create a thread lock for a specific file path."""
    path_str = str(Path(path).resolve())
    with _lock_creation_lock:
        if path_str not in _file_locks:
            _file_locks[path_str] = Lock()
        return _file_locks[path_str]


@contextmanager
def file_lock(path: Union[str, Path]) -> Iterator[None]:
    """Context manager for file locking using fcntl."""
    path = Path(path)
    lock_path = path.parent / f".{path.name}.lock"
    
    try:
        with open(lock_path, "w") as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            yield
    finally:
        try:
            lock_path.unlink()
        except OSError:
            pass


def atomic_write(
    path: Union[str, Path],
    content: Union[str, bytes],
    mode: str = "w",
    **kwargs: Any
) -> None:
    """Write content to a file atomically.
    
    Args:
        path: Path to write file to
        content: Content to write to file
        mode: File open mode ('w' for text, 'wb' for binary)
        **kwargs: Additional arguments passed to open()
        
    Raises:
        FileOperationError: If write operation fails
    """
    path = Path(path)
    tmp_path = path.parent / f".{path.name}.tmp"
    
    with get_file_lock(path):
        try:
            # Write to temporary file
            with open(tmp_path, mode, **kwargs) as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())
            
            # Atomic rename
            tmp_path.replace(path)
        
        except Exception as e:
            # Clean up temp file if something goes wrong
            try:
                tmp_path.unlink()
            except OSError:
                pass
            raise FileOperationError(f"Failed to write to {path}: {str(e)}") from e


def safe_read(
    path: Union[str, Path],
    mode: str = "r",
    **kwargs: Any
) -> Union[str, bytes]:
    """Read file content with proper error handling and locking.
    
    Args:
        path: Path to read file from
        mode: File open mode ('r' for text, 'rb' for binary)
        **kwargs: Additional arguments passed to open()
        
    Returns:
        File contents as string or bytes depending on mode
        
    Raises:
        FileOperationError: If read operation fails
    """
    path = Path(path)
    
    with get_file_lock(path):
        try:
            with open(path, mode, **kwargs) as f:
                return f.read()
        except Exception as e:
            raise FileOperationError(f"Failed to read {path}: {str(e)}") from e


def safe_copy(
    src: Union[str, Path],
    dst: Union[str, Path],
    **kwargs: Any
) -> None:
    """Copy file with proper error handling and locking.
    
    Args:
        src: Source file path
        dst: Destination file path
        **kwargs: Additional arguments passed to shutil.copy2()
        
    Raises:
        FileOperationError: If copy operation fails
    """
    src, dst = Path(src), Path(dst)
    
    with get_file_lock(src), get_file_lock(dst):
        try:
            shutil.copy2(src, dst, **kwargs)
        except Exception as e:
            raise FileOperationError(
                f"Failed to copy {src} to {dst}: {str(e)}"
            ) from e


def safe_json_read(path: Union[str, Path]) -> Dict[str, Any]:
    """Read JSON file with proper error handling.
    
    Args:
        path: Path to JSON file
        
    Returns:
        Parsed JSON content as dictionary
        
    Raises:
        FileOperationError: If file read or JSON parsing fails
    """
    try:
        content = safe_read(path)
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise FileOperationError(f"Invalid JSON in {path}: {str(e)}") from e


def safe_json_write(
    path: Union[str, Path],
    data: Dict[str, Any],
    **kwargs: Any
) -> None:
    """Write JSON file atomically with proper error handling.
    
    Args:
        path: Path to write JSON file to
        data: Data to serialize to JSON
        **kwargs: Additional arguments passed to json.dumps()
        
    Raises:
        FileOperationError: If JSON serialization or write fails
    """
    try:
        content = json.dumps(data, **kwargs)
        atomic_write(path, content)
    except (TypeError, ValueError) as e:
        raise FileOperationError(f"Failed to serialize JSON for {path}: {str(e)}") from e


class FileOperationsMixin:
    """Mixin class providing file operation methods.
    
    This mixin provides thread-safe file operations with proper error handling
    and atomic writes.
    """
    
    @staticmethod
    def atomic_write(
        path: Union[str, Path],
        content: Union[str, bytes],
        mode: str = "w",
        **kwargs: Any
    ) -> None:
        """Write content to a file atomically."""
        return atomic_write(path, content, mode, **kwargs)
    
    @staticmethod
    def safe_read(
        path: Union[str, Path],
        mode: str = "r",
        **kwargs: Any
    ) -> Union[str, bytes]:
        """Read file content safely."""
        return safe_read(path, mode, **kwargs)
    
    @staticmethod
    def safe_copy(
        src: Union[str, Path],
        dst: Union[str, Path],
        **kwargs: Any
    ) -> None:
        """Copy file safely."""
        return safe_copy(src, dst, **kwargs)
    
    @staticmethod
    def safe_json_read(path: Union[str, Path]) -> Dict[str, Any]:
        """Read JSON file safely."""
        return safe_json_read(path)
    
    @staticmethod
    def safe_json_write(
        path: Union[str, Path],
        data: Dict[str, Any],
        **kwargs: Any
    ) -> None:
        """Write JSON file safely."""
        return safe_json_write(path, data, **kwargs)
