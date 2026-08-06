"""
Jack AI Windows Agent — File Control Action
Creates, deletes, and lists local files and folders.
"""
import os
from loguru import logger

class FileController:

    def create_file(self, params: dict) -> dict:
        """Create a file with optional content."""
        filepath = params.get("path") or params.get("filepath") or params.get("filename")
        content = params.get("content", "")

        if not filepath:
            return {"success": False, "message": "File path ya naam specify nahi kiya gaya"}

        # Resolve relative paths relative to Desktop by default, or keep absolute
        if not os.path.isabs(filepath):
            desktop = os.path.expanduser("~/Desktop")
            filepath = os.path.join(desktop, filepath)

        try:
            # Create directories if they don't exist
            parent_dir = os.path.dirname(filepath)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

            logger.success(f"✅ File ban gayi: {filepath}")
            return {
                "success": True,
                "message": f"File '{os.path.basename(filepath)}' kamyabi se ban gayi hai.",
                "data": {"path": filepath}
            }
        except Exception as e:
            logger.error(f"❌ File banane mein error: {e}")
            return {"success": False, "message": f"File nahi ban saki: {str(e)}"}

    def delete_file(self, params: dict) -> dict:
        """Delete a local file."""
        filepath = params.get("path") or params.get("filepath")

        if not filepath:
            return {"success": False, "message": "File path specify nahi kiya gaya"}

        if not os.path.isabs(filepath):
            desktop = os.path.expanduser("~/Desktop")
            filepath = os.path.join(desktop, filepath)

        if not os.path.exists(filepath):
            return {"success": False, "message": f"File '{filepath}' nahi mili"}

        try:
            if os.path.isdir(filepath):
                os.rmdir(filepath)  # Only deletes empty directory
                msg = f"Folder '{os.path.basename(filepath)}' delete ho gaya."
            else:
                os.remove(filepath)
                msg = f"File '{os.path.basename(filepath)}' delete ho gayi."

            logger.success(f"✅ Removed: {filepath}")
            return {"success": True, "message": msg}
        except Exception as e:
            logger.error(f"❌ Delete error: {e}")
            return {"success": False, "message": f"Delete nahi ho saka: {str(e)}"}
