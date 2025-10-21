# Terraform + Ansible: Web App with AWS RDS

This project deploys a Flask web application on AWS EC2 with PostgreSQL RDS using Terraform for infrastructure and Ansible for configuration.

---

## Architecture

- **EC2 Instance:** Runs Flask app in Docker container  
- **RDS PostgreSQL:** Managed database in private subnet  
- **Nginx:** Reverse proxy in Docker container  
- **Security:** Proper security groups for SSH, HTTP, and database access  

---

## Quick Start

### 1. Provision AWS Infrastructure
```bash
terraform init
terraform apply -auto-approve
```

### 2. Deploy Application
```bash
# Export Terraform outputs
terraform output -json > ansible/outputs.json

# Generate inventory and deploy
cd ansible
ansible-playbook generate-inventory.yml
ansible-playbook -i inventory.ini site.yml
```

### 3. Setup Database
Connect to your RDS instance and create the table:
```sql
CREATE TABLE entries (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4. Test Your Application
Open in browser:  
`http://YOUR_EC2_PUBLIC_IP/`

- Fill out the contact form  
- Submit a message — it will be saved to PostgreSQL  

---

## Manual Steps

### Get Connection Details
```bash
terraform output ec2_public_ip        # Your webapp URL
terraform output rds_endpoint         # Database host
terraform output rds_username         # Database user
terraform output -raw rds_password    # Database password
```

### Test Health Check
```bash
curl http://YOUR_EC2_PUBLIC_IP/health
# Expected: {"ok": true}
```

### Check Database
```bash
psql -h YOUR_RDS_ENDPOINT -U YOUR_DB_USER -d appdb -c "SELECT * FROM entries;"
```

---

## Project Structure
```
├── terraform/           # AWS infrastructure
├── ansible/
│   ├── roles/
│   │   ├── common/      # Base packages, Docker
│   │   └── webapp/      # Flask app, nginx, containers
│   ├── site.yml         # Main playbook
│   └── vars/main.yml    # Application variables
└── webapp/
    ├── app.py           # Flask application
    └── templates/       # HTML templates
```

---

## Troubleshooting

**Application not accessible?**
- Check security groups allow HTTP (port 80)
- Verify containers are running: `docker-compose ps`

**Database connection issues?**
- Confirm RDS security group allows EC2 instance
- Check database credentials in Ansible variables

**Form not working?**
- Verify `entries` table exists in database
- Check webapp logs: `docker-compose logs webapp`

---

## Clean Up
```bash
terraform destroy -auto-approve
```

Your webapp will be available at:  
`http://YOUR_EC2_PUBLIC_IP/`  
with a simple contact form that saves data to PostgreSQL RDS!
