"""
Tools module - DOE Execution Layer

All tools that agents use to interact with external services.
"""

from .apify import (
    analisar_perfil_instagram,
    buscar_ads_meta_library,
    buscar_google_trends,
    buscar_reels_virais,
    buscar_videos_youtube,
    monitorar_canal_youtube,
)
from .calendar import (
    CalComService,
    agendar_consulta,
    cancelar_consulta,
    listar_consultas,
    verificar_disponibilidade,
)
from .chatwoot import ChatwootService
from .crm import (
    atualizar_lead,
    buscar_lead,
    criar_lead,
    listar_leads,
    mover_pipeline,
)
from .database_tools import (
    atualizar_aprovacao,
    buscar_aprovacoes_pendentes,
    buscar_contexto_cliente,
    criar_aprovacao,
    salvar_mensagem,
)
from .image_gen import (
    gerar_imagem,
    gerar_imagem_nanobanana,
    gerar_variacao_nanobanana,
    gerar_variantes,
)
from .instagram_publish import agendar_post, publicar_post, publicar_story
from .notifications import notificar_admin, notificar_esposa
from .whatsapp import WhatsAppService, get_whatsapp_service

__all__ = [
    # WhatsApp
    "WhatsAppService",
    "get_whatsapp_service",
    # Chatwoot
    "ChatwootService",
    # CRM
    "buscar_lead",
    "criar_lead",
    "atualizar_lead",
    "mover_pipeline",
    "listar_leads",
    # Calendar (Cal.com)
    "CalComService",
    "verificar_disponibilidade",
    "agendar_consulta",
    "cancelar_consulta",
    "listar_consultas",
    # Apify
    "buscar_reels_virais",
    "analisar_perfil_instagram",
    "buscar_ads_meta_library",
    "buscar_videos_youtube",
    "monitorar_canal_youtube",
    "buscar_google_trends",
    # Image Gen
    "gerar_imagem",
    "gerar_imagem_nanobanana",
    "gerar_variacao_nanobanana",
    "gerar_variantes",
    # Instagram Publish
    "publicar_post",
    "agendar_post",
    "publicar_story",
    # Database
    "buscar_contexto_cliente",
    "salvar_mensagem",
    "criar_aprovacao",
    "atualizar_aprovacao",
    "buscar_aprovacoes_pendentes",
    # Notifications
    "notificar_esposa",
    "notificar_admin",
]
