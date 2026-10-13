"""Read-only audit of direct runtime IAM grants; no tokens or inference requests."""
import json
import subprocess

PROJECT = "llm-2k5"
BUCKET = "llm-2k5-control-326898036708"
ACCOUNT = "franchise-runtime@llm-2k5.iam.gserviceaccount.com"
INFERENCE = "projects/llm-2k5/roles/franchiseInference"
CONTROL = "projects/llm-2k5/roles/franchiseControlReader"
EXPRESSION = 'resource.name == "projects/_/buckets/' + BUCKET + '/objects/ai-control.json"'


def read(*arguments):
    result = subprocess.run(["gcloud", *arguments, "--format=json"], check=True,
                            capture_output=True, text=True, timeout=45)
    return json.loads(result.stdout)


def main():
    inference = read("iam", "roles", "describe", "franchiseInference", "--project", PROJECT)
    control = read("iam", "roles", "describe", "franchiseControlReader", "--project", PROJECT)
    assert set(inference["includedPermissions"]) == {"aiplatform.endpoints.predict", "serviceusage.services.use"}
    assert set(control["includedPermissions"]) == {"storage.objects.get"}
    principal = "serviceAccount:" + ACCOUNT
    project_policy = read("projects", "get-iam-policy", PROJECT)
    bucket_policy = read("storage", "buckets", "get-iam-policy", "gs://" + BUCKET)
    project_grants = [binding for binding in project_policy["bindings"] if principal in binding["members"]]
    bucket_grants = [binding for binding in bucket_policy["bindings"] if principal in binding["members"]]
    assert len(project_grants) == 1 and project_grants[0]["role"] == INFERENCE
    assert "condition" not in project_grants[0]
    assert len(bucket_grants) == 1 and bucket_grants[0]["role"] == CONTROL
    assert bucket_grants[0]["condition"]["expression"] == EXPRESSION
    keys = read("iam", "service-accounts", "keys", "list", "--iam-account", ACCOUNT,
                "--project", PROJECT, "--managed-by=user")
    assert not keys, "Runtime has user-managed keys"
    print(json.dumps({"project": PROJECT, "runtime_identity": ACCOUNT,
        "direct_inference_permissions": sorted(inference["includedPermissions"]),
        "control_read_permission": "storage.objects.get", "control_condition": EXPRESSION,
        "direct_switch_write_grants": False, "user_managed_keys": 0,
        "scope": "Direct project/bucket grants; inherited organization/folder policies not evaluated"}, indent=2))


if __name__ == "__main__":
    main()
