import requests
import json,os
import datetime
from flask import Flask,send_file,request
from flask.ext.cache import Cache
from random import randint
from collections import OrderedDict


app = Flask(__name__)


@app.route('/')
def index():
    return "Yo, it's working!"


if __name__ == "__main__":
    app.run()

WORDNIK_URL = 'http://api.wordnik.com:80/v4/'
API_KEY = '6b7418187bd740d53c01975443c56826e52ec538526c7875f'
ALL_UPLOADED_FILE = OrderedDict()
cache = Cache(app, config={'CACHE_TYPE': 'simple'})


@cache.memoize(timeout=86400)
def get_auth_token():
    params = {
        'api_key': API_KEY,
        'password': 'jacksparrow'
    }

    response = requests.get(
        WORDNIK_URL + 'account.json/authenticate/raynaya', params=params)
    print(response.text)
    if response.status_code == 200:
        response = response.json()
        return response.get('token')
    # else:
    #   return json.dumps({'msg': 'Failed to get auth token'})


@cache.memoize(timeout=86400)
def get_word_list(url, params, headers):
    response = requests.get(url, params=params, headers=headers)
    print(response.text)
    if response.status_code != 200:
        return None

    return response.json()


@cache.memoize(timeout=604800)
@app.route('/get_usage/<word>', methods=['GET'])
def get_usage(word):
    word = word.lower()
    params = {
        'useCanonical': False,
        'api_key': '6b7418187bd740d53c01975443c56826e52ec538526c7875f'
    }
    try:
        # print(WORDNIK_URL + 'v4/word.json/{}/topExample'.format(word))
        response = requests.get(
            WORDNIK_URL + 'word.json/{}/topExample'.format(word), params=params)
        print(response.text)
        if response.status_code == 200:
            response = response.json()
            title = response.get('word')
            title = title.title()
            print(title)
            if not title:
                return json.dumps({'msg': 'Failed to get a word'})

            usage = response.get('text')
            if not usage:
                return json.dumps({'msg': 'Failed to get usage examples'})

            url = 'https://www.wordnik.com/words/{}'.format(word)

            payload = {

                'templates': [{
                    'title': 'Example',
                    'subtitle': usage,
                    'default_action': {
                        'type': 'web_url',
                        'url': url
                    },
                    'buttons': [
                        {
                            'title': 'Related Words',
                            'type': 'web_url',
                            'payload': url
                        }
                    ]
                }
                ]
            }
            return payload
        else:
            return None

    except Exception as e:
        print(e)
        return None


@app.route('/random_word/', methods=['GET'])
def random_word():
    auth_token = get_auth_token()
    if not auth_token:
        cache.delete_memoized(get_auth_token)
        return json.dumps({'msg': 'Failed to get auth token'})
    try:
        params = {
            'api_key': API_KEY
        }
        headers = {
            'auth_token': auth_token
        }
        wordList = get_word_list(
            WORDNIK_URL + 'wordList.json/wordbot/words', params, headers)

        if not wordList:
            return json.dumps({'msg': 'Failed to get wordList'})

        random_index = randint(0, len(wordList))
        word = wordList[random_index].get('word')

        params = {
            'limit': 1,
            'includeRelated': True,
            'sourceDictionaries': 'wiktionary',
            'useCanonical': False,
            'includeTags': False,
            'api_key': '6b7418187bd740d53c01975443c56826e52ec538526c7875f'
        }

        response = requests.get(
            WORDNIK_URL + 'word.json/{}/definitions'.format(word), params=params, headers=headers)
        if response.status_code != 200:
            return json.dumps({'msg': 'Failed to get wordDefinition'})

        response = response.json()
        meaning = response[0].get('text')
        partOfSpeech = response[0].get('partOfSpeech')

        url = 'https://www.wordnik.com/words/{}'.format(word)

        payload = {
            'data': {
                'type': 'carousel',
                'templates': [{
                        'title': '{}'.format(word.title()),
                        'subtitle': 'Definition: {}'.format(meaning),
                    'default_action': {
                            'type': 'web_url',
                            'url': url
                        },
                    'buttons': [{
                        "title": "See More",
                        "type": "postback",
                        "payload": "flow_B9BFF21F148E48B19808E517CE1FFBE2"
                    }
                    ]
                }
                ]
            }
        }
        usage_templates = get_usage(word)
        if usage_templates:
            payload['data']['templates'].extend(
                usage_templates['templates'])
        return json.dumps(payload)

    except Exception:
        return json.dumps({'msg': 'Failed to get a word'})


