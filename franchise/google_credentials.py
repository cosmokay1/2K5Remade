"""Explicit short-lived service-account impersonation; no keys or fallback."""


def runtime_credentials(project: str, principal: str):
    if (type(project) is not str or not project.strip() or type(principal) is not str
            or not principal.endswith("@" + project + ".iam.gserviceaccount.com")):
        raise ValueError("Runtime service account must belong to the configured project")
    try:
        import google.auth
        from google.auth import impersonated_credentials
        scopes = ["https://www.googleapis.com/auth/cloud-platform"]
        source, _ = google.auth.default(scopes=scopes)
        return impersonated_credentials.Credentials(source_credentials=source,
            target_principal=principal, target_scopes=scopes, lifetime=900,
            quota_project_id=project)
    except Exception:
        raise RuntimeError("Runtime impersonation unavailable; check ADC and target-account permission") from None
