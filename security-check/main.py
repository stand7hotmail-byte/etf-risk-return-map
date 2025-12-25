import uvicorn
from fastapi import Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Import the configured FastAPI app instance from the 'app' module
from app.main import app
from app.api.admin import get_admin_user # Import the admin user dependency
from fastapi.staticfiles import StaticFiles # Import StaticFiles


# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Mount blog static files to /blog prefix
# This will serve files like static/blog/my-post.html at /blog/my-post.html
app.mount("/blog", StaticFiles(directory="static/blog"), name="blog_static")


# Setup templates
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse, tags=["UI"])
async def read_root(request: Request):
    """
    Serves the main index.html page.
    """
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/brokers", response_class=HTMLResponse, tags=["UI"])
async def brokers_page(request: Request):
    """
    Serves the broker comparison page.
    """
    return templates.TemplateResponse("brokers.html", {"request": request, "title": "ETF投資におすすめの証券会社"})


@app.get("/admin/affiliate", response_class=HTMLResponse, tags=["Admin UI"])
async def admin_affiliate_dashboard(request: Request, admin_user: dict = Depends(get_admin_user)):
    """
    Serves the affiliate dashboard for administrators.
    """
    return templates.TemplateResponse("admin/affiliate_dashboard.html", {"request": request})


@app.get("/blog", response_class=HTMLResponse, tags=["UI"])
async def blog_index(request: Request):
    """
    Serves the blog index page.
    """
    return templates.TemplateResponse("blog/index.html", {"request": request, "title": "すべての記事"})


if __name__ == "__main__":
    # Run the application using uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload for development
    )