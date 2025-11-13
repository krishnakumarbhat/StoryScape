from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist
from .models import Story, FlashCard, CardConnection
from .utils import (
    generate_embedding, 
    generate_story_segment, 
    generate_image, 
    perform_rag_search
)
import logging

logger = logging.getLogger(__name__)


@shared_task
def generate_story_segment_task(story_id: int, user_prompt: str, parent_card_id: int = None):
    """
    Celery task to generate a new story segment using RAG pipeline.
    
    Args:
        story_id: ID of the story
        user_prompt: User's prompt for continuing the story
        parent_card_id: ID of the parent card to connect from
    """
    try:
        story = Story.objects.get(id=story_id)
        
        # Generate embedding for user prompt
        query_embedding = generate_embedding(user_prompt)
        
        # Perform RAG search to get relevant context
        context_segments = perform_rag_search(story_id, query_embedding, top_k=5)
        context = "\n\n".join(context_segments) if context_segments else "No previous context available."
        
        # Generate story segment using LLM
        generated_text = generate_story_segment(context, user_prompt)
        
        # Create new flashcard
        new_card = FlashCard.objects.create(
            story=story,
            content_text=generated_text,
            embedding=query_embedding  # We'll update this with the actual text embedding
        )
        
        # Update embedding with the actual generated text
        new_card.embedding = generate_embedding(generated_text)
        new_card.save()
        
        # Create connection if parent card exists
        if parent_card_id:
            try:
                parent_card = FlashCard.objects.get(id=parent_card_id, story=story)
                CardConnection.objects.create(
                    story=story,
                    source_card=parent_card,
                    target_card=new_card
                )
            except ObjectDoesNotExist:
                logger.warning(f"Parent card {parent_card_id} not found for story {story_id}")
        
        logger.info(f"Successfully generated story segment for story {story_id}")
        return {
            'success': True,
            'card_id': new_card.id,
            'generated_text': generated_text
        }
        
    except Exception as e:
        logger.error(f"Error generating story segment for story {story_id}: {e}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def generate_image_task(flashcard_id: int, style: str = None):
    """
    Celery task to generate an image for a flashcard.
    
    Args:
        flashcard_id: ID of the flashcard
        style: Optional style specification for image generation
    """
    try:
        flashcard = FlashCard.objects.get(id=flashcard_id)
        
        # Generate image based on flashcard content
        image_url = generate_image(flashcard.content_text, style)
        
        # Update flashcard with image URL
        flashcard.image_url = image_url
        flashcard.save()
        
        logger.info(f"Successfully generated image for flashcard {flashcard_id}")
        return {
            'success': True,
            'image_url': image_url
        }
        
    except Exception as e:
        logger.error(f"Error generating image for flashcard {flashcard_id}: {e}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def recalculate_embedding_task(flashcard_id: int):
    """
    Celery task to recalculate embedding for a flashcard.
    Used when user manually edits a flashcard.
    
    Args:
        flashcard_id: ID of the flashcard
    """
    try:
        flashcard = FlashCard.objects.get(id=flashcard_id)
        
        # Generate new embedding for the updated text
        new_embedding = generate_embedding(flashcard.content_text)
        
        # Update the flashcard
        flashcard.embedding = new_embedding
        flashcard.save()
        
        logger.info(f"Successfully recalculated embedding for flashcard {flashcard_id}")
        return {
            'success': True,
            'flashcard_id': flashcard_id
        }
        
    except Exception as e:
        logger.error(f"Error recalculating embedding for flashcard {flashcard_id}: {e}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def create_initial_story_task(story_id: int):
    """
    Celery task to create the first flashcard for a new story.
    
    Args:
        story_id: ID of the newly created story
    """
    try:
        story = Story.objects.get(id=story_id)
        
        # Generate the first story segment based on the initial prompt
        generated_text = generate_story_segment("", story.initial_prompt)
        
        # Create the first flashcard
        first_card = FlashCard.objects.create(
            story=story,
            content_text=generated_text,
            embedding=generate_embedding(generated_text)
        )
        
        logger.info(f"Successfully created initial story segment for story {story_id}")
        return {
            'success': True,
            'card_id': first_card.id,
            'generated_text': generated_text
        }
        
    except Exception as e:
        logger.error(f"Error creating initial story for story {story_id}: {e}")
        return {
            'success': False,
            'error': str(e)
        } 