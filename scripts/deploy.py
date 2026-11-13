#!/usr/bin/env python3
"""Deploy the IVA calculator.

The app has no runtime secrets. The only Vault lookup is an optional GHCR
read token, so a private package can be pulled without leaving credentials
on disk. Passwords are never written to a file.

    ./scripts/deploy.py up -d                  # pull and start
    ./scripts/deploy.py up -d --tag sha-abc1234
    ./scripts/deploy.py up -d --build          # build on the VM instead
    ./scripts/deploy.py logs -f app
    ./scripts/deploy.py ps

Requires, when pulling a private image:
    OCI_VAULT_OCID
    OCI_COMPARTMENT_ID
and an ACTIVE secret named iva-ghcr-token.
A public GHCR package needs neither.
"""

from __future__ import annotations

import argparse
import base64
import os
import subprocess
import sys

GHCR_TOKEN_SECRET = "iva-ghcr-token"
GHCR_REGISTRY = "ghcr.io"
GHCR_USERNAME = "e-motta"
COMPOSE_FILES = ["-f", "docker-compose.yml", "-f", "docker-compose.production.yml"]


def fetch_ghcr_token() -> str | None:
    vault_ocid = os.environ.get("OCI_VAULT_OCID")
    compartment_id = os.environ.get("OCI_COMPARTMENT_ID")
    if not vault_ocid or not compartment_id:
        print(
            "OCI_VAULT_OCID or OCI_COMPARTMENT_ID is unset; skipping registry login.",
            file=sys.stderr,
        )
        return None
    try:
        from oci.auth.signers import InstancePrincipalsSecurityTokenSigner
        from oci.secrets import SecretsClient
        from oci.vault import VaultsClient
    except ImportError:
        print("OCI SDK is not installed; skipping registry login.", file=sys.stderr)
        return None

    print("Authenticating with OCI instance principal...", file=sys.stderr)
    try:
        signer = InstancePrincipalsSecurityTokenSigner()
    except Exception as exc:
        print(f"Instance principal auth failed: {exc}", file=sys.stderr)
        return None

    secrets_client = SecretsClient(config={}, signer=signer)
    vault_client = VaultsClient(config={}, signer=signer)
    try:
        found = vault_client.list_secrets(
            compartment_id=compartment_id,
            vault_id=vault_ocid,
            name=GHCR_TOKEN_SECRET,
            lifecycle_state="ACTIVE",
        ).data
        if not found:
            print("  GHCR token: not found (will try a public pull)", file=sys.stderr)
            return None
        bundle = secrets_client.get_secret_bundle(secret_id=found[0].id).data
        content = bundle.secret_bundle_content
        if content.content_type == "BASE64":
            token = base64.b64decode(content.content).decode("utf-8")
        else:
            token = content.content
    except Exception as exc:
        print(f"  GHCR token: failed ({exc})", file=sys.stderr)
        return None
    print("  GHCR token: loaded", file=sys.stderr)
    return token


def docker_login(token: str) -> bool:
    print(f"Logging in to {GHCR_REGISTRY}...", file=sys.stderr)
    result = subprocess.run(
        ["docker", "login", GHCR_REGISTRY, "-u", GHCR_USERNAME, "--password-stdin"],
        input=token.encode(),
        capture_output=True,
    )
    if result.returncode != 0:
        print(f"WARNING: GHCR login failed: {result.stderr.decode()}", file=sys.stderr)
        return False
    print(f"  Logged in to {GHCR_REGISTRY}", file=sys.stderr)
    return True


def docker_logout() -> None:
    print(f"Logging out from {GHCR_REGISTRY}...", file=sys.stderr)
    subprocess.run(["docker", "logout", GHCR_REGISTRY], capture_output=True)


def parse_args() -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(
        description="Deploy the IVA calculator", add_help=False
    )
    parser.add_argument("--tag", default="latest", help="Image tag (default: latest)")
    parser.add_argument(
        "--build", action="store_true", help="Build locally instead of pulling"
    )
    return parser.parse_known_args()


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    args, docker_args = parse_args()
    needs_pull = not args.build and any(
        cmd in docker_args for cmd in ("up", "pull", "create")
    )

    env = os.environ.copy()
    env["APP_IMAGE_TAG"] = args.tag

    logged_in = False
    if needs_pull:
        token = fetch_ghcr_token()
        if token:
            logged_in = docker_login(token)

    try:
        if needs_pull and "up" in docker_args:
            pull = ["docker", "compose", *COMPOSE_FILES, "pull", "app"]
            print(f"\nPulling image (tag: {args.tag})...", file=sys.stderr)
            print(f"Running: {' '.join(pull)}", file=sys.stderr)
            pulled = subprocess.run(pull, env=env)
            if pulled.returncode != 0:
                print("ERROR: Failed to pull image", file=sys.stderr)
                sys.exit(pulled.returncode)

        command = ["docker", "compose", *COMPOSE_FILES, *docker_args]
        if args.build and "up" in docker_args and "--build" not in docker_args:
            command.append("--build")
        print(f"\nRunning: {' '.join(command)}", file=sys.stderr)
        result = subprocess.run(command, env=env)
    finally:
        if logged_in:
            docker_logout()
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
