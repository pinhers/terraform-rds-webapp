## Terraform + Ansible: EC2 Web App with AWS RDS (PostgreSQL)

This project provisions AWS infrastructure with Terraform and configures the EC2 instance with Ansible to run a Flask web app that connects to a managed PostgreSQL RDS instance.

## Architecture
- VPC with one public subnet (EC2) and two private subnets (RDS subnet group)
- Security Groups:
  - Web SG: SSH (22) and HTTP (80) from anywhere
  - DB SG: PostgreSQL (5432) only from the Web SG
- EC2 Ubuntu 22.04 instance in the public subnet
- RDS PostgreSQL 15 in private subnets
- Ansible installs base packages, nginx, Docker, Python venv, clones the app, and installs Python deps

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
With the provided `ansible.cfg`, `inventory.ini` is used automatically. You can also be explicit:
```bash
ansible-playbook -i inventory.ini site.yml
```

## 3) Initialize the PostgreSQL database (manual)
You can initialize the DB from your local machine using `psql`.

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

3. Create your application database:
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

4. Option B — Initialize via the Flask app using SQLAlchemy:
- SSH into EC2: `ssh -i ~/.ssh/KEY1.pem ubuntu@$(terraform output -raw ec2_public_ip)`
- Activate venv and run initialization:
```bash
source ~/venv/bin/activate
cd ~/terraform-rds-webapp/
python3
```
In the Python shell:
```python
from app import db, app
with app.app_context():
    db.create_all()
```
Then `exit()` the Python shell.

## Project layout (Ansible)
- `ansible/site.yml` — main playbook
- `ansible/generate-inventory.ini` — playbook to render `inventory.ini` from `outputs.json`
- `ansible/inventory.ini.j2` — inventory template (uses `ec2_public_ip`)
- `ansible/vars/main.yml` — repo URL and paths
- `ansible/ansible.cfg` — defaults (inventory, roles path, etc.)
- `ansible/requirements.yml` — collections (`community.general`, `community.docker`)
- Roles:
  - `roles/common` — base packages (git, python3, nginx, docker), services, handlers
  - `roles/webapp` — clone repo, create venv, install pip packages

## Troubleshooting
- Inventory generation: ensure `ansible/outputs.json` exists (`terraform output -json > ansible/outputs.json`).
- SSH errors: confirm `~/.ssh/KEY1.pem` path and permissions, and that `var.key_name` matches your key pair.
- Database connectivity: verify SG rules (web → db on 5432), `rds_endpoint`, and credentials.

## Next Steps
- Add nginx site config to proxy the Flask app (e.g., to a Gunicorn service) and manage it via Ansible handlers.
- Optionally containerize the app and use Docker Compose; wire nginx as a reverse proxy.