@app.route('/word_of_the_day/', methods=['GET'])
@cache.memoize(timeout=86400)
def word_of_the_day():
    # http://api.wordnik.com:80/v4/words.json/wordOfTheDay?date=2017-10-15&api_key=6b7418187bd740d53c01975443c56826e52ec538526c7875f
    params = {
        'date': datetime.datetime.today().strftime('%Y-%m-%d'),
        'api_key': '6b7418187bd740d53c01975443c56826e52ec538526c7875f'
    }
    try:
        response = requests.get(
            WORDNIK_URL + 'words.json/wordOfTheDay', params=params)
        print(response.text)
        if response.status_code == 200:
            response = response.json()
            title = response.get('word')
            title = title.title()
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

            note = response.get('note', '')
            partOfSpeech = definitions[0].get('partOfSpeech', '')
            url = 'https://www.wordnik.com/word-of-the-day'

            examples = response.get('examples',[])
            usage = ''
            for example in examples:
                usage = '{}\n - {}'.format(usage, example['text'])
           

            payload = {
                'data': {
                    'type': 'msg_options',
                    'text': 'Word Of the day : {}\n\nDefinition: {}\n\nPartOfSpeech: {}\n\nNote: {}\n\nHow to use{}'.format(title, meaning, partOfSpeech, note, usage),
                    'options' : [   
                    {
                        "text": "See a random word",
                        "postback": "flow_B9BFF21F148E48B19808E517CE1FFBE2"
                    }
                ]
                }
            }
            # if usage_templates:
            #     payload['data']['templates'].extend(
            #         usage_templates['templates'])

            return json.dumps(payload)
        else:
            return json.dumps({'msg': 'Failed to get a word'})
    except Exception:
        return json.dumps({'msg': 'Failed to get a word'}), 500

@app.route('/zoom_meeting', methods=['GET'])
def zoom_meeting():
    # http://api.wordnik.com:80/v4/words.json/wordOfTheDay?date=2017-10-15&api_key=6b7418187bd740d53c01975443c56826e52ec538526c7875f
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzTzgwTGRWSFNYYXV3WUNVZG9UZlZBIiwiZXhwIjoxNTI2NzAzNzA3fQ.DHBUT7TLooibGKPq421-E4WKqUqb1YTf3iNnN1KoAkY'
    }

    try:
        response = requests.get('https://api.zoom.us/v2/meetings/4564560909', headers=headers)
        print(response.text)
        if response.status_code == 200:
            response = response.json()
            join_url = response["join_url"]
            return json.dumps({"data": {"type": "carousel", "templates": [{"title": "Genius Bar", "image_url": "https://gm1.ggpht.com/jrqhyBQvj4rRLq06JfLxPtiEiBJ8lySzpzA-f01rUKXhbKmn6aYnDGwIZDUdcshZKSrXN_Jf_QEh7XrZgD1WhkkCgVXy4zEcok9Y4KAlIbgQasUGU0cyhUPHas0LrPyf0K4tVz9VQvOQhCwSXmLubRMyck_W0BigmCkkutR34fNO7Q0WBMA2hBVY7sTL4QLf84Z8httsXI3GNDx9RnnJ56fYAGSWpFjNhDhIt9SY-QcuA0HcyAsmLTMhGIhsVliXmurBLT2Xf3vZqrmeN7ozSMfbK8OxwseczKjuwvT2FCE1NsLw7ShKai6jCPNCkUMBa_M3vrFVVBDK0us9cVxC34HbTyDO_BH08hng2I_AjcTzDYZMGttWV7zF7IXEncwJQO9dOf5xLqwmFQNqp_b4KCx5irQCY9KyDiPV2BYbaFDQ49RYA2NtQhmfgxsk7KoA2gKjSknH452VUko9tp2sBdm5m--QOobaORD88Kx_htgezOMJQX3GFc5zwDua-rQ2eQlvCNvhCZnqQ0vYyRscy0MUeQKdWlRkfMiGW9JXlHSMS7Br_hD4Wa7XZ1pz8qEDwkUe1eLzjHvOoQPYft9xa8IkhxMQrhmV3EVf7AmwDs2-yT_rzIXIYsLjyWeam7kSCPy0_sU4bhzy4tjxFjsIOmPLNQ45p1Dwyn4-IeoWJZqNvbmFH_eDHdBG1AXqHw=w580-h228-l75-ft", "subtitle": "Connect instantly to Genius Bar by clicking the button below", "buttons": [ {"title": "Connect", "type": "web_url","payload": join_url}]}]}})
        else:
            return json.dumps({"data": {"type": "text", "text": "Please try again later!"}}), 500
    except Exception:
        return json.dumps({"data": {"type": "text", "text": "Please try again later!"}}), 500


