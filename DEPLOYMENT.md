# Upbeat Attendance API — Deployment Guide

This guide explains how to push your REST API repository to your personal GitHub and deploy it to a hosting provider like **Render** or **Railway** so that the desktop apps can communicate with the hosted API instead of localhost.

---

## 1. Push to Your Personal GitHub

### Step 1: Initialize Git (if not already done)
Open your terminal in the project root folder (`Upbeat-Employee-Attendance/`) and run:
```bash
git init
```

### Step 2: Add all files
The project includes a `.gitignore` that correctly excludes local files (such as `attendance.db`, executables in `dist/`, logs, and temporary caches).
```bash
git add .
```

### Step 3: Commit files
```bash
git commit -m "Initial commit of Upbeat Attendance System"
```

### Step 4: Push to your GitHub Repository
1. Go to [GitHub](https://github.com) and create a new **private** or **public** repository named `Upbeat-Employee-Attendance`.
2. Copy the remote URL.
3. Link your local project to GitHub and push:
```bash
# Link the remote repository
git remote add origin <your-github-repo-url>

# Rename branch to main
git branch -M main

# Push code to GitHub
git push -u origin main
```

---

## 2. Deploy the API to Hosting Providers

FastAPI is highly compatible with cloud platforms. Below are deployment instructions for two popular options.

### Option A: Deploying on Render (Free/Paid Tier)
Render is simple to set up and connects directly to your GitHub repo.

1. Create a free account at [Render](https://render.com).
2. Click **New** -> **Web Service**.
3. Connect your GitHub repository.
4. Set the following configuration parameters:
   - **Name**: `upbeat-attendance-api`
   - **Environment**: `Python 3`
   - **Region**: Select closest to your timezone.
   - **Branch**: `main`
   - **Build Command**: `pip install -r api/requirements.txt`
   - **Start Command**: `python -m uvicorn api.main:app --host 0.0.0.0 --port $PORT`
5. Under **Environment Variables**, add:
   - `DATABASE_URL`: `sqlite:///api/attendance.db` (For SQLite. Note: Render's free tier has ephemeral disks; for production, upgrade to a persistent disk or link to a Render PostgreSQL database.)
   - `API_KEY`: `upbeat-attendance-api-key-2024-secure` (Change this to a strong secret key for production.)
   - `JWT_SECRET_KEY`: (A random secure string for Admin JWT signing.)
6. Click **Deploy Web Service**. Render will build and launch your API. Copy the unique URL (e.g., `https://upbeat-attendance-api.onrender.com`).

---

### Option B: Deploying on Railway (Paid/Developer Tier)
Railway is extremely fast and has built-in support for persistent SQLite storage.

1. Sign up at [Railway](https://railway.app).
2. Click **New Project** -> **Deploy from GitHub repo**.
3. Connect your repository.
4. Click **Variables** and add:
   - `PORT`: `8000`
   - `DATABASE_URL`: `sqlite:///api/attendance.db`
   - `API_KEY`: `<your-secure-key>`
   - `JWT_SECRET_KEY`: `<your-jwt-secret>`
5. Click **Settings** and look for **Build & Deploy**:
   - Set **Build Command** to: `pip install -r api/requirements.txt`
   - Set **Start Command** to: `python -m uvicorn api.main:app --host 0.0.0.0 --port $PORT`
6. Click **Generate Domain** under Settings to get your public API URL (e.g., `https://upbeat-employee-attendance.up.railway.app`).

---

## 3. Integrating the Hosted API with the Desktop Apps

Now that you have your hosted API URL (e.g., `https://upbeat-attendance-api.onrender.com`), you can integrate it without re-compiling the apps.

### Dynamic JSON Configuration
Both the **Employee App** and **Admin App** dynamically generate a `config.json` file in the same directory as the executable the first time they are launched.

1. Launch `Upbeat_Attendance.exe` (Employee App) or `Upbeat_Admin.exe` (Admin App).
2. Close the app. A file named `config.json` will be generated next to the executable.
3. Open `config.json` in a text editor (e.g., Notepad) and update the `API_BASE_URL` with your hosted URL:

```json
{
    "API_BASE_URL": "https://upbeat-attendance-api.onrender.com",
    "API_KEY": "upbeat-attendance-api-key-2024-secure"
}
```

4. Save the file and restart the applications. They will now connect directly to your hosted cloud backend.
