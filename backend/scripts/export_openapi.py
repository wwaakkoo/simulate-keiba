import sys
import os
import json
from pathlib import Path

# Backend root directory adding to path (backend/)
backend_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_dir))

try:
    from app.main import app
except ImportError as e:
    print(f"Error importing app: {e}")
    sys.exit(1)

def export_openapi():
    # Docs directory (simulate-keiba/docs)
    docs_dir = backend_dir.parent / "docs"
    output_path = docs_dir / "openapi.json"
    
    docs_dir.mkdir(exist_ok=True)
    
    print(f"Exporting OpenAPI schema...")
    openapi_schema = app.openapi()
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2, ensure_ascii=False)
    
    print(f"Successfully exported OpenAPI schema to {output_path}")

if __name__ == "__main__":
    export_openapi()