@app.route('/message/<workflow>/<language>/', methods=['GET'])
@cache.memoize(timeout=86400)
def get_localize_mesasge(workflow,language):
    messages = {"WASL_POST_RESOLUTION":{"english":"Thank you for connecting with wasl Properties.\nDo you have any further queries?", "arabic":"شكرًا للتوصل مع الوصل العقاريه .\nهل من شئ اخر نستطيع مساعدتكم به ."}, "WASL_DEFAULT_FALLBACK":{"english":"We thank you for your patience. An agent will be with you shortly.", "arabic":"شكرأ لتواصلك مع وصل العقاريه ، سيقوم بالرد عليك احد موظيفنا بعد قليل ، الرجاء الانتظار"}, "WASL_HELLO":{"english":"Hello", "arabic":"مرحبا"}}
    fallback = {"WASL_POST_RESOLUTION":"We thank you for your patience. An agent will be with you shortly.", "WASL_DEFAULT_FALLBACK":"Thank you for connecting with wasl Properties.\nDo you have any further queries?", "WASL_HELLO": "Hello"}
    if messages.get(workflow):
        message = messages.get(workflow).get(language, fallback.get(workflow))
    else:
        message = "Something went wrong. Please try again or get in touch with the administrator" 
    return json.dumps({"data": {"type": "text", "text": message}},ensure_ascii=False), 200

@app.route('/upload-file/',methods=['PUT'])
def upload_file():
    try:
        if request.files and request.files.get("file"):
            file = request.files.get("file")
            if file.filename:
                file_path = os.path.join("/tmp/",file.filename)
                file.save(file_path)
                f = open(file_path)
                resp = ("File uploded successfully",200)
            else:
                resp = ("Invalid file format", 400)
        else:
            resp = ("parameter file is missing", 400)
    except Exception as e:
        print(
            "Unknown error while uploading-file request: {} , exception: {},".format(request.data, e))
        resp = ("Unknown error", 500)
    finally:
        if len(ALL_UPLOADED_FILE) >= 10:
            ALL_UPLOADED_FILE.popitem(last=False)
        ALL_UPLOADED_FILE.update({file.filename:f})
        return resp

@app.route('/download-file/<file_name>/',methods=['GET'])
def download_file(file_name):
    try:
        if ALL_UPLOADED_FILE.get(file_name):
            file = ALL_UPLOADED_FILE.get(file_name)
            resp = send_file(open(file.name), as_attachment=True)
        else:
            resp = ("File not found",400)
    except Exception as e:
        print("Unknown error while download-file file-name: {}, Exception: {}".format(file_name,e))
        resp = ("Unknown error",500)
    finally:
        return resp

