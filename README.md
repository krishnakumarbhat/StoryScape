# StoryScape

An AI-powered platform for creating illustrated, branching stories with RAG (Retrieval-Augmented Generation) capabilities.

## Features

- **User Authentication**: Register and login with email-based authentication
- **Story Creation**: Create stories from initial prompts
- **AI-Powered Story Generation**: Generate story segments using LLMs with RAG context
- **Image Generation**: Generate illustrations for story segments using diffusion models
- **Branching Narratives**: Create complex story graphs with multiple paths
- **Vector Search**: Use pgvector for semantic search and RAG pipeline
- **RESTful API**: Complete API for frontend integration

## Tech Stack

- **Backend**: Django 4.2.7
- **API**: Django REST Framework 3.14.0
- **Database**: PostgreSQL with pgvector extension
- **Vector Database**: django-pgvector (integrated with PostgreSQL)
- **Task Queue**: Celery with Redis
- **Authentication**: DRF Token Authentication
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **AI Models**: Placeholder functions for LLM and diffusion models

## Project Structure

```
storyscape_project/
├── storyscape/                 # Main Django project
│   ├── settings.py            # Django settings
│   ├── urls.py                # Main URL configuration
│   ├── celery.py              # Celery configuration
│   └── wsgi.py                # WSGI configuration
├── users/                     # User management app
│   ├── models.py              # CustomUser model
│   ├── serializers.py         # User serializers
│   ├── views.py               # Authentication views
│   └── urls.py                # User URLs
├── stories/                   # Story management app
│   ├── models.py              # Story, FlashCard, CardConnection models
│   ├── serializers.py         # Story serializers
│   ├── views.py               # Story API views
│   ├── tasks.py               # Celery tasks for AI generation
│   ├── utils.py               # Utility functions for AI models
│   └── urls.py                # Story URLs
├── manage.py                  # Django management script
├── requirements.txt           # Python dependencies
└── env.example                # Environment variables template
```

## Database Schema

### Users App
- **CustomUser**: Extended user model with email authentication

### Stories App
- **Story**: Main story entity with title, initial prompt, and owner
- **FlashCard**: Story segments with text content, vector embeddings, and optional images
- **CardConnection**: Graph structure representing connections between story segments

## API Endpoints

### Authentication
- `POST /api/auth/register/` - User registration
- `POST /api/auth/token/` - User login
- `GET /api/auth/profile/` - User profile

### Stories
- `GET /api/stories/` - List user's stories
- `POST /api/stories/` - Create new story
- `GET /api/stories/{id}/` - Get story details with flashcards
- `GET /api/stories/{id}/graph/` - Get story graph structure

### Flashcards
- `POST /api/stories/{story_id}/flashcards/` - Create new flashcard (triggers AI generation)
- `PUT /api/flashcards/{id}/` - Update flashcard content
- `POST /api/flashcards/{id}/generate-image/` - Generate image for flashcard

## Setup Instructions

### Prerequisites
- Python 3.8+
- PostgreSQL 12+ with pgvector extension
- Redis server

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd StoryScape
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up PostgreSQL with pgvector**
   ```sql
   -- Install pgvector extension
   CREATE EXTENSION IF NOT EXISTS vector;
   
   -- Create database
   CREATE DATABASE storyscape_db;
   ```

5. **Configure environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your database and Redis credentials
   ```

6. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

7. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

8. **Start Redis server**
   ```bash
   redis-server
   ```

9. **Start Celery worker**
   ```bash
   celery -A storyscape worker --loglevel=info
   ```

10. **Run development server**
    ```bash
    python manage.py runserver
    ```

## AI Model Integration

The project includes placeholder functions for AI model integration. To use actual models:

### LLM Integration
Edit `stories/utils.py` in the `generate_story_segment` function:

```python
# Example with OpenAI
import openai
response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a creative storyteller..."},
        {"role": "user", "content": augmented_prompt}
    ]
)
return response.choices[0].message.content
```

### Image Generation Integration
Edit `stories/utils.py` in the `generate_image` function:

```python
# Example with Stable Diffusion
from diffusers import StableDiffusionPipeline
import torch

pipe = StableDiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=torch.float16
)

image = pipe(prompt).images[0]
image_path = f"media/generated_images/{uuid.uuid4()}.png"
image.save(image_path)
return image_path
```

## RAG Pipeline

The RAG (Retrieval-Augmented Generation) pipeline works as follows:

1. **User provides a prompt** for continuing the story
2. **Generate embedding** for the user's prompt using sentence-transformers
3. **Search similar flashcards** within the same story using pgvector cosine distance
4. **Retrieve top 3-5 relevant segments** as context
5. **Augment the prompt** with retrieved context
6. **Generate new story segment** using the LLM
7. **Create embedding** for the new segment and save to database

## Development

### Running Tests
```bash
python manage.py test
```

### Code Formatting
```bash
# Install black and flake8
pip install black flake8

# Format code
black .

# Check code style
flake8 .
```

### Database Management
```bash
# Create new migration
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Reset database
python manage.py flush
```

## Deployment

### Production Settings
1. Set `DEBUG=False` in environment variables
2. Configure proper `SECRET_KEY`
3. Set up production database
4. Configure static file serving
5. Set up proper CORS settings
6. Use production Redis instance

### Docker Deployment
Create a `Dockerfile` and `docker-compose.yml` for containerized deployment.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.