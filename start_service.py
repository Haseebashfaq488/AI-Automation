import os
import sys
import time
import signal
import atexit
import requests
from pathlib import Path
import subprocess as sp
from pyngrok import ngrok

# ================= CONFIGURATION =================
BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR / "backend"
WHATSAPP_DIR = BACKEND_DIR / "whatsapp_service"
LOG_FILE = BASE_DIR / "tunnel_service.log"

BACKEND_PORT = 8000
WHATSAPP_PORT = 4097

VERCEL_TOKEN = os.getenv("VERCEL_TOKEN", "")
TEAM_ID = os.getenv("VERCEL_TEAM_ID", "")
PROJECT_ID = os.getenv("VERCEL_PROJECT_ID", "")
ENV_VAR_KEYS = [
    os.getenv("VERCEL_ENV_VAR_KEY", "OPENCODE_TUNNEL_URL"),
    "NEXT_PUBLIC_API_URL",
]

# Optional: set via environment variables if desired
NGROK_AUTHTOKEN = os.getenv("NGROK_AUTHTOKEN", "")
NGROK_DOMAIN = os.getenv("NGROK_DOMAIN", "")

# Process tracking for cleanup
_processes = []
# =================================================


def log(msg: str):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {msg}"
    print(formatted, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except Exception:
        pass


def update_vercel_env(new_url: str):
    if not VERCEL_TOKEN or not PROJECT_ID:
        log("Vercel token or project ID not configured; skipping Vercel env update.")
        return False

    headers = {
        "Authorization": f"Bearer {VERCEL_TOKEN}",
        "Content-Type": "application/json",
    }

    query_params = f"?teamId={TEAM_ID}" if TEAM_ID else ""
    url = f"https://api.vercel.com/v9/projects/{PROJECT_ID}/env{query_params}"

    log(f"Fetching existing Vercel environment variables for project {PROJECT_ID}...")
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            log(f"Failed to fetch Vercel env vars ({response.status_code}): {response.text}")
            return False

        env_vars = response.json().get("envs", [])

        # Unique keys to update
        keys_to_update = list(dict.fromkeys(ENV_VAR_KEYS))
        success_all = True

        for target_key in keys_to_update:
            var_id = None
            for var in env_vars:
                if var.get("key") == target_key:
                    var_id = var.get("id")
                    break

            payload = {
                "key": target_key,
                "value": new_url,
                "type": "plain",
                "target": ["production", "preview", "development"],
            }

            if var_id:
                update_url = f"https://api.vercel.com/v9/projects/{PROJECT_ID}/env/{var_id}{query_params}"
                res = requests.patch(update_url, headers=headers, json=payload, timeout=15)
            else:
                res = requests.post(url, headers=headers, json=payload, timeout=15)

            if res.status_code in [200, 201]:
                log(f"Successfully updated Vercel ENV var '{target_key}' -> {new_url}")
            else:
                log(f"Failed to update Vercel ENV var '{target_key}' ({res.status_code}): {res.text}")
                success_all = False

        return success_all
    except Exception as e:
        log(f"Exception during Vercel ENV update: {str(e)}")
        return False


def trigger_vercel_redeploy():
    if not VERCEL_TOKEN or not PROJECT_ID:
        return False

    headers = {
        "Authorization": f"Bearer {VERCEL_TOKEN}",
        "Content-Type": "application/json",
    }

    query_params = f"?teamId={TEAM_ID}" if TEAM_ID else ""
    log(f"Triggering Vercel redeployment for project {PROJECT_ID}...")
    try:
        # Fetch the latest deployment ID for the project
        get_deployments_url = f"https://api.vercel.com/v6/deployments{query_params}&projectId={PROJECT_ID}&limit=1"
        res_get = requests.get(get_deployments_url, headers=headers, timeout=15)

        latest_deployment_id = None
        if res_get.status_code == 200:
            deployments = res_get.json().get("deployments", [])
            if deployments:
                latest_deployment_id = deployments[0].get("uid") or deployments[0].get("id")
                log(f"Found latest deployment ID: {latest_deployment_id}")

        if latest_deployment_id:
            post_deploy_url = f"https://api.vercel.com/v13/deployments{query_params}"
            payload = {
                "name": PROJECT_ID,
                "deploymentId": latest_deployment_id,
                "target": "production",
            }
            res = requests.post(post_deploy_url, headers=headers, json=payload, timeout=30)
            if res.status_code in [200, 201]:
                dep_data = res.json()
                log(f"Successfully triggered Vercel deployment! ID: {dep_data.get('id')}, URL: {dep_data.get('url')}")
                return True

            redeploy_url = f"https://api.vercel.com/v13/deployments/{latest_deployment_id}/redeploy{query_params}"
            res_re = requests.post(redeploy_url, headers=headers, json={"name": PROJECT_ID, "target": "production"}, timeout=30)
            if res_re.status_code in [200, 201]:
                dep_data = res_re.json()
                log(f"Successfully triggered Vercel redeployment via endpoint! ID: {dep_data.get('id')}")
                return True
            else:
                log(f"Failed to trigger Vercel deployment ({res.status_code}): {res.text} | Redeploy response: {res_re.text}")
                return False
        else:
            log("No previous deployment found to redeploy.")
            return False
    except Exception as e:
        log(f"Exception during Vercel redeploy trigger: {str(e)}")
        return False


def is_backend_running() -> bool:
    try:
        response = requests.get(f"http://127.0.0.1:{BACKEND_PORT}/health", timeout=2)
        return response.status_code == 200
    except Exception:
        return False


def is_whatsapp_running() -> bool:
    try:
        response = requests.get(f"http://127.0.0.1:{WHATSAPP_PORT}/status", timeout=2)
        return response.status_code == 200
    except Exception:
        return False


def start_backend():
    log("Starting FastAPI Backend server (uvicorn app.main:app --reload)...")
    proc = sp.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", str(BACKEND_PORT), "--reload"],
        cwd=str(BACKEND_DIR),
    )
    _processes.append(proc)
    return proc


