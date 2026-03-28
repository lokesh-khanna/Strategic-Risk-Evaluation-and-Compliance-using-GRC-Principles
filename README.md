# 🛡️ PaySecure Technologies GRC Platform

> **Governance · Risk · Compliance** — Enterprise-grade GRC platform for a Fintech payment gateway startup.

---

## 📋 Business Scenario

**PaySecure Technologies Pvt. Ltd.** is a Series-B funded fintech company headquartered in Bengaluru, India.

| Attribute | Details |
|---|---|
| Industry | Payment Gateway / Fintech |
| Funding | Series-B (₹300 Cr raised) |
| Employees | ~200 |
| Transaction Volume | $50M/month (≈ ₹415 Cr) |
| Data | Customer KYC, card data, UPI credentials |
| Regulators | RBI, NPCI, GDPR (EU customers), PCI DSS Council |

### Compliance Requirements

| Framework | Scope |
|---|---|
| **PCI-DSS v4.0** | Cardholder data environment (CDE), Req 1–12 |
| **GDPR (EU) 2016/679** | EU customer PII, data subject rights |
| **ISO 27001:2022** | Information Security Management System (ISMS) |
| **RBI PA/PG Guidelines 2020** | Payment Aggregator / Payment Gateway licensing |

---

## 🚀 Quick Setup

### Prerequisites

- Python 3.9+
- MySQL 8.0+
- pip

### 1. Clone & Install

```bash
git clone <repo-url>
cd grc-platform
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure Database

Copy and edit the environment file:

```bash
cp .env.example .env
```

Edit `.env`:

```env
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DB=grc_db
SECRET_KEY=your_very_long_random_secret_key_here
```

### 3. Seed the Database

```bash
# Create DB and seed with fintech scenario data
mysql -u root -p < scripts/seed_fintech_data.sql
```

This creates:
- 6 realistic user accounts
- 23 risk scenarios
- 21 compliance controls (PCI-DSS, GDPR, ISO 27001, RBI)
- Risk-control mappings
- Sample audit trail entries

### 4. Run the Application

```bash
python run.py
```

Open: **http://localhost:5000**

---

## 👥 Demo Accounts

| Role | Username | Password | Person |
|---|---|---|---|
| **Admin / CISO** | `sarah.chen` | `SecurePass@2025!` | Sarah Chen |
| **Risk Manager** | `michael.torres` | `SecurePass@2025!` | Michael Torres (IT Risk Manager) |
| **Compliance Officer** | `priya.sharma` | `SecurePass@2025!` | Priya Sharma (GDPR Lead) |
| **Internal Auditor** | `james.wilson` | `SecurePass@2025!` | James Wilson |
| **VP Engineering** | `ravi.kumar` | `SecurePass@2025!` | Ravi Kumar |
| **Head of Payments** | `ananya.mehta` | `SecurePass@2025!` | Ananya Mehta |

---

## 🏗️ Project Structure

```
grc-platform/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── db.py                    # MySQL connection pool
│   ├── auth/
│   │   ├── routes.py            # Login / logout
│   │   └── utils.py             # RBAC decorators
│   ├── dashboard/
│   │   └── routes.py            # Live GRC metrics dashboard
│   ├── risk/
│   │   └── routes.py            # Risk CRUD, heatmap, lifecycle
│   ├── compliance/
│   │   └── routes.py            # Controls, risk-control mapping
│   ├── audit/
│   │   └── routes.py            # Audit trail + CSV export
│   └── templates/
│       ├── auth/login.html      # Premium dark login page
│       ├── dashboard/index.html # Live KPI dashboard
│       ├── risk/register.html   # Risk register + heatmap
│       ├── compliance/controls.html  # Multi-framework controls
│       └── audit/trail.html     # Immutable audit log viewer
├── config/
│   └── settings.py              # App configuration
├── scripts/
│   └── seed_fintech_data.sql    # Full database seed script
├── requirements.txt
└── README.md
```

---

## 🔐 Security Features

| Feature | Implementation |
|---|---|
| Password hashing | Flask-Bcrypt (bcrypt, cost 12) |
| Session timeout | 30 minutes (PCI-DSS Req 8.2.8) |
| Failed login lockout | After 5 attempts (PCI-DSS Req 8.3.4) |
| RBAC | Role-based access (admin, risk_manager, compliance_officer, auditor) |
| SQL injection prevention | Parameterized queries (no string formatting) |
| Session security | `HTTPONLY`, `SAMESITE=Lax` cookies |
| Audit logging | All actions logged with user, IP, timestamp |

---

## ⚠️ Risk Register Highlights (23 Risks)

| Risk Code | Risk | Level | Score |
|---|---|---|---|
| RISK-2025-001 | Unauthorized API access to payment gateway | 🔴 High | 20 |
| RISK-2025-002 | Customer PII data breach via SQL injection | 🔴 High | 20 |
| RISK-2025-003 | Ransomware attack on transaction DB | 🔴 High | 25 |
| RISK-2025-005 | GDPR non-compliance – data subject rights | 🟡 Medium | 12 |
| RISK-2025-008 | Third-party payment processor failure | 🟡 Medium | 9 |
| RISK-2025-015 | RBI PA/PG license revocation | 🟡 Medium | 8 |

---

## 📊 Compliance Dashboard

| Framework | Controls | Status |
|---|---|---|
| PCI-DSS v4.0 | 6 controls | Req 1.2, 3.3, 6.4, 8.3, 10.2, 11.3 |
| GDPR | 7 controls | Art. 5, 13, 17, 25, 32, 33, 37 |
| ISO 27001:2022 | 6 controls | A.5.1, A.5.23, A.8.2, A.8.7, A.8.24, A.8.28 |
| RBI PA/PG | 3 controls | Req 3.1, 5.2, 7.1 |

---

## 🔄 Risk Lifecycle

```
Identified → Assessed → Treatment Planned → Mitigating → Accepted → Closed
```

## 📁 Audit Log Retention

- **Retention period:** 7 years (RBI mandate)
- **Log events:** 15+ event types including `RISK_CREATED`, `RISK_CONTROL_MAPPED`, `COMPLIANCE_REPORT_EXPORTED`
- **Standards:** ISO 27001:2022 A.8.15 · PCI-DSS Requirement 10
