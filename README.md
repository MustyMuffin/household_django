# Household Management App
README v0.4

This Django project was created by a parent who wanted to motivate their young laborers to help around the house more (and be excited about it). It grew into something that I believe everyone could use and benefit from as well.

At its core, it is a household productivity and tracking tool, designed to manage, track, and gamify various aspects of home life by awarding experience points for various chores or reading milestones. The leveling curve is customizable by admin, with a recommended base of 100-200 and a curve of 1.1 to 1.7. 

It currently tracks books read (and total words), chores completed (and earnings), as well as maintains leaderboards to encourage friendly competition.

## Prerequisites
- Python and pip
- Redis or other celery messages broker
- Everything else can be found and installed through requirements.txt

Optional but recommended:
- Nginx for Gunicorn proxy
- PostgreSQL for better db management and control

## Deployment

- Recommended to use Gunicorn as WSGI server and Nginx as a reverse proxy
- PostgreSQL as the recommended database


## In developement 

actively in development (test branch):
- Badges system that allows site admin to create badges that track admin selected number of books read, amount of words read, frequency of chores done, and total "wage" earned from chores. 
- Schedule function for scheduling chores and other tasks

planned for future development:
- Stats/Analytics section for displaying various data information such as who did what chore the most last week/month/year, who read most books, etc. 


## Features

- 📚 **Book Club Integration**

  - Add books and log book entries
  - Automatically tracks total words read
  - Leaderboard for most words read by user

- 💸 **Earnings Tracker**

  - Track earnings from household chores
  - Has convenient "payout" button for admin (parents) to reset "earned since last payout" number, Upon payout of "wage" to laborer.
  - Displays both current (earned since last payout) and lifetime earnings as well
  - Leaderboard for lifetime earnings for all members of household

- 📊 **Leaderboards**

  - Separate leaderboards for words read and earnings
  - Top performers are styled and highlighted
  - Collapsible cards for clean layout

- 🧠 **Admin-Friendly Design**

  - Timestamps for tracking entry dates
  - Easily editable via admin panel or database
  - Uses Django’s built-in user authentication
  - Admin(s) can reset or delete most settings or user data in django admin backend

## Technologies Used

- Python / Django 5.1
- PostgreSQL (production database)
- Bootstrap 5 for frontend styling
- Gunicorn + Nginx for production/household deployment
- Celery for scheduling tasks

## Notes

- Currently this needs to be hosted and served locally but if there is enough interest, I will host on website over the internet as well. I will not do so until I can promise users full data encryption, both at rest and in travel. 

---

📬 *Feel free to fork, contribute, or suggest features!*

License

Not responsible for hardware damage or any other adverse complications that arise from using this software.
See License.md for more information.
