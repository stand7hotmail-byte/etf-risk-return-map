import uvicorn
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Import the configured FastAPI app instance from the 'app' module
from app.main import app

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse, tags=["UI"])
async def read_root(request: Request):
    """
    Serves the main index.html page.
    """
    return templates.TemplateResponse("index.html", {"request": request})


if __name__ == "__main__":
    # Run the application using uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload for development
    )