from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from .models import Story, FlashCard
from .serializers import (
    StorySerializer, StoryCreateSerializer, FlashCardSerializer,
    FlashCardCreateSerializer, FlashCardUpdateSerializer, ImageGenerationSerializer
)
from .tasks import (
    generate_story_segment_task, generate_image_task, create_initial_story_task
)


class StoryListView(generics.ListCreateAPIView):
    """API view for listing and creating stories."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Story.objects.filter(owner=self.request.user)
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return StoryCreateSerializer
        return StorySerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        story = serializer.save()
        
        # Trigger initial story generation
        create_initial_story_task.delay(story.id)
        
        return Response(
            StorySerializer(story, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )


class StoryDetailView(generics.RetrieveAPIView):
    """API view for retrieving a single story with all its flashcards."""
    serializer_class = StorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Story.objects.filter(owner=self.request.user)


class FlashCardCreateView(generics.CreateAPIView):
    """API view for creating new flashcards in a story."""
    serializer_class = FlashCardCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return FlashCard.objects.filter(story__owner=self.request.user)
    
    def create(self, request, *args, **kwargs):
        story_id = self.kwargs.get('story_pk')
        story = get_object_or_404(Story, id=story_id, owner=request.user)
        
        serializer = self.get_serializer(
            data=request.data,
            context={'story_id': story_id, 'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        # Extract data
        user_prompt = serializer.validated_data['user_prompt']
        parent_card_id = serializer.validated_data.get('parent_card_id')
        
        # Trigger story segment generation
        task_result = generate_story_segment_task.delay(
            story_id=story_id,
            user_prompt=user_prompt,
            parent_card_id=parent_card_id
        )
        
        return Response({
            'message': 'Story segment generation started',
            'task_id': task_result.id,
            'story_id': story_id
        }, status=status.HTTP_202_ACCEPTED)


class FlashCardUpdateView(generics.UpdateAPIView):
    """API view for updating flashcard content."""
    serializer_class = FlashCardUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return FlashCard.objects.filter(story__owner=self.request.user)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def generate_image_view(request, pk):
    """API view for generating an image for a flashcard."""
    flashcard = get_object_or_404(
        FlashCard.objects.filter(story__owner=request.user),
        pk=pk
    )
    
    serializer = ImageGenerationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    style = serializer.validated_data.get('style')
    
    # Trigger image generation
    task_result = generate_image_task.delay(
        flashcard_id=flashcard.id,
        style=style
    )
    
    return Response({
        'message': 'Image generation started',
        'task_id': task_result.id,
        'flashcard_id': flashcard.id
    }, status=status.HTTP_202_ACCEPTED)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def story_graph_view(request, pk):
    """API view for getting the story graph structure."""
    story = get_object_or_404(Story.objects.filter(owner=request.user), pk=pk)
    
    # Get all flashcards and connections for the story
    flashcards = story.flashcards.all()
    connections = story.connections.all()
    
    # Build graph structure
    graph_data = {
        'nodes': [
            {
                'id': card.id,
                'content': card.content_text,
                'image_url': card.image_url,
                'created_at': card.created_at.isoformat()
            }
            for card in flashcards
        ],
        'edges': [
            {
                'source': conn.source_card.id,
                'target': conn.target_card.id,
                'created_at': conn.created_at.isoformat()
            }
            for conn in connections
        ]
    }
    
    return Response(graph_data) 