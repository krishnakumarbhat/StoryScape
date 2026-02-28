import json

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from stories.models import CardConnection, FlashCard, Story
from stories.utils import generate_embedding, generate_image


class Command(BaseCommand):
    help = 'Seed a Ramayan-style multiverse story graph with branching nodes.'

    @transaction.atomic
    def handle(self, *args, **options):
        user_model = get_user_model()
        user, _ = user_model.objects.get_or_create(
            email='demo@storyscape.local',
            defaults={'username': 'demo', 'password': 'demo-pass-unsafe'},
        )

        story = Story.objects.create(
            owner=user,
            title='Ramayan Multiverse Demo',
            initial_prompt='Sharat starts by moving along the river and choices branch into different futures.',
        )

        def make_card(content_text):
            card = FlashCard.objects.create(
                story=story,
                content_text=content_text,
                embedding=generate_embedding(content_text),
            )
            card.image_url = generate_image(content_text)
            card.save(update_fields=['image_url'])
            return card

        n1 = make_card('Sharat starts near the river bank at dawn and reflects on duty.')
        n2 = make_card('He walks along the river and sees tracks leading into the forest.')
        n3 = make_card('Path A: He goes hunting to protect villagers from danger in the woods.')
        n4 = make_card('Path B (multiverse): Instead of hunting, he joins a village feast and gathers allies.')
        n5 = make_card('From hunting path: He discovers a hidden cave with ancient inscriptions.')
        n6 = make_card('From feast path: He learns a peaceful route that avoids conflict entirely.')

        CardConnection.objects.bulk_create([
            CardConnection(story=story, source_card=n1, target_card=n2),
            CardConnection(story=story, source_card=n2, target_card=n3),
            CardConnection(story=story, source_card=n2, target_card=n4),
            CardConnection(story=story, source_card=n3, target_card=n5),
            CardConnection(story=story, source_card=n4, target_card=n6),
        ])

        graph_payload = {
            'story_id': story.id,
            'title': story.title,
            'nodes': [
                {'id': card.id, 'content': card.content_text, 'image_url': card.image_url}
                for card in story.flashcards.all()
            ],
            'edges': [
                {'source': edge.source_card_id, 'target': edge.target_card_id}
                for edge in story.connections.all()
            ],
        }

        self.stdout.write(self.style.SUCCESS(f'Seeded story id: {story.id}'))
        self.stdout.write(json.dumps(graph_payload, indent=2))
