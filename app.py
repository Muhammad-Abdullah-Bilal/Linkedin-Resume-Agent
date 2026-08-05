import os
from server import run_server

if __name__ == "__main__":
    # Hugging Face spaces bind to the port defined in the PORT env variable (usually 7860)
    port = int(os.environ.get("PORT", 7860))
    print(f"Hugging Face Space: Booting Dashboard on port {port}...")
    run_server(port)
