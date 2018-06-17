import webapp2
from main import BusStop, Alarm

config = {
  'webapp2_extras.auth': {
    'user_model': 'models.User',
    'user_attributes': ['name']
  },
  'webapp2_extras.sessions': {
    'secret_key': 'PORNTHIP_IS_AWESOME'
  }
}


app = webapp2.WSGIApplication([
  (r'/run_alarm', Alarm),
  (r'/?$', BusStop)
], debug=True, config = config)