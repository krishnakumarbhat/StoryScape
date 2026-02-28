from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch

from .models import Story, FlashCard
from .utils import generate_embedding, perform_rag_search

User = get_user_model()


class StoryModelTest(TestCase):
    """Test cases for Story model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_story_creation(self):
        """Test creating a story."""
        story = Story.objects.create(
            owner=self.user,
            title='Test Story',
            initial_prompt='Once upon a time...'
        )
        self.assertEqual(story.title, 'Test Story')
        self.assertEqual(story.owner, self.user)
        self.assertEqual(story.initial_prompt, 'Once upon a time...')


class FlashCardModelTest(TestCase):
    """Test cases for FlashCard model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.story = Story.objects.create(
            owner=self.user,
            title='Test Story',
            initial_prompt='Once upon a time...'
        )
    
    def test_flashcard_creation(self):
        """Test creating a flashcard."""
        flashcard = FlashCard.objects.create(
            story=self.story,
            content_text='This is a test flashcard content.'
        )
        self.assertEqual(flashcard.story, self.story)
        self.assertEqual(flashcard.content_text, 'This is a test flashcard content.')
        self.assertIsNotNone(flashcard.embedding)


class StoryAPITest(APITestCase):
    """Test cases for Story API endpoints."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    @patch('stories.views.create_initial_story_task.delay')
    def test_create_story(self, mock_delay):
        """Test creating a story via API."""
        data = {
            'title': 'API Test Story',
            'initial_prompt': 'This is a test story created via API.'
        }
        response = self.client.post('/api/stories/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Story.objects.count(), 1)
        self.assertEqual(Story.objects.first().title, 'API Test Story')
        mock_delay.assert_called_once()
    
    def test_list_stories(self):
        """Test listing user's stories."""
        Story.objects.create(
            owner=self.user,
            title='Test Story 1',
            initial_prompt='First story'
        )
        Story.objects.create(
            owner=self.user,
            title='Test Story 2',
            initial_prompt='Second story'
        )
        
        response = self.client.get('/api/stories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    @patch('stories.views.generate_story_segment_task.delay')
    def test_create_flashcard_triggers_generation_task(self, mock_delay):
        """Test flashcard endpoint dispatches async generation task."""
        mock_delay.return_value.id = 'task-123'
        story = Story.objects.create(
            owner=self.user,
            title='Test Story',
            initial_prompt='First prompt'
        )

        response = self.client.post(
            f'/api/stories/{story.id}/flashcards/',
            {'user_prompt': 'Continue this story'},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(response.data['task_id'], 'task-123')
        mock_delay.assert_called_once_with(
            story_id=story.id,
            user_prompt='Continue this story',
            parent_card_id=None,
        )


class GuestStoryAPITest(APITestCase):
    """Tests for guest mode with story cap."""

    def test_guest_can_create_up_to_five_stories(self):
        for index in range(5):
            response = self.client.post(
                '/api/stories/',
                {
                    'title': f'Guest Story {index}',
                    'initial_prompt': 'Guest prompt'
                },
                format='json'
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        blocked_response = self.client.post(
            '/api/stories/',
            {
                'title': 'Guest Story 6',
                'initial_prompt': 'Guest prompt'
            },
            format='json'
        )
        self.assertEqual(blocked_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_guest_list_only_shows_guest_session_stories(self):
        self.client.post(
            '/api/stories/',
            {
                'title': 'Guest Session Story',
                'initial_prompt': 'Session prompt'
            },
            format='json'
        )

        response = self.client.get('/api/stories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)


class GraphEditorAPITest(APITestCase):
    """Tests for manual graph editing endpoints."""

    def setUp(self):
        self.story_response = self.client.post(
            '/api/stories/',
            {'title': 'Graph Story', 'initial_prompt': 'Start graph'},
            format='json'
        )
        self.story_id = self.story_response.data['id']

    def test_manual_node_create(self):
        response = self.client.post(
            f'/api/stories/{self.story_id}/nodes/',
            {'content_text': 'A manual branch node'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)

    def test_generate_next_node_with_mode(self):
        response = self.client.post(
            f'/api/stories/{self.story_id}/generate-next/',
            {'mode': 'adventure'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['mode'], 'adventure')


class UtilityFunctionTest(TestCase):
    """Test cases for utility functions."""
    
    def test_generate_embedding(self):
        """Test embedding generation."""
        text = "This is a test text for embedding generation."
        embedding = generate_embedding(text)
        
        self.assertIsInstance(embedding, list)
        self.assertEqual(len(embedding), 384)
        self.assertTrue(all(isinstance(x, (int, float)) for x in embedding))
    
    def test_perform_rag_search(self):
        """Test RAG search functionality."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        story = Story.objects.create(
            owner=user,
            title='Test Story',
            initial_prompt='Once upon a time...'
        )
        
        # Create some test flashcards
        FlashCard.objects.create(
            story=story,
            content_text='First story segment about a brave knight.'
        )
        FlashCard.objects.create(
            story=story,
            content_text='Second story segment about a magical forest.'
        )
        
        query_embedding = generate_embedding('knight adventure')
        results = perform_rag_search(story.id, query_embedding, top_k=2)
        
        self.assertIsInstance(results, list)
        self.assertLessEqual(len(results), 2) 