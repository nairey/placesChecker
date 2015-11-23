#!/usr/bin/env python

__author__ = "Nathan Airey"
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "Nathan Airey"
__email__ = "Nathan@eatnow.com.au"
__status__ = "Development"

#   TEST URLS
#
#  https://maps.googleapis.com/maps/api/place/radarsearch/json?location=-37.831403,144.956211&radius=2000&types=food|cafe|restaurant&keyword=Baked In South Melbourne+South Melbourne&key=AIzaSyDWo5YWnO6nu-92nf1C-_XhgPfse23N-SE
#  https://maps.googleapis.com/maps/api/place/details/json?placeid=ChIJy1sHif9n1moRhrYlgC8oeuk&key=AIzaSyDWo5YWnO6nu-92nf1C-_XhgPfse23N-SE
#
#
#


# import modules used here -- sys is a very standard one
import sys
import json
import requests
import csv
import unicodedata

# Gather our code in a main() function
def main():
	KEY = 'AIzaSyDWo5YWnO6nu-92nf1C-_XhgPfse23N-SE'
	RAD = '2000'

	job_status = None

	places = []

	#data  = open('places_data.csv', 'rU')
	data  = open('example.csv', 'rU')
	reader = csv.reader(data, delimiter=',', quotechar='"')

	rownum = 0
	for row in reader:
	    # Save header row.
	    if rownum == 0:
	    	header = row
	    else:
	    	colnum = 0
	    	place = Place()
	    	place.tr_id = row[0]
	    	place.restaurant_name = ''.join([x for x in row[1] if ord(x) < 128]) 
	    	place.street = ''.join([x for x in row[2] if ord(x) < 128]) 
	    	place.suburb = row[3]
	    	place.postcode = row[4]
	    	place.state = row[5]
	    	place.country = row[6]
	    	place.restaurant_website = row[7]
	    	place.gp_status = None
	    	place.gp_website_match = None
	    	place.error = None
	    	r_lat = None
	    	r_long = None
	    	place.num_places = 0

	    	print rownum, place.tr_id, place.restaurant_name

	    	# step 1 - find location coordinates using google mapping api
	    	location = api_location_coordinates(place.street, place.suburb, place.postcode, place.state, place.country, KEY)
	    	if location != 'error':
	    		r_lat, r_long = location['c_lat'], location['c_long']
	    		place.r_lat = r_lat

    		place.r_long = r_long

			# step 2 - do a radar search using the google maps api
	    	places_results = api_places_results(place.r_lat, place.r_long, place.restaurant_name, place.suburb, KEY, RAD)

	    	# step 3 - start looping through the places results
	    	if location != 'error':
	    		place.gp_status = places_results['status']

		    	num_places = 0
		    	gp_list = []
		    	for pr in places_results['results']:


					# step 3a - check each result for websites and add to a list.
					place_loc = api_places(pr["place_id"], KEY)
					
					gp = Gp()
					try:
						gp.id =  place_loc['result']['id']
					except Exception: 
	  					pass
					try:
						gp.website =  place_loc['result']['website']
					except Exception: 
	  					pass
	  				gp_list.append(gp)

					num_places += 1

		    	place.num_places = num_places

				# step 3b - check if the website matches the website provided in the original list
		    	if gp_list:
		    		for gp in gp_list:
		    			if place.restaurant_website and gp.website:
			    			if place.restaurant_website in gp.website:
			    				place.gp_website_match = "TRUE"
			    				break
			    			else:
								place.gp_website_match = "NO MATCH FOUND"
		    	else:
			    	place.error = "No website info found"

	    	places.append(place)
	    rownum += 1
	

	data.close()

	# step 4 - create a new csv of data.
	c = csv.writer(open("places_output.csv", "wb"))
	c.writerow(["tr_id","restaurant_name","street","suburb","postcode","state","country","restaurant_website","num_places","latitude","longitude","gp_status","gp_website_match","error"])

	for p in places:
		c.writerow([
			str(unicodedata.normalize('NFKD',unicode(p.tr_id)).encode('ascii','ignore')),
			str(unicodedata.normalize('NFKD',unicode(p.restaurant_name)).encode('ascii','ignore')),
			str(unicodedata.normalize('NFKD',unicode(p.street)).encode('ascii','ignore')),
			str(unicodedata.normalize('NFKD',unicode(p.suburb)).encode('ascii','ignore')),
			str(unicodedata.normalize('NFKD',unicode(p.postcode)).encode('ascii','ignore')),
			str(unicodedata.normalize('NFKD',unicode(p.state)).encode('ascii','ignore')),
			str(unicodedata.normalize('NFKD',unicode(p.country)).encode('ascii','ignore')),
			str(unicodedata.normalize('NFKD',unicode(p.restaurant_website)).encode('ascii','ignore')),
			str(unicodedata.normalize('NFKD',unicode(p.num_places)).encode('ascii','ignore')),
			str(unicodedata.normalize('NFKD',unicode(p.r_lat)).encode('ascii','ignore')),
			str(unicodedata.normalize('NFKD',unicode(p.r_long)).encode('ascii','ignore')),
			str(unicodedata.normalize('NFKD',unicode(p.gp_status)).encode('ascii','ignore')),
			str(unicodedata.normalize('NFKD',unicode(p.gp_website_match)).encode('ascii','ignore')),
			str(unicodedata.normalize('NFKD',unicode(p.error)).encode('ascii','ignore'))
		])	


# generic api request
def api_request(url):
	response = None
	try:
		url.replace(' ','+')
		req = requests.get(url)
		body = json.loads(req.content)
		response = body
	except Exception: 
		response = "error"
  		pass
	return response

def api_location_coordinates(street, suburb, postcode, state, country, KEY):
	location_url = 'https://maps.googleapis.com/maps/api/geocode/json?address=%(street)s+%(suburb)s+%(postcode)s+%(state)s+%(country)s&key=%(KEY)s' % locals()
	location = api_request(location_url)
	
	if (location != 'error') and (location['status'] == 'OK'):
		for loc in location['results']:
			c_lat = loc['geometry']['location']['lat']
			c_long = loc['geometry']['location']['lng']

			return {'c_lat':c_lat, 'c_long':c_long}
	else:
		return 'error'

def api_places_results(c_lat,c_long,restaurant,suburb, KEY, RAD):
	places_results_url = "https://maps.googleapis.com/maps/api/place/radarsearch/json?location=%(c_lat)s,%(c_long)s&radius=%(RAD)s&types=food|cafe|restaurant&keyword=%(restaurant)s+%(suburb)s&key=%(KEY)s" % locals()
	places_results = api_request(places_results_url)
	return places_results

def api_places(place_id, KEY):
	place_url = "https://maps.googleapis.com/maps/api/place/details/json?placeid=%(place_id)s&key=%(KEY)s" % locals()
	place = api_request(place_url)
	return place

class Place:
	tr_id = None
	restaurant_name = None
	street = None
	suburb = None
	postcode = None
	state = None
	country = None
	restaurant_website = None
	num_places = 0
	r_lat = None
	r_long = None
	gp_status = None
	gp_website_match = None
	error = None

class Gp:
	id = None
	website = None

# Standard boilerplate to call the main() function to begin
# the program.
if __name__ == '__main__':
    main()