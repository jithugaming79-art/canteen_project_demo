# 🚀 CampusBites — Deploy to Render (Free Tier)

## Prerequisites
- A [GitHub](https://github.com) account with your project pushed
- A [Render](https://render.com) account (sign up free with GitHub)

---

## Step 1: Push Code to GitHub

```bash
# Initialize git (if not already done)
git init
git add .
git commit -m "Initial commit — ready for Render deploy"

# Create a new GitHub repo, then:
git remote add origin https://github.com/YOUR_USERNAME/campusbites.git
git branch -M main
git push -u origin main
```

> ⚠️ Make sure `.env` is in `.gitignore` — never commit secrets!

---

## Step 2: Create PostgreSQL Database on Render

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **New** → **PostgreSQL**
3. Settings:
   - **Name**: `campusbites-db`
   - **Plan**: Free
4. Click **Create Database**
5. Once created, copy the **Internal Database URL** (starts with `postgres://...`)

---

## Step 3: Create Web Service on Render

1. Click **New** → **Web Service**
2. Connect your GitHub repo
3. Configure:
   | Setting | Value |
   |---------|-------|
   | **Name** | `campusbites` |
   | **Runtime** | Python |
   | **Build Command** | `./build.sh` |
   | **Start Command** | `gunicorn canteen.wsgi:application` |
   | **Plan** | Free |

---

## Step 4: Set Environment Variables

In your Web Service → **Environment** tab, add these:

| Key | Value |
|-----|-------|
| `DATABASE_URL` | *(paste Internal Database URL from Step 2)* |
| `SECRET_KEY` | *(generate a strong random key)* |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `campusbites.onrender.com` *(your Render URL)* |
| `PYTHON_VERSION` | `3.13.0` |
| `EMAIL_HOST` | `smtp.gmail.com` |
| `EMAIL_PORT` | `587` |
| `EMAIL_USE_TLS` | `True` |
| `EMAIL_HOST_USER` | *(your email)* |
| `EMAIL_HOST_PASSWORD` | *(your app password)* |
| `DEFAULT_FROM_EMAIL` | *(your email)* |
| `STRIPE_PUBLISHABLE_KEY` | *(your Stripe key)* |
| `STRIPE_SECRET_KEY` | *(your Stripe secret)* |
| `STRIPE_WEBHOOK_SECRET` | *(your webhook secret)* |
| `FIREBASE_API_KEY` | *(your Firebase key)* |
| `FIREBASE_AUTH_DOMAIN` | *(your Firebase domain)* |
| `FIREBASE_PROJECT_ID` | *(your Firebase project)* |
| `FIREBASE_STORAGE_BUCKET` | *(your bucket)* |
| `FIREBASE_MESSAGING_SENDER_ID` | *(your sender ID)* |
| `FIREBASE_APP_ID` | *(your app ID)* |

---

## Step 5: Deploy

1. Click **Manual Deploy** → **Deploy latest commit**
2. Watch the build logs for any errors
3. Once deployed, visit your URL: `https://campusbites.onrender.com`

---

## Step 6: Create Superuser (Admin)

After deployment, go to **Shell** tab in your Render web service and run:

```bash
python manage.py createsuperuser
```

---

## 🔄 Auto-Deploy
Every time you push to `main` branch, Render will automatically rebuild and deploy!

## ⚠️ Free Tier Notes
- The app goes to **sleep after 15 min of inactivity** (first visit takes ~30s to wake up)
- PostgreSQL free database expires after **90 days** (manual renewal needed)
- **WebSockets/Channels** are not supported on free tier — real-time features will be disabled
