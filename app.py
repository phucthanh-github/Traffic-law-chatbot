import os
import uvicorn
from api import app

if __name__ == "__main__":
    # Hugging Face Spaces will set the PORT environment variable to 7860
    port = int(os.environ.get("PORT", 7860))
    print(f"Starting FastAPI server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