def start_whatsapp():
    log("Starting WhatsApp Sidecar (node server.js)...")
    # Use 'node' or 'node.exe' directly
    proc = sp.Popen(
        ["node", "server.js"],
        cwd=str(WHATSAPP_DIR),
    )
    _processes.append(proc)
    return proc


def establish_tunnel():
    """Start ngrok tunnel pointing to FastAPI backend (port 8000)."""
    log("Starting ngrok Tunnel...")
    if NGROK_AUTHTOKEN:
        ngrok.set_auth_token(NGROK_AUTHTOKEN)

    try:
        connect_kwargs = {}
        if NGROK_DOMAIN:
            connect_kwargs["domain"] = NGROK_DOMAIN

        tunnel = ngrok.connect(BACKEND_PORT, "http", **connect_kwargs)
        tunnel_url = tunnel.public_url
        log(f"Captured ngrok Tunnel URL: {tunnel_url}")

        if VERCEL_TOKEN:
            updated = update_vercel_env(tunnel_url)
            if updated:
                trigger_vercel_redeploy()

        ngrok_process = ngrok.get_ngrok_process()
        proc = ngrok_process.proc if ngrok_process and hasattr(ngrok_process, "proc") else None
        return proc
    except Exception as e:
        log(f"ngrok failed: {str(e)}")
        try:
            ngrok.kill()
        except Exception:
            pass
    return None


def cleanup():
    log("Cleaning up active child processes...")
    try:
        ngrok.kill()
    except Exception:
        pass

    for p in _processes:
        try:
            if p and p.poll() is None:
                p.terminate()
                p.wait(timeout=2)
        except Exception:
            try:
                p.kill()
            except Exception:
                pass


def main():
    log("=== AI Automation Control Plane Starting ===")
    log(f"Workspace Root : {BASE_DIR}")
    log(f"Backend Path   : {BACKEND_DIR}")
    log(f"WhatsApp Path  : {WHATSAPP_DIR}")

    # Register cleanup handlers
    atexit.register(cleanup)
    signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))
    signal.signal(signal.SIGTERM, lambda s, f: sys.exit(0))

    # Clear any stale ngrok processes so they don't block new tunnel creation
    try:
        ngrok.kill()
    except Exception:
        pass

    # 1. Start WhatsApp DOM service if not already running
    whatsapp_proc = None
    if is_whatsapp_running():
        log(f"WhatsApp service already running on port {WHATSAPP_PORT}, reusing it.")
    else:
        whatsapp_proc = start_whatsapp()

    # 2. Start FastAPI Backend if not already running
    backend_proc = None
    if is_backend_running():
        log(f"Backend already running on port {BACKEND_PORT}, reusing it.")
    else:
        backend_proc = start_backend()

    # Wait briefly for services to initialize
    time.sleep(2)

    # 3. Establish tunnel loop & monitor health
    while True:
        tunnel_proc = None
        try:
            tunnel_proc = establish_tunnel()
        except Exception as e:
            log(f"Tunnel setup exception: {str(e)}")

        if tunnel_proc:
            log("Tunnel active. Monitoring services and tunnel process...")
            try:
                tunnel_proc.wait()
            except Exception as e:
                log(f"Tunnel process wait error: {str(e)}")
            log("Tunnel process has stopped.")
        else:
            log("No tunnel could be established.")

        # Health monitor and restart if any service died
        try:
            if backend_proc is None or backend_proc.poll() is not None:
                if not is_backend_running():
                    log("Backend not running. Restarting FastAPI backend...")
                    backend_proc = start_backend()
        except Exception as e:
            log(f"Backend restart error: {str(e)}")

        try:
            if whatsapp_proc is None or whatsapp_proc.poll() is not None:
                if not is_whatsapp_running():
                    log("WhatsApp service not running. Restarting WhatsApp service...")
                    whatsapp_proc = start_whatsapp()
        except Exception as e:
            log(f"WhatsApp restart error: {str(e)}")

        log("Re-establishing tunnel in 10 seconds...")
        time.sleep(10)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        pass
    except Exception as e:
        log(f"Fatal error: {str(e)}")
    finally:
        cleanup()
