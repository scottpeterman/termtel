import json
import click
import uvicorn
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException, status, Cookie
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.responses import HTMLResponse, Response
import asyncio

from termtel.config import static_path, templates_path
from termtel.routers import workspace, search
from termtel.routers.search import load_sessions_for_user
from termtel.routers.workspace import create_workspace_for_user
from termtel.ssh.ssh_manager import SSHClientManager

# Create FastAPI app
app = FastAPI()

# Include only necessary routers
app.include_router(workspace.router, tags=["workspace"])
app.include_router(search.router, tags=["search"])

# Static files
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Jinja2 templates
templates = Jinja2Templates(directory=str(templates_path))


# Settings
settings = {'theme': "default", "sessions": None}


# Modified get_current_user function
async def get_current_user(access_token: str = Cookie(None)):
    # Always return "user" regardless of token
    return "user"


# Add auto-login middleware
from termtel.routers.auth import auto_login_middleware

app.middleware("http")(auto_login_middleware)

@app.get("/terminal", response_class=HTMLResponse)
async def terminal_page(request: Request):
    """Return a bare terminal page without tabs."""
    return templates.TemplateResponse("terminal.html", {
        "request": request,
        "theme": settings['theme']
    })

@app.get("/", response_class=HTMLResponse)
async def main_page(request: Request, theme: str = "default"):
    # No need to check authentication - we're always logged in as "user"
    username = "user"

    # Load user workspace and settings
    user_workspace, user_settings = create_workspace_for_user(username)

    # Get the default session file and theme from the user settings
    sessions_file = user_settings.get("default_sessions_file", "sessions.yaml")
    theme = user_settings.get("theme", "theme-default.css")

    # Load user sessions
    sessions = load_sessions_for_user(username, sessions_file)

    for folder in sessions:
        for session in folder.get("sessions", []):
            session.pop("credsid", None)
            session['json'] = json.dumps(session)

    return templates.TemplateResponse("base2.html", {
        "request": request,
        "sessions": sessions,
        "theme": theme,
        "title": "Termtel"
    })


# SSHClientManager and WebSocket connections
ssh_manager = SSHClientManager()


@app.websocket("/ws/terminal/{tab_id}")
async def websocket_terminal(websocket: WebSocket, tab_id: str):
    # No authentication check needed for websocket
    await websocket.accept()
    await ssh_manager.create_client(tab_id)
    listen_task = asyncio.create_task(ssh_manager.listen_to_ssh_output(tab_id, websocket))

    try:
        while True:
            data = await websocket.receive_json()
            if data['type'] == 'connect':
                await ssh_manager.connect(tab_id, data['hostname'], data['port'],
                                          data['username'], data['password'], websocket)
            elif data['type'] == 'input':
                await ssh_manager.send_input(tab_id, data['data'])
            elif data['type'] == 'resize':
                await ssh_manager.resize_terminal(tab_id, data['cols'], data['rows'])
    except WebSocketDisconnect:
        await ssh_manager.disconnect(tab_id)
        listen_task.cancel()
    except Exception as e:
        print(f"SSH / Websocket error {e}")
        await ssh_manager.disconnect(tab_id)
        listen_task.cancel()
    finally:
        if not listen_task.done():
            listen_task.cancel()
        await ssh_manager.disconnect(tab_id)


def run_server():
    from helpers.utils import find_available_port
    port = find_available_port()
    uvicorn.run(app, host="127.0.0.1", port=port)


# CLI to start the application
@click.command()
@click.option('--settheme', default='default', help='Set the theme for the application.')
@click.option('--sessionfile', default='sessions.yaml', help='YAML file with session data.')
def start_app(settheme, sessionfile):
    settings['theme'] = settheme
    settings['sessionfile'] = sessionfile
    run_server()


if __name__ == "__main__":
    start_app()