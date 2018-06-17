

import hmac
import hashlib
import datetime
import logging

secret_key = "&*GdkJDFy.fz&J9w"
class Authenticate():
    	
	# make a cookie for each visit
    # @classmethod
    # def make_cookie(cls,visit):		
    #     return cls.hash_function(visit)

    # # check hash function based on salt and number of visit
    # @classmethod
    # def check_cookie(cls,hash):
    #     h=hash.split('|')
    #     check = cls.hash_function(h[1][-1],h[1][:-1])
    #     if check.split('|')[0]==h[0]:
    #             return h[1][-1]
    #     else:
    #             return None
    # @classmethod               
    # def register(cls,username,pw,email,phone):	
    # 	q= User.query_username(username)
    #     user = q.get()
    #     # check if datastore if this username exist
    #     if user:
    #     	return False
    #     else:
    #         # register it this username is new
    #     	hash_pw=cls.hash_function(username+pw,salt="")
    #     	salt=hash_pw.split('|')[1][:12]
    #     	User(username=username,password=hash_pw.split('|')[0],salt=salt,email=email,phone=long(phone)).put()
    #     	return True

    @classmethod
    def check_user(cls,user,pw):
    	# q= User.query_username(username)
    	# user = q.get()
    	# if user:
        if user:
        	salt=user.salt
        	if salt:
        		hash_pw = cls.hash_function(pw,salt=salt)
        	    	if hash_pw.split('|')[0]==user.password:
        	    		logging.info('Log in successful')
        		        return True
        		else:
        			return False

        	# else:
        	# 	return False
    	

    # generate hash function from salt, visit and secret key visit=pw!
    @classmethod
    def hash_function(cls,visit,salt=""):
        if len(salt)==0:
            salt=cls.make_salt()
            logging.info("salt"+salt)
        h1 = hmac.new(secret_key,salt+visit).hexdigest()
        logging.info(h1[-6:])
        h2 = hashlib.sha1(h1[-6:]).hexdigest()
        return '%s|%s' % (h2,salt+visit)

 	# make a random number with millisecond time
    @classmethod
    def make_salt(cls):
        nTrial = 10
        # seed with time
        s='%s'% datetime.datetime.now()
        seed= long(filter(lambda c:c.isdigit(),s))
        # randomiser
        for x in range(nTrial):
            seed = long(cls.xorShift(seed))
        # get the first 6 and last 6 digits
        return str(seed)[:5] + str(seed)[-7:]
    @classmethod
    def xorShift(cls,y):
        y ^= (y << 6)
        y ^= (y >> 21)
        y ^= (y << 7)
        return y
