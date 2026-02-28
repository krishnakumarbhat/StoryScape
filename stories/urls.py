from django.urls import path
from .views import (
    StoryListView, StoryDetailView, FlashCardCreateView,
    FlashCardUpdateView, generate_image_view, story_graph_view,
    StoryDeleteView, FlashCardDeleteView,
    manual_node_create_view, connect_nodes_view, upload_node_image_view,
    generate_next_node_view
)

urlpatterns = [
    # Story endpoints
    path('stories/', StoryListView.as_view(), name='story-list'),
    path('stories/<int:pk>/', StoryDetailView.as_view(), name='story-detail'),
    path('stories/<int:pk>/delete/', StoryDeleteView.as_view(), name='story-delete'),
    path('stories/<int:pk>/graph/', story_graph_view, name='story-graph'),
    path('stories/<int:story_pk>/nodes/', manual_node_create_view, name='manual-node-create'),
    path('stories/<int:story_pk>/connect/', connect_nodes_view, name='connect-nodes'),
    path('stories/<int:story_pk>/generate-next/', generate_next_node_view, name='generate-next-node'),
    
    # FlashCard endpoints
    path('stories/<int:story_pk>/flashcards/', FlashCardCreateView.as_view(), name='flashcard-create'),
    path('flashcards/<int:pk>/', FlashCardUpdateView.as_view(), name='flashcard-update'),
    path('flashcards/<int:pk>/delete/', FlashCardDeleteView.as_view(), name='flashcard-delete'),
    path('flashcards/<int:pk>/generate-image/', generate_image_view, name='flashcard-generate-image'),
    path('flashcards/<int:pk>/upload-image/', upload_node_image_view, name='flashcard-upload-image'),
] 