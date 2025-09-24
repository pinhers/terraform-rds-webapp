## Terraform + Ansible: EC2 Web App with AWS RDS (PostgreSQL)

This project provisions AWS infrastructure with Terraform and configures an EC2 host with Ansible to run a Flask web app (Gunicorn) behind nginx, both as Docker containers, connected to a managed PostgreSQL RDS instance.

## Architecture
- VPC with one public subnet (EC2) and two private subnets (RDS subnet group)
- Security Groups:
  - Web SG: SSH (22) and HTTP (80) from anywhere
  - DB SG: PostgreSQL (5432) only from the Web SG
- EC2 Ubuntu 22.04 instance in the public subnet
- RDS PostgreSQL 15 in private subnets
- Ansible installs base packages, Docker, clones the app, and deploys Docker Compose with two services:
  - `webapp`: Python 3.11 slim image running `gunicorn` on port 5000
  - `nginx`: proxies port 80 → `webapp:5000`

## Prerequisites
- Terraform >= 1.5
- Ansible >= 2.14
- AWS credentials configured (env vars or shared config)
- Existing EC2 Key Pair in your region (`var.key_name`, default `KEY1`)
- Local SSH private key at `~/.ssh/KEY1.pem` with correct permissions (chmod 600)

## 1) Provision infrastructure with Terraform
```bash
terraform init
terraform apply -auto-approve
```

Important outputs:
- `ec2_public_ip` — Public IPv4 of EC2
- `rds_endpoint` — PostgreSQL endpoint
- `rds_port`, `rds_username`, `rds_password`

Export outputs for Ansible:
```bash
terraform output -json > ansible/outputs.json
```

Get the raw RDS password (sensitive) when needed:
```bash
terraform output -raw rds_password
```

## 2) Configure EC2 and deploy app with Ansible
Install collections once:
```bash
cd ansible
ansible-galaxy collection install -r requirements.yml
```

Generate dynamic inventory from Terraform outputs (writes `inventory.ini`):
```bash
ansible-playbook generate-inventory.ini
``;
This reads `outputs.json` via `inventory.ini.j2` and sets the `web` group using `ec2_public_ip`.

Run the main playbook (dry-run then apply):
```bash
ansible-playbook site.yml --check
ansible-playbook site.yml
```
What this does:
- Installs Docker and prerequisites
- Clones this repo onto the EC2 host at `{{ app_dir }}`
- Renders and starts a Docker Compose stack: `webapp` + `nginx`
- Sets the `DATABASE_URL` env for `webapp` using Terraform RDS outputs

With the provided `ansible.cfg`, `inventory.ini` is used automatically. You can also be explicit:
```bash
ansible-playbook -i inventory.ini site.yml
```

## 3) Manual database initialization and verification
You can initialize the DB from your local machine using `psql`. This is required before the app can insert records.

1. Retrieve connection details:
   - Endpoint: `terraform output rds_endpoint`
   - Port: `terraform output rds_port`
   - User: `terraform output rds_username`
   - Password: `terraform output -raw rds_password`

2. Connect to the RDS instance (to the default admin DB, often `postgres`):
```bash
psql -h <rds_endpoint> -p <rds_port> -U <db_user> -d postgres
```
Enter the password when prompted.

3. Create your application database (match `db_name` used by Ansible; default `appdb` in `ansible/vars/main.yml`):
```sql
CREATE DATABASE <db_name>;
```

4. Option A — Create tables manually in `<db_name>`:
```sql
\c <db_name>
CREATE TABLE entries (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

4. Option B — Initialize via the running web app:
- The running `webapp` container uses `DATABASE_URL` and exposes a health endpoint. You can create tables via migrations or manual SQL; for this simple app, creating the table manually (Option A) is enough.

5. Verify the application containers and health:
- SSH into EC2:
```bash
ssh -i ~/.ssh/KEY1.pem ubuntu@$(terraform output -raw ec2_public_ip)
```
- Check containers:
```bash
docker compose -f /home/ubuntu/terraform-rds-webapp/docker-compose.yml ps
docker compose -f /home/ubuntu/terraform-rds-webapp/docker-compose.yml logs --no-log-prefix -n 100
```
- Healthcheck via nginx (from your local machine):
```bash
curl -s http://$(terraform output -raw ec2_public_ip)/health | jq .
```
Expected: `{ "ok": true }`. If false, check RDS SG rules and credentials.

## Project layout (Ansible)
- `ansible/site.yml` — main playbook
- `ansible/generate-inventory.ini` — playbook to render `inventory.ini` from `outputs.json`
- `ansible/inventory.ini.j2` — inventory template (uses `ec2_public_ip`)
- `ansible/vars/main.yml` — repo URL and paths
- `ansible/ansible.cfg` — defaults (inventory, roles path, etc.)
- `ansible/requirements.yml` — collections (`community.general`, `community.docker`)
- Roles:
  - `roles/common` — base packages (git, python3, docker), stop/disable host nginx
  - `roles/webapp` — clone repo, render Docker Compose for `webapp` + `nginx`, start stack

## Troubleshooting
- Inventory generation: ensure `ansible/outputs.json` exists (`terraform output -json > ansible/outputs.json`).
- SSH errors: confirm `~/.ssh/KEY1.pem` path and permissions, and that `var.key_name` matches your key pair.
- Database connectivity: verify SG rules (web → db on 5432), `rds_endpoint`, and credentials.
- Compose not running: `docker compose -f /home/ubuntu/terraform-rds-webapp/docker-compose.yml up -d` then check logs.
- Healthcheck failing: confirm the `entries` table exists in `<db_name>`; create it manually if not.

## Next Steps
- Add nginx site config to proxy the Flask app (e.g., to a Gunicorn service) and manage it via Ansible handlers.
- Optionally containerize the app and use Docker Compose; wire nginx as a reverse proxy.
