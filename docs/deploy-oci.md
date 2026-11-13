# Deploying the IVA calculator on the existing OCI VM

The finance app at `https://finance.eduardomotta.dev` already runs on this VM: Docker Compose, Caddy on ports 80 and 443, secrets from OCI Vault, and a GitHub Actions deploy over a forced SSH command. This app is a second service on that same machine. It does not replace Caddy, Postgres, or the finance containers.

Public URL: `https://iva.eduardomotta.dev`. The UI and the API are the same origin.

Do the steps below once, on the VM and in DNS and GitHub. Nothing here changes the finance repository. A finance deploy does check its own Caddyfile back out, so the last step is a small reattach script that puts the IVA site back.

## What gets installed

```
Internet :443
    │
    ▼
finance Caddy  ──── finance.eduardomotta.dev ──► finance app
    │
    └── network "edge" ── iva.eduardomotta.dev ──► iva-app:8000
                                                      │
                                              ghcr.io/e-motta/tax-reform-calc
```

`iva-app` publishes nothing except `127.0.0.1:8000` on the host, for debugging. TLS stays on the existing Caddy.

## 1. Squarespace DNS

The VM already has a public IPv4 (the same address `finance` uses). Add one record. Do not change the finance record.

| Type | Host | Value | TTL |
|------|------|-------|-----|
| A | `iva` | the VM's public IPv4 | 1 hour |

If the VM has a public IPv6 and finance has an AAAA record, add the same AAAA for `iva`.

Check, from anywhere:

```bash
dig +short iva.eduardomotta.dev
```

The address must match `dig +short finance.eduardomotta.dev`.

## 2. GitHub secrets for this repository

Use a **new** deploy key. The finance key is pinned to `/opt/portfolio-manager-v2/scripts/remote-deploy.sh`. Reusing it would deploy the finance app, or fail the forced command.

On your machine:

```bash
ssh-keygen -t ed25519 -C "github-deploy@iva" -f ~/.ssh/iva_deploy_ed25519 -N ""
```

In this repository: **Settings → Environments → New environment**, name `production`. Limit the deployment branches to `main`.

Then **Settings → Secrets and variables → Actions → Repository secrets** (or environment secrets on `production`):

| Secret | Value |
|--------|-------|
| `DEPLOY_SSH_KEY` | contents of `~/.ssh/iva_deploy_ed25519`, including the BEGIN and END lines |
| `DEPLOY_KNOWN_HOSTS` | one line from `ssh-keyscan -t ed25519 <VM public IP>` |
| `DEPLOY_HOST` | the VM public IP, or `finance.eduardomotta.dev` |
| `DEPLOY_USER` | the user that already owns the finance checkout, usually `ubuntu` |

Confirm the host key before saving it:

```bash
ssh-keyscan -t ed25519 <VM-IP> 2>/dev/null | ssh-keygen -lf -
```

That fingerprint must match `ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub` run on the VM.

The package is pushed to GHCR by the workflow in `.github/workflows/build-and-push.yml`. The workflow grants `packages: write`. If the package stays private, step 4 creates a read token for the VM. A public package needs no token.

## 3. VM: checkout, network, deploy env

SSH in with your normal admin key (not the new forced-command key).

```bash
sudo mkdir -p /opt/tax-reform-calc /opt/caddy /etc/iva
sudo chown ubuntu:ubuntu /opt/tax-reform-calc /opt/caddy

git clone https://github.com/e-motta/tax-reform-calc.git /opt/tax-reform-calc
chmod +x /opt/tax-reform-calc/scripts/remote-deploy.sh \
         /opt/tax-reform-calc/scripts/deploy.py \
         /opt/tax-reform-calc/scripts/reattach-iva.sh

cp /opt/tax-reform-calc/deploy/caddy/iva-site.caddy /opt/caddy/iva-site.caddy
cp /opt/tax-reform-calc/scripts/reattach-iva.sh /opt/caddy/reattach-iva.sh
chmod +x /opt/caddy/reattach-iva.sh

docker network create edge
```

`/etc/iva/deploy.env` holds OCIDs, not secret values. Copy the two OCIDs already used by the finance app (`OCI_VAULT_OCID` and `OCI_COMPARTMENT_ID` in `/etc/portfolio/deploy.env`):

```bash
sudo tee /etc/iva/deploy.env >/dev/null << 'EOF'
OCI_VAULT_OCID="ocid1.vault.oc1...."
OCI_COMPARTMENT_ID="ocid1.compartment.oc1...."
EOF
sudo chmod 644 /etc/iva/deploy.env
```

`scripts/remote-deploy.sh` runs with `/opt/portfolio-venv/bin/python`, the virtualenv the finance app already uses for the OCI SDK. It only imports `oci` when a GHCR token is needed. To point at a different interpreter, add `IVA_VENV_PYTHON=/opt/iva-venv/bin/python` to `deploy.env`. Do not reinstall packages into the finance virtualenv.

