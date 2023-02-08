from seoanalyzer import analyze
import json
from flask import Flask, request, jsonify 
from flask_cors import CORS, cross_origin

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

@app.route('/get-url-info/', methods=['GET'])
@cross_origin()
def respond():
    query = request.args.get("q")
    output = analyze(query)
    return jsonify(output)

# json.dumps()

if __name__ =="__main__":
    app.run(port=5000)
