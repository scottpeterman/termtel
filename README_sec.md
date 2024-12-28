# Secure Credentials Management System

## Overview

The Secure Credentials Management System is a cross-platform solution for securely storing and managing sensitive credentials in desktop applications. It implements industry-standard encryption practices while providing a modern, user-friendly interface. The system is designed to work across Windows, macOS, and Linux platforms, utilizing platform-specific secure storage locations and machine-specific identifiers.

## Architecture

### Core Components

1. **SecureCredentials Class (`credslib.py`)**
   - Handles all cryptographic operations
   - Manages secure storage and retrieval of credentials
   - Implements platform-specific storage locations
   - Provides machine-specific identity verification

2. **WebPasswordDialog Class**
   - Provides a modern, secure login interface
   - Implements rate limiting and attempt tracking
   - Handles credential reset functionality
   - Manages user session security

### Security Features

#### Encryption and Key Derivation
- Uses PBKDF2-HMAC-SHA256 for key derivation
- Implements 480,000 iterations for computational resistance
- Employs Fernet (AES-128-CBC) with HMAC authentication
- Generates and securely stores unique salts

#### Platform Security
- Windows: Uses APPDATA directory and MachineGuid
- macOS: Uses Application Support directory and hardware serial
- Linux: Uses .config directory and machine-id
- Fallback mechanisms for each platform

#### Access Control
- Master password authentication
- Rate limiting with maximum attempt tracking
- Machine-specific binding
- Session management
- Secure credential reset functionality

## Implementation Details

### Credential Storage Structure

```yaml
last_modified: "2024-12-27T10:30:00"
credentials:
    - username: "user123"
      password: "<encrypted_string>"
      service: "service_name"
```

### Encryption Process

1. **Key Derivation**
```python
kdf = PBKDF2HMAC(
    algorithm=hashes.SHA256(),
    length=32,
    salt=salt,
    iterations=480000,
)
key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
```

2. **Data Encryption**
```python
def encrypt_value(self, value: str) -> str:
    if not self._fernet:
        raise RuntimeError("Credential manager not unlocked")
    encrypted = self._fernet.encrypt(value.encode())
    return base64.b64encode(encrypted).decode('utf-8')
```

### Authentication Flow

1. **Initial Setup**
   - Check for existing credentials store
   - If none exists:
     - Prompt for new master password
     - Generate salt and derive encryption key
     - Create empty credentials file
     - Store machine identifier

2. **Unlock Process**
   - Verify machine identifier
   - Load stored salt
   - Derive key from master password
   - Verify key with test encryption
   - Load and decrypt credentials

## User Interface

The system implements a modern, cyberpunk-themed interface with:

- Password strength indicators
- Clear error messaging
- Visual feedback
- Secure input handling
- Reset functionality

### UI Security Features

1. **Input Protection**
```javascript
// Sanitize and validate all user input
if (!input.value.trim()) {
    document.getElementById('error-message').textContent = 'Password cannot be empty';
    return;
}
```

2. **Rate Limiting**
```python
self.attempts += 1
if self.attempts >= self.max_attempts:
    self.dialog.reject()
```

## Usage Example

### Basic Implementation

```python
from secure_cartography.credslib import SecureCredentials

# Initialize the credential manager
creds_manager = SecureCredentials()

# Setup new credentials store
if not creds_manager.is_initialized:
    success = creds_manager.setup_new_credentials(master_password)

# Unlock existing store
if creds_manager.unlock(master_password):
    # Load credentials
    creds = creds_manager.load_credentials(creds_path)
```

### Integration Example

```python
class MyApplication:
    def __init__(self):
        self.cred_manager = SecureCredentials()
        self.initialize_credentials()

    def initialize_credentials(self):
        dialog = WebPasswordDialog(self.cred_manager)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.start_application()
        else:
            sys.exit()
```

## Security Best Practices

1. **Password Requirements**
   - Minimum length: 12 characters
   - Must contain: uppercase, lowercase, numbers, special characters
   - Implement password strength indicators

2. **Error Handling**
   - Never reveal specific encryption details in errors
   - Use generic error messages for security-related failures
   - Implement proper logging with sensitive data sanitization

3. **Session Management**
   - Implement session timeouts
   - Clear sensitive data from memory after use
   - Implement secure session termination

## Platform-Specific Considerations

### Windows
```python
with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                    "SOFTWARE\\Microsoft\\Cryptography",
                    0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
    return winreg.QueryValueEx(key, "MachineGuid")[0]
```

### macOS
```python
result = subprocess.run(['system_profiler', 'SPHardwareDataType'],
                        capture_output=True, text=True)
```

### Linux
```python
with open("/etc/machine-id", "r") as f:
    return f.read().strip()
```

## Contributing

When contributing to this system, ensure:

1. All cryptographic operations use approved algorithms
2. Platform-specific code is properly isolated
3. Error handling follows security best practices
4. User interface maintains security features
5. All changes include appropriate tests

## Testing

Implement tests for:

1. Cryptographic operations
2. Platform-specific features
3. Error handling
4. User interface functionality
5. Security feature verification

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Security Considerations

Remember to:

1. Regular security audits
2. Keep dependencies updated
3. Monitor for cryptographic vulnerabilities
4. Implement secure update mechanisms
5. Maintain proper key rotation policies

For more information on implementation details or security considerations, please refer to the source code documentation or contact the development team.
# Example 1: YAML Credential Storage
import yaml
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

