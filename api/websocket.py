"""
WebSocket handler for real-time updates and authentication system.
"""

import asyncio
import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field

from fastapi import WebSocket, WebSocketDisconnect, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel


# ==================== Configuration ====================

SECRET_KEY = secrets.token_hex(32)  # Generate on startup
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


# ==================== Models ====================

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserLogin(BaseModel):
    username: str
    password: str


class User(BaseModel):
    username: str
    role: str = "user"  # user, admin
    disabled: bool = False


@dataclass
class WSMessage:
    """WebSocket message structure."""
    type: str  # scan_update, finding_new, project_update, etc.
    data: dict
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


# ==================== In-Memory User Store (Demo) ====================

# In production, use proper database with hashed passwords
USERS_DB = {
    "admin": {
        "username": "admin",
        "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
        "role": "admin",
        "disabled": False
    },
    "user": {
        "username": "user",
        "password_hash": hashlib.sha256("user123".encode()).hexdigest(),
        "role": "user",
        "disabled": False
    }
}


# ==================== Authentication Functions ====================

def hash_password(password: str) -> str:
    """Hash password with SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return hash_password(plain_password) == hashed_password


def get_user(username: str) -> Optional[dict]:
    """Get user from database."""
    return USERS_DB.get(username)


def authenticate_user(username: str, password: str) -> Optional[dict]:
    """Authenticate user with username and password."""
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    if user.get("disabled"):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """Decode and verify JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# ==================== Auth Dependencies ====================

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Get current authenticated user from token."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = credentials.credentials
    payload = decode_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    username = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    user_data = get_user(username)
    if user_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return User(
        username=user_data["username"],
        role=user_data["role"],
        disabled=user_data.get("disabled", False)
    )


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Ensure current user is active."""
    if current_user.disabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    return current_user


async def require_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Require admin role."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


# ==================== WebSocket Connection Manager ====================

class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "global": set(),
        }
        self.user_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, channel: str = "global", user_id: str = None):
        """Accept WebSocket connection and add to channel."""
        await websocket.accept()
        
        if channel not in self.active_connections:
            self.active_connections[channel] = set()
        
        self.active_connections[channel].add(websocket)
        
        if user_id:
            self.user_connections[user_id] = websocket
    
    def disconnect(self, websocket: WebSocket, channel: str = "global", user_id: str = None):
        """Remove WebSocket from channel."""
        if channel in self.active_connections:
            self.active_connections[channel].discard(websocket)
        
        if user_id and user_id in self.user_connections:
            del self.user_connections[user_id]
    
    async def send_personal(self, message: dict, websocket: WebSocket):
        """Send message to specific connection."""
        try:
            await websocket.send_json(message)
        except Exception:
            pass
    
    async def send_to_user(self, message: dict, user_id: str):
        """Send message to specific user."""
        websocket = self.user_connections.get(user_id)
        if websocket:
            await self.send_personal(message, websocket)
    
    async def broadcast(self, message: dict, channel: str = "global"):
        """Broadcast message to all connections in a channel."""
        connections = self.active_connections.get(channel, set())
        
        for connection in list(connections):
            try:
                await connection.send_json(message)
            except Exception:
                # Connection probably closed
                connections.discard(connection)
    
    async def broadcast_all(self, message: dict):
        """Broadcast to all connections in all channels."""
        for channel in self.active_connections:
            await self.broadcast(message, channel)
    
    def get_connection_count(self, channel: str = None) -> int:
        """Get number of active connections."""
        if channel:
            return len(self.active_connections.get(channel, set()))
        return sum(len(c) for c in self.active_connections.values())


# Global connection manager
manager = ConnectionManager()


# ==================== Event Emitters ====================

async def emit_scan_update(scan_id: int, status: str, progress: int = 0):
    """Emit scan status update."""
    await manager.broadcast({
        "type": "scan_update",
        "data": {
            "scan_id": scan_id,
            "status": status,
            "progress": progress
        },
        "timestamp": datetime.now().isoformat()
    })


async def emit_finding_new(project_id: int, finding: dict):
    """Emit new finding notification."""
    await manager.broadcast({
        "type": "finding_new",
        "data": {
            "project_id": project_id,
            "finding": finding
        },
        "timestamp": datetime.now().isoformat()
    }, channel=f"project_{project_id}")


async def emit_project_update(project_id: int, action: str = "updated"):
    """Emit project update notification."""
    await manager.broadcast({
        "type": "project_update",
        "data": {
            "project_id": project_id,
            "action": action
        },
        "timestamp": datetime.now().isoformat()
    })


# ==================== WebSocket Routes (to add to main.py) ====================

async def websocket_endpoint(websocket: WebSocket, channel: str = "global"):
    """
    WebSocket endpoint for real-time updates.
    
    Usage:
        Connect to ws://localhost:8000/ws/global for global updates
        Connect to ws://localhost:8000/ws/project_1 for project-specific updates
    """
    await manager.connect(websocket, channel)
    
    try:
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "channel": channel,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_json()
            
            # Handle ping/pong
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            
            # Handle subscribe to additional channel
            elif data.get("type") == "subscribe":
                new_channel = data.get("channel")
                if new_channel:
                    if new_channel not in manager.active_connections:
                        manager.active_connections[new_channel] = set()
                    manager.active_connections[new_channel].add(websocket)
                    await websocket.send_json({
                        "type": "subscribed",
                        "channel": new_channel
                    })
            
            # Handle unsubscribe
            elif data.get("type") == "unsubscribe":
                old_channel = data.get("channel")
                if old_channel and old_channel in manager.active_connections:
                    manager.active_connections[old_channel].discard(websocket)
                    await websocket.send_json({
                        "type": "unsubscribed",
                        "channel": old_channel
                    })
                    
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)
    except Exception:
        manager.disconnect(websocket, channel)


# ==================== Auth Routes (to add to main.py) ====================

def create_auth_routes(app):
    """Add authentication routes to FastAPI app."""
    
    @app.post("/api/auth/login", response_model=Token)
    async def login(credentials: UserLogin):
        """Login and get access token."""
        user = authenticate_user(credentials.username, credentials.password)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["username"], "role": user["role"]},
            expires_delta=access_token_expires
        )
        
        return Token(
            access_token=access_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    @app.get("/api/auth/me")
    async def get_me(current_user: User = Depends(get_current_active_user)):
        """Get current user info."""
        return current_user
    
    @app.post("/api/auth/refresh", response_model=Token)
    async def refresh_token(current_user: User = Depends(get_current_active_user)):
        """Refresh access token."""
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": current_user.username, "role": current_user.role},
            expires_delta=access_token_expires
        )
        
        return Token(
            access_token=access_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    @app.websocket("/ws/{channel}")
    async def ws_endpoint(websocket: WebSocket, channel: str = "global"):
        """WebSocket endpoint."""
        await websocket_endpoint(websocket, channel)
    
    return app
