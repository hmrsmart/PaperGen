"""
Server entrypoint for Academic Research Paper Generator Agent.
"""

import sys
import uvicorn

if __name__ == "__main__":
    print("=" * 70)
    print("🚀 Starting Academic Research Paper Generator Agent Server")
    print("🌐 Open your browser at: http://localhost:8000")
    print("=" * 70)
    uvicorn.run("app.server:app", host="0.0.0.0", port=8000, reload=True)
