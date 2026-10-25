"""MathTeacher AI shared provider layer and AI-group contracts."""

from .config import AIPlatformConfig
from .contracts import AIProvider, AIRequest, AIResponse
from .factory import build_ai_provider

__all__ = ["AIPlatformConfig", "AIProvider", "AIRequest", "AIResponse", "build_ai_provider"]
