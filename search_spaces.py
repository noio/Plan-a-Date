import json
import urllib, pickle

API_KEY = "AIzaSyCDVMO3-PEsnU22lgvjp0ltnqMwW4R8TE4"
LOCATION = "Amsterdam"
LOCATION = {"lat" : 52.37021570, "lng" : 4.895167900000001}
LOCATION_GET = str(LOCATION['lat']) + ',' + str(LOCATION['lng'])
RADIUS = 10000

running = True

choice_file = open("choices.pkl", 'rb')
choices_so_far = pickle.load(choice_file)
print choices_so_far

# Pickle dictionary using protocol 0.
pickle.dump(data1, output)

if __name__ == "__main__":
	while(running):
	
		# TODO:Find out lat/lng of current location:
		#params = urllib.urlencode({'adress': LOCATION, 'sensor': 'false'})#, 'key': API_KEY})
		#f = urllib.urlopen("http://maps.googleapis.com/maps/api/geocode/json?%s" % params)

		term = raw_input('Search Google Pages for: ')
		#params = urllib.urlencode({'location': LOCATION['lat'] + ', ' + LOCATION['lng'], 'radius': RADIUS, 'name': term)
		params = urllib.urlencode({'radius': RADIUS, 'name': term, 'key': API_KEY, 'sensor': 'false'})
		url = "https://maps.googleapis.com/maps/api/place/search/json?location=%s&%s" % (LOCATION_GET, params)
		f = urllib.urlopen(url)

		results = json.loads(f.read())
		print "Found the following places:"

		for (i, result) in enumerate(results['results']):
			print "%d %s, %s" % (i+1,result['name'], result['vicinity'])

		choice = int(raw_input("Choose venue or 0 to try again (-1 to quit)")) + 1

		if(choice < 0):
			running = false
		elif(choice > 0):
			print choice
	
	
	#https://maps.googleapis.com/maps/api/place/search/json?location=52.3702157,4.8951679&radius=10000&name=test&key=AIzaSyCDVMO3-PEsnU22lgvjp0ltnqMwW4R8TE4
	#https://maps.googleapis.com/maps/api/place/search/json?location=-33.8670522,151.1957362&radius=500&types=food&name=harbour&sensor=false&key=AIzaSyCDVMO3-PEsnU22lgvjp0ltnqMwW4R8TE4