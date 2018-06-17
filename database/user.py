from google.appengine.api import memcache
from google.appengine.ext import ndb

from logic.Logic import Authenticate

# class User(ndb.Model):
# 	password = ndb.StringProperty(required=True)
# 	salt = ndb.StringProperty(required=True)
# 	email = ndb.StringProperty(required=True)
# 	phone = ndb.IntegerProperty(required=True)
# 	mobile_log_in=ndb.BooleanProperty(default=False)
# 	# favourites = db.StringArrayProperty()
# 	bike_owned=ndb.KeyProperty(kind='Bike')
	
# 	@classmethod
# 	def by_id(cls, uid):
# 	        return cls.get_by_id(uid)
# 	@classmethod
# 	def by_email(cls,query):
# 		#return db.GqlQuery('SELECT * FROM User WHERE username = :query',query=query)
# 		return cls.query(cls.email==query)

# 	@classmethod
# 	def login(cls, email, pw):
#         	u = cls.by_email(email)
# 	        if u and Authenticate.check_user(u.get(),pw):
# 			return u.get()

# 	@classmethod               
# 	def register(cls,pw,email,phone):	
# 	    	q= cls.by_email(email)
# 	        user = q.get()
# 	        # check if datastore if this username exist
# 	        if user:
# 	        	return None
# 	        else:
# 	            # register it this username is new
# 	        	hash_pw=Authenticate.hash_function(pw,salt="")
# 	        	salt=hash_pw.split('|')[1][:12]
# 	        	user=cls(password=hash_pw.split('|')[0],salt=salt,email=email,phone=long(phone))
# 	        	user.put()
# 	        	return user
import logging
class User(ndb.Model):
	#### Menu class 
	telegramID = ndb.StringProperty(required=True)
	firstname = ndb.StringProperty(required=True)
	lastname = ndb.StringProperty(required=True)
	busStopList = ndb.JsonProperty(default=[])

	@classmethod
	def by_telegramID(cls,query):
		return cls.query(cls.telegramID==query)

	def add_to_list(self,food):
		self.busStopList.append(food)
		return

	def remove_from_list(self,key):
		self.busStopList.remove(key)
		return
			

def users_key(group = 'default'):
    return db.Key.from_path('users', group)

