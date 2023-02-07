from seoanalyzer import analyze
import json
from flask import Flask, request, jsonify 


app = Flask(__name__)

@app.route('/get-url-info/', methods=['GET'])
def respond():
    query = request.args.get("q")
    output = analyze(query)
    return jsonify(output)

# json.dumps()

if __name__ =="__main__":
    app.run(port=5000)