"""
Cliente LLM unificado - suporta Gemini API direta e Vertex AI.

Este módulo abstrai a diferença entre:
- Gemini API direta (google.generativeai) - chaves AIza...
- Vertex AI (vertexai) - chaves AQ... ou autenticação Google Cloud

Detecta automaticamente qual usar baseado na chave fornecida.
"""

import os
from typing import Optional, Any

# Tenta importar ambas as bibliotecas
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    import vertexai
    from vertexai.generative_models import GenerativeModel as VertexGenerativeModel
    VERTEX_AVAILABLE = True
except ImportError:
    VERTEX_AVAILABLE = False


class LLMClient:
    """
    Cliente unificado para LLM que suporta Gemini API e Vertex AI.
    
    Detecta automaticamente qual usar baseado na chave:
    - Chaves começando com "AIza" → Gemini API direta
    - Chaves começando com "AQ" → Vertex AI
    """
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash", 
                 project_id: Optional[str] = None, location: str = "us-central1"):
        """
        Inicializa o cliente LLM.
        
        Args:
            api_key: Chave de API (AIza... para Gemini API ou AQ... para Vertex AI)
            model_name: Nome do modelo (ex: "gemini-2.5-flash")
            project_id: ID do projeto Google Cloud (necessário para Vertex AI)
            location: Localização do Vertex AI (padrão: us-central1)
        """
        self.api_key = api_key
        self.model_name = model_name
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = location
        self.model = None
        self.client_type = None
        
        if not api_key:
            return
        
        # Detecta tipo de chave
        if api_key.startswith("AIza"):
            # Gemini API direta
            self._init_gemini_api()
        elif api_key.startswith("AQ") or project_id:
            # Vertex AI
            self._init_vertex_ai()
        else:
            # Tenta Gemini API primeiro
            try:
                self._init_gemini_api()
            except:
                # Se falhar, tenta Vertex AI
                self._init_vertex_ai()
    
    def _init_gemini_api(self):
        """Inicializa cliente Gemini API direta."""
        if not GEMINI_AVAILABLE:
            raise ImportError("google-generativeai não está instalado. Execute: uv add google-generativeai")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)
        self.client_type = "gemini_api"
    
    def _init_vertex_ai(self):
        """Inicializa cliente Vertex AI."""
        if not VERTEX_AVAILABLE:
            raise ImportError(
                "vertexai não está instalado. Execute: uv add google-cloud-aiplatform\n"
                "E configure autenticação: https://cloud.google.com/vertex-ai/docs/authentication"
            )
        
        if not self.project_id:
            raise ValueError(
                "Para usar Vertex AI, você precisa configurar GOOGLE_CLOUD_PROJECT no .env\n"
                "Exemplo: GOOGLE_CLOUD_PROJECT=meu-projeto-123456\n"
                "Ou passar project_id ao inicializar LLMClient\n\n"
                "Encontre o Project ID em: https://console.cloud.google.com/"
            )
        
        # Inicializa Vertex AI
        # Vertex AI usa Application Default Credentials (gcloud auth application-default login)
        # ou variável GOOGLE_APPLICATION_CREDENTIALS apontando para service account JSON
        try:
            vertexai.init(project=self.project_id, location=self.location)
            self.model = VertexGenerativeModel(self.model_name)
            self.client_type = "vertex_ai"
        except Exception as e:
            raise ValueError(
                f"Erro ao inicializar Vertex AI: {e}\n\n"
                "Certifique-se de:\n"
                "1. Ter autenticado: gcloud auth application-default login\n"
                "2. Ter habilitado Vertex AI API no console\n"
                "3. Ter o project_id correto"
            )
    
    def generate_content(self, prompt: str, **kwargs) -> Any:
        """
        Gera conteúdo usando o modelo configurado.
        
        Args:
            prompt: Texto do prompt
            **kwargs: Argumentos adicionais para o modelo
            
        Returns:
            Resposta do modelo (compatível com ambas as APIs)
        """
        if not self.model:
            raise ValueError("Modelo não inicializado. Verifique a chave de API.")
        
        # Ambas as APIs têm interface similar
        response = self.model.generate_content(prompt, **kwargs)
        return response
    
    def __repr__(self) -> str:
        return f"LLMClient(type={self.client_type}, model={self.model_name})"


def create_llm_client(api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash",
                     project_id: Optional[str] = None) -> LLMClient:
    """
    Função helper para criar cliente LLM.
    
    Args:
        api_key: Chave de API
        model_name: Nome do modelo
        project_id: ID do projeto Google Cloud (para Vertex AI)
        
    Returns:
        LLMClient configurado
    """
    return LLMClient(api_key=api_key, model_name=model_name, project_id=project_id)