@app.route('/waslresolution/<language>/', methods=['GET'])
@cache.memoize(timeout=86400)
def get_resolution_mesasge(language):
    WASL_POST_RESOLUTION_JSON_ENGLISH = {"data":{"type":"msg_options","text":"Thank you for connecting with wasl Properties.\nDo you have any further queries?","options":[{"text":"Yes","postback":"flow_4C050C077F1249C38CA71343DECA99C6||data_user_language=english"},{"text":"No thank you.","postback":"flow_554B615A8D8D4271A57E76F3F5CBEBD2||data_user_language=english"}]}}

    WASL_POST_RESOLUTION_JSON_ARABIC = {"data":{"type":"msg_options","text":"شكرًا للتوصل مع الوصل العقاريه.\nهل من شئ اخر نستطيع مساعدتكم به .","options":[{"text":"نعم","postback":"flow_5B83AB817E544CC6833B0CA89E4E74D1||data_user_language=arabic"},{"text":"لا شكرًا","postback":"flow_F54028C8555E4905B183D177A7403D41||data_user_language=arabic"}]}}

    if language == 'arabic':
         content = WASL_POST_RESOLUTION_JSON_ARABIC
    else:
        content = WASL_POST_RESOLUTION_JSON_ENGLISH
    return json.dumps(content, ensure_ascii=False), 200

@app.route('/setStream/', methods=['GET'])
def manipal_set_stream_and_redirect():
    stream = request.args.get("stream", "Allied Health")
    content = {
	"data": {
		"path_to_follow": "C68721F3E3A340D997C5938EF757C663"
	},
	"attributes": [{
		"name": "stream",
		"value": stream
	}]
     }
    return json.dumps(content, ensure_ascii=False), 200

@app.route('/redirectStream/', methods=['GET'])
def manipal_redirect():
    stream = request.args.get("stream", "Allied Health")
    stream_path_keys = {"Allied Health" : "EECDC320EE784CBFAC6E2DE603418194", "Architecture and Design" : "C98B744C49834D7FB3D57259CF73CFAE", "Arts and Humanities" : "2274C896F1BC463BA30A08B3946A120F", "Atomic and Molecular Physics" : "AA8675FC5FEB498C80BD24E501330ED1", "Basic and Advance Sciences" : "7BA370617BD24A9A8485707689490855", "Computer Applications" : "EF4C66C6CF7A499E8BD9AF223B58B4D4", "Dentistry" : "3ED9BA3BDDBD470399DB06CDAF9F4DEF", "Engineering" : "A73D1D8B050E445382D14E1033B5D161", "European Studies" : "A15F3F130B9041C39978FF28F97A9D3E", "European Studies and Foreign Languages" : "6A1B924E667A42AB8A3F03339B4A0567", "Geopolitics" : "A991671F34394D938583C1198B1B4FB9", "Hospitality" : "65BA0D7CA7DF4F0699886ABCBB03A6AF", "Hotel Management and Culinary Arts" : "ED1834B167734242BB717C447EABE979", "Information Science" : "880FC319E86D46388724DCC770AC9D7A", "Library Science" : "1B45B250D7F04EEC8F7C8F4BBBF64E29", "Life sciences" : "313B0336995B451FB679FC0F13DF3D84", "Management" : "413DB7DAFDA44513B008EABA7327177A", "Media and Communication" : "6CC68AA1AF164A16B1B2D89F91A6D953", "Medicine" : "9ECC6D0A248A476EB9CC481A895BD85B", "Nursing" : "99BA6B72B0534AE8B4E49BD0B2FDBB9B", "Pharmacy" : "7799EC8378F44FEE8C2E89E8AB3DA9A7", "Public Health" : "840D0C5E3CA742D6A435AFC68CFBC1E1", "Statistics" : "2512DA01F4D4770AAD1C16A0F1AFFF8", "Commerce" : "1B39E26333B2427CBC88F570E8E2B9A3"}
    flow_key = stream_path_keys.get(stream)    
    content = {"data": {"path_to_follow": flow_key}}
    return json.dumps(content, ensure_ascii=False), 200

@app.route('/clearContext/', methods=['GET'])
def manipal_clear_context():
    content = {"data": {}, "attributes": [{"name": "context_val", "value": "abcdef"}]}
    return json.dumps(content, ensure_ascii=False), 200

@app.route('/triggerDynamicFlow/', methods=['GET'])
def trigger_dynamic_flow():
    flow_key = request.args.get("flow_key", "")
    content = {"data": {"path_to_follow": flow_key}}
    return json.dumps(content, ensure_ascii=False), 200

