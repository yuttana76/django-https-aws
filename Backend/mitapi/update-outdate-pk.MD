https://www.djangoproject.com/download/

>pip show django

>python manage.py test

## Update  django, Packages to new ver

>pip list

https://www.youtube.com/watch?v=8zDeeXZ8-X8
# List package is outdate version
>pip list -o

# Install package 
https://pypi.org/project/pip-upgrader/
>pip install pip-upgrader

# Start auto update
>pip-upgrade

# Manual update
>pip install -U setuptools

# which can automate many of the necessary code changes 
https://pypi.org/project/django-upgrade/
>pip install django-upgrade
>django-upgrade --target-version 5.2 --all-files

>django-upgrade --target-version 5.2 --all-files
>django-upgrade --target-version 5.2 models.py
>django-upgrade --target-version 5.2 urls.py


>git ls-files -z -- '*.py' | xargs -0r django-upgrade --target-version 5.2

# Create virtual env.
>python -m venv venv5
>source venv5/bin/activate
>deactivate



