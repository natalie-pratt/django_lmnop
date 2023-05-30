# LMNOP

LMNOP is a musical venue and artist booking site that facilitates the discovery and bookings of shows between local performing artists and venues. This site lets you list new artists and venues, and create notes to share with other users.

## Getting Started

### Installation

Make sure to be in the root directory of the project and that you have Python 3.6 or above installed.

#### Create Virtual Environment

In terminal/command prompt, root directoty of the project.

Setting up virtual environment, Mac

```
virtualenv -p python3 venv
source venv/bin/activate
```

Setting up virtual environment, PC (assuming lab PC with only Python 3 installed)

```
virtualenv venv
venv/bin/activate
```

To utilize API keys, you will need to create a .env file in your main directory. You will not be able to upload it to this repo as most .gitignore will ignore the file. This is for security reasons as you do not want to post your API Keys to these services out in the open. When you are done creating the .env file, insert your respective keys into the text below and then save the .env file.

```
TICKETMASTER_KEY ='INSERT TICKETMASTER_KEY KEY HERE'
```

To install all project's dependencies, simply run:

```
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

Site at

http://127.0.0.1:8000

### Create superuser

```
python manage.py createsuperuser
```

enter username and password

Then you will be able to use these to log into admin console at

127.0.0.1:8000/admin/

To load Artist, Venue, and Show data navigate to

http://127.0.0.1:8000/artist

<img width="273" alt="image" src="https://user-images.githubusercontent.com/111803746/236979549-6db316d1-34b8-4728-8d17-3f01f6f2d3b2.png">

http://127.0.0.1:8000/venue

<img width="272" alt="image" src="https://user-images.githubusercontent.com/111803746/236979584-47a7718f-704b-462c-a5d2-0307200f49c8.png">

http://127.0.0.1:8000/show

<img width="272" alt="image" src="https://user-images.githubusercontent.com/111803746/236979608-51f8bf11-c4c9-474c-8e84-fc96533d8648.png">

A user will create Notes using the app.

### Run tests

```
python manage.py test
```

Or just some of the tests,

```
python manage.py test lmn.tests.test_views
python manage.py test lmn.tests.test_views.TestUserAuthentication
python manage.py test lmn.tests.test_views.TestUserAuthentication.test_user_registration_logs_user_in
```

### Functional Tests with Selenium

Make sure you have the latest version of Chrome or Firefox, and the most recent chromedriver or geckodriver, and latest Selenium.

chromedriver/geckodriver needs to be in path or you need to tell Selenium where it is. Pick an approach: http://stackoverflow.com/questions/40208051/selenium-using-python-geckodriver-executable-needs-to-be-in-path

If your DB is hosted at Elephant, your tests might time out, and you might need to use longer waits http://selenium-python.readthedocs.io/waits.html

Run tests with

```
python manage.py test lmn.tests.functional_tests.functional_tests
```

Or select tests, for example,

```
python manage.py test lmn.functional_tests.functional_tests.HomePageTest
python manage.py test lmn.functional_tests.functional_tests.BrowseArtists.test_searching_artists
```

### Test coverage

From directory with manage.py in it,

```
coverage run --source='.' manage.py test lmn.tests
coverage report
```

### Linting

Ensure requirements are installed, then run,

```
flake8 .
```

Configure linting rules if desired in the .flake8 file.

### Databases

You will likely want to configure the app to use SQLite locally, and PaaS database when deployed.

### Deployment

App is currently deployed and is running at this address: https://lmn-2023.uc.r.appspot.com
