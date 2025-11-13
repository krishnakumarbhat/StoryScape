from django.db import models
from django.conf import settings
from pgvector.django import VectorField
from django.contrib.auth import get_user_model

User = get_user_model()


class Story(models.Model):
    """Model representing a story created by a user."""
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stories')
    title = models.CharField(max_length=200)
    initial_prompt = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Stories'
    
    def __str__(self):
        return f"{self.title} by {self.owner.username}"


class FlashCard(models.Model):
    """Model representing a story segment (flashcard) with vector embedding."""
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='flashcards')
    content_text = models.TextField()
    embedding = VectorField(dimensions=384)  # For all-MiniLM-L6-v2 model
    image_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Card {self.id} in {self.story.title}"
    
    def save(self, *args, **kwargs):
        # Generate embedding if not provided
        if not self.embedding:
            from .utils import generate_embedding
            self.embedding = generate_embedding(self.content_text)
        super().save(*args, **kwargs)


class CardConnection(models.Model):
    """Model representing connections between flashcards in the story graph."""
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='connections')
    source_card = models.ForeignKey(FlashCard, on_delete=models.CASCADE, related_name='outgoing_connections')
    target_card = models.ForeignKey(FlashCard, on_delete=models.CASCADE, related_name='incoming_connections')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['source_card', 'target_card']
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.source_card.id} -> {self.target_card.id} in {self.story.title}"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.source_card.story != self.target_card.story:
            raise ValidationError("Source and target cards must belong to the same story")
        if self.source_card == self.target_card:
            raise ValidationError("A card cannot connect to itself") 