import os
from streamlit.web import bootstrap
os.environ["STREAMLIT_SERVER_PORT"] = "8501"
bootstrap.run("/home/NedeeshaW/mysite/app.py", "", [], [])