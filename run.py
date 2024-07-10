import uvicorn

def run_uvicorn():
    """Run the Uvicorn server with specified configurations."""
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    run_uvicorn()
