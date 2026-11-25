FEATURES = {
    "parcels": ("Parcels", "Log and track parcels"),
    "backup":  ("Google Drive Backup", "Back up DB, photos, passes, reports"),
}
ADMIN_CODE = "CHANGE_ME_MENTOR"  
def allowed_features(license_payload):
    return [f for f in license_payload.get("features", []) if f in FEATURES]

def bootstrap_features(db, license_payload, chosen: list[str] | None = None):
    if db.get_features():
        return
    allowed = allowed_features(license_payload)
    chosen = chosen if chosen is not None else allowed
    for key in allowed:
        name, desc = FEATURES[key]
        db.set_feature(key, name, key in chosen, desc)