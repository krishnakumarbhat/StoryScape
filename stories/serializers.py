from rest_framework import serializers
from .models import Story, FlashCard, CardConnection


class FlashCardSerializer(serializers.ModelSerializer):
    """Serializer for FlashCard model."""
    class Meta:
        model = FlashCard
        fields = ['id', 'content_text', 'image_url', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class CardConnectionSerializer(serializers.ModelSerializer):
    """Serializer for CardConnection model."""
    source_card_id = serializers.IntegerField(write_only=True)
    target_card_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = CardConnection
        fields = ['id', 'source_card_id', 'target_card_id', 'created_at']
        read_only_fields = ['id', 'created_at']


class StorySerializer(serializers.ModelSerializer):
    """Serializer for Story model with nested flashcards."""
    flashcards = FlashCardSerializer(many=True, read_only=True)
    connections = CardConnectionSerializer(many=True, read_only=True)
    owner = serializers.ReadOnlyField(source='owner.username')
    
    class Meta:
        model = Story
        fields = [
            'id', 'title', 'initial_prompt', 'owner', 
            'created_at', 'updated_at', 'flashcards', 'connections'
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']


class StoryCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new story."""
    class Meta:
        model = Story
        fields = ['title', 'initial_prompt']
    
    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)


class FlashCardCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new flashcard."""
    parent_card_id = serializers.IntegerField(required=False, allow_null=True)
    user_prompt = serializers.CharField(write_only=True)
    
    class Meta:
        model = FlashCard
        fields = ['parent_card_id', 'user_prompt']
    
    def validate_parent_card_id(self, value):
        if value:
            story_id = self.context.get('story_id')
            try:
                FlashCard.objects.get(id=value, story_id=story_id)
            except FlashCard.DoesNotExist:
                raise serializers.ValidationError("Parent card does not exist in this story")
        return value


class FlashCardUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a flashcard."""
    class Meta:
        model = FlashCard
        fields = ['content_text']
    
    def update(self, instance, validated_data):
        # Trigger embedding recalculation when content is updated
        instance = super().update(instance, validated_data)
        from .tasks import recalculate_embedding_task
        recalculate_embedding_task.delay(instance.id)
        return instance


class ImageGenerationSerializer(serializers.Serializer):
    """Serializer for image generation request."""
    style = serializers.CharField(required=False, allow_blank=True) 