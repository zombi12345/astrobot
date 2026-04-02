from .start import router as start_router
from .ai_handler import router as ai_router
from .natal import router as natal_router
from .admin_simple import router as admin_router
from .horoscope import router as horoscope_router
from .profile import router as profile_router
from .pdf_handler import router as pdf_router

__all__ = [
    'start_router',
    'ai_router',
    'natal_router',
    'admin_router',
    'horoscope_router',
    'profile_router',
    'pdf_router'
]