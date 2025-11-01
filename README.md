- To transfer files to remote server.
rsync -avP --exclude=".*/"  $(pwd) user@hostname:/home/debian/
- Crontab for scheduling.
/bin/bash -lc 'cd "$HOME/notion" && set -a; source .env; set +a && uv run main.py' >>"$HOME/notion/cron.log" 2>&1