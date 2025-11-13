from django.urls import path
from .views import (
    StoryListView, StoryDetailView, FlashCardCreateView,
    FlashCardUpdateView, generate_image_view, story_graph_view
)

urlpatterns = [
    # Story endpoints
    path('stories/', StoryListView.as_view(), name='story-list'),
    path('stories/<int:pk>/', StoryDetailView.as_view(), name='story-detail'),
    path('stories/<int:pk>/graph/', story_graph_view, name='story-graph'),
    
    # FlashCard endpoints
    path('stories/<int:story_pk>/flashcards/', FlashCardCreateView.as_view(), name='flashcard-create'),
    path('flashcards/<int:pk>/', FlashCardUpdateView.as_view(), name='flashcard-update'),
    path('flashcards/<int:pk>/generate-image/', generate_image_view, name='flashcard-generate-image'),
] 