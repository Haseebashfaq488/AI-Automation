import os
import sys
import time
import signal
import atexit
import requests
from pathlib import Path
import subprocess as sp
from dotenv import load_dotenv
from pyngrok import ngrok

# ================= CONFIGURATION =================
BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR / "backend"
WHATSAPP_DIR = BACKEND_DIR / "whatsapp_service"
CHROME_PROFILE = WHATSAPP_DIR / "chrome_profile_copy"
LOG_FILE = BASE_DIR / "tunnel_service.log"
BACKEND_LOG = BASE_DIR / "backend_service.log"
WHATSAPP_LOG = BASE_DIR / "whatsapp_service.log"

# Load environment variables from backend/.env and .env
load_dotenv(BACKEND_DIR / ".env")
load_dotenv(BASE_DIR / ".env")

BACKEND_PORT = 8000
WHATSAPP_PORT = 4097

VERCEL_TOKEN = os.getenv("VERCEL_TOKEN", "")
TEAM_ID = os.getenv("VERCEL_TEAM_ID", "")
PROJECT_ID = os.getenv("VERCEL_PROJECT_ID", "")
ENV_VAR_KEYS = [
    os.getenv("VERCEL_ENV_VAR_KEY", "OPENCODE_TUNNEL_URL"),
    "NEXT_PUBLIC_API_URL",
]

NGROK_AUTHTOKEN = os.getenv("NGROK_AUTHTOKEN", "")
NGROK_DOMAIN = os.getenv("NGROK_DOMAIN", "")

# Process tracking for cleanup
_processes = []
_open_files = []
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


def wait_for_network(max_wait_seconds: int = 60) -> bool:
    """Ensure active network & internet connectivity before starting dependent services."""
    log("Verifying internet connectivity...")
    start_time = time.time()
    while time.time() - start_time < max_wait_seconds:
        try:
            res = requests.get("https://1.1.1.1", timeout=3)
            if res.status_code in [200, 301, 302, 403, 404]:
                log("Internet connectivity confirmed.")
                return True
        except Exception:
            time.sleep(2)
    log("Internet check timed out; proceeding anyway.")
    return False


def clean_stale_chrome_locks():
    """Remove stale Chrome singleton locks from profile copy if Chrome crashed previously."""
    if not CHROME_PROFILE.exists():
        return
    lock_names = ["SingletonLock", "SingletonSocket", "SingletonCookie"]
    for lock in lock_names:
        lock_path = CHROME_PROFILE / lock
        if lock_path.exists():
            try:
                if lock_path.is_file() or lock_path.is_symlink():
                    lock_path.unlink(missing_ok=True)
                    log(f"Cleaned up stale Chrome lock: {lock}")
            except Exception as e:
                log(f"Notice: Could not remove {lock}: {e}")


