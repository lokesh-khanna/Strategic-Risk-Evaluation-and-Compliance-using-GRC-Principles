"""
Fix login: Re-seeds the GRC database with PaySecure Technologies fintech data.
Run with: python scripts/reset_and_seed.py
"""
import mysql.connector, os, sys
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host':     os.getenv('MYSQL_HOST', 'localhost'),
    'user':     os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
}
DB_NAME = os.getenv('MYSQL_DB', 'grc_db')

print("=" * 60)
print("PaySecure GRC Platform – Database Reset & Seed")
print("=" * 60)

# ── Bcrypt hashes ──────────────────────────────────────────────────────────
# Pre-generated bcrypt hashes for 'SecurePass@2025!'
# Generated with: bcrypt.hashpw(b'SecurePass@2025!', bcrypt.gensalt(rounds=12))
# We generate them fresh at runtime so they're always correct.
try:
    import bcrypt
except ImportError:
    print("ERROR: bcrypt not installed. Run: pip install Flask-Bcrypt")
    sys.exit(1)

PASSWORD = b'SecurePass@2025!'
print(f"\nGenerating bcrypt hashes for password: SecurePass@2025!")

def make_hash():
    return bcrypt.hashpw(PASSWORD, bcrypt.gensalt(12)).decode()

hashes = {
    'sarah.chen':    make_hash(),
    'michael.torres': make_hash(),
    'priya.sharma':  make_hash(),
    'james.wilson':  make_hash(),
    'ravi.kumar':    make_hash(),
    'ananya.mehta':  make_hash(),
}
print("✅ Hashes generated")

# ── Connect ────────────────────────────────────────────────────────────────
print(f"\nConnecting to MySQL at {DB_CONFIG['host']}...")
conn = mysql.connector.connect(**DB_CONFIG)
cur  = conn.cursor()

