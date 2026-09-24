import os
import sys
import time
import signal
import requests
from pathlib import Path
from dotenv import load_dotenv
from pyngrok import ngrok

BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR / "backend"

load_dotenv(BACKEND_DIR / ".env")
load_dotenv(BASE_DIR / ".env")

BACKEND_PORT = 8000
VERCEL_TOKEN = os.getenv("VERCEL_TOKEN", "")
TEAM_ID = os.getenv("VERCEL_TEAM_ID", "")
PROJECT_ID = os.getenv("VERCEL_PROJECT_ID", "")
ENV_VAR_KEYS = [
    os.getenv("VERCEL_ENV_VAR_KEY", "OPENCODE_TUNNEL_URL"),
    "NEXT_PUBLIC_API_URL",
]
NGROK_AUTHTOKEN = os.getenv("NGROK_AUTHTOKEN", "")
NGROK_DOMAIN = os.getenv("NGROK_DOMAIN", "")


def log(msg: str):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}", flush=True)


def wait_for_network(max_wait=60):
    log("Verifying internet connectivity...")
    start = time.time()
    while time.time() - start < max_wait:
        try:
            r = requests.get("https://1.1.1.1", timeout=3)
            if r.status_code in [200, 301, 302, 403, 404]:
                log("Internet connectivity confirmed.")
                return True
        except Exception:
            time.sleep(2)
    log("Internet check timed out, proceeding anyway.")
    return False


def wait_for_backend(max_wait=120):
    log(f"Waiting for local backend on port {BACKEND_PORT} to be ready...")
    start = time.time()
    while time.time() - start < max_wait:
        try:
            r = requests.get(f"http://127.0.0.1:{BACKEND_PORT}/health", timeout=2)
            if r.status_code == 200:
                log("Backend is UP and healthy on port 8000.")
                return True
        except Exception:
            pass
        time.sleep(2)
    log("Backend check timed out; establishing tunnel anyway.")
    return False


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

    log(f"Fetching Vercel environment variables for project {project_id}...")
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            log(f"Failed to fetch Vercel env vars ({response.status_code}): {response.text}")
            return False

        env_vars = response.json().get("envs", [])
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


def main():
    log("=== Jarvis ngrok Tunnel Runner Starting ===")
    wait_for_network(max_wait=60)
    wait_for_backend(max_wait=120)

    auth_token = os.getenv("NGROK_AUTHTOKEN", NGROK_AUTHTOKEN)
    domain = os.getenv("NGROK_DOMAIN", NGROK_DOMAIN)

    if auth_token:
        ngrok.set_auth_token(auth_token)

    try:
        ngrok.kill()
    except Exception:
        pass

    while True:
        try:
            log("Opening ngrok Tunnel on port 8000...")
            connect_kwargs = {}
            if domain:
                connect_kwargs["domain"] = domain

            tunnel = ngrok.connect(BACKEND_PORT, "http", **connect_kwargs)
            tunnel_url = tunnel.public_url
            log(f"ngrok Tunnel is LIVE at: {tunnel_url}")

            if os.getenv("VERCEL_TOKEN", VERCEL_TOKEN):
                if update_vercel_env(tunnel_url):
                    trigger_vercel_redeploy()

            ngrok_process = ngrok.get_ngrok_process()
            proc = ngrok_process.proc if ngrok_process and hasattr(ngrok_process, "proc") else None
            
            if proc:
                proc.wait()
            else:
                while True:
                    time.sleep(10)
        except Exception as e:
            log(f"ngrok tunnel error: {e}")
            try:
                ngrok.kill()
            except Exception:
                pass
            log("Re-attempting tunnel in 30 seconds...")
            time.sleep(30)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))
    signal.signal(signal.SIGTERM, lambda s, f: sys.exit(0))
    try:
        main()
    except KeyboardInterrupt:
        ngrok.kill()
