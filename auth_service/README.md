# auth_service/auth_service/README.md

# Auth Service

This project is a Django-based authentication service that implements user account management, including registration, login with JWT authentication, and a password reset feature using Redis cache.

## Features

- User registration
- JWT authentication for login
- Password reset functionality
- Redis cache for managing password reset tokens

## Requirements

- Python 3.8 or higher
- PostgreSQL
- Redis

## Setup Instructions

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd auth_service
   ```

2. **Create a virtual environment:**

   ```bash
   python -m venv venv
   OR
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**

   Create a `.env` file in the root directory and add the following variables:

   ```
   SECRET_KEY=<your-secret-key>
   DEBUG=True
   DATABASE_URL=postgres://<user>:<password>@localhost:5432/<dbname>
   REDIS_URL=redis://localhost:6379/0
   ```

5. **Run migrations:**

   ```bash
   python manage.py migrate
   OR
   python3 manage.py migrate
   ```

   

6. **Create a superuser (optional):**

   ```bash
   python manage.py createsuperuser
   OR
   python3 manage.py createsuperuser
   ```

7. **Run the development server:**

   ```bash
   python manage.py runserver
   ```

## API Endpoints

- **POST /api/register/** - User registration
- **POST /api/login/** - User login
- **POST /api/password-reset/** - Request password reset
- **POST /api/password-reset-confirm/** - Confirm password reset

## Deployment Instructions

### Using Docker

1. **Build the Docker image:**

   ```bash
   docker build -t auth_service .
   ```

2. **Run the application with Docker Compose:**

   ```bash
   docker-compose up
   ```

This will start the Django application and a Redis service.

## License

This project is licensed under the MIT License. See the LICENSE file for details.