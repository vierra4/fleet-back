# Trunk Project

Welcome to the **Trunk Project**! This guide walks you through cloning the repo, setting up your environment, running the server, and testing API endpoints. Follow each step to get your local copy up and running smoothly.

---

## Prerequisites

* **Git** (version control)
* **Python 3.8+**
* **(Optional)** [ngrok](https://ngrok.com/) for exposing your local server online

---

## 1. Clone the Repository

```bash
git clone https://github.com/unmatched78/trunk
cd trunk
```

This downloads the project into a new `TrunkProject` folder and switches into it.

---

## 2. Virtual Environment Setup

Creating an isolated Python environment ensures dependencies don’t conflict system-wide.

### Windows

```bash
py -m venv venv
venv\Scripts\activate
```

### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

Once activated, your prompt will show `(venv)` indicating you’re inside the virtual environment.

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

This reads `requirements.txt` and installs all needed Python packages.

---

## 4. Database Migrations

Prepare and apply migrations to sync your database schema.

```bash
# Create new migration files based on model changes
py manage.py makemigrations

# Apply migrations (uses SQLite by default)
py manage.py migrate
```

---

## 5. Start the Development Server

```bash
py manage.py runserver
```

* **App URL:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
* **Admin Panel:** [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

  * **Username:** `chris`
  * **Password:** `123`

---

## 6. Expose Locally via Ngrok (Optional)

1. Run your server on port 8000:

   ```bash
   py manage.py runserver localhost:8000
   ```
2. In a new terminal, start an ngrok tunnel:

   ```bash
   ngrok http 8000
   ```
3. Use the generated ngrok URL to access your server from anywhere.

---

## 7. API Endpoint Testing

### Main URLs (`Trunk/urls.py`)

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("core.urls")),
]
```

### Core App URLs (`core/urls.py`)

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
# Register viewsets
router.register(r"drivers", DriverViewSet)
router.register(r"clients", ClientViewSet)
router.register(r"cars", CarViewSet)
# ... add other viewsets as needed

urlpatterns = [
    # Authentication endpoints
    path("auth/signup/", SignupView.as_view(), name="signup"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/user/", UserInfoView.as_view(), name="user-info"),

    # Public endpoint
    path("public/jobposts/", PublicJobPostListView.as_view(), name="public-jobposts"),

    # API routes
    path("", include(router.urls)),
]
```

#### Example: Login Request

```http
POST http://127.0.0.1:8000/api/auth/login/
Content-Type: application/json

{
  "username": "testuser",
  "password": "123"
}
```

---

## 8. Need Help?

If you encounter issues or have questions, please let me know. Happy coding!