# ── Drop & recreate DB ─────────────────────────────────────────────────────
print(f"Dropping and recreating database '{DB_NAME}'...")
cur.execute(f"DROP DATABASE IF EXISTS `{DB_NAME}`")
cur.execute(f"CREATE DATABASE `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
cur.execute(f"USE `{DB_NAME}`")
conn.commit()
print("✅ Database reset")

# ── Schema ─────────────────────────────────────────────────────────────────
print("\nCreating schema...")
schema_sql = """
CREATE TABLE roles (
    role_id     INT AUTO_INCREMENT PRIMARY KEY,
    role_name   VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE users (
    user_id             INT AUTO_INCREMENT PRIMARY KEY,
    username            VARCHAR(50)  NOT NULL UNIQUE,
    email               VARCHAR(100) NOT NULL UNIQUE,
    password_hash       VARCHAR(255) NOT NULL,
    full_name           VARCHAR(100) NOT NULL,
    job_title           VARCHAR(100),
    department          VARCHAR(100),
    phone               VARCHAR(20),
    is_active           BOOLEAN DEFAULT TRUE,
    failed_login_count  INT DEFAULT 0,
    account_locked      BOOLEAN DEFAULT FALSE,
    last_login          TIMESTAMP NULL,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE user_roles (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT NOT NULL,
    role_id    INT NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_role (user_id, role_id)
);

CREATE TABLE risk_categories (
    category_id     INT AUTO_INCREMENT PRIMARY KEY,
    category_name   VARCHAR(100) NOT NULL,
    nist_csf_domain VARCHAR(50),
    description     TEXT,
    color_code      VARCHAR(10) DEFAULT '#6366f1',
    is_active       BOOLEAN DEFAULT TRUE
);

CREATE TABLE risks (
    risk_id         INT AUTO_INCREMENT PRIMARY KEY,
    risk_code       VARCHAR(20)  NOT NULL UNIQUE,
    risk_title      VARCHAR(255) NOT NULL,
    risk_description TEXT,
    category_id     INT NOT NULL,
    risk_owner_id   INT NOT NULL,
    probability     INT NOT NULL CHECK (probability BETWEEN 1 AND 5),
    impact          INT NOT NULL CHECK (impact BETWEEN 1 AND 5),
    risk_score      INT GENERATED ALWAYS AS (probability * impact) STORED,
    risk_level      VARCHAR(10) GENERATED ALWAYS AS (
                        CASE
                            WHEN (probability * impact) >= 16 THEN 'High'
                            WHEN (probability * impact) >= 6  THEN 'Medium'
                            ELSE 'Low'
                        END
                    ) STORED,
    status          VARCHAR(30) DEFAULT 'Identified',
    treatment_type  VARCHAR(20) DEFAULT 'Mitigate',
    mitigation_plan TEXT,
    business_impact TEXT,
    review_date     DATE,
    created_by      INT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id)   REFERENCES risk_categories(category_id),
    FOREIGN KEY (risk_owner_id) REFERENCES users(user_id),
    FOREIGN KEY (created_by)    REFERENCES users(user_id)
);

CREATE TABLE compliance_controls (
    control_id              INT AUTO_INCREMENT PRIMARY KEY,
    control_code            VARCHAR(50) NOT NULL,
    control_name            VARCHAR(255) NOT NULL,
    control_description     TEXT,
    regulation              VARCHAR(100) NOT NULL,
    control_category        VARCHAR(100),
    implementation_status   VARCHAR(30) DEFAULT 'Not Started',
    last_tested             DATE,
    next_review             DATE,
    evidence_location       VARCHAR(255),
    is_mandatory            BOOLEAN DEFAULT TRUE,
    is_active               BOOLEAN DEFAULT TRUE,
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE risk_compliance_mapping (
    mapping_id   INT AUTO_INCREMENT PRIMARY KEY,
    risk_id      INT NOT NULL,
    control_id   INT NOT NULL,
    mapping_type VARCHAR(30) DEFAULT 'Mitigating',
    mapped_by    INT,
    mapped_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (risk_id)    REFERENCES risks(risk_id) ON DELETE CASCADE,
    FOREIGN KEY (control_id) REFERENCES compliance_controls(control_id) ON DELETE CASCADE,
    FOREIGN KEY (mapped_by)  REFERENCES users(user_id),
    UNIQUE KEY unique_mapping (risk_id, control_id)
);

CREATE TABLE audit_logs (
    log_id      INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT,
    action      VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id   INT,
    details     TEXT,
    ip_address  VARCHAR(45),
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user   (user_id),
    INDEX idx_action (action),
    INDEX idx_time   (created_at)
);
"""
for stmt in schema_sql.strip().split(';'):
    stmt = stmt.strip()
    if stmt:
        cur.execute(stmt)
conn.commit()
print("✅ Schema created")

# ── Roles ──────────────────────────────────────────────────────────────────
print("\nInserting roles...")
cur.executemany(
    "INSERT INTO roles (role_name, description) VALUES (%s, %s)",
    [
        ('admin',               'System Administrator – full access'),
        ('risk_manager',        'IT Risk Manager – risk CRUD and lifecycle'),
        ('compliance_officer',  'Compliance Officer – controls and mapping'),
        ('auditor',             'Internal Auditor – read-only audit trail'),
    ]
)
conn.commit()

# ── Users ──────────────────────────────────────────────────────────────────
print("Inserting users...")
cur.executemany(
    """INSERT INTO users
       (username, email, password_hash, full_name, job_title, department, is_active)
       VALUES (%s,%s,%s,%s,%s,%s,TRUE)""",
    [
        ('sarah.chen',    'sarah.chen@paysecure.io',    hashes['sarah.chen'],
         'Sarah Chen',    'Chief Information Security Officer (CISO)', 'Information Security'),
        ('michael.torres','michael.torres@paysecure.io',hashes['michael.torres'],
         'Michael Torres','IT Risk Manager',                           'Risk & Compliance'),
        ('priya.sharma',  'priya.sharma@paysecure.io',  hashes['priya.sharma'],
         'Priya Sharma',  'GDPR Compliance Lead',                      'Risk & Compliance'),
        ('james.wilson',  'james.wilson@paysecure.io',  hashes['james.wilson'],
         'James Wilson',  'Internal Auditor',                          'Internal Audit'),
        ('ravi.kumar',    'ravi.kumar@paysecure.io',    hashes['ravi.kumar'],
         'Ravi Kumar',    'VP Engineering',                            'Engineering'),
        ('ananya.mehta',  'ananya.mehta@paysecure.io',  hashes['ananya.mehta'],
         'Ananya Mehta',  'Head of Payment Operations',               'Payment Operations'),
    ]
)
conn.commit()

# ── Role assignments ───────────────────────────────────────────────────────
cur.execute("SELECT user_id, username FROM users")
user_map = {r[1]: r[0] for r in cur.fetchall()}
cur.execute("SELECT role_id, role_name FROM roles")
role_map = {r[1]: r[0] for r in cur.fetchall()}

cur.executemany(
    "INSERT INTO user_roles (user_id, role_id) VALUES (%s, %s)",
    [
        (user_map['sarah.chen'],     role_map['admin']),
        (user_map['sarah.chen'],     role_map['risk_manager']),
        (user_map['michael.torres'], role_map['risk_manager']),
        (user_map['priya.sharma'],   role_map['compliance_officer']),
        (user_map['james.wilson'],   role_map['auditor']),
    ]
)
conn.commit()
print("✅ Users + roles inserted")

# ── Risk Categories ────────────────────────────────────────────────────────
print("Inserting risk categories...")
cur.executemany(
    "INSERT INTO risk_categories (category_name, nist_csf_domain, description) VALUES (%s,%s,%s)",
    [
        ('Cybersecurity & Data Protection', 'Protect',  'API security, encryption, access control for payment systems'),
        ('Regulatory & Compliance',         'Identify', 'PCI-DSS, GDPR, RBI PA/PG and ISO 27001 compliance obligations'),
        ('Third-Party & Vendor Risk',       'Identify', 'Payment processors, cloud providers, KYC/KYB vendors'),
        ('Operational Risk',                'Respond',  'System availability, incident response, BCP/DR'),
        ('Financial & Fraud Risk',          'Detect',   'Transaction fraud, chargeback abuse, money laundering'),
        ('Technology & Infrastructure',     'Protect',  'Cloud infrastructure, network security, vulnerability management'),
    ]
)
conn.commit()
cur.execute("SELECT category_id, category_name FROM risk_categories")
cat_map = {r[1]: r[0] for r in cur.fetchall()}
uid = user_map['sarah.chen']

# ── Risks ──────────────────────────────────────────────────────────────────
print("Inserting 23 risks...")
risks = [
    # (code, title, desc, cat_key, owner, prob, impact, status, treatment, mitigation, business_impact)
    ('RISK-2025-001','Unauthorized API access to payment gateway',
     'Threat actors exploiting misconfigured REST API endpoints to inject fraudulent transactions or exfiltrate cardholder data. Attack vectors include broken object-level authorization (OWASP API Top-10 #1) and JWT token forgery.',
     'Cybersecurity & Data Protection','michael.torres',4,5,'Mitigating','Mitigate',
     'Deploy API gateway with OAuth 2.0 / mTLS; enforce rate limiting 1000 req/min; implement OWASP API Security Top-10 checklist; quarterly pen-test.',
     'Potential GDPR fine up to €20M or 4% global turnover; RBI enforcement action; estimated ₹50Cr transaction fraud exposure.'),

    ('RISK-2025-002','Customer PII data breach via SQL injection',
     'Unparameterized SQL queries in legacy onboarding microservice allow attackers to extract KYC data including Aadhaar numbers, PAN cards, and bank account details for all 150,000+ customers.',
     'Cybersecurity & Data Protection','michael.torres',4,5,'Mitigating','Mitigate',
     'Migrate to ORM (SQLAlchemy); deploy DAST scanning in CI/CD pipeline; implement WAF rule set for SQLi; complete SAST review by 2025-06-30.',
     'GDPR Art. 83 fine up to €20M; mandatory RBI breach reporting within 6 hours; severe brand damage; potential class-action litigation.'),

    ('RISK-2025-003','Ransomware attack on transaction database',
     'Ransomware encrypting primary MySQL transaction database and backups, causing complete payment processing outage. Risk vector: phishing email targeting operations team with privilege escalation to DB server.',
     'Cybersecurity & Data Protection','ravi.kumar',5,5,'Treatment Planned','Mitigate',
     'Implement immutable S3 backup with 30-day retention; segment DB network; deploy EDR on all endpoints; conduct tabletop ransomware exercise Q2 2025.',
     'Complete payment processing outage; estimated ₹2Cr/hour revenue loss; RBI PA/PG license suspension risk; reputational damage to merchants.'),

    ('RISK-2025-004','PCI-DSS non-compliance during annual QSA audit',
     'Failure to meet PCI-DSS v4.0 requirements during annual Qualified Security Assessor audit, specifically Req 6.4 (software development) and Req 11.3 (penetration testing), risking merchant acquiring bank relationships.',
     'Regulatory & Compliance','priya.sharma',3,5,'Assessed','Mitigate',
     'Engage QSA for pre-assessment gap analysis; remediate Req 6.4 dev controls; complete penetration test by 2025-05-15; implement compliance calendar.',
     'Loss of card brand participation (Visa/Mastercard); merchant acquiring bank termination; business model collapse; ₹25Cr annual payment volume at risk.'),

    ('RISK-2025-005','GDPR non-compliance – data subject rights violation',
     'Failure to respond to GDPR Art. 17 Right to Erasure (Right to be Forgotten) requests within 30-day deadline due to data scattered across 12 microservices with no unified deletion workflow.',
     'Regulatory & Compliance','priya.sharma',3,4,'Mitigating','Mitigate',
     'Build unified data deletion API across all microservices; appoint DPO (Priya Sharma); implement DSR tracking system; GDPR training for all staff by 2025-Q2.',
     'GDPR Art. 83 supervisory authority fine up to €10M; negative press coverage in EU markets; loss of EU merchant partnerships worth ₹8Cr annually.'),

    ('RISK-2025-006','RBI PA/PG license non-renewal due to governance gaps',
     'Reserve Bank of India may decline to renew Payment Aggregator license due to unresolved governance deficiencies including inadequate board-level risk oversight and missing Information Security Policy documentation.',
     'Regulatory & Compliance','sarah.chen',2,5,'Identified','Mitigate',
     'Constitute Board Risk Committee; complete IS Policy documentation; engage RBI-registered external auditor; submit compliance evidence by 2025-09-30.',
     'Complete business shutdown; ₹50Cr investment write-off; dissolution of 200 merchant relationships; Series-C funding round collapse.'),

    ('RISK-2025-007','Third-party payment processor (Razorpay) outage',
     'Dependency on single payment processor causing service unavailability. Razorpay SLA is 99.9% (8.7 hrs downtime/year) but extended outages during peak shopping seasons (Diwali, sale events) exceed tolerance.',
     'Third-Party & Vendor Risk','ananya.mehta',3,4,'Mitigating','Mitigate',
     'Integrate secondary processor (PayU/CCAvenue) with automatic failover; implement circuit-breaker pattern; negotiate enhanced SLA with penalty clauses.',
     'During peak sales: ₹1Cr/hour transaction loss; merchant SLA breaches; chargeback liability; customer trust erosion.'),

    ('RISK-2025-008','KYC vendor data leak – Aadhaar/PAN exposure',
     'Third-party KYC vendor (DigiLocker integration) suffers data breach exposing customer Aadhaar numbers and PAN details stored in vendor system, including retroactive access to PaySecure customer records.',
     'Third-Party & Vendor Risk','michael.torres',2,5,'Assessed','Transfer',
     'Mandate annual SOC 2 Type II from all KYC vendors; include breach liability clauses in contracts (min ₹5Cr coverage); implement vendor security scoring.',
     'GDPR and IT Act Section 43A liability; UIDAI enforcement action; RBI data localisation violation; estimated legal cost ₹3Cr+.'),

    ('RISK-2025-009','Cloud infrastructure misconfiguration (AWS S3 public bucket)',
     'AWS S3 bucket containing merchant settlement reports and transaction logs misconfigured as public, exposing sensitive financial data. Previously occurred at competitor (similar fintech exposed 7M records in 2024).',
     'Technology & Infrastructure','ravi.kumar',3,4,'Mitigating','Mitigate',
     'Deploy AWS Config rules for bucket public-access enforcement; enable S3 Block Public Access organization-wide; implement CloudTrail + Security Hub alerts.',
     'PCI-DSS Req 1.3 violation; merchant financial data exposure; potential regulatory fines; estimated forensic cost ₹50L.'),

    ('RISK-2025-010','Insider threat – DBA privilege abuse',
     'Database administrator with unrestricted access to production MySQL (cardholder data) potentially accessing or exfiltrating payment card data or manipulating transaction records for financial gain.',
     'Cybersecurity & Data Protection','sarah.chen',2,5,'Treatment Planned','Mitigate',
     'Implement privileged access management (PAM) solution; enable database activity monitoring (DAM); enforce dual-control for production DB access; quarterly access review.',
     'PCI-DSS Req 7/8 violation; cardholder data breach; brand destruction; potential criminal liability for DBA and executives.'),

    ('RISK-2025-011','DDoS attack causing payment processing downtime',
     'Volumetric DDoS attack (UDP flood >100 Gbps) overwhelming payment gateway servers during high-value sale event, causing complete service unavailability and triggering merchant SLA liability.',
     'Technology & Infrastructure','ravi.kumar',3,4,'Mitigating','Mitigate',
     'Implement Cloudflare Enterprise DDoS protection; configure auto-scaling on AWS; deploy rate limiting at CDN edge; conduct annual DR drill.',
     '₹2Cr/hour merchant compensation; SLA penalty clauses triggered; acquirer relationship risk; negative media coverage.'),

    ('RISK-2025-012','Fraudulent transaction injection via stolen merchant API keys',
     'Compromised merchant API credentials used to inject fraudulent UPI/card transactions into payment stream, exploiting insufficient merchant authentication controls.',
     'Financial & Fraud Risk','ananya.mehta',3,4,'Mitigating','Detect',
     'Mandate merchant 2FA for API access; implement ML-based fraud scoring (velocity checks, geolocation anomalies); deploy real-time transaction monitoring.',
     '₹5Cr chargeback liability; Visa/Mastercard fraud threshold breach; acquiring bank relationship at risk; regulatory reporting obligation.'),

    ('RISK-2025-013','Payment card data interception (man-in-the-middle)',
     'Network-level interception of payment card data during transmission due to TLS 1.0/1.1 still enabled on legacy merchant integration endpoints, enabling downgrade attacks.',
     'Cybersecurity & Data Protection','ravi.kumar',2,4,'Assessed','Mitigate',
     'Enforce TLS 1.2+ only across all endpoints; disable legacy cipher suites; implement certificate pinning for mobile SDK; complete by 2025-04-30.',
     'PCI-DSS Req 4.2.1 violation; cardholder data breach; Visa/Mastercard security program fines; reputational damage.'),

    ('RISK-2025-014','Insufficient logging – inability to detect breach',
     'Absence of centralised log management means security events across 12 microservices are not correlated, making breach detection average >72 hours vs industry standard 24 hours (PCI-DSS Req 10 requirement).',
     'Technology & Infrastructure','michael.torres',3,3,'Mitigating','Mitigate',
     'Deploy ELK Stack (Elasticsearch, Logstash, Kibana); implement SIEM with real-time alerting; achieve PCI-DSS Req 10.2 compliance; set 7-year log retention.',
     'Delayed breach detection increasing data exposure window; PCI-DSS Req 10 non-compliance; QSA audit failure.'),

    ('RISK-2025-015','Money laundering via payment gateway (AML risk)',
     'Payment gateway used as vehicle for structured money laundering transactions splitting large amounts below ₹50,000 PMLA threshold, exposing PaySecure to FIU-IND enforcement and FEMA violations.',
     'Financial & Fraud Risk','ananya.mehta',2,5,'Treatment Planned','Mitigate',
     'Implement AML transaction monitoring with rule-based + ML models; file CTRs and STRs with FIU-IND; appoint MLRO; conduct AML risk assessment annually.',
     'FIU-IND enforcement; FEMA violation; RBI license revocation; criminal liability for senior management; ₹100Cr+ penalty exposure.'),

    ('RISK-2025-016','Weak password policy – brute force account takeover',
     'Merchant portal and internal dashboard allow weak passwords (min 6 chars, no complexity), enabling credential stuffing attacks using breached password databases.',
     'Cybersecurity & Data Protection','michael.torres',3,3,'Implemented','Mitigate',
     'Enforce 12-char minimum with complexity; implement account lockout (5 attempts); deploy MFA for all admin accounts; integrate HaveIBeenPwned API check.',
     'PCI-DSS Req 8.3 violation; merchant account compromise; fraudulent transactions; reputational damage.'),

    ('RISK-2025-017','Business continuity – no DR site',
     'Single AWS ap-south-1 (Mumbai) region deployment with no disaster recovery site. AWS region outage (historically rare but occurred in Dec 2021) would cause 100% service outage with no RTO capability.',
     'Operational Risk','ravi.kumar',1,5,'Identified','Mitigate',
     'Deploy active-passive DR in AWS ap-southeast-1 (Singapore); achieve RTO 4 hours, RPO 1 hour; conduct annual DR failover test; RBI BCMS compliance.',
     'Total payment processing outage; merchant contract breach; RBI BCMS guideline violation; Series-C investor confidence impact.'),

    ('RISK-2025-018','Vulnerability in open-source payment library (supply chain)',
     'Critical CVE in open-source payment processing library (e.g. log4j-style vulnerability) in production dependency, allowing remote code execution on payment servers.',
     'Technology & Infrastructure','ravi.kumar',2,5,'Mitigating','Mitigate',
     'Implement Software Composition Analysis (SCA) in CI/CD (Snyk/Dependabot); enforce dependency update SLA (critical CVE: 24 hours); maintain SBOM.',
     'Complete payment system compromise; PCI-DSS Req 6.3 violation; ₹20Cr breach cost estimate; regulatory reporting obligation.'),

    ('RISK-2025-019','NPCI UPI system change impact on integration',
     'NPCI releasing UPI 2.0 protocol changes requiring PaySecure integration updates within mandated 90-day window. Failure causes UPI transaction blocking for all 200+ merchants.',
     'Regulatory & Compliance','ananya.mehta',2,4,'Mitigating','Accept',
     'Establish NPCI change management subscription; maintain dedicated UPI integration team; build automated regression test suite for UPI flows.',
     'UPI transaction blocking for all merchants; merchant penalty claims; NPCI participant status risk; ₹15Cr UPI transaction volume at risk.'),

    ('RISK-2025-020','Chargebacks exceeding Visa/Mastercard threshold',
     'Chargeback ratio breaching 1% Visa/Mastercard threshold due to CNP fraud and merchant disputes, triggering Excessive Chargeback Program enrollment and potential merchant termination.',
     'Financial & Fraud Risk','ananya.mehta',2,4,'Mitigating','Mitigate',
     'Deploy real-time chargeback monitoring dashboard; implement Verifi/Ethoca chargeback alerts; conduct merchant fraud training; monthly chargeback review.',
     'Visa/Mastercard ECP fines ($25/chargeback); acquiring bank relationship termination; ₹30Cr payment volume threat.'),

    ('RISK-2025-021','Data residency violation – cross-border data transfer',
     'Customer financial data being processed on AWS US-East servers (Virginia) for analytics workloads, violating RBI data localisation mandate requiring payment data storage exclusively in India.',
     'Regulatory & Compliance','priya.sharma',2,5,'Treatment Planned','Avoid',
     'Migrate all analytics workloads to AWS Mumbai (ap-south-1); implement data classification and residency controls; conduct data flow mapping audit.',
     'RBI enforcement action; potential PA license suspension; GDPR SCCs required for EU data; ₹5Cr migration cost.'),

    ('RISK-2025-022','Social engineering attack on Customer Support',
     'Threat actors impersonating merchants and convincing customer support to reset 2FA or bypass verification, enabling account takeover and fraudulent fund transfers.',
     'Operational Risk','sarah.chen',2,3,'Mitigating','Mitigate',
     'Implement strict identity verification protocol for CS team; mandatory security awareness training quarterly; deploy call recording with anomaly detection.',
     'Merchant account fraud; reputational damage; potential ₹50L per incident financial loss.'),

    ('RISK-2025-023','ISO 27001:2022 recertification failure',
     'Loss of ISO 27001:2022 certification during triennial recertification audit due to ISMS documentation gaps and control implementation failures identified by BSI certification body.',
     'Regulatory & Compliance','priya.sharma',1,3,'Identified','Mitigate',
     'Conduct internal ISMS gap assessment; update 93 Annex A controls documentation; schedule pre-audit with BSI; complete management review by 2025-08-01.',
     'Loss of ISO certification impacting enterprise sales; reduced investor confidence; higher cyber insurance premiums.'),
]

risk_insert = """INSERT INTO risks
    (risk_code, risk_title, risk_description, category_id, risk_owner_id,
     probability, impact, status, treatment_type, mitigation_plan, business_impact, created_by)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

for r in risks:
    owner_id = user_map[r[4]]
    cat_id   = cat_map[r[3]]
    cur.execute(risk_insert, (
        r[0], r[1], r[2], cat_id, owner_id,
        r[5], r[6], r[7], r[8], r[9], r[10], uid
    ))
conn.commit()
print("✅ 23 risks inserted")

# ── Compliance Controls ────────────────────────────────────────────────────
print("Inserting compliance controls...")
controls = [
    # PCI-DSS v4.0
    ('PCI-DSS-1.2.1', 'Network Access Control Policy',
     'Restrict inbound and outbound network traffic to that which is necessary for the cardholder data environment. All other traffic must be denied.',
     'PCI-DSS v4.0', 'Network Security', 'Implemented', '2024-11-15'),
    ('PCI-DSS-3.3.1', 'Encryption of Stored Cardholder Data',
     'SAD must not be retained after authorization. PAN must be rendered unreadable using AES-256 encryption or tokenisation.',
     'PCI-DSS v4.0', 'Data Protection', 'Implemented', '2024-10-20'),
    ('PCI-DSS-6.4.1', 'Web Application Firewall Deployment',
     'Deploy a WAF in front of all public-facing web applications to detect and block common web attacks (SQLi, XSS, CSRF).',
     'PCI-DSS v4.0', 'Application Security', 'In Progress', None),
    ('PCI-DSS-8.3.1', 'Multi-Factor Authentication for CDE',
     'MFA must be implemented for all non-console access to the cardholder data environment and for all remote access.',
     'PCI-DSS v4.0', 'Access Control', 'Implemented', '2024-12-01'),
    ('PCI-DSS-10.2.1', 'Audit Log Management',
     'Capture audit logs for all access to cardholder data, all actions by privileged users, and all access to audit trails.',
     'PCI-DSS v4.0', 'Logging & Monitoring', 'In Progress', None),
    ('PCI-DSS-11.3.1', 'Annual Penetration Testing',
     'Perform internal and external penetration testing at least annually and after significant infrastructure changes.',
     'PCI-DSS v4.0', 'Security Testing', 'Not Started', None),
    # GDPR
    ('GDPR-Art5', 'Data Processing Principles',
     'Personal data must be processed lawfully, fairly and transparently; collected for specified, explicit purposes; adequate, relevant and limited to necessity.',
     'GDPR', 'Data Governance', 'Implemented', '2024-09-30'),
    ('GDPR-Art13', 'Privacy Notice at Collection',
     'Provide clear privacy information to data subjects at the time of data collection including purposes, legal basis, retention periods and rights.',
     'GDPR', 'Transparency', 'Implemented', '2024-09-30'),
    ('GDPR-Art17', 'Right to Erasure (Right to be Forgotten)',
     'Implement automated data deletion workflows to fulfil data subject erasure requests within 30 days across all systems.',
     'GDPR', 'Data Subject Rights', 'In Progress', None),
    ('GDPR-Art25', 'Privacy by Design and Default',
     'Implement data protection by design and default in all new product development, including data minimisation and pseudonymisation.',
     'GDPR', 'Engineering Controls', 'Not Started', None),
    ('GDPR-Art32', 'Technical and Organisational Security Measures',
     'Implement appropriate TOMs including encryption at rest/transit, access controls, regular testing, and staff training.',
     'GDPR', 'Security Controls', 'Implemented', '2024-11-01'),
    ('GDPR-Art33', 'Data Breach Notification (72-hour)',
     'Establish and test incident response procedure to detect, report, and notify supervisory authority within 72 hours of breach discovery.',
     'GDPR', 'Incident Response', 'In Progress', None),
    ('GDPR-Art37', 'Data Protection Officer Appointment',
     'Appoint a qualified DPO with sufficient resources and report DPO details to supervisory authority.',
     'GDPR', 'Governance', 'Implemented', '2024-06-01'),
    # ISO 27001:2022
    ('ISO-A5.1', 'Information Security Policies',
     'Define, approve by management, publish and communicate an Information Security Policy and topic-specific policies covering all A.5 controls.',
     'ISO 27001:2022', 'Governance', 'In Progress', None),
    ('ISO-A5.23', 'Cloud Services Information Security',
     'Establish processes for acquisition, use, management and exit from cloud services aligned with information security requirements.',
     'ISO 27001:2022', 'Cloud Security', 'Not Started', None),
    ('ISO-A8.2', 'Privileged Access Rights Management',
     'Restrict and manage allocation of privileged access rights; review quarterly; implement PAM solution for administrative accounts.',
     'ISO 27001:2022', 'Access Control', 'In Progress', None),
    ('ISO-A8.7', 'Protection Against Malware',
     'Deploy detection, prevention and recovery controls against malware on all endpoints, servers and email gateways.',
     'ISO 27001:2022', 'Endpoint Security', 'Implemented', '2024-10-15'),
    ('ISO-A8.24', 'Cryptography Policy',
     'Define and implement rules for effective use of cryptography including key management, algorithm selection, and key lifecycle.',
     'ISO 27001:2022', 'Cryptography', 'Implemented', '2024-08-20'),
    ('ISO-A8.28', 'Secure Coding Practices',
     'Establish, document and apply secure coding principles (OWASP Top-10) in software development; integrate SAST/DAST in CI/CD pipeline.',
     'ISO 27001:2022', 'Secure Development', 'In Progress', None),
    # RBI PA/PG Guidelines
    ('RBI-PA-3.1', 'Information Security Policy (RBI)',
     'Maintain a board-approved Information Security Policy reviewed annually, covering all aspects of payment operations and data protection.',
     'RBI PA/PG Guidelines 2020', 'Governance', 'Not Started', None),
    ('RBI-PA-5.2', 'Merchant Due Diligence',
     'Conduct comprehensive due diligence on all merchants before onboarding including background checks, business verification and ongoing monitoring.',
     'RBI PA/PG Guidelines 2020', 'Merchant Management', 'Implemented', '2024-10-01'),
    ('RBI-PA-7.1', 'Data Localisation Compliance',
     'Ensure all payment system data is stored only in India; no data mirroring or processing outside India except for cross-border transactions.',
     'RBI PA/PG Guidelines 2020', 'Data Residency', 'In Progress', None),
]

ctrl_insert = """INSERT INTO compliance_controls
    (control_code, control_name, control_description, regulation,
     control_category, implementation_status, last_tested, is_mandatory)
    VALUES (%s,%s,%s,%s,%s,%s,%s,TRUE)"""

for c in controls:
    cur.execute(ctrl_insert, c)
conn.commit()
print("✅ 22 compliance controls inserted")

# ── Risk–Control Mappings ──────────────────────────────────────────────────
print("Inserting risk–control mappings...")
cur.execute("SELECT risk_id, risk_code FROM risks")
risk_map = {r[1]: r[0] for r in cur.fetchall()}
cur.execute("SELECT control_id, control_code FROM compliance_controls")
ctrl_map = {r[1]: r[0] for r in cur.fetchall()}

mappings = [
    ('RISK-2025-001', 'PCI-DSS-8.3.1',  'Mitigating'),
    ('RISK-2025-001', 'ISO-A8.28',       'Mitigating'),
    ('RISK-2025-002', 'PCI-DSS-6.4.1',  'Mitigating'),
    ('RISK-2025-002', 'GDPR-Art32',      'Mitigating'),
    ('RISK-2025-002', 'ISO-A8.28',       'Mitigating'),
    ('RISK-2025-003', 'ISO-A8.7',        'Mitigating'),
    ('RISK-2025-004', 'PCI-DSS-11.3.1', 'Mitigating'),
    ('RISK-2025-004', 'PCI-DSS-6.4.1',  'Mitigating'),
    ('RISK-2025-005', 'GDPR-Art17',      'Mitigating'),
    ('RISK-2025-005', 'GDPR-Art5',       'Mitigating'),
    ('RISK-2025-005', 'GDPR-Art37',      'Mitigating'),
    ('RISK-2025-006', 'RBI-PA-3.1',      'Mitigating'),
    ('RISK-2025-009', 'PCI-DSS-1.2.1',  'Mitigating'),
    ('RISK-2025-010', 'ISO-A8.2',        'Mitigating'),
    ('RISK-2025-010', 'PCI-DSS-8.3.1',  'Mitigating'),
    ('RISK-2025-013', 'PCI-DSS-3.3.1',  'Mitigating'),
    ('RISK-2025-014', 'PCI-DSS-10.2.1', 'Mitigating'),
    ('RISK-2025-016', 'PCI-DSS-8.3.1',  'Mitigating'),
    ('RISK-2025-018', 'ISO-A8.28',       'Mitigating'),
    ('RISK-2025-021', 'RBI-PA-7.1',      'Mitigating'),
    ('RISK-2025-021', 'GDPR-Art25',      'Mitigating'),
    ('RISK-2025-023', 'ISO-A5.1',        'Mitigating'),
    ('RISK-2025-023', 'ISO-A8.24',       'Mitigating'),
]
for risk_code, ctrl_code, mtype in mappings:
    rid = risk_map.get(risk_code)
    cid = ctrl_map.get(ctrl_code)
    if rid and cid:
        cur.execute(
            "INSERT IGNORE INTO risk_compliance_mapping (risk_id, control_id, mapping_type, mapped_by) VALUES (%s,%s,%s,%s)",
            (rid, cid, mtype, uid)
        )
conn.commit()
print("✅ Risk–control mappings inserted")

# ── Sample Audit Logs ──────────────────────────────────────────────────────
print("Inserting sample audit logs...")
import json as _json
log_entries = [
    (user_map['sarah.chen'],     'USER_LOGIN',              None, None,
     _json.dumps({'username': 'sarah.chen', 'result': 'success'}), '10.0.1.5'),
    (user_map['michael.torres'], 'RISK_CREATED',            'risks', 1,
     _json.dumps({'risk_code': 'RISK-2025-001', 'risk_level': 'High', 'score': 20}), '10.0.1.12'),
    (user_map['priya.sharma'],   'COMPLIANCE_CONTROLS_VIEWED', 'compliance_controls', None,
     _json.dumps({'viewed_by': 'priya.sharma', 'control_count': 22}), '10.0.1.18'),
    (user_map['james.wilson'],   'AUDIT_TRAIL_VIEWED',      'audit_logs', None,
     _json.dumps({'viewed_by': 'james.wilson', 'filter_days': 7}), '10.0.1.25'),
    (user_map['sarah.chen'],     'RISK_STATUS_UPDATED',     'risks', 3,
     _json.dumps({'risk_code': 'RISK-2025-003', 'previous_status': 'Assessed', 'new_status': 'Treatment Planned'}), '10.0.1.5'),
    (user_map['priya.sharma'],   'RISK_CONTROL_MAPPED',     'risk_compliance_mapping', 5,
     _json.dumps({'risk_code': 'RISK-2025-005', 'control': 'GDPR-Art17', 'mapping_type': 'Mitigating'}), '10.0.1.18'),
    (user_map['michael.torres'], 'COMPLIANCE_REPORT_EXPORTED', 'compliance_controls', None,
     _json.dumps({'exported_by': 'michael.torres', 'framework': 'PCI-DSS v4.0'}), '10.0.1.12'),
    (user_map['james.wilson'],   'AUDIT_LOG_EXPORTED',      'audit_logs', None,
     _json.dumps({'exported_by': 'james.wilson', 'record_count': 47, 'last_n_days': 30}), '10.0.1.25'),
]
for entry in log_entries:
    cur.execute(
        "INSERT INTO audit_logs (user_id, action, entity_type, entity_id, details, ip_address) VALUES (%s,%s,%s,%s,%s,%s)",
        entry
    )
conn.commit()
print("✅ Audit logs inserted")

cur.close()
conn.close()

print("\n" + "=" * 60)
print("✅ DATABASE SEEDED SUCCESSFULLY!")
print("=" * 60)
print("\nDemo login credentials (all use password: SecurePass@2025!)")
print(f"  {'USERNAME':<20} {'ROLE':<25} {'FULL NAME'}")
print("-" * 65)
demo = [
    ('sarah.chen',    'Admin / CISO',            'Sarah Chen'),
    ('michael.torres','Risk Manager',             'Michael Torres'),
    ('priya.sharma',  'Compliance Officer',       'Priya Sharma'),
    ('james.wilson',  'Internal Auditor',         'James Wilson'),
    ('ravi.kumar',    'VP Engineering (no role)', 'Ravi Kumar'),
    ('ananya.mehta',  'Head of Payments (no role)','Ananya Mehta'),
]
for username, role, name in demo:
    print(f"  {username:<20} {role:<25} {name}")
print()
