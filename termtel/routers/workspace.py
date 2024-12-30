import yaml
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from pathlib import Path
from starlette.responses import FileResponse
from termtel.helpers.auth_helper import get_current_user  # Import from the new auth_helpers module

# Define the router
router = APIRouter()

# Base directory for storing user-specific session files
BASE_WORKSPACE_DIR = Path("./workspaces")

# Function to create a user-specific workspace
def create_workspace_for_user(username: str):
    user_workspace = BASE_WORKSPACE_DIR / username
    user_workspace.mkdir(parents=True, exist_ok=True)

    # Path to user profile settings
    profile_settings_path = user_workspace / "profile_settings.yaml"

    # Default settings
    default_settings = {
        "default_sessions_file": "sessions.yaml",
        "theme": "theme-default.css"
    }

    # If profile settings do not exist, create them
    if not profile_settings_path.exists():
        with open(profile_settings_path, 'w') as f:
            yaml.dump(default_settings, f)

    # Load the profile settings to return
    with open(profile_settings_path, 'r') as f:
        user_settings = yaml.safe_load(f)

    return user_workspace, user_settings

@router.get("/workspace/files")
async def list_files(username: str = Depends(get_current_user)):
    user_workspace = create_workspace_for_user(username)
    files = [f.name for f in user_workspace.iterdir() if f.is_file()]
    return {"files": files}


# File upload route (protected with JWT)
@router.post("/upload/")
async def upload_file(file: UploadFile = File(...), username: str = Depends(get_current_user)):
    user_workspace = create_workspace_for_user(username)
    file_path = user_workspace / file.filename
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    return {"filename": file.filename}

# File download route (protected with JWT)
@router.get("/download/{filename}")
async def download_file(filename: str, username: str = Depends(get_current_user)):
    user_workspace = create_workspace_for_user(username)
    file_path = user_workspace / filename

    if file_path.exists():
        return FileResponse(path=file_path, filename=filename)
    else:
        raise HTTPException(status_code=404, detail="File not found")

# List files in user workspace
@router.get("/workspace/files")
async def list_files(username: str = Depends(get_current_user)):
    user_workspace = create_workspace_for_user(username)
    files = [f.name for f in user_workspace.iterdir() if f.is_file()]
    return {"files": files}

@router.post("/upload/")
async def upload_file(file: UploadFile = File(...), username: str = Depends(get_current_user)):
    user_workspace = create_workspace_for_user(username)
    file_path = user_workspace / file.filename
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    return {"filename": file.filename}

@router.get("/download/{filename}")
async def download_file(filename: str, username: str = Depends(get_current_user)):
    user_workspace = create_workspace_for_user(username)
    file_path = user_workspace / filename

    if file_path.exists():
        return FileResponse(path=file_path, filename=filename)
    else:
        raise HTTPException(status_code=404, detail="File not found")