@app.route('/cricInitializeUser/', methods=['GET'])
def crickbot_initialize_user():
    content = {"data": {}, "attributes": [{"name": "registered", "value": "1"}, {"name": "prediction_setup", "value": "1"}, {"name": "pref_follow", "value": "over"}, {"name": "pref_others", "value": "innings"}]}
    return json.dumps(content, ensure_ascii=False), 200

@app.route('/crickbot_groups', methods=['GET'])
def crickbot_groups():
    headers = {
        'Content-Type': 'application/json',
        'X-CrikBot-Security-key': '+JCie80eO02u7sU00OjqAg=='
    }
    user_id = request.args.get("user_id", "")
    if user_id == None:
        return json.dumps({"data": {"type": "text", "text": "User not found"}}), 200
    try:
        response = requests.get('http://dev-new-1424632230.ap-south-1.elb.amazonaws.com:8080/v1/user/listOfGroups?userId=' + user_id, headers=headers)
        if response.status_code == 200:
            response = response.json()
            responseObject = response['responseObject']
            print(responseObject)
            if len(responseObject) == 0:
            	return json.dumps({"data": {"type": "text", "text": "Uh oh! you aren't part of any groups 😞"}}), 200

            data = {}
            data['type'] = 'msg_options'
            data['text'] = 'These are the groups you are a part of. Select one to see the leaderboard'

            options = []
            for group in responseObject:
                option = {}
                option['text'] = group['groupNames']
                option['postback'] = 'flow_C50560D5E5F94F8EA5B65A6742A25AAB||data_leaderboard_group_id=' + group['groupIds']
                options.append(option)
            data['options'] = options
            return json.dumps({'data': data})
        else:
            return json.dumps({"data": {"type": "text", "text": "Please try again later!"}}), 500
    except Exception:
        return json.dumps({"data": {"type": "text", "text": "Please try again later!"}}), 500

@app.route('/crickbot_prediction', methods=['GET'])
def crickbot_prediction():
    headers = {
        'Content-Type': 'application/json',
        'X-CrikBot-Security-key': '+JCie80eO02u7sU00OjqAg=='
    }
    questionId = request.args.get("questionId", "")
    if questionId == None:
        return json.dumps({"data": {"type": "text", "text": "Invalid question"}}), 200
    try:
        response = requests.get('http://dev-new-1424632230.ap-south-1.elb.amazonaws.com:8080/v1/prediction/getPredictionQuestion?questionId=' + questionId, headers=headers)
        if response.status_code == 200:
            response = response.json()
            responseObject = response['responseObject']

            data = {}
            data['type'] = 'msg_options'
            data['text'] = responseObject['questionText']

            options = []
            predictionOptions = responseObject['predictionOptions']
            for opt in predictionOptions:
                option = {}
                option['text'] = opt['optionValue']
                option['postback'] = 'flow_660CCD6E62D54E9E805797416C399076||data_pred_resp_opt=' + opt['optionKey']
                options.append(option)
            data['options'] = options
            return json.dumps({'data': data})
        else:
            return json.dumps({"data": {"type": "text", "text": "Please try again later!"}}), 500
    except Exception:
        return json.dumps({"data": {"type": "text", "text": "Please try again later!"}}), 500

@app.route('/clearStoreEntity/', methods=['GET'])
def nouf_clear_store():

    entity_value = request.args.get("entity_value", "")    
    original_entity_value = request.args.get("original_entity_value", "")
    query_string = request.args.get("query_string", "")
    print('ev - ' + entity_value +  ' oev - ' + original_entity_value + ' qs - ' + query_string)
    content = {}
    if original_entity_value != "" and original_entity_value.lower() in query_string:
        content = {"data": {}, "attributes": [{"name": "resolved_store", "value": entity_value}]}
    else:
        content = {"data": {}, "attributes": [{"name": "resolved_store", "value": ""}]}
    print(JSON - json.dumps(content, ensure_ascii=False))	
    return json.dumps(content, ensure_ascii=False), 200