## 4. GHCR read token, only if the package is private

The finance token was minted for `e-motta/portfolio-manager-v2` and will not read this package.

1. GitHub → Settings → Developer settings → Fine-grained tokens.
2. Repository access: only `e-motta/tax-reform-calc`. Permission: Packages, read.
3. OCI Vault (the vault in `OCI_VAULT_OCID`) → Create secret.
   - Name: `iva-ghcr-token`
   - Contents: the token.

The instance principal that already reads the finance secrets can read this one. No new dynamic group is required if that group matches the same instance.

`scripts/deploy.py` logs in for the pull and logs out afterwards, same as the finance deploy. The token is not written to disk.

## 5. Forced command

Append a new line to `/home/ubuntu/.ssh/authorized_keys`. Do not edit the finance line.

```
restrict,command="/opt/tax-reform-calc/scripts/remote-deploy.sh" ssh-ed25519 AAAA... github-deploy@iva
```

`restrict` turns off forwarding, a PTY, and everything except the command. The command ignores whatever else the client asked to run and reads the image tag from `SSH_ORIGINAL_COMMAND`.

From your machine, this should fail with `Invalid tag format`, which means the key and the forced command are in place:

```bash
ssh -i ~/.ssh/iva_deploy_ed25519 -o StrictHostKeyChecking=yes ubuntu@<VM-IP> "sha-0000000"
```

## 6. Caddy: attach the site, without a second listener

Caddy in the finance stack is the only process on 80 and 443. This repo's `Caddyfile` is the site block. It is also stored at `deploy/caddy/iva-site.caddy`.

Run the reattach script once DNS from step 1 answers:

```bash
/opt/caddy/reattach-iva.sh
```

The script:

1. Creates the Docker network `edge` if it is missing.
2. Appends the site block to `/opt/portfolio-manager-v2/Caddyfile` when `iva.eduardomotta.dev` is not already in it. It does not rewrite the finance site.
3. Connects the running finance Caddy container to `edge`.
4. Runs `caddy reload` inside that container.

Install the timer so a later finance deploy, which checks that Caddyfile out again and recreates Caddy, does not drop the site:

```bash
sudo cp /opt/tax-reform-calc/deploy/caddy/iva-reattach.service /etc/systemd/system/
sudo cp /opt/tax-reform-calc/deploy/caddy/iva-reattach.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now iva-reattach.timer
```

The timer runs as `ubuntu` two minutes after each run. The finance health check does not depend on this file, so a finance deploy still completes on its own. There can be a short gap where `iva.eduardomotta.dev` 404s until the timer rewrites the block. Finance is unaffected.

Caddy will ask Let's Encrypt for a certificate on the first request to the new name. Port 80 must stay open, which it already is.

## 7. First deploy

Wait until the GitHub workflow on `main` has pushed an image, or push to `main` after the secrets exist. The workflow SSHs the tag `sha-<7 hex chars>`. The forced command checks the commit out, pulls `ghcr.io/e-motta/tax-reform-calc:sha-...`, and curls:

```bash
curl -sf --resolve iva.eduardomotta.dev:443:127.0.0.1 https://iva.eduardomotta.dev/api/health
```

A failed health check rolls the previous image back. There is no database, so there is nothing to migrate.

Manual equivalent, on the VM:

```bash
cd /opt/tax-reform-calc
set -a; source /etc/iva/deploy.env; set +a
./scripts/deploy.py up -d --tag sha-<7 hex chars>
```

Rollback:

```bash
./scripts/deploy.py up -d --tag sha-<previous>
```

Logs from this stack only:

```bash
./scripts/deploy.py logs -f iva
tail -f /opt/tax-reform-calc/deploy-history.log
```

## 8. What this must not touch

- Do not change `/opt/portfolio-manager-v2/scripts/remote-deploy.sh` or the finance `authorized_keys` line.
- Do not publish Postgres, and do not add a second Caddy on 80 or 443.
- Do not put the IVA site block in a commit on the finance repository from this app. The reattach script is the seam.
- The finance Caddyfile's own site block stays the one that repository ships. The script only appends, and only when the marker is absent.
- **Do not use generic service names on the shared `edge` network.** The compose service must be named `iva`, not `app`. Docker Compose automatically adds a DNS alias for the service name on every network the container joins. A generic name like `app` would shadow other projects' containers. The deploy script checks for this and rolls back if it detects a collision. If renaming the service, remember to update `deploy.py`, `remote-deploy.sh`, and the docs.

## Local compose is a different file

`docker compose up --build` on a laptop uses `docker-compose.yml` only and serves `http://127.0.0.1:8000`. It does not need Vault, DNS, or the `edge` network. Production is `docker-compose.yml` plus `docker-compose.production.yml`, which is what `deploy.py` runs.
