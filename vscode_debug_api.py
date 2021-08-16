from api.src.app import app

# with this file selected, run with debugging in vscode works
# it boots up the server like using the start.sh file
# which means you need to not run it in Docker, ie comment it out in docker-compose

# this file is here so its scoped to project root to make sure imports work
# python runtime doesnt have access to files outside the directory the file is running in
# so for api/wsgi.py, it wouldnt know about common, gamechangerml etc which breaks imports
# google python runtime (sys.path / PYTHONPATH) issues for more info

if __name__ == "__main__":
    app.run()