def update_vercel_env(new_url: str):
    token = os.getenv("VERCEL_TOKEN", VERCEL_TOKEN)
    project_id = os.getenv("VERCEL_PROJECT_ID", PROJECT_ID)
    team_id = os.getenv("VERCEL_TEAM_ID", TEAM_ID)

    if not token or not project_id:
        log("Vercel token or project ID not configured; skipping Vercel env update.")
        return False

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    query_params = f"?teamId={team_id}" if team_id else ""
    url = f"https://api.vercel.com/v9/projects/{project_id}/env{query_params}"

    log(f"Fetching existing Vercel environment variables for project {project_id}...")
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
                update_url = f"https://api.vercel.com/v9/projects/{project_id}/env/{var_id}{query_params}"
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
    token = os.getenv("VERCEL_TOKEN", VERCEL_TOKEN)
    project_id = os.getenv("VERCEL_PROJECT_ID", PROJECT_ID)
    team_id = os.getenv("VERCEL_TEAM_ID", TEAM_ID)

    if not token or not project_id:
        return False

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    query_params = f"?teamId={team_id}" if team_id else ""
    log(f"Triggering Vercel redeployment for project {project_id}...")
    try:
        get_deployments_url = f"https://api.vercel.com/v6/deployments{query_params}&projectId={project_id}&limit=1"
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
                "name": project_id,
                "deploymentId": latest_deployment_id,
                "target": "production",
            }
            res = requests.post(post_deploy_url, headers=headers, json=payload, timeout=30)
            if res.status_code in [200, 201]:
                dep_data = res.json()
                log(f"Successfully triggered Vercel deployment! ID: {dep_data.get('id')}, URL: {dep_data.get('url')}")
                return True

            redeploy_url = f"https://api.vercel.com/v13/deployments/{latest_deployment_id}/redeploy{query_params}"
            res_re = requests.post(redeploy_url, headers=headers, json={"name": project_id, "target": "production"}, timeout=30)
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
        response = requests.get(f"http://127.0.0.1:{BACKEND_PORT}/health", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


def is_whatsapp_running() -> bool:
    try:
        response = requests.get(f"http://127.0.0.1:{WHATSAPP_PORT}/status", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


def start_backend():
    log("Starting FastAPI Backend server (uvicorn app.main:app)...")
    try:
        backend_log_f = open(BACKEND_LOG, "a", encoding="utf-8")
        _open_files.append(backend_log_f)
    except Exception:
        backend_log_f = sp.DEVNULL

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    proc = sp.Popen(
        [sys.executable, "-u", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", str(BACKEND_PORT)],
        cwd=str(BACKEND_DIR),
        stdout=backend_log_f,
        stderr=sp.STDOUT,
        env=env,
    )
    _processes.append(proc)
    return proc


def start_whatsapp():
    log("Starting WhatsApp Sidecar (node server.js)...")
    clean_stale_chrome_locks()
    try:
        whatsapp_log_f = open(WHATSAPP_LOG, "a", encoding="utf-8")
        _open_files.append(whatsapp_log_f)
    except Exception:
        whatsapp_log_f = sp.DEVNULL

    env = os.environ.copy()
    proc = sp.Popen(
        ["node", "server.js"],
        cwd=str(WHATSAPP_DIR),
        stdout=whatsapp_log_f,
        stderr=sp.STDOUT,
        env=env,
    )
    _processes.append(proc)
    return proc


def establish_tunnel():
    """Start ngrok tunnel pointing to FastAPI backend (port 8000)."""
    log("Starting ngrok Tunnel...")
    auth_token = os.getenv("NGROK_AUTHTOKEN", NGROK_AUTHTOKEN)
    domain = os.getenv("NGROK_DOMAIN", NGROK_DOMAIN)

    if auth_token:
        ngrok.set_auth_token(auth_token)

    try:
        connect_kwargs = {}
        if domain:
            connect_kwargs["domain"] = domain

        tunnel = ngrok.connect(BACKEND_PORT, "http", **connect_kwargs)
        tunnel_url = tunnel.public_url
        log(f"Captured ngrok Tunnel URL: {tunnel_url}")

        if os.getenv("VERCEL_TOKEN", VERCEL_TOKEN):
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


def is_tunnel_alive(tunnel_proc) -> bool:
    if tunnel_proc is not None and hasattr(tunnel_proc, "poll") and tunnel_proc.poll() is not None:
        return False
    try:
        tunnels = ngrok.get_tunnels()
        return len(tunnels) > 0
    except Exception:
        return False


def kill_proc(proc):
    if proc:
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass


def cleanup():
    log("Cleaning up active child processes...")
    try:
        ngrok.kill()
    except Exception:
        pass

    for p in _processes:
        kill_proc(p)

    for f in _open_files:
        try:
            f.close()
        except Exception:
            pass


def main():
    log("=== AI Automation Control Plane Starting ===")
    log(f"Workspace Root : {BASE_DIR}")
    log(f"Backend Path   : {BACKEND_DIR}")
    log(f"WhatsApp Path  : {WHATSAPP_DIR}")

    atexit.register(cleanup)
    signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))
    signal.signal(signal.SIGTERM, lambda s, f: sys.exit(0))

    # Pre-flight: Wait for active internet connection (especially important on boot)
    wait_for_network(max_wait_seconds=60)

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

    # 3. Settle wait
    time.sleep(3)

    tunnel_proc = establish_tunnel()

    log("Active monitoring loop engaged. Checking services and tunnel health continuously...")
    last_heartbeat_time = time.time()

    # 4. Reliable Non-Intrusive Monitoring Loop
    while True:
        now = time.time()

        # Check FastAPI Backend: ONLY restart if process actually died
        if backend_proc is not None and backend_proc.poll() is not None:
            log("FastAPI backend process exited unexpectedly. Restarting backend...")
            backend_proc = start_backend()

        # Check WhatsApp Sidecar: ONLY restart if process actually died
        if whatsapp_proc is not None and whatsapp_proc.poll() is not None:
            log("WhatsApp sidecar process exited unexpectedly. Restarting WhatsApp service...")
            whatsapp_proc = start_whatsapp()

        # Check ngrok Tunnel: Re-establish if tunnel dropped
        if not is_tunnel_alive(tunnel_proc):
            log("ngrok Tunnel is down. Re-establishing tunnel...")
            try:
                ngrok.kill()
            except Exception:
                pass
            tunnel_proc = establish_tunnel()

        # Periodic Heartbeat Log (Every 60 seconds)
        if now - last_heartbeat_time >= 60:
            b_status = "UP" if is_backend_running() else "STARTING/INITIALIZING"
            w_status = "UP" if is_whatsapp_running() else "STARTING/INITIALIZING"
            t_status = "UP" if is_tunnel_alive(tunnel_proc) else "DOWN"
            log(f"Heartbeat: Backend [{b_status}], WhatsApp [{w_status}], Tunnel [{t_status}]")
            last_heartbeat_time = now

        time.sleep(5)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        pass
    except Exception as e:
        log(f"Fatal error: {str(e)}")
    finally:
        cleanup()
