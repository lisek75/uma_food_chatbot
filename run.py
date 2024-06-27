# run.py
import uvicorn
from typing import List


def run_uvicorn():
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_excludes=[".venv/*"]
    )

if __name__ == "__main__":
    run_uvicorn()

