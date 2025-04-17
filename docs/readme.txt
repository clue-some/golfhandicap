Development on Ubuntu.

To install all dependencies in a virtual environment
    > <venv> pip install -r requirements.txt

To run the web server in debug mode:
    > <venv> flask --app handicap run --debug

To access the db from python:
    > <venv> python3
  >>> from handicap import db, create_app; app = create_app(); ctx = app.app_context(); ctx.push();
  >>> from handicap.models import User, Score, NineHoleScore, IndexHistory
  >>> User.query.all()
  >>> ctx.pop(); exit()
