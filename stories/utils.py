from typing import List, Optional
import logging
import base64
import hashlib
import os
import uuid

import requests
from django.conf import settings
from .ai_engine import generate_with_lang_stack

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Lightweight deterministic embedding provider for SQLite-first setup."""

    _instance = None
    _dim = 384

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def dimension(self) -> int:
        return self._dim

    def generate(self, text: str) -> List[float]:
        if not text:
            return [0.0] * self.dimension

        digest = hashlib.sha256(text.encode('utf-8')).digest()
        numbers = []
        for index in range(self.dimension):
            byte = digest[index % len(digest)]
            numbers.append((byte / 255.0) * 2.0 - 1.0)
        return numbers


embedding_service = EmbeddingService()


def generate_embedding(text: str) -> List[float]:
    """
    Generate embedding for given text using sentence-transformers.
    
    Args:
        text: The text to generate embedding for
        
    Returns:
        List of floats representing the embedding vector
    """
    return embedding_service.generate(text)


def generate_story_segment(context: str, user_prompt: str) -> str:
    """
    Generate a story segment using LLM with RAG context.
    
    This is a placeholder function. In production, you would integrate with:
    - OpenAI GPT models
    - Anthropic Claude
    - Local models like Llama 2
    - Hugging Face Transformers
    
    Args:
        context: Retrieved context from previous story segments
        user_prompt: User's prompt for continuing the story
        
    Returns:
        Generated story segment text
    """
    return generate_with_lang_stack(context, user_prompt)


def generate_image(prompt: str, style: Optional[str] = None) -> str:
    """
    Generate an image for a story segment using diffusion models.
    
    This is a placeholder function. In production, you would integrate with:
    - Stable Diffusion
    - DALL-E
    - Midjourney API
    - Hugging Face Diffusers
    
    Args:
        prompt: Text description for image generation
        style: Optional style specification
        
    Returns:
        URL or path to the generated image
    """
    gemini_api_key = os.getenv('GEMINI_API_KEY', '').strip()
    if not gemini_api_key:
        return f"https://placeholder.com/image?text={prompt.replace(' ', '+')}"

    model = os.getenv('GEMINI_IMAGE_MODEL', 'gemini-2.0-flash-exp')
    endpoint = (
        os.getenv('GEMINI_IMAGE_API_URL')
        or f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_api_key}"
    )
    composed_prompt = prompt if not style else f"{prompt}. Style: {style}."

    payload = {
        'contents': [{'parts': [{'text': composed_prompt}]}],
        'generationConfig': {'responseModalities': ['TEXT', 'IMAGE']},
    }

    try:
        response = requests.post(endpoint, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()

        candidates = data.get('candidates', [])
        for candidate in candidates:
            parts = candidate.get('content', {}).get('parts', [])
            for part in parts:
                inline_data = part.get('inlineData') or part.get('inline_data')
                if not inline_data:
                    continue
                raw_b64 = inline_data.get('data')
                if not raw_b64:
                    continue

                binary_data = base64.b64decode(raw_b64)
                os.makedirs(os.path.join(settings.MEDIA_ROOT, 'generated_images'), exist_ok=True)
                filename = f"generated_images/{uuid.uuid4()}.png"
                file_path = os.path.join(settings.MEDIA_ROOT, filename)
                with open(file_path, 'wb') as file_handle:
                    file_handle.write(binary_data)
                return f"{settings.MEDIA_URL}{filename}"
    except Exception as error:
        logger.warning("Gemini image generation failed, using placeholder: %s", error)

    return f"https://placeholder.com/image?text={prompt.replace(' ', '+')}"


def perform_rag_search(story_id: int, query_embedding: List[float], top_k: int = 5) -> List[str]:
    """
    Perform RAG search to find relevant story segments.
    
    Args:
        story_id: ID of the story to search within
        query_embedding: Embedding of the user's query
        top_k: Number of top results to return
        
    Returns:
        List of relevant story segment texts
    """
    from .models import FlashCard
    
    try:
        recent_cards = FlashCard.objects.filter(story_id=story_id).order_by('-created_at')[:top_k]
        return [card.content_text for card in reversed(list(recent_cards))]
    except Exception as error:
        logger.error("Error in RAG search: %s", error)
        return [] 