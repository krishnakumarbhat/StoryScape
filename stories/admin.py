from django.contrib import admin
from .models import Story, FlashCard, CardConnection


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    """Admin configuration for Story model."""
    list_display = ['title', 'owner', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['title', 'initial_prompt', 'owner__username', 'owner__email']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'


@admin.register(FlashCard)
class FlashCardAdmin(admin.ModelAdmin):
    """Admin configuration for FlashCard model."""
    list_display = ['id', 'story', 'content_preview', 'has_image', 'created_at']
    list_filter = ['created_at', 'updated_at', 'story']
    search_fields = ['content_text', 'story__title']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    def content_preview(self, obj):
        """Show a preview of the content text."""
        return obj.content_text[:100] + '...' if len(obj.content_text) > 100 else obj.content_text
    content_preview.short_description = 'Content Preview'
    
    def has_image(self, obj):
        """Check if the flashcard has an image."""
        return bool(obj.image_url)
    has_image.boolean = True
    has_image.short_description = 'Has Image'


@admin.register(CardConnection)
class CardConnectionAdmin(admin.ModelAdmin):
    """Admin configuration for CardConnection model."""
    list_display = ['id', 'story', 'source_card', 'target_card', 'created_at']
    list_filter = ['created_at', 'story']
    search_fields = ['story__title', 'source_card__content_text', 'target_card__content_text']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at' 