class YAMLCredentialManager:
    def __init__(self, secure_creds):
        self.secure_creds = secure_creds
        self.config_dir = secure_creds._get_config_dir()
        self.creds_file = self.config_dir / "credentials.yaml"

    def add_credential(self, username: str, password: str, service: str) -> bool:
        """Add or update a credential entry."""
        try:
            # Load existing credentials
            credentials = self.load_credentials()
            
            # Create new credential entry
            new_cred = {
                'username': username,
                'password': self.secure_creds.encrypt_value(password),
                'service': service,
                'last_modified': datetime.now().isoformat()
            }
            
            # Update existing or append new
            for cred in credentials:
                if cred['username'] == username and cred['service'] == service:
                    cred.update(new_cred)
                    break
            else:
                credentials.append(new_cred)
            
            # Save updated credentials
            self.save_credentials(credentials)
            return True
            
        except Exception as e:
            logger.error(f"Failed to add credential: {e}")
            return False

    def get_credential(self, username: str, service: str) -> Optional[Dict]:
        """Retrieve a specific credential."""
        try:
            credentials = self.load_credentials()
            for cred in credentials:
                if cred['username'] == username and cred['service'] == service:
                    decrypted_cred = cred.copy()
                    decrypted_cred['password'] = self.secure_creds.decrypt_value(
                        cred['password']
                    )
                    return decrypted_cred
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve credential: {e}")
            return None

    def load_credentials(self) -> List[Dict]:
        """Load all credentials from YAML file."""
        if not self.creds_file.exists():
            return []
            
        with open(self.creds_file) as f:
            data = yaml.safe_load(f) or {'credentials': []}
        return data.get('credentials', [])

    def save_credentials(self, credentials: List[Dict]) -> None:
        """Save credentials to YAML file."""
        with open(self.creds_file, 'w') as f:
            yaml.safe_dump({
                'last_modified': datetime.now().isoformat(),
                'credentials': credentials
            }, f)

# Usage example for YAML storage
def yaml_example():
    # Initialize secure credentials
    secure_creds = SecureCredentials(app_name="MyApp")
    if not secure_creds.is_initialized:
        secure_creds.setup_new_credentials("master_password")
    secure_creds.unlock("master_password")
    
    # Initialize YAML manager
    yaml_manager = YAMLCredentialManager(secure_creds)
    
    # Add new credential
    yaml_manager.add_credential(
        username="admin",
        password="secretpass123",
        service="myapp"
    )
    
    # Retrieve credential
    cred = yaml_manager.get_credential("admin", "myapp")
    if cred:
        print(f"Found credential: {cred['username']}, {cred['password']}")

# Example 2: SQLite Credential Storage
import sqlite3
from contextlib import contextmanager

class SQLiteCredentialManager:
    def __init__(self, secure_creds, db_path: str):
        self.secure_creds = secure_creds
        self.db_path = db_path
        self.initialize_db()

    @contextmanager
    def get_db_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def initialize_db(self):
        """Initialize SQLite database with required schema."""
        with self.get_db_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username VARCHAR(150) NOT NULL UNIQUE,
                    password VARCHAR(150),
                    ldap_user BOOLEAN,
                    is_admin BOOLEAN
                )
            """)
            conn.commit()

    def add_user(self, username: str, password: Optional[str] = None,
                 ldap_user: bool = False, is_admin: bool = False) -> bool:
        """Add or update a user in the database."""
        try:
            # Encrypt password if provided
            encrypted_password = None
            if password:
                encrypted_password = self.secure_creds.encrypt_value(password)

            with self.get_db_connection() as conn:
                conn.execute("""
                    INSERT INTO users (username, password, ldap_user, is_admin)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(username) DO UPDATE SET
                        password = excluded.password,
                        ldap_user = excluded.ldap_user,
                        is_admin = excluded.is_admin
                """, (username, encrypted_password, ldap_user, is_admin))
                conn.commit()
            return True

        except Exception as e:
            logger.error(f"Failed to add/update user: {e}")
            return False

    def get_user(self, username: str) -> Optional[Dict]:
        """Retrieve user details from database."""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.execute("""
                    SELECT username, password, ldap_user, is_admin
                    FROM users WHERE username = ?
                """, (username,))
                row = cursor.fetchone()
                
                if not row:
                    return None
                    
                user_dict = {
                    'username': row[0],
                    'password': None,
                    'ldap_user': bool(row[2]),
                    'is_admin': bool(row[3])
                }
                
                # Decrypt password if exists and not LDAP user
                if row[1] and not user_dict['ldap_user']:
                    user_dict['password'] = self.secure_creds.decrypt_value(row[1])
                
                return user_dict

        except Exception as e:
            logger.error(f"Failed to retrieve user: {e}")
            return None

    def verify_user_password(self, username: str, password: str) -> bool:
        """Verify user's password."""
        try:
            user = self.get_user(username)
            if not user or user['ldap_user'] or not user['password']:
                return False
            return user['password'] == password

        except Exception as e:
            logger.error(f"Failed to verify password: {e}")
            return False

# Usage example for SQLite storage
def sqlite_example():
    # Initialize secure credentials
    secure_creds = SecureCredentials(app_name="MyApp")
    if not secure_creds.is_initialized:
        secure_creds.setup_new_credentials("master_password")
    secure_creds.unlock("master_password")
    
    # Initialize SQLite manager
    db_path = Path.home() / ".myapp" / "users.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    sqlite_manager = SQLiteCredentialManager(secure_creds, str(db_path))
    
    # Add regular user
    sqlite_manager.add_user(
        username="user1",
        password="userpass123",
        ldap_user=False,
        is_admin=False
    )
    
    # Add LDAP user
    sqlite_manager.add_user(
        username="ldapuser",
        ldap_user=True,
        is_admin=True
    )
    
    # Verify password
    is_valid = sqlite_manager.verify_user_password("user1", "userpass123")
    print(f"Password valid: {is_valid}")
    
    # Retrieve user
    user = sqlite_manager.get_user("ldapuser")
    if user:
        print(f"Found user: {user['username']}, LDAP: {user['ldap_user']}")