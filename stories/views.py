from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.conf import settings
import os
import uuid
from .models import Story, FlashCard
from .serializers import (
    StorySerializer, StoryCreateSerializer, FlashCardSerializer,
    FlashCardCreateSerializer, FlashCardUpdateSerializer, ImageGenerationSerializer,
    ManualFlashCardCreateSerializer, ConnectionCreateSerializer, GenerateNextNodesSerializer
)
from .tasks import (
    generate_story_segment_task, generate_image_task, create_initial_story_task
)
from .utils import generate_embedding, generate_story_segment
from .models import CardConnection

GUEST_STORY_IDS_KEY = 'guest_story_ids'
GUEST_STORY_LIMIT = 5
GUEST_EMAIL = 'guest@storyscape.local'


def get_guest_user():
    user_model = get_user_model()
    guest_user, _ = user_model.objects.get_or_create(
        email=GUEST_EMAIL,
        defaults={'username': 'guest'},
    )
    return guest_user


def ensure_session(request):
    if not request.session.session_key:
        request.session.create()


def get_guest_story_ids(request):
    ensure_session(request)
    return request.session.get(GUEST_STORY_IDS_KEY, [])


def set_guest_story_ids(request, story_ids):
    ensure_session(request)
    request.session[GUEST_STORY_IDS_KEY] = story_ids
    request.session.modified = True


def get_accessible_story_queryset(request):
    if request.user.is_authenticated:
        return Story.objects.filter(owner=request.user)

    guest_ids = get_guest_story_ids(request)
    if not guest_ids:
        return Story.objects.none()
    return Story.objects.filter(owner=get_guest_user(), id__in=guest_ids)


def save_uploaded_image(file_obj, request):
    os.makedirs(os.path.join(settings.MEDIA_ROOT, 'uploaded_images'), exist_ok=True)
    extension = os.path.splitext(file_obj.name)[1] or '.png'
    relative_path = f"uploaded_images/{uuid.uuid4()}{extension}"
    absolute_path = os.path.join(settings.MEDIA_ROOT, relative_path)

    with open(absolute_path, 'wb+') as destination:
        for chunk in file_obj.chunks():
            destination.write(chunk)

    return request.build_absolute_uri(f"{settings.MEDIA_URL}{relative_path}")

def dispatch_task(task_func, **kwargs):
    """Dispatch Celery task, fallback to sync execution when broker is unavailable."""
    try:
        return task_func.delay(**kwargs)
    except Exception:
        result = task_func(**kwargs)

        class InlineTaskResult:
            id = 'inline-execution'
            output = result

        return InlineTaskResult()


class StoryListView(generics.ListCreateAPIView):
    """API view for listing and creating stories."""
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        return get_accessible_story_queryset(self.request)
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return StoryCreateSerializer
        return StorySerializer
    
    def create(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            owner = request.user
        else:
            guest_story_ids = get_guest_story_ids(request)
            if len(guest_story_ids) >= GUEST_STORY_LIMIT:
                return Response(
                    {
                        'detail': (
                            f'Guest mode allows maximum {GUEST_STORY_LIMIT} stories. '
                            'Login to create unlimited stories.'
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
            owner = get_guest_user()

        serializer = self.get_serializer(
            data=request.data,
            context={**self.get_serializer_context(), 'owner_override': owner},
        )
        serializer.is_valid(raise_exception=True)
        story = serializer.save()

        if not request.user.is_authenticated:
            guest_story_ids = get_guest_story_ids(request)
            guest_story_ids.append(story.id)
            set_guest_story_ids(request, guest_story_ids)
        
        # Trigger initial story generation
        dispatch_task(create_initial_story_task, story_id=story.id)
        
        return Response(
            StorySerializer(story, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )


class StoryDetailView(generics.RetrieveAPIView):
    """API view for retrieving a single story with all its flashcards."""
    serializer_class = StorySerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        return get_accessible_story_queryset(self.request)


class StoryDeleteView(generics.DestroyAPIView):
    """API view for deleting a story."""
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return get_accessible_story_queryset(self.request)

    def destroy(self, request, *args, **kwargs):
        story = self.get_object()
        response = super().destroy(request, *args, **kwargs)
        if not request.user.is_authenticated:
            guest_story_ids = get_guest_story_ids(request)
            if story.id in guest_story_ids:
                guest_story_ids.remove(story.id)
                set_guest_story_ids(request, guest_story_ids)
        return response


class FlashCardCreateView(generics.CreateAPIView):
    """API view for creating new flashcards in a story."""
    serializer_class = FlashCardCreateSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        return FlashCard.objects.filter(story__in=get_accessible_story_queryset(self.request))
    
    def create(self, request, *args, **kwargs):
        story_id = self.kwargs.get('story_pk')
        story = get_object_or_404(get_accessible_story_queryset(request), id=story_id)
        
        serializer = self.get_serializer(
            data=request.data,
            context={'story_id': story_id, 'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        # Extract data
        user_prompt = serializer.validated_data['user_prompt']
        parent_card_id = serializer.validated_data.get('parent_card_id')
        
        # Trigger story segment generation
        task_result = dispatch_task(
            generate_story_segment_task,
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
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        return FlashCard.objects.filter(story__in=get_accessible_story_queryset(self.request))


class FlashCardDeleteView(generics.DestroyAPIView):
    """API view for deleting a flashcard node."""
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return FlashCard.objects.filter(story__in=get_accessible_story_queryset(self.request))


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def generate_image_view(request, pk):
    """API view for generating an image for a flashcard."""
    flashcard = get_object_or_404(
        FlashCard.objects.filter(story__in=get_accessible_story_queryset(request)),
        pk=pk
    )
    
    serializer = ImageGenerationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    style = serializer.validated_data.get('style')
    
    # Trigger image generation
    task_result = dispatch_task(
        generate_image_task,
        flashcard_id=flashcard.id,
        style=style
    )
    
    return Response({
        'message': 'Image generation started',
        'task_id': task_result.id,
        'flashcard_id': flashcard.id
    }, status=status.HTTP_202_ACCEPTED)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def story_graph_view(request, pk):
    """API view for getting the story graph structure."""
    story = get_object_or_404(get_accessible_story_queryset(request), pk=pk)
    
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


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def manual_node_create_view(request, story_pk):
    """Create a manual node in graph view and optionally connect from parent."""
    story = get_object_or_404(get_accessible_story_queryset(request), pk=story_pk)
    serializer = ManualFlashCardCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    content_text = serializer.validated_data['content_text']
    parent_card_id = serializer.validated_data.get('parent_card_id')

    new_card = FlashCard.objects.create(
        story=story,
        content_text=content_text,
        embedding=generate_embedding(content_text),
    )

    if parent_card_id:
        parent_card = get_object_or_404(FlashCard, pk=parent_card_id, story=story)
        CardConnection.objects.get_or_create(
            story=story,
            source_card=parent_card,
            target_card=new_card,
        )

    return Response(FlashCardSerializer(new_card).data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def connect_nodes_view(request, story_pk):
    """Create a graph edge between two existing nodes."""
    story = get_object_or_404(get_accessible_story_queryset(request), pk=story_pk)
    serializer = ConnectionCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    source_card = get_object_or_404(FlashCard, pk=serializer.validated_data['source_card_id'], story=story)
    target_card = get_object_or_404(FlashCard, pk=serializer.validated_data['target_card_id'], story=story)

    if source_card.id == target_card.id:
        return Response({'detail': 'Cannot connect node to itself.'}, status=status.HTTP_400_BAD_REQUEST)

    connection, created = CardConnection.objects.get_or_create(
        story=story,
        source_card=source_card,
        target_card=target_card,
    )
    return Response(
        {
            'id': connection.id,
            'source': source_card.id,
            'target': target_card.id,
            'created': created,
        },
        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
    )


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def upload_node_image_view(request, pk):
    """Upload image file for a node and attach resulting URL."""
    flashcard = get_object_or_404(
        FlashCard.objects.filter(story__in=get_accessible_story_queryset(request)),
        pk=pk,
    )

    upload = request.FILES.get('image')
    if not upload:
        return Response({'detail': 'No image file provided.'}, status=status.HTTP_400_BAD_REQUEST)

    image_url = save_uploaded_image(upload, request)
    flashcard.image_url = image_url
    flashcard.save(update_fields=['image_url'])
    return Response({'image_url': image_url}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def generate_next_node_view(request, story_pk):
    """Generate one next node using selected mode and optional parent node."""
    story = get_object_or_404(get_accessible_story_queryset(request), pk=story_pk)
    serializer = GenerateNextNodesSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    parent_card_id = serializer.validated_data.get('parent_card_id')
    mode = serializer.validated_data['mode']

    mode_prompts = {
        'adventure': 'Continue this story in an adventurous high-stakes way.',
        'peaceful': 'Continue this story in a calm, peaceful, compassionate way.',
        'mystic': 'Continue this story with mythic mystery and spiritual symbolism.',
    }

    context = ''
    parent_card = None
    if parent_card_id:
        parent_card = get_object_or_404(FlashCard, pk=parent_card_id, story=story)
        context = parent_card.content_text

    generated_text = generate_story_segment(context, mode_prompts[mode])
    new_card = FlashCard.objects.create(
        story=story,
        content_text=generated_text,
        embedding=generate_embedding(generated_text),
    )

    if parent_card:
        CardConnection.objects.get_or_create(
            story=story,
            source_card=parent_card,
            target_card=new_card,
        )

    return Response(
        {
            'mode': mode,
            'node': FlashCardSerializer(new_card).data,
        },
        status=status.HTTP_201_CREATED,
    )