"""
Tool: TeamworkGenerateUploadUrlTool
-----------------------------------

Step 1 of the Teamwork file-upload workflow – obtain a presigned S3 URL and a
ref-ID by calling

GET /projects/api/v1/pendingfiles/presignedurl.json

via :pyfunc:`aider.api.teamwork_projects.generate_upload_url`.

Required parameters
-------------------
• file_name (string) – name of the file including extension  
• file_size (integer) – size in **bytes**

The JSON response (containing ``ref`` and ``url``) is returned as a UTF-8 string.
"""
from __future__ import annotations

import json
from typing import Any, Dict

from aider.tools.base_tool import BaseTool
from aider.api import teamwork_projects as tw_projects
from aider.api import ApiError


class TeamworkGenerateUploadUrlTool(BaseTool):
    """Generate a presigned S3 URL for uploading a file to Teamwork."""

    name = "teamwork_generate_upload_url"
    description = (
        "Generate a presigned S3 URL + ref-ID for uploading a file to Teamwork. "
        "Provide `file_name` (e.g. report.pdf) and `file_size` in bytes. The tool "
        "calls GET /projects/api/v1/pendingfiles/presignedurl.json and returns the "
        "API’s JSON response as a UTF-8 string."
    )

    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "file_name": {
                "type": "string",
                "description": "File name including extension (example.txt)",
            },
            "file_size": {
                "type": "integer",
                "description": "File size in bytes",
                "minimum": 1,
            },
        },
        "required": ["file_name", "file_size"],
        "additionalProperties": True,
    }

    def run(self, file_name: str, file_size: int, **kwargs: Dict[str, Any]):  # noqa: D401
        try:
            resp = tw_projects.generate_upload_url(file_name, file_size, **kwargs)
            return json.dumps(resp.json(), ensure_ascii=False)
        except ApiError as api_exc:
            return json.dumps({"error": str(api_exc)}, ensure_ascii=False)
        except Exception as exc:  # pragma: no cover
            return json.dumps({"error": f"Unexpected error: {exc}"}, ensure_ascii=False)
