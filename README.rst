phoenix
==============================
Everyone has a problem with his name on it.

Settings
------------

phoenix relies extensively on environment settings which **will not work with Apache/mod_wsgi setups**. It has been deployed successfully with both Gunicorn/Nginx and even uWSGI/Nginx.

For configuration purposes, the following table maps the 'phoenix' environment variables to their Django setting:

======================================= =========================== ============================================== ======================================================================
Environment Variable                    Django Setting              Development Default                            Production Default
======================================= =========================== ============================================== ======================================================================
DJANGO_CACHES                           CACHES (default)            locmem                                         redis
DJANGO_DATABASES                        DATABASES (default)         See code                                       See code
DJANGO_DEBUG                            DEBUG                       True                                           False
DJANGO_SECRET_KEY                       SECRET_KEY                  CHANGEME!!!                                    raises error
DJANGO_SECURE_BROWSER_XSS_FILTER        SECURE_BROWSER_XSS_FILTER   n/a                                            True
DJANGO_SECURE_SSL_REDIRECT              SECURE_SSL_REDIRECT         n/a                                            True
DJANGO_SECURE_CONTENT_TYPE_NOSNIFF      SECURE_CONTENT_TYPE_NOSNIFF n/a                                            True
DJANGO_SECURE_FRAME_DENY                SECURE_FRAME_DENY           n/a                                            True
DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS   HSTS_INCLUDE_SUBDOMAINS     n/a                                            True
DJANGO_SESSION_COOKIE_HTTPONLY          SESSION_COOKIE_HTTPONLY     n/a                                            True
DJANGO_SESSION_COOKIE_SECURE            SESSION_COOKIE_SECURE       n/a                                            False
DJANGO_DEFAULT_FROM_EMAIL               DEFAULT_FROM_EMAIL          n/a                                            "phoenix <noreply@farmguru.ansgax.com>"
DJANGO_SERVER_EMAIL                     SERVER_EMAIL                n/a                                            "phoenix <noreply@farmguru.ansgax.com>"
DJANGO_EMAIL_SUBJECT_PREFIX             EMAIL_SUBJECT_PREFIX        n/a                                            "[phoenix] "
======================================= =========================== ============================================== ======================================================================

The following table lists settings and their defaults for third-party applications:

======================================= =========================== ============================================== ======================================================================
Environment Variable                    Django Setting              Development Default                            Production Default
======================================= =========================== ============================================== ======================================================================
DJANGO_AWS_ACCESS_KEY_ID                AWS_ACCESS_KEY_ID           n/a                                            raises error
DJANGO_AWS_SECRET_ACCESS_KEY            AWS_SECRET_ACCESS_KEY       n/a                                            raises error
DJANGO_AWS_STORAGE_BUCKET_NAME          AWS_STORAGE_BUCKET_NAME     n/a                                            raises error

DJANGO_MAILGUN_API_KEY                  MAILGUN_ACCESS_KEY          n/a                                            raises error
DJANGO_MAILGUN_SERVER_NAME              MAILGUN_SERVER_NAME         n/a                                            raises error
======================================= =========================== ============================================== ======================================================================

Getting up and running
----------------------

Basics
^^^^^^

The steps below will get you up and running with a local development environment. We assume you have the following installed:

* pip
* virtualenv
* PostgreSQL

First make sure to create and activate a virtualenv_, then open a terminal at the project root and install the requirements for local development::

    $ pip install -r requirements/local.txt

.. _virtualenv: http://docs.python-guide.org/en/latest/dev/virtualenvs/

Create a local PostgreSQL database::

    $ createdb phoenix

Run ``migrate`` on your new database::

    $ python manage.py migrate

You can now run the ``runserver_plus`` command::

    $ python manage.py runserver_plus

Open up your browser to http://127.0.0.1:8000/ to see the site running locally.

Setting Up Your Users
^^^^^^^^^^^^^^^^^^^^^

To create a **normal user account**, just go to Sign Up and fill out the form. Once you submit it, you'll see a "Verify Your E-mail Address" page. Go to your console to see a simulated email verification message. Copy the link into your browser. Now the user's email should be verified and ready to go.

To create an **superuser account**, use this command::

    $ python manage.py createsuperuser

For convenience, you can keep your normal user logged in on Chrome and your superuser logged in on Firefox (or similar), so that you can see how the site behaves for both kinds of users.

Test coverage
^^^^^^^^^^^^^

To run the tests, check your test coverage, and generate an HTML coverage report::

    $ coverage run manage.py test
    $ coverage html
    $ open htmlcov/index.html

Live reloading and Sass CSS compilation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you'd like to take advantage of live reloading and Sass / Compass CSS compilation you can do so with a little bit of prep work.

Make sure that nodejs_ is installed. Then in the project root run::

    $ npm install

.. _nodejs: http://nodejs.org/download/

If you don't already have it, install `compass` (doesn't hurt if you run this command twice)::

    gem install compass

Now you just need::

    $ grunt serve

The base app will now run as it would with the usual ``manage.py runserver`` but with live reloading and Sass compilation enabled.

To get live reloading to work you'll probably need to install an `appropriate browser extension`_

.. _appropriate browser extension: http://feedback.livereload.com/knowledgebase/articles/86242-how-do-i-install-and-use-the-browser-extensions-


Celery
^^^^^^
This app comes with Celery.

To run a celery worker:

.. code-block:: bash

    cd phoenix
    celery -A phoenix.taskapp worker -l info

Please note: For Celerys import magic to work, it is important *where* the celery commands are run. If you are in the same folder with *manage.py*, you should be right.


Email Server
^^^^^^^^^^^^

In development, it is often nice to be able to see emails that are being sent from your application. For this purpose,
a Grunt task exists to start an instance of `maildump`_ which is a local SMTP server with an online interface.

.. _maildump: https://github.com/ThiefMaster/maildump

Make sure you have nodejs installed, and then type the following::

    $ grunt start-email-server

This will start an email server. The project is setup to deliver to the email server by default. To view messages
that are sent by your application, open your browser to http://127.0.0.1:1080

To stop the email server::

    $ grunt stop-email-server

The email server listens on 127.0.0.1:1025