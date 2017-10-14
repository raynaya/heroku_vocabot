from flask import Flask
import requests
import json

app = Flask(__name__)
@app.route('/')
def index():
	return "Yo, it's working!"
if __name__ == "__main__":
	app.run()

WORDNIK_URL='http://api.wordnik.com:80/v4/words.json/'
API_KEY = 'a2a73e7b926c924fad7001ca3111acd55af2ffabf50eb4ae5'

@app.route('/word_of_the_day/', methods=['GET'])
def word_of_the_day():
	#http://api.wordnik.com:80/v4/words.json/wordOfTheDay?date=2017-10-15&api_key=a2a73e7b926c924fad7001ca3111acd55af2ffabf50eb4ae5
	params={
		'date' : '2017-10-15',
		'api_key' : API_KEY
	}
	try:
		response = requests.get(WORDNIK_URL+'wordOfTheDay', params=params)
		print(response.text)
		if response.status_code == 200:
			response = response.json()
			title = response.get('word')
			print(title)
			if not title:
				return json.dumps({'msg': 'Failed to get a word'})

			definitions = response.get('definitions')
			if definitions:
				meaning = definitions[0].get('text')
				if not meaning:
					return json.dumps({'msg': 'Failed to get a meaning'})
			else:
				return json.dumps({'msg': 'Failed to get a definition'})
			print(meaning)

			note = response.get('note','')
			url = 'https://www.wordnik.com/word-of-the-day'

			payload  = {
				'data' : {
					'type':'carousel',
					 'templates' : [{
						'title' : title,
						'subtitle': meaning,
						'default_action' : {
							'type' : 'web_url',
							'url' : url
							}
						}
					]
				}
			}
			return json.dumps(payload)
		else:
			return json.dumps({'msg': 'Failed to get a word'})
	except Exception:
		return json.dumps({'msg': 'Failed to get a word'}),500