import shutil, tempfile
from pathlib import Path
from datetime import datetime

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
CREDENTIALS = Path(__file__).resolve().parent.parent / "credentials.json"
TOKEN = Path(__file__).resolve().parent.parent / "token.json"

def _zip_folder(root: Path) -> Path:
    root = Path(root)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = Path(tempfile.gettempdir()) / f"backup_{stamp}.zip"
    with tempfile.TemporaryDirectory() as tmp:
        stage = Path(tmp) / "backup"
        shutil.copytree(root, stage, ignore=shutil.ignore_patterns("*.log"))
        shutil.make_archive(str(out.with_suffix("")), "zip", stage)
    return out

def backup_to_drive(data_dir: Path) -> str:
    """Uploads a zip of data_dir. If credentials missing, returns local path."""
    zip_path = _zip_folder(data_dir)
    if not CREDENTIALS.exists():
        return f"LOCAL-ONLY (no credentials.json): {zip_path}"
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    creds = None
    if TOKEN.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN), SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS), SCOPES)
        creds = flow.run_local_server(port=0)
        TOKEN.write_text(creds.to_json())
    svc = build("drive", "v3", credentials=creds)
    media = MediaFileUpload(str(zip_path), mimetype="application/zip", resumable=True)
    f = svc.files().create(body={"name": zip_path.name}, media_body=media,
                           fields="id, webViewLink").execute()
    zip_path.unlink(missing_ok=True)
    return f.get("webViewLink", f["id"])