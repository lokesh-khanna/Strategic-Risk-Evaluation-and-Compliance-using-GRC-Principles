-- ============================================================
-- PaySecure Technologies Pvt. Ltd.
-- GRC Platform - Realistic Fintech Seed Data
-- Industry: Payment Gateway / Fintech
-- Compliance: PCI-DSS v4.0, GDPR, ISO 27001:2022, RBI Guidelines
-- Generated: 2026-02-24
-- ============================================================

-- ============================================================
-- SECTION 1: SCHEMA SETUP (Run ONCE on fresh DB)
-- ============================================================

CREATE DATABASE IF NOT EXISTS grc_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE grc_db;

-- Roles table
CREATE TABLE IF NOT EXISTS roles (
    role_id INT AUTO_INCREMENT PRIMARY KEY,
    role_name VARCHAR(50) UNIQUE NOT NULL,
    role_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Users table
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    employee_id VARCHAR(20) UNIQUE,
    department VARCHAR(100),
    job_title VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    failed_login_attempts INT DEFAULT 0,
    locked_until TIMESTAMP NULL,
    last_login TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- User-Roles junction table
CREATE TABLE IF NOT EXISTS user_roles (
    user_role_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    role_id INT NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by INT,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (role_id) REFERENCES roles(role_id),
    UNIQUE KEY unique_user_role (user_id, role_id)
);

-- Risk categories table
CREATE TABLE IF NOT EXISTS risk_categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL,
    nist_csf_domain VARCHAR(50),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Risks table
CREATE TABLE IF NOT EXISTS risks (
    risk_id INT AUTO_INCREMENT PRIMARY KEY,
    risk_code VARCHAR(20) UNIQUE NOT NULL,
    risk_title VARCHAR(200) NOT NULL,
    risk_description TEXT,
    category_id INT,
    risk_owner_id INT,
    probability TINYINT NOT NULL CHECK (probability BETWEEN 1 AND 5),
    impact TINYINT NOT NULL CHECK (impact BETWEEN 1 AND 5),
    risk_score TINYINT GENERATED ALWAYS AS (probability * impact) STORED,
    risk_level VARCHAR(10) GENERATED ALWAYS AS (
        CASE
            WHEN (probability * impact) >= 16 THEN 'High'
            WHEN (probability * impact) >= 6  THEN 'Medium'
            ELSE 'Low'
        END
    ) STORED,
    status ENUM('Identified','Assessed','Treatment Planned','Mitigating','Accepted','Closed') DEFAULT 'Identified',
    mitigation_plan TEXT,
    residual_risk VARCHAR(10),
    treatment_type ENUM('Mitigate','Accept','Transfer','Avoid') DEFAULT 'Mitigate',
    review_date DATE,
    business_impact TEXT,
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES risk_categories(category_id),
    FOREIGN KEY (risk_owner_id) REFERENCES users(user_id),
    FOREIGN KEY (created_by) REFERENCES users(user_id)
);

-- Compliance controls table
CREATE TABLE IF NOT EXISTS compliance_controls (
    control_id INT AUTO_INCREMENT PRIMARY KEY,
    control_code VARCHAR(30) NOT NULL,
    control_name VARCHAR(200) NOT NULL,
    control_description TEXT,
    regulation VARCHAR(50) NOT NULL,
    control_objective TEXT,
    implementation_status ENUM('Not Started','In Progress','Implemented','Under Review','Not Applicable') DEFAULT 'Not Started',
    control_owner_id INT,
    evidence_location TEXT,
    last_tested DATE,
    next_review DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (control_owner_id) REFERENCES users(user_id)
);

-- Risk-Compliance mapping table
CREATE TABLE IF NOT EXISTS risk_compliance_mapping (
    mapping_id INT AUTO_INCREMENT PRIMARY KEY,
    risk_id INT NOT NULL,
    control_id INT NOT NULL,
    mapping_justification TEXT,
    mapped_by INT,
    mapped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (risk_id) REFERENCES risks(risk_id),
    FOREIGN KEY (control_id) REFERENCES compliance_controls(control_id),
    UNIQUE KEY unique_risk_control (risk_id, control_id)
);

-- Audit logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id INT,
    details TEXT,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- ============================================================
-- SECTION 2: CLEAR EXISTING DATA (Safe re-seed)
-- ============================================================

SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE audit_logs;
TRUNCATE TABLE risk_compliance_mapping;
TRUNCATE TABLE compliance_controls;
TRUNCATE TABLE risks;
TRUNCATE TABLE risk_categories;
TRUNCATE TABLE user_roles;
TRUNCATE TABLE users;
TRUNCATE TABLE roles;
SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================
-- SECTION 3: ROLES
-- ============================================================

INSERT INTO roles (role_name, role_description) VALUES
('admin',             'System Administrator - Full access to all GRC modules including user management'),
('risk_manager',      'IT Risk Manager - Create, assess, and manage enterprise risk register'),
('compliance_officer','Compliance Lead - Manage regulatory controls (PCI-DSS, GDPR, ISO 27001, RBI)'),
('auditor',           'Internal Auditor - Read-only access to audit trails and compliance reports');

-- ============================================================
-- SECTION 4: USERS (PaySecure Technologies Team)
-- Passwords are bcrypt hashes of: SecurePass@2025!
-- ============================================================

INSERT INTO users (username, password_hash, full_name, email, employee_id, department, job_title) VALUES
('sarah.chen',   '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMlJafgtwBmIiu2ASM0mov8gqu', 'Sarah Chen',    'sarah.chen@paysecure.in',    'EMP-001', 'Information Security', 'Chief Information Security Officer'),
('michael.torres','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMlJafgtwBmIiu2ASM0mov8gqu', 'Michael Torres', 'michael.torres@paysecure.in','EMP-002', 'IT Risk',              'IT Risk Manager'),
('priya.sharma',  '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMlJafgtwBmIiu2ASM0mov8gqu', 'Priya Sharma',  'priya.sharma@paysecure.in',  'EMP-003', 'Legal & Compliance',   'GDPR Compliance Lead'),
('james.wilson',  '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMlJafgtwBmIiu2ASM0mov8gqu', 'James Wilson',  'james.wilson@paysecure.in',  'EMP-004', 'Internal Audit',       'Internal Auditor'),
('ravi.kumar',    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMlJafgtwBmIiu2ASM0mov8gqu', 'Ravi Kumar',    'ravi.kumar@paysecure.in',    'EMP-005', 'Engineering',          'VP of Engineering'),
('ananya.mehta',  '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMlJafgtwBmIiu2ASM0mov8gqu', 'Ananya Mehta',  'ananya.mehta@paysecure.in',  'EMP-006', 'Operations',           'Head of Payment Operations');

-- ============================================================
-- SECTION 5: USER ROLE ASSIGNMENTS
-- ============================================================

INSERT INTO user_roles (user_id, role_id, assigned_by) VALUES
(1, 1, 1),  -- sarah.chen       → admin
(2, 2, 1),  -- michael.torres   → risk_manager
(3, 3, 1),  -- priya.sharma     → compliance_officer
(4, 4, 1),  -- james.wilson     → auditor
(5, 2, 1),  -- ravi.kumar       → risk_manager (VP Eng also manages IT risks)
(6, 3, 1);  -- ananya.mehta     → compliance_officer

-- ============================================================
-- SECTION 6: RISK CATEGORIES (NIST CSF Aligned)
-- ============================================================

INSERT INTO risk_categories (category_name, nist_csf_domain, description) VALUES
('Cybersecurity & API Security',    'Protect',  'Risks related to unauthorized access, API vulnerabilities, and network-layer attacks on payment infrastructure'),
('Data Privacy & Compliance',       'Identify', 'GDPR, PCI-DSS, and RBI data localization compliance risks involving customer PII and KYC data'),
('Third-Party & Vendor Risk',       'Identify', 'Risks from payment processor integrations, cloud providers, and outsourced KYC/AML vendors'),
('Operational & Infrastructure',    'Recover',  'System availability, disaster recovery, and business continuity risks for payment processing'),
('Financial Crime & Fraud',         'Detect',   'Transaction fraud, money laundering, and identity theft risks on the payment gateway'),
('Regulatory & Legal',              'Respond',  'Fines, penalties, and enforcement actions from RBI, SEBI, GDPR supervisory authorities'),
('Human & Process Risk',            'Protect',  'Insider threats, social engineering, and process failures in payment operations');

-- ============================================================
-- SECTION 7: RISKS (23 Realistic Fintech Risks)
-- ============================================================

INSERT INTO risks (risk_code, risk_title, risk_description, category_id, risk_owner_id,
                   probability, impact, status, treatment_type, mitigation_plan, business_impact, review_date, created_by) VALUES

-- ═══ HIGH RISKS (Score ≥ 16) ═══
('RISK-2025-001',
 'Unauthorized API Access to Payment Gateway',
 'Attackers exploit weak OAuth2 token validation or API key leakage in our REST payment API endpoints (/v2/payments, /v2/refunds), allowing unauthorized transaction initiation, refund manipulation, or customer data exfiltration. Particularly critical for our $50M/month transaction volume.',
 1, 2, 4, 5, 'Treatment Planned', 'Mitigate',
 'Implement API gateway with rate limiting (max 1000 req/min per merchant). Enforce OAuth 2.0 + PKCE for all API consumers. Deploy mTLS for B2B merchant connections. Conduct quarterly API penetration testing. Implement anomaly detection via AWS WAF and CloudWatch alerts.',
 'Direct financial loss up to ₹25 Cr/incident. PCI-DSS Level 1 audit failure. Merchant churn risk estimated at 30%. RBI regulatory action under PSS Act 2007.',
 '2025-06-30', 1),

('RISK-2025-002',
 'Customer PII Data Breach via SQL Injection',
 'SQL injection vulnerabilities in customer onboarding endpoints could expose PII (Name, PAN, Aadhaar, bank account numbers) of 2.5M registered users. Legacy PHP modules in KYC portal have not been reviewed since 2023.',
 2, 2, 4, 5, 'Mitigating', 'Mitigate',
 'Migrate all raw SQL to parameterized queries (ORM). Deploy SAST scanning in CI/CD pipeline (Semgrep rules for SQLi). WAF rule deployment for SQLi patterns. Data masking for PAN/Aadhaar in application logs. VAPT in Q1 2025.',
 'GDPR Article 83 fine up to €20M or 4% global turnover. RBI data localization violation. CERT-In 6-hour breach notification obligation. Reputation loss - estimated 40% customer churn.',
 '2025-03-31', 1),

('RISK-2025-003',
 'Ransomware Encryption of Transaction Database',
 'Ransomware attack targeting our primary MySQL transaction database (transactions, settlement_records, merchant_accounts tables) could halt $50M/month payment processing. Attack vector: phishing email to ops team or compromised vendor VPN access.',
 4, 5, 3, 5, 'Treatment Planned', 'Mitigate',
 'Implement immutable S3 backups with 30-day retention (WORM policy). Network segmentation - isolate DB subnet. EDR deployment on all endpoints (CrowdStrike). Offline backup tested quarterly. Incident Response Plan updated for ransomware scenario. Cyber insurance coverage of ₹50Cr.',
 'Payment processing downtime: ₹8.5Cr/hour revenue loss. Merchant SLA breach penalties: ₹2Cr. Settlement failure for 85,000 daily transactions. RBI reporting obligation within 2 hours of major outage.',
 '2025-04-30', 2),

-- ═══ MEDIUM RISKS (Score 6-15) ═══
('RISK-2025-004',
 'PCI-DSS v4.0 Non-Compliance Penalty',
 'Failure to achieve PCI-DSS v4.0 compliance by March 2025 deadline could result in fines from card networks (Visa/Mastercard) and suspension of card processing capability. Gap analysis revealed 12 non-compliant controls.',
 6, 3, 3, 4, 'Treatment Planned', 'Mitigate',
 'Engage QSA (Qualified Security Assessor) for gap remediation. Prioritize Req 6.4.3 (client-side scripts), Req 10.7 (automated log analysis), Req 11.6 (payment page integrity monitoring). Complete compensating controls documentation by Feb 2025.',
 'Card network fines: $5,000-$100,000/month. Potential loss of card processing license. Merchant confidence erosion.',
 '2025-03-31', 3),

('RISK-2025-005',
 'Third-Party KYC Vendor Security Failure',
 'Our KYC verification partner (DataVerify Inc.) processes Aadhaar and PAN card images for 500 new customers daily. A security breach at their end could expose our customers'' sensitive identity documents. Vendor VAPT report is 18 months old.',
 3, 2, 3, 4, 'Assessed', 'Mitigate',
 'Mandate annual VAPT reports from DataVerify. Include right-to-audit clause in contract renewal (Q2 2025). Evaluate vendor SOC 2 Type II certification. Implement data minimization - send only necessary fields. Deploy API-level DLP to detect abnormal data exfiltration patterns.',
 'Joint liability for customer PII exposure. Trust breakdown - potential loss of RBI KYC authorization. Media coverage risk.',
 '2025-05-31', 2),

('RISK-2025-006',
 'RBI Payment System Directive Non-Compliance',
 'Non-compliance with RBI circular on data storage localization (PA/PG Guidelines 2020) and PSO annual audit requirements. Failure to file timely Regulatory Reports (CIMS portal) with RBI.',
 6, 3, 2, 5, 'Identified', 'Mitigate',
 'Assign dedicated RBI compliance officer. Automate CIMS report generation. Migrate EU-region transaction data to AWS Mumbai (ap-south-1). Legal review of all data sharing agreements for cross-border compliance.',
 'Cancellation of Payment Aggregator license. Business shutdown risk. Director-level personal liability under PSS Act.',
 '2025-04-15', 3),

('RISK-2025-007',
 'Insider Threat - Privileged Database Access Abuse',
 'A malicious or compromised employee with DBA or admin access could extract customer financial data, manipulate transactions, or plant backdoors. Current 12 employees have unrestricted production DB access.',
 7, 1, 2, 4, 'Treatment Planned', 'Mitigate',
 'Implement PAM solution (CyberArk). Enforce just-in-time access for production DBs. Segregation of duties - separate DBA and app accounts. UEBA (User Entity Behavior Analytics) monitoring. Quarterly access recertification.',
 'Internal fraud risk: estimated ₹5Cr exposure. Regulatory breach for insider-enabled fraud. Reputational damage.',
 '2025-06-30', 2),

('RISK-2025-008',
 'Payment Page Skimming (Magecart Attack)',
 'Malicious JavaScript injected into our hosted payment page (HPP) could capture card details at the point of entry. Our checkout page loads 15 third-party scripts including analytics and chat widgets.',
 1, 2, 3, 4, 'Assessed', 'Mitigate',
 'Implement Content Security Policy (CSP) headers. Deploy SubResource Integrity (SRI) for third-party scripts. Payment page integrity monitoring (PCI DSS Req 11.6.1). Remove unnecessary JavaScript dependencies. Weekly script inventory review.',
 'Mass card data compromise. VISA GLOB alert, potential Level 1 PCI audit trigger. Chargeback liability.',
 '2025-05-31', 2),

('RISK-2025-009',
 'Cloud Misconfiguration Exposing S3 Settlement Files',
 'Misconfigured AWS S3 bucket access policies could expose daily settlement files (containing merchant bank details and transaction summaries). We process 120 settlement files daily across 800+ merchant accounts.',
 4, 5, 2, 5, 'Mitigating', 'Mitigate',
 'Deploy AWS Config rules for S3 public access blocking. Implement AWS Macie for sensitive data discovery. S3 bucket policy review automated via Security Hub. Encrypt all S3 objects with KMS. Enable S3 access logging.',
 'Merchant banking credential exposure. Settlement disruption. Regulatory notification requirement.',
 '2025-03-15', 2),

('RISK-2025-010',
 'Transaction Fraud via Account Takeover (ATO)',
 'Credential stuffing attacks using leaked username/password combinations from other breaches can result in ATO of customer payment accounts, enabling fraudulent transactions and unauthorized fund transfers.',
 5, 6, 4, 3, 'Mitigating', 'Mitigate',
 'Enforce MFA for all customer payment accounts. Deploy CAPTCHA on login endpoints. Implement velocity checks per account. Dark web credential monitoring via HaveIBeenPwned API. Device fingerprinting and behavioral biometrics.',
 'Fraud liability: estimated ₹1.2Cr/month. Customer trust erosion. Chargeback increase.',
 '2025-04-30', 2),

('RISK-2025-011',
 'GDPR Data Subject Rights Non-Fulfillment',
 'Failure to respond to DSAR (Data Subject Access Requests) within 30 days or incomplete erasure requests for EU-resident customers violates GDPR Articles 15-17. Current manual process handles 45 requests/month.',
 2, 3, 2, 4, 'Identified', 'Mitigate',
 'Implement automated DSAR workflow (ServiceNow integration). Create data map for all EU customer PII. Deploy right-to-erasure automation. Appoint EU GDPR representative. Train customer support team on DSAR handling.',
 'GDPR fines up to €20M. EU DPA investigation risk. Operational disruption from manual process.',
 '2025-05-31', 3),

('RISK-2025-012',
 'Payment Gateway DDoS Attack',
 'Large-scale DDoS targeting our payment API infrastructure (/v2/payments endpoint) could cause service unavailability. Our peak load is 5,000 TPS and we have had 2 DDoS incidents in the past 12 months.',
 4, 5, 3, 3, 'Mitigating', 'Mitigate',
 'Deploy AWS Shield Advanced (L3/L4 + L7 protection). CloudFront for origin IP obfuscation. Auto-scaling for web tier triggered at 70% CPU. Failover routing to DR site (N. Virginia). SLA: 99.99% uptime commitment to merchants.',
 'Revenue loss: ₹8.5Cr/hour. Merchant SLA penalty: ₹50L/hour. Regulatory report to RBI for outage >2 hours.',
 '2025-06-30', 5),

('RISK-2025-013',
 'Weak Encryption of Stored Card Data (PCI-DSS Req 3)',
 'Legacy tokenization service uses outdated AES-128 encryption for PAN storage. PCI-DSS v4.0 Requirement 3 mandates AES-256 and enhanced key management procedures.',
 1, 5, 2, 4, 'Treatment Planned', 'Mitigate',
 'Upgrade tokenization to AES-256-GCM. Implement HSM-based key management (AWS CloudHSM). Rotate encryption keys quarterly. Delete all stored PANs where tokenization is feasible. Engage PCI-certified tokenization provider.',
 'PCI-DSS audit failure. Card network fines. In case of breach - card replacement liability.',
 '2025-04-30', 2),

('RISK-2025-014',
 'SWIFT/NEFT Integration Vulnerability',
 'Our RTGS/NEFT integration with partner banks via SFTP has hardcoded credentials in legacy configuration files committed to the application repository. Secret exposure risk through GitHub public repositories.',
 1, 2, 2, 4, 'Mitigating', 'Mitigate',
 'Scan GitHub repos with truffleHog and GitGuardian. Migrate all secrets to AWS Secrets Manager. Revoke and rotate all hardcoded credentials immediately. Implement pre-commit hooks to prevent secret commits.',
 'Unauthorized fund transfer initiation. Settlement disruption. Partner bank trust breakdown.',
 '2025-03-15', 2),

('RISK-2025-015',
 'Insufficient Audit Logging for PCI-DSS Req 10',
 'Audit logs for payment transactions are not retained for the required 12-month period (PCI-DSS Req 10.5). Log integrity is not protected, allowing potential tampering.',
 6, 1, 2, 3, 'Assessed', 'Mitigate',
 'Deploy centralized SIEM (Splunk). Enable CloudTrail with S3 log archival for 12 months. Implement log integrity with SHA-256 hashing. Alert on log deletion events. Automate log review for failed authentication and privilege escalation.',
 'PCI-DSS audit finding. Inability to investigate fraud incidents. Non-availability of forensic evidence.',
 '2025-05-31', 3),

('RISK-2025-016',
 'Third-Party Payment Processor Downtime (Razorpay/PayU)',
 'Over-reliance on Razorpay as primary payment aggregator without adequate failover. Any Razorpay outage directly impacts our merchant payment success rates.',
 3, 6, 3, 3, 'Treatment Planned', 'Mitigate',
 'Implement multi-acquirer routing (Razorpay primary + PayU fallback). Dynamic failover based on success rate thresholds. Daily reconciliation dashboard for each processor. SLA enforcement with contractual penalties.',
 'Transaction failure impact: ₹4Cr/hour. Merchant SLA breach. Customer experience degradation.',
 '2025-06-30', 5),

('RISK-2025-017',
 'Money Laundering via Payment Platform (AML Risk)',
 'High-value transactions structured to evade ₹50,000 reporting threshold. Shell company merchants registered on platform facilitating layering of illicit funds.',
 5, 6, 2, 4, 'Assessed', 'Mitigate',
 'Enhance transaction monitoring rules (velocity, amount thresholds). Implement automated CTR filing for cash transactions >₹10L. Merchant risk scoring with enhanced due diligence for high-risk sectors. Appoint MLRO (Money Laundering Reporting Officer).',
 'FIU-IND reporting violation. License revocation. Criminal liability under PMLA 2002.',
 '2025-05-31', 3),

-- ═══ LOW RISKS (Score 1-5) ═══
('RISK-2025-018',
 'Employee Phishing Leading to BEC (Business Email Compromise)',
 'Spear-phishing emails targeting finance and payment operations teams could result in fraudulent payment instructions or credential compromise.',
 7, 1, 3, 2, 'Mitigating', 'Mitigate',
 'Quarterly phishing simulation with KnowBe4. MFA enforcement for all corporate email. DMARC/DKIM/SPF email authentication. BEC awareness training for finance team. Dual-approval for outbound wire transfers >₹5L.',
 'Internal fraud via misdirected payments. Credential theft enabling lateral movement.',
 '2025-06-30', 2),

('RISK-2025-019',
 'Inadequate Business Continuity Plan (BCP) Testing',
 'BCP for payment processing has not been tested in 18 months. DR site at Hyderabad has untested failover procedures. RTO of 4 hours and RPO of 15 minutes are not validated.',
 4, 5, 2, 3, 'Identified', 'Mitigate',
 'Schedule biannual BCP tabletop exercises. Conduct DR failover test in Q2 2025. Validate RTO/RPO targets through load testing. Update runbooks for payment system recovery. Communicate BCP procedures to all ops team.',
 'Extended outage during disaster scenario. Regulatory non-compliance with RBI business continuity guidelines.',
 '2025-07-31', 5),

('RISK-2025-020',
 'GDPR Cross-Border Data Transfer (Standard Contractual Clauses)',
 'Post-Schrems II, our data transfer to US-based analytics vendors (Segment, Mixpanel) may be non-compliant without updated SCCs. 85,000 EU merchant data points transferred monthly.',
 2, 3, 2, 3, 'Identified', 'Mitigate',
 'Audit all data processing agreements with US vendors. Execute updated SCCs per EC Decision 2021/914. Evaluate EU-based alternatives for analytics. DP impact assessment for US data transfers.',
 'GDPR enforcement action. Fine up to 4% global annual turnover. Operational disruption if transfers halted.',
 '2025-06-30', 3),

('RISK-2025-021',
 'Outdated TLS Version on Merchant API Endpoints',
 'Three merchant-facing API endpoints still support TLS 1.0 and 1.1 which are deprecated and vulnerable to BEAST/POODLE attacks. PCI-DSS Req 4.2.1 mandates TLS 1.2 minimum.',
 1, 5, 2, 3, 'Mitigating', 'Mitigate',
 'Disable TLS 1.0/1.1 on all ALB and API Gateway configurations. Enforce TLS 1.2+ with strong cipher suites. Notify merchant integrations of deprecation timeline. Certificate management via AWS ACM with auto-renewal.',
 'Cryptographic vulnerability exposure. PCI-DSS audit non-compliance finding.',
 '2025-03-31', 2),

('RISK-2025-022',
 'Shadow IT - Unauthorized SaaS Applications in Ops Team',
 'Payment operations team using unauthorized Slack, Google Sheets, and Airtable for processing settlement queries containing transaction data outside DLP controls.',
 7, 1, 3, 2, 'Identified', 'Mitigate',
 'Deploy CASB solution (Microsoft Defender for Cloud Apps). SaaS application inventory and risk rating. Acceptable use policy enforcement. Provide approved collaboration tools for sensitive data. Data loss prevention policies for cloud upload.',
 'Data exfiltration through unsanctioned cloud apps. PCI-DSS scope expansion. Audit trail gaps.',
 '2025-07-31', 2),

('RISK-2025-023',
 'Key Person Dependency - Single Cloud Architect',
 'Only one employee (Ravi Kumar, VP Engineering) has full knowledge of AWS infrastructure architecture. No documented runbooks or infrastructure-as-code for 40% of production systems.',
 4, 5, 2, 2, 'Identified', 'Accept',
 'Document all infrastructure using Terraform/CDK. Cross-train 2 senior engineers on critical AWS components. Knowledge transfer sessions monthly. Architecture diagrams maintained in Confluence.',
 'Service delivery risk if key person unavailable. Extended outage resolution times.',
 '2025-08-31', 1);

-- ============================================================
-- SECTION 8: COMPLIANCE CONTROLS
-- ============================================================

INSERT INTO compliance_controls (control_code, control_name, control_description, regulation, control_objective, implementation_status, control_owner_id, last_tested, next_review) VALUES

-- PCI-DSS v4.0 Controls
('PCI-DSS-1.2',
 'Network Security Controls - Firewall Configuration',
 'Install and maintain network security controls to protect the cardholder data environment (CDE). Define and implement firewall rules that restrict inbound and outbound traffic to the minimum necessary.',
 'PCI-DSS v4.0',
 'Ensure only authorized traffic can access the CDE. Block all traffic not explicitly required for payment processing.',
 'Implemented', 5, '2025-01-15', '2025-07-15'),

('PCI-DSS-3.3',
 'Sensitive Authentication Data Protection',
 'Do not retain sensitive authentication data (SAD) after authorization, even if encrypted. This includes full track data, card verification codes, and PINs.',
 'PCI-DSS v4.0',
 'Ensure SAD is purged immediately post-authorization. Implement controls to prevent SAD storage in logs, databases, or temporary files.',
 'Implemented', 2, '2025-01-20', '2025-07-20'),

('PCI-DSS-6.4',
 'Web-Facing Application Security - Payment Pages',
 'Protect public-facing web applications against known attacks by deploying a WAF or reviewing via application-layer vulnerability assessment. For payment pages, implement integrity mechanisms to detect unauthorized modifications.',
 'PCI-DSS v4.0',
 'Prevent unauthorized script execution on payment pages. Detect and alert on script changes within 1 hour.',
 'In Progress', 5, '2024-11-01', '2025-05-01'),

('PCI-DSS-8.3',
 'Multi-Factor Authentication for CDE Access',
 'Implement MFA for all access into the CDE for non-console administrative access and all remote network access. MFA must be implemented for all accounts with access to the cardholder data environment.',
 'PCI-DSS v4.0',
 'Prevent unauthorized access to CDE using stolen/compromised credentials. Verify identity through multiple authentication factors.',
 'Implemented', 1, '2025-01-10', '2025-07-10'),

('PCI-DSS-10.2',
 'Audit Log Events for CDE',
 'Implement audit logs to capture all individual user access to cardholder data, all actions by root or admin, access to audit logs, invalid logical access attempts, use of identification and authentication mechanisms, initialization/stopping/pausing of audit logs, and creation/deletion of system-level objects.',
 'PCI-DSS v4.0',
 'Enable forensic investigation capability. Detect anomalous behavior and unauthorized access attempts in real-time.',
 'In Progress', 1, '2024-12-01', '2025-06-01'),

('PCI-DSS-11.3',
 'External and Internal Vulnerability Scans',
 'Perform internal and external network vulnerability scans at least once every three months and after any significant network change. External scans must be performed by an Approved Scanning Vendor (ASV).',
 'PCI-DSS v4.0',
 'Identify and remediate technical vulnerabilities before they can be exploited. Maintain quarterly vulnerability scan cadence.',
 'Implemented', 2, '2025-01-05', '2025-04-05'),

-- GDPR Controls
('GDPR-Art.5',
 'Principles of Personal Data Processing',
 'Personal data must be processed lawfully, fairly, and transparently. Data must be collected for specified, explicit, and legitimate purposes and not further processed in a manner incompatible with those purposes.',
 'GDPR',
 'Establish lawful basis for all PII processing. Maintain record of processing activities (RoPA) per Art. 30.',
 'Implemented', 3, '2025-01-12', '2025-07-12'),

('GDPR-Art.13',
 'Privacy Notice - Transparency at Collection',
 'Provide privacy information to data subjects at the time of data collection including identity of controller, purposes and legal basis for processing, data retention periods, and data subject rights.',
 'GDPR',
 'Ensure data subjects are informed about how their PII is used. Maintain up-to-date, plain-language privacy notice.',
 'Implemented', 3, '2025-01-01', '2025-07-01'),

('GDPR-Art.17',
 'Right to Erasure (Right to be Forgotten)',
 'Data subjects have the right to request erasure of personal data without undue delay. Implement technical mechanisms to honor erasure requests within 30 days, including third-party processors.',
 'GDPR',
 'Enable data subjects to exercise erasure rights. Cascade deletion to all downstream processors and ensure complete data removal from all systems.',
 'In Progress', 3, '2024-10-15', '2025-04-15'),

('GDPR-Art.25',
 'Data Protection by Design and by Default',
 'Implement appropriate technical and organisational measures to integrate data protection into processing activities. By default, only personal data necessary for each specific purpose should be processed.',
 'GDPR',
 'Embed privacy into system design. Minimize data collection to what is strictly necessary for payment processing.',
 'In Progress', 3, '2025-01-08', '2025-07-08'),

('GDPR-Art.32',
 'Security of Processing - Encryption and Pseudonymization',
 'Implement appropriate technical measures to ensure data security: pseudonymisation and encryption of personal data, ability to ensure ongoing confidentiality, integrity, availability, resilience of processing systems.',
 'GDPR',
 'Protect personal data against unauthorized access, accidental loss, destruction, or alteration using encryption, access controls, and backup procedures.',
 'Implemented', 3, '2025-01-15', '2025-07-15'),

('GDPR-Art.33',
 'Personal Data Breach Notification within 72 Hours',
 'In the event of a personal data breach, notify the competent supervisory authority within 72 hours of becoming aware of the breach. Where feasible, notify without undue delay.',
 'GDPR',
 'Maintain breach notification readiness. Ensure breach detection, assessment, and reporting within 72 hours regulatory window.',
 'In Progress', 1, '2025-01-10', '2025-07-10'),

('GDPR-Art.37',
 'Data Protection Officer (DPO) Appointment',
 'Appoint a DPO where processing operations require regular and systematic monitoring of data subjects on a large scale. DPO must have expert knowledge of data protection law.',
 'GDPR',
 'Ensure independent data protection oversight. DPO to advise on DPIA, monitor compliance, and act as supervisory authority contact point.',
 'Implemented', 3, '2024-09-01', '2025-09-01'),

-- ISO 27001:2022 Controls
('ISO-A.5.1',
 'Policies for Information Security',
 'Information security policy and topic-specific policies shall be defined, approved by management, published, communicated to and acknowledged by relevant personnel and relevant interested parties, and reviewed at planned intervals.',
 'ISO 27001:2022',
 'Establish management direction and support for information security through a documented policy framework aligned with organizational objectives.',
 'Implemented', 1, '2025-01-01', '2026-01-01'),

('ISO-A.5.23',
 'Information Security for Use of Cloud Services',
 'Processes for acquisition, use, management, and exit from cloud services shall be established in accordance with the organization''s information security requirements.',
 'ISO 27001:2022',
 'Ensure AWS services are configured securely. Define cloud security baseline and continuously monitor compliance against CIS Benchmarks.',
 'In Progress', 5, '2025-01-15', '2025-07-15'),

('ISO-A.8.2',
 'Privileged Access Rights',
 'The allocation and use of privileged access rights shall be restricted and managed. Privileged access shall be reviewed at regular intervals. Least privilege principle shall be enforced.',
 'ISO 27001:2022',
 'Prevent privilege escalation and insider threats. Ensure only authorized personnel have elevated access to production systems.',
 'In Progress', 1, '2024-12-15', '2025-06-15'),

('ISO-A.8.7',
 'Protection Against Malware',
 'Protection against malware shall be implemented and supported by appropriate user awareness. Anti-malware software shall be deployed on all endpoints and servers.',
 'ISO 27001:2022',
 'Detect and prevent malware infections. Maintain up-to-date endpoint protection across all company assets.',
 'Implemented', 2, '2025-01-20', '2025-07-20'),

('ISO-A.8.24',
 'Use of Cryptography',
 'Rules for the effective use of cryptography, including cryptographic key management, shall be defined and implemented. Encryption algorithms must meet current industry standards (AES-256, RSA-2048+).',
 'ISO 27001:2022',
 'Ensure confidentiality and integrity of sensitive data through approved cryptographic standards. Manage encryption keys securely using HSM.',
 'In Progress', 5, '2025-01-10', '2025-07-10'),

('ISO-A.8.28',
 'Secure Coding',
 'Secure coding principles shall be applied to software development. Developers shall be trained in secure coding practices. Code reviews and SAST tooling shall be implemented in the SDLC.',
 'ISO 27001:2022',
 'Eliminate security vulnerabilities in application code. Enforce OWASP Top 10 mitigations in all payment application development.',
 'In Progress', 5, '2025-01-05', '2025-07-05'),

-- RBI PA/PG Guidelines
('RBI-PA.3.1',
 'KYC Verification for Merchant Onboarding',
 'Payment Aggregators must conduct and document KYC verification for all merchants before activation. KYC includes GST certificate, PAN, business registration documents, and beneficial ownership details.',
 'RBI PA/PG Guidelines 2020',
 'Prevent shell company misuse of payment platform. Ensure legitimate merchant onboarding with complete KYC documentation.',
 'Implemented', 6, '2025-01-01', '2025-07-01'),

('RBI-PA.5.2',
 'Data Localization - Transaction Data Storage in India',
 'All payment transaction data involving Indian customers must be stored only in India (data localization). No transaction data shall be stored abroad, even temporarily.',
 'RBI PA/PG Guidelines 2020',
 'Ensure all financial transaction data resides within Indian jurisdictional boundaries. Audit all data flows for cross-border transfers.',
 'Implemented', 3, '2025-01-10', '2025-07-10'),

('RBI-PA.7.1',
 'Information Security Policy for PA/PG',
 'Payment Aggregators must adopt/maintain an Information Security Policy covering network security, access control, encryption, vendor management, and incident response aligned with RBI guidelines.',
 'RBI PA/PG Guidelines 2020',
 'Maintain comprehensive IS policy framework meeting RBI prescriptive requirements for payment aggregators.',
 'Implemented', 1, '2025-01-01', '2026-01-01');

-- ============================================================
-- SECTION 9: RISK-COMPLIANCE MAPPINGS (Realistic linkages)
-- ============================================================

INSERT INTO risk_compliance_mapping (risk_id, control_id, mapping_justification, mapped_by) VALUES
-- RISK-2025-001 (Unauthorized API Access) → Multiple controls
(1, 4,  'MFA for CDE access directly mitigates unauthorized API access using stolen credentials', 1),
(1, 5,  'Comprehensive audit logging detects anomalous API access patterns', 1),
(1, 14, 'ISO privileged access controls limit blast radius of compromised API credentials', 2),

-- RISK-2025-002 (SQL Injection) → Data + Coding controls
(2, 11, 'GDPR Art. 32 encryption protects data even if SQL injection succeeds', 3),
(2, 18, 'Secure coding (ISO A.8.28) directly prevents SQL injection vulnerabilities', 2),
(2, 6,  'PCI-DSS WAF deployment filters SQLi attack patterns at the network layer', 2),

-- RISK-2025-003 (Ransomware)
(3, 17, 'Anti-malware (ISO A.8.7) provides endpoint-level ransomware prevention', 2),
(3, 1,  'Network segmentation (PCI-DSS 1.2) limits ransomware lateral movement', 2),
(3, 5,  'Audit logging enables early detection of ransomware precursor activities', 1),

-- RISK-2025-004 (PCI-DSS Non-Compliance)
(4, 1,  'Firewall configuration compliance is core PCI-DSS Req 1 requirement', 3),
(4, 2,  'SAD protection is PCI-DSS Req 3 - directly relevant to compliance gap', 3),
(4, 6,  'Vulnerability scanning program addresses PCI-DSS Req 11 compliance gap', 3),

-- RISK-2025-008 (Magecart/Skimming)
(8, 3,  'PCI-DSS Req 6.4 payment page integrity monitoring directly targets Magecart attacks', 2),
(8, 6,  'Vulnerability scanning identifies script injection opportunities before attackers', 2),

-- RISK-2025-009 (S3 Misconfiguration)
(9, 17, 'Encryption of S3 objects (ISO A.8.24) limits data exposure from misconfigured buckets', 5),
(9, 15, 'ISO cloud security controls (A.5.23) cover S3 bucket configuration standards', 5),

-- RISK-2025-011 (GDPR DSAR)
(11, 9,  'GDPR Art. 17 right to erasure controls directly address DSAR fulfillment', 3),
(11, 7,  'GDPR Art. 5 processing principles establish lawful basis for handling DSAR', 3),
(11, 13, 'DPO (GDPR Art. 37) oversees DSAR process and regulatory compliance', 3),

-- RISK-2025-013 (Weak Encryption)
(13, 17, 'ISO A.8.24 cryptography controls mandate AES-256 - directly addresses AES-128 gap', 2),
(13, 2,  'PCI-DSS Req 3.3 SAD protection requires strong encryption for stored card data', 2),
(13, 11, 'GDPR Art. 32 encryption requirements align with PCI-DSS Req 3 for card data', 3),

-- RISK-2025-015 (Insufficient Logging)
(15, 5,  'PCI-DSS Req 10.2 audit logging controls directly address log retention gaps', 1),
(15, 14, 'ISO A.5.1 policy framework includes log management policy requirements', 1);

-- ============================================================
-- SECTION 10: REALISTIC AUDIT TRAIL
-- ============================================================

INSERT INTO audit_logs (user_id, action, entity_type, entity_id, details, ip_address, user_agent, created_at) VALUES

-- Recent Activity (Last 7 Days)
(1, 'USER_LOGIN', 'auth', NULL,
 '{"event":"successful_login","user":"sarah.chen","role":"admin","session_duration":null}',
 '203.176.52.10', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
 DATE_SUB(NOW(), INTERVAL 2 HOUR)),

(2, 'RISK_SCORE_UPDATED', 'risks', 1,
 '{"risk_code":"RISK-2025-001","risk_title":"Unauthorized API Access to Payment Gateway","previous_score":16,"new_score":20,"previous_probability":4,"new_probability":4,"previous_impact":4,"new_impact":5,"reason":"Increased impact rating after Q4 merchant security review revealed 3 additional exploit vectors","changed_by":"michael.torres"}',
 '203.176.52.11', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
 DATE_SUB(NOW(), INTERVAL 4 HOUR)),

(3, 'CONTROL_STATUS_UPDATED', 'compliance_controls', 11,
 '{"control_code":"GDPR-Art.32","control_name":"Security of Processing - Encryption and Pseudonymization","previous_status":"In Progress","new_status":"Implemented","evidence":"AES-256 encryption deployed on all customer PII tables. HSM key rotation automated. Evidence document: GRC-EVD-2025-0089","updated_by":"priya.sharma"}',
 '203.176.52.12', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
 DATE_SUB(NOW(), INTERVAL 6 HOUR)),

(4, 'COMPLIANCE_REPORT_EXPORTED', 'compliance_controls', NULL,
 '{"report_type":"Q4 2025 ISO 27001 Compliance Report","format":"PDF","controls_covered":22,"compliant_controls":14,"non_compliant_controls":8,"compliance_percentage":63.6,"exported_by":"james.wilson","purpose":"External audit preparation for ISO 27001:2022 recertification"}',
 '203.176.52.13', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
 DATE_SUB(NOW(), INTERVAL 8 HOUR)),

(2, 'RISK_CREATED', 'risks', 23,
 '{"risk_code":"RISK-2025-023","risk_title":"Key Person Dependency - Single Cloud Architect","risk_level":"Low","probability":2,"impact":2,"category":"Operational & Infrastructure","created_by":"michael.torres"}',
 '203.176.52.11', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
 DATE_SUB(NOW(), INTERVAL 1 DAY)),

(3, 'RISK_CONTROL_MAPPED', 'risk_compliance_mapping', 11,
 '{"risk_id":2,"risk_code":"RISK-2025-002","risk_title":"Customer PII Data Breach via SQL Injection","control_id":11,"control_code":"GDPR-Art.32","control_name":"Security of Processing - Encryption","justification":"GDPR Art.32 encryption requirements protect PII even if SQL injection extracts raw data from database","mapped_by":"priya.sharma"}',
 '203.176.52.12', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
 DATE_SUB(NOW(), INTERVAL 1 DAY)),

(1, 'RISK_TREATMENT_PLAN_APPROVED', 'risks', 3,
 '{"risk_code":"RISK-2025-003","risk_title":"Ransomware Encryption of Transaction Database","treatment_type":"Mitigate","approved_by":"sarah.chen","approver_role":"CISO","estimated_cost":"INR 45,00,000","expected_residual_risk":"Low","target_completion":"2025-06-30"}',
 '203.176.52.10', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
 DATE_SUB(NOW(), INTERVAL 2 DAY)),

(5, 'VULNERABILITY_SCAN_INITIATED', 'compliance_controls', 6,
 '{"scan_type":"External Vulnerability Scan (ASV)","control_code":"PCI-DSS-11.3","vendor":"Trustwave Holdings","scope":"All external-facing payment API endpoints","initiated_by":"ravi.kumar","scheduled_completion":"2025-03-01"}',
 '10.0.1.50', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
 DATE_SUB(NOW(), INTERVAL 2 DAY)),

(4, 'AUDIT_TRAIL_VIEWED', 'audit_logs', NULL,
 '{"filter_applied":"last_7_days","user_filter":"all","action_filter":"RISK_SCORE_UPDATED","records_viewed":12,"exported":false,"viewed_by":"james.wilson","purpose":"Weekly audit review for board reporting"}',
 '203.176.52.13', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
 DATE_SUB(NOW(), INTERVAL 3 DAY)),

(2, 'RISK_STATUS_UPDATED', 'risks', 14,
 '{"risk_code":"RISK-2025-014","risk_title":"SWIFT/NEFT Integration Vulnerability","previous_status":"Identified","new_status":"Mitigating","action_taken":"Rotated all hardcoded SFTP credentials. Migrated to AWS Secrets Manager. GitGuardian deployment in progress.","updated_by":"michael.torres"}',
 '203.176.52.11', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
 DATE_SUB(NOW(), INTERVAL 3 DAY)),

(3, 'USER_LOGIN', 'auth', NULL,
 '{"event":"successful_login","user":"priya.sharma","role":"compliance_officer","mfa_used":true}',
 '203.176.52.12', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
 DATE_SUB(NOW(), INTERVAL 3 DAY)),

(6, 'MERCHANT_KYC_COMPLETED', 'compliance_controls', 20,
 '{"merchant_id":"MERCH-2025-0891","merchant_name":"FoodMart Express Pvt Ltd","kyc_status":"Approved","documents_verified":["GST Certificate","PAN Card","Business Registration","Beneficial Ownership Declaration"],"control_code":"RBI-PA.3.1","completed_by":"ananya.mehta"}',
 '203.176.52.14', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
 DATE_SUB(NOW(), INTERVAL 4 DAY)),

(1, 'USER_LOGOUT', 'auth', NULL,
 '{"event":"user_logout","user":"sarah.chen","session_duration_minutes":47}',
 '203.176.52.10', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
 DATE_SUB(NOW(), INTERVAL 4 DAY)),

(2, 'RISK_SCORE_UPDATED', 'risks', 8,
 '{"risk_code":"RISK-2025-008","risk_title":"Payment Page Skimming (Magecart Attack)","previous_score":9,"new_score":12,"reason":"Updated after discovering 2 additional JavaScript dependencies loaded from CDNs without SRI hashes","changed_by":"michael.torres"}',
 '203.176.52.11', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
 DATE_SUB(NOW(), INTERVAL 5 DAY)),

(4, 'COMPLIANCE_REPORT_EXPORTED', 'compliance_controls', NULL,
 '{"report_type":"GDPR Compliance Status Report - February 2025","format":"PDF","gdpr_controls":7,"implemented":4,"in_progress":3,"not_started":0,"gdpr_compliance_pct":78.5,"exported_by":"james.wilson","purpose":"Monthly compliance status update for DPO review"}',
 '203.176.52.13', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
 DATE_SUB(NOW(), INTERVAL 5 DAY)),

(5, 'RISK_ACCEPTED', 'risks', 23,
 '{"risk_code":"RISK-2025-023","risk_title":"Key Person Dependency - Single Cloud Architect","treatment_type":"Accept","acceptance_rationale":"Low risk score (4). Infrastructure-as-code documentation project initiated. Cross-training plan approved for Q2 2025. Risk owner: Ravi Kumar","accepted_by":"sarah.chen","accepted_role":"CISO"}',
 '203.176.52.10', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
 DATE_SUB(NOW(), INTERVAL 6 DAY)),

(3, 'CONTROL_EVIDENCE_UPLOADED', 'compliance_controls', 7,
 '{"control_code":"GDPR-Art.5","evidence_file":"GDPR_RoPA_PaySecure_Feb2025.pdf","evidence_type":"Record of Processing Activities (Art.30)","uploaded_by":"priya.sharma","document_size_kb":284}',
 '203.176.52.12', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
 DATE_SUB(NOW(), INTERVAL 7 DAY)),

(1, 'USER_ACCOUNT_LOCKED', 'users', 5,
 '{"event":"account_locked_max_attempts","affected_user":"ravi.kumar","failed_attempts":5,"locked_duration_minutes":30,"unlocked_by":"sarah.chen","unlock_reason":"Confirmed legitimate user - password reset initiated"}',
 '203.176.52.99', 'Unknown',
 DATE_SUB(NOW(), INTERVAL 7 DAY));

-- ============================================================
-- SECTION 11: VERIFICATION QUERIES
-- ============================================================

SELECT '=== SEED DATA SUMMARY ===' AS '';
SELECT COUNT(*) AS total_users FROM users;
SELECT COUNT(*) AS total_risks FROM risks;
SELECT COUNT(*) AS total_controls FROM compliance_controls;
SELECT COUNT(*) AS total_mappings FROM risk_compliance_mapping;
SELECT COUNT(*) AS total_audit_logs FROM audit_logs;
SELECT '' AS '';
SELECT '=== RISK BREAKDOWN BY LEVEL ===' AS '';
SELECT risk_level, COUNT(*) AS count FROM risks GROUP BY risk_level;
SELECT '' AS '';
SELECT '=== COMPLIANCE STATUS ===' AS '';
SELECT regulation, implementation_status, COUNT(*) AS count 
FROM compliance_controls 
GROUP BY regulation, implementation_status 
ORDER BY regulation, implementation_status;
