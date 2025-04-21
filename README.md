# Household Management App

This Django project is a household productivity and tracking tool, designed to manage and gamify various aspects of home life. It allows users to track books read (and total words), monitor earnings from chores, and maintain leaderboards to encourage friendly competition.

## Features

- 📚 **Book Club Integration**

  - Add books and log book entries
  - Automatically tracks total words read
  - Leaderboard for most words read by user

- 💸 **Earnings Tracker**

  - Track earnings from household chores
  - Displays both current and lifetime earnings
  - Leaderboard for lifetime earnings

- 📊 **Leaderboards**

  - Separate leaderboards for words read and earnings
  - Top performers are styled and highlighted
  - Collapsible cards for clean layout

- 🧠 **Admin-Friendly Design**

  - Timestamps for tracking entry dates
  - Easily editable via admin panel or database
  - Uses Django’s built-in user authentication

## Technologies Used

- Python / Django 5.1
- PostgreSQL (production database)
- Bootstrap 5 for frontend styling
- Gunicorn + Nginx for production deployment
- GitHub for version control

## Development

1. Clone the repository:

   ```bash
   git clone https://github.com/MustyMuffin/household_django.git
   cd household_django
   ```

2. Create and activate virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Apply migrations:

   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. Run development server:

   ```bash
   python manage.py runserver
   ```

## Deployment

- Uses Gunicorn as WSGI server and Nginx as a reverse proxy
- PostgreSQL as the production database
- See `django_production_checklist.md` for deployment steps

## Notes

- Leaderboards sort users by words read or earnings
- All book entries track their `date_added` so data is visible historically
- Models include `BooksRead`, `WordsRead`, and `EarnedWage`
- Pages were renamed to Words globally for accuracy

---

📬 *Feel free to fork, contribute, or suggest features!*

License

This project is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License.See the full license in the LICENSE.md file or visit creativecommons.org/licenses/by-nc/4.0.