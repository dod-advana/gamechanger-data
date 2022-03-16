export SERVER_NAME='localhost'

function send_email_notification() {
  local job_name="$1"
  local status="$2"
  local timestamp
  local to="${NOTIFICATION_EMAIL}"
  local sender='no-reply@data.mil'
  timestamp="$(date "+DATE: %Y-%m-%d TIME: %H:%M:%S")"
  local body="${job_name} ${status} at ${timestamp}"
  echo -e "GC NOTIFICATIONS-${job_name} ${status}\n${body}" | sendmail -f "${sender}" -t "${to}"
}