import sys, importlib.util, os
from dotenv import load_dotenv
def die(msg): print("ENV ERROR:", msg, file=sys.stderr); raise SystemExit(1)
if sys.version_info < (3, 10): die(f"Python {sys.version.split()[0]} < 3.10")
if "conda" in sys.version.lower(): die("Conda interpreter detected; use project .venv")
try:
    import pydantic
    if int(pydantic.__version__.split(".")[0]) < 2:
        die(f"Pydantic {pydantic.__version__} < 2.x")
except Exception as e:
    die(f"Pydantic import failed: {e}")
spec = importlib.util.find_spec("agents")
if spec and "site-packages" in (spec.origin or ""):
    # heuristic for the TF/Gym fossil
    try:
        import importlib; importlib.import_module("agents.scripts.networks"); die("Legacy 'agents' package detected")
    except Exception: pass
print("SANITY OK:", sys.version.split()[0])

# Optional: validate OpenAI key works before launching any UI
try:
    load_dotenv(override=True)
    k = os.environ.get("OPENAI_API_KEY", "").strip()
    if k:
        from openai import OpenAI
        c = OpenAI(api_key=k, project=os.environ.get("OPENAI_PROJECT"))
        # Touch the models list to verify auth; swallow network hiccups
        _ = next(iter(c.models.list().data), None)
except Exception:
    pass